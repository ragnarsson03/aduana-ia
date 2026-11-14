"""Aplicación de escritorio: Litestar (Granian, 1 worker) + ventana nativa PyWebView.

Ejecuta Granian en un subproceso dedicado de proceso único (compatible con ``signal.signal`` y
``multiprocessing.freeze_support()`` para PyInstaller), en puerto efímero libre, inyectando el
token por sesión a la ventana vía ``evaluate_js`` (nunca en la URL) y con ``private_mode=True``.
"""

from __future__ import annotations

import json
import multiprocessing
import os
import secrets
import socket
import tempfile
import time
import urllib.request
from typing import Any

READY_TIMEOUT_S = 15.0


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _serve(port: int, token: str | None = None) -> None:
    from granian import Granian

    os.environ["ADUANA_PORT"] = str(port)
    if token is not None:
        os.environ["ADUANA_API_TOKEN"] = token

    class _SingleProcessGranian(Granian):
        """Ejecuta el worker ASGI en este mismo subproceso (sin nietos huérfanos al cerrar)."""

        def _serve(self, spawn_target: Any, target_loader: Any) -> None:
            if hasattr(self, "_spawn_proc"):
                # Granian 1.x
                sock = self.startup(spawn_target, target_loader)
                worker = self._spawn_proc(
                    idx=0,
                    target=spawn_target,
                    callback_loader=target_loader,
                    socket_loader=lambda: sock,
                )
                spawn_target(*worker.proc._args)  # noqa: SLF001
            else:
                # Granian 2.x
                self.startup(spawn_target, target_loader)
                worker = self._spawn_worker(
                    idx=0,
                    target=spawn_target,
                    callback_loader=target_loader,
                )
                proc_obj = getattr(worker, "inner", getattr(worker, "proc", None))
                if proc_obj is not None:
                    proc_obj._target(*proc_obj._args)  # noqa: SLF001

        def _spawn_workers(self, *args: Any, **kwargs: Any) -> None:
            return

    _SingleProcessGranian(
        "app.server:create_app",
        interface="asgi",
        factory=True,
        workers=1,
        address="127.0.0.1",
        port=port,
    ).serve()


def start_server_process(port: int, token: str) -> multiprocessing.Process:
    proc = multiprocessing.Process(
        target=_serve,
        args=(port, token),
        name="aduana-granian-desktop",
        daemon=True,
    )
    proc.start()
    return proc


def stop_server_process(proc: multiprocessing.Process, timeout_s: float = 5.0) -> None:
    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=timeout_s)
    if proc.is_alive():
        proc.kill()
        proc.join(timeout=1.0)


def _wait_ready(port: int) -> None:
    url = f"http://127.0.0.1:{port}/api/v1/health/system"
    deadline = time.monotonic() + READY_TIMEOUT_S
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):  # noqa: S310 (loopback fijo)
                return
        except OSError:
            time.sleep(0.15)
    raise TimeoutError("El servidor local no arrancó a tiempo.")


def main() -> None:
    multiprocessing.freeze_support()
    import webview  # import perezoso: el servidor no depende de pywebview

    from app.rbac_bootstrap import prepare_rbac_environment

    prepare_rbac_environment()  # llave persistente + ADUANA_RBAC=1 + usuarios sembrados (1.ª vez)
    port = _free_port()
    token = secrets.token_urlsafe(32)
    proc = start_server_process(port, token)
    os.environ.pop("ADUANA_MASTER_KEY", None)  # el hijo ya heredó la llave; el padre no la retiene
    try:
        _wait_ready(port)
        window = webview.create_window(
            "Aduana IA — Perímetro Soberano",
            f"http://127.0.0.1:{port}",
        )
        window.events.loaded += lambda: window.evaluate_js(
            f"window.__ADUANA_TOKEN__={json.dumps(token)}"
        )
        with tempfile.TemporaryDirectory(prefix="aduana-wv-") as storage:
            webview.start(private_mode=True, storage_path=storage, debug=False)
    finally:
        stop_server_process(proc)


if __name__ == "__main__":
    main()
