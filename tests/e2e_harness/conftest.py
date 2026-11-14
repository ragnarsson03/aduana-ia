from __future__ import annotations

import json
import os
import queue
import signal
import subprocess
import sys
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class LiveStack:
    url: str
    token: str = field(repr=False)
    db_path: Path
    pid: int


@pytest.fixture(scope="session")
def live_stack() -> Iterator[LiveStack]:
    env = {**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"}
    process = subprocess.Popen(  # noqa: S603
        [sys.executable, str(ROOT / "scripts/run_e2e_stack.py"), "--duration", "180"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
    )
    lines: queue.Queue[str] = queue.Queue()

    def read_startup() -> None:
        assert process.stdout is not None
        lines.put(process.stdout.readline())

    threading.Thread(target=read_startup, daemon=True).start()
    try:
        try:
            line = lines.get(timeout=40)
            info = json.loads(line)
        except (queue.Empty, ValueError):
            pytest.fail("Live stack did not produce readiness JSON; backend output redacted")
        yield LiveStack(info["url"], info["token"], Path(info["db_path"]), info["pid"])
    finally:
        if process.poll() is None:
            process.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT)
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
                pytest.fail("Harness failed to shut down within 20 seconds")
        if process.stdout is not None:
            process.stdout.close()
        assert process.returncode == 0, "Harness did not shut down cleanly; output redacted"


@pytest.fixture
def live_http(live_stack: LiveStack) -> Iterator[httpx.Client]:
    with httpx.Client(
        base_url=live_stack.url,
        headers={"X-Aduana-Token": live_stack.token},
        timeout=10,
        trust_env=False,
        follow_redirects=False,
    ) as client:
        yield client
