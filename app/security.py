"""Guard de API: token por proceso (``X-Aduana-Token``) + Content-Type JSON estricto.

El header personalizado fuerza preflight CORS (anula CSRF "simple") y el 415 evita que un
``text/plain`` cruzado llegue al parser. ``/health`` y los estáticos quedan fuera.
"""

from __future__ import annotations

import secrets
from typing import Final

from litestar.connection import ASGIConnection
from litestar.exceptions import HTTPException, NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler

TOKEN_HEADER: Final[str] = "x-aduana-token"  # noqa: S105 (nombre de cabecera HTTP)
_BODY_METHODS: Final[frozenset[str]] = frozenset({"POST", "PUT", "PATCH"})


def api_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    expected: str = connection.app.state.aduana.api_token
    supplied = connection.headers.get(TOKEN_HEADER, "")
    if not secrets.compare_digest(supplied.encode(), expected.encode()):
        raise NotAuthorizedException(detail="UNAUTHORIZED")
    if connection.scope["method"] in _BODY_METHODS:
        content_type = connection.headers.get("content-type", "").split(";")[0].strip().lower()
        if content_type != "application/json":
            raise HTTPException(status_code=415, detail="UNSUPPORTED_MEDIA_TYPE")
