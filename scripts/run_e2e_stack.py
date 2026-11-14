"""Run the real ASGI application on loopback with disposable, synthetic-only storage."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from types import FrameType

import httpx

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOKEN = "e2e-token-" + "0" * 32
TEST_MASTER_KEY = bytes(range(32)).hex()


def server_command(port: int) -> tuple[str, list[str]]:
    target = "app.server:create_app"
    if importlib.util.find_spec("granian") is not None:
        return "granian", [
            sys.executable, "-m", "granian", target, "--interface", "asgi", "--factory",
            "--workers", "1", "--host", "127.0.0.1", "--port", str(port),
            "--no-access-log", "--log-level", "error",
        ]
    if importlib.util.find_spec("uvicorn") is not None:
        return "uvicorn", [
            sys.executable, "-m", "uvicorn", target, "--factory", "--workers", "1",
            "--host", "127.0.0.1", "--port", str(port), "--no-access-log", "--log-level", "error",
        ]
    raise RuntimeError("Install Granian or uvicorn in the selected Python environment")


def stop_server(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT)
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        # Reap descendants too if the ASGI supervisor cannot stop its worker.
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
            )
        else:
            process.kill()
        process.wait(timeout=5)
        raise RuntimeError("ASGI server exceeded graceful shutdown deadline")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token", default=DEFAULT_TOKEN, help="Fixed local test token (>=32 characters)")
    parser.add_argument("--duration", type=float, help="Seconds after readiness before clean shutdown")
    parser.add_argument("--static-dir", type=Path, default=ROOT / "static")
    args = parser.parse_args()
    if len(args.token) < 32 or (args.duration is not None and args.duration <= 0):
        parser.error("token must have >=32 characters; duration must be positive")
    static_dir = args.static_dir.resolve()
    if not static_dir.is_relative_to(ROOT) or not (static_dir / "index.html").is_file():
        parser.error("static-dir must contain index.html and be inside this worktree")

    stopped = threading.Event()

    def on_signal(_signum: int, _frame: FrameType | None) -> None:
        stopped.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, on_signal)
    if os.name == "nt":
        signal.signal(signal.SIGBREAK, on_signal)

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = int(sock.getsockname()[1])
    backend, command = server_command(port)
    print(f"e2e backend: {backend}", file=sys.stderr, flush=True)
    # Keep all writes inside the allowed harness area, never data/ledger.db.
    with tempfile.TemporaryDirectory(prefix="live-stack-", dir=ROOT / "tests/e2e_harness") as directory:
        db_path = Path(directory) / "ledger.db"
        env = {
            **os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1",
            "ADUANA_API_TOKEN": args.token, "ADUANA_MASTER_KEY": TEST_MASTER_KEY,
            "ADUANA_DEMO_MODE": "1", "ADUANA_DB_PATH": str(db_path),
            "ADUANA_STATIC_DIR": str(static_dir), "ADUANA_HOST": "127.0.0.1",
            "ADUANA_PORT": str(port), "ADUANA_ALLOW_REMOTE": "0",
            "ADUANA_RATE_LIMIT_PER_MINUTE": "600",
        }
        process = subprocess.Popen(
            command, cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
        url = f"http://127.0.0.1:{port}"
        try:
            deadline = time.monotonic() + 30
            with httpx.Client(timeout=0.5, trust_env=False) as client:
                while not stopped.is_set():
                    if process.poll() is not None:
                        raise RuntimeError("ASGI server exited before readiness; output redacted")
                    try:
                        health = client.get(f"{url}/api/v1/health/system")
                        if health.status_code == 200 and health.json().get("status") == "ok":
                            break
                    except (httpx.HTTPError, ValueError):
                        pass
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Timed out waiting for backend health; output redacted")
                    stopped.wait(0.1)
                else:
                    return 0
            print(json.dumps({
                "url": url, "token": args.token, "db_path": str(db_path), "pid": process.pid,
            }), flush=True)
            expires = None if args.duration is None else time.monotonic() + args.duration
            while not stopped.wait(0.1):
                if process.poll() is not None:
                    raise RuntimeError("ASGI server exited unexpectedly; output redacted")
                if expires is not None and time.monotonic() >= expires:
                    break
        finally:
            stop_server(process)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None
