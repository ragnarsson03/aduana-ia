"""Controladores REST agrupados por dominio."""

from __future__ import annotations

from litestar.exceptions import HTTPException


def pending(detail: str) -> HTTPException:
    """501 para endpoints cuyo gatillo SDD aún no se implementa."""
    return HTTPException(status_code=501, detail=detail)
