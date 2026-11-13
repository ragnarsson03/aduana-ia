"""Aplicación de escritorio: Litestar (Granian, 1 worker) + ventana nativa PyWebView.

Puerto efímero libre, token por sesión inyectado a la ventana (no en la URL), ventana en modo
privado (sin autofill ni caché persistentes). SIN VERIFICAR: Granian en hilo y webview no
se han ejecutado todavía (Gatillo 7).
"""

from __future__ import annotations

import json
import os
import secrets
import socket
import tempfile
import threading
import time
import urllib.request

READY_TIMEOUT_S = 15.0


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _serve(port: int) -> None:
    from granian import Granian

    Granian(
        "app.server:create_app",
        interface="asgi",
        factory=True,
        workers=1,
        address="127.0.0.1",
        port=port,
    ).serve()


def _wait_ready(port: int) -> None:
    url = f"http://127.0.0.1:{port}/api/v1/health/system"
    deadline = time.monotonic() + READY_TIMEOUT_S
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):  # noqa: S310 (loopback fijo)
                return
        except OSError:
            time.sleep(0.2)
    raise TimeoutError("El servidor local no arrancó a tiempo.")


def main() -> None:
    import webview  # import perezoso: el servidor no depende de pywebview

    port = _free_port()
    token = secrets.token_urlsafe(32)
    os.environ["ADUANA_PORT"] = str(port)
    os.environ["ADUANA_API_TOKEN"] = token
    threading.Thread(target=_serve, args=(port,), daemon=True).start()
    _wait_ready(port)

    window = webview.create_window("Aduana IA — Perímetro Soberano", f"http://127.0.0.1:{port}")
    window.events.loaded += lambda: window.evaluate_js(f"window.__ADUANA_TOKEN__={json.dumps(token)}")
    with tempfile.TemporaryDirectory(prefix="aduana-wv-") as storage:
        webview.start(private_mode=True, storage_path=storage, debug=False)


if __name__ == "__main__":
    main()
