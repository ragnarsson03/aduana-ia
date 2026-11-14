"""Guards de permiso por rol (RBAC aduanero, specs/06 §4). Solo actúan con ``rbac_enabled``.

Orden: ``api_guard`` (X-Aduana-Token) -> guard de permiso. El usuario se resuelve contra la BD en
cada petición (Zero-Trust) y se guarda en ``scope['aduana_user']``. Los errores son de dominio y
``server._ERROR_TABLE`` los mapea a códigos estables sin eco de datos.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

from litestar import Request
from litestar.connection import ASGIConnection
from litestar.exceptions import HTTPException
from litestar.handlers.base import BaseRouteHandler

from core.context import AduanaRoleType, UsuarioAduana
from core.errors import AuthenticationError
from core.identity import AUTH_ERROR_MESSAGE
from core.rbac import Permission

SCOPE_USER_KEY: Final[str] = "aduana_user"
_BEARER_SCHEME: Final[str] = "bearer"
_DEMO_COOKIE_NAME: Final[str] = "aduana_session"
_DEMO_ROLE_TO_ADUANA: Final[dict[str, AduanaRoleType]] = {
    "administrador": "SUPERVISOR_PUERTO_ADUANERO",
    "auditor": "INSPECTOR_TRIBUTARIO_SENIAT",
    "analista": "ANALISTA_VALORACION_ADUANERA",
}

Guard = Callable[[ASGIConnection, BaseRouteHandler], None]


def _extract_demo_token(connection: ASGIConnection) -> str:
    header = connection.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    token = token.strip()
    if scheme.lower() == _BEARER_SCHEME and token:
        return token
    cookie_token = connection.cookies.get(_DEMO_COOKIE_NAME, "").strip()
    if cookie_token:
        return cookie_token
    raise AuthenticationError(AUTH_ERROR_MESSAGE)


def extract_bearer(connection: ASGIConnection) -> str:
    header = connection.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    token = token.strip()
    if scheme.lower() != _BEARER_SCHEME or not token:
        raise AuthenticationError(AUTH_ERROR_MESSAGE)
    return token


def authenticate(connection: ASGIConnection) -> UsuarioAduana | None:
    """Resuelve y cachea el usuario del Bearer; ``None`` si RBAC está apagado."""
    state = connection.app.state.aduana
    if not state.settings.rbac_enabled or state.identity is None:
        return None
    cached = connection.scope.get(SCOPE_USER_KEY)
    if cached is not None:
        return cached
    if state.settings.demo_mode:
        token = _extract_demo_token(connection)
        if token.startswith("v1."):
            user = state.identity.resolve_token(token)
        else:
            entry = state.session_store.validate_jwt(state.keys, token)
            if entry is None:
                raise AuthenticationError(AUTH_ERROR_MESSAGE)
            demo_user = state.auth_repo.find_active_by_id(entry.user_id)
            if demo_user is None:
                raise AuthenticationError(AUTH_ERROR_MESSAGE)
            aduana_role = _DEMO_ROLE_TO_ADUANA.get(demo_user.role, "ANALISTA_VALORACION_ADUANERA")
            user = UsuarioAduana(
                user_id=demo_user.id,
                codigo_usuario=demo_user.username,
                blind_identifier=demo_user.id,
                rol=aduana_role,
                estado="ACTIVO",
                created_utc="",
            )
    else:
        user = state.identity.resolve_token(extract_bearer(connection))
    connection.scope[SCOPE_USER_KEY] = user  # type: ignore[typeddict-unknown-key]
    return user


def require_any_permission(*permissions: Permission) -> Guard:
    """Guard que exige al menos uno de los permisos (Bearer válido + usuario ACTIVO)."""

    def guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
        user = authenticate(connection)
        if user is None:
            return
        state = connection.app.state.aduana
        denied: Exception | None = None
        for permission in permissions:
            try:
                state.identity.authorize(user, permission)
                return
            except Exception as exc:  # AuthorizationError: probar el siguiente permiso
                denied = exc
        if denied is not None:
            raise denied

    return guard


def require_permission(permission: Permission) -> Guard:
    return require_any_permission(permission)


def require_authenticated(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Cualquier usuario activo (p. ej. ``GET /auth/me``)."""
    authenticate(connection)


def provide_current_user(request: Request) -> UsuarioAduana:
    """Dependencia ``current_user``: lee lo que dejó el guard (solo rutas con RBAC)."""
    user = request.scope.get(SCOPE_USER_KEY)
    if user is None:
        if not request.app.state.aduana.settings.rbac_enabled:
            raise HTTPException(status_code=503, detail="RBAC_DISABLED")
        raise AuthenticationError(AUTH_ERROR_MESSAGE)
    return user
