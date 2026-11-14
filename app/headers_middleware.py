"""Middleware ASGI que añade las cabeceras de seguridad a TODA respuesta HTTP.

``Litestar(response_headers=...)`` solo alcanza a los manejadores de la API: los archivos
estáticos (``/``, ``/assets/*``) y los 404 salían sin CSP, ``nosniff`` ni ``no-store``, justo
la página que ejecuta el JavaScript. Este middleware envuelve la aplicación completa.
Nunca pisa una cabecera que el manejador ya haya fijado.
"""

from __future__ import annotations

from collections.abc import Mapping

from litestar.datastructures import MutableScopeHeaders
from litestar.types import ASGIApp, Message, Receive, Scope, Send


def security_headers_middleware(app: ASGIApp, headers: Mapping[str, str]) -> ASGIApp:
    """Devuelve una app ASGI que inyecta ``headers`` en cada ``http.response.start``."""

    async def middleware(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = MutableScopeHeaders.from_message(message)
                for name, value in headers.items():
                    if name not in response_headers:
                        response_headers[name] = value
            await send(message)

        await app(scope, receive, send_with_headers)

    return middleware
