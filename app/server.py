"""Servidor Litestar: API /api/v1/* + estáticos locales offline-first.

Sin efectos de import: la app se crea con ``create_app`` (Granian ``factory=True``, ``workers=1``:
bóveda, llaves y rate-guard viven en un único proceso).
"""

from __future__ import annotations

import logging
from typing import Final

from litestar import Litestar, Request, Response
from litestar.config.allowed_hosts import AllowedHostsConfig
from litestar.datastructures import State
from litestar.exceptions import HTTPException
from litestar.middleware import DefineMiddleware
from litestar.static_files import create_static_files_router

from app.controllers.audit import AuditController
from app.controllers.auth import AuthController
from app.controllers.explica import ExplicaController
from app.controllers.gateway import GatewayController, ShieldController
from app.controllers.health import HealthController
from app.controllers.ledger import DemoLedgerController, LedgerController, ReceiptController
from app.controllers.metrics import MetricsController
from app.controllers.usuarios import UsuariosController
from app.dependencies import AppState, build_state
from app.headers_middleware import security_headers_middleware
from core.config import (
    MAX_BODY_BYTES,
    Settings,
    load_api_token_from_env,
    load_keys_from_env,
)
from core.errors import (
    AccountLockedError,
    AduanaError,
    AuthenticationError,
    AuthorizationError,
    ConsentError,
    DuplicateUserError,
    ImmutableLedgerError,
    InvalidFeaturesError,
    LLMUnavailableError,
    OverrideJustificationError,
    RateLimitError,
    ShieldResidualPiiError,
    WeakPasswordError,
)
from core.keyring import KeyRing

logger = logging.getLogger("aduana")

SECURITY_HEADERS: Final[dict[str, str]] = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; "
        "frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cache-Control": "no-store",
}

# Códigos estables; jamás el nombre de clase interno ni contenido ciudadano.
_ERROR_TABLE: Final[dict[type[AduanaError], tuple[int, str]]] = {
    ConsentError: (403, "ERR_CONSENT_REQUIRED"),
    RateLimitError: (429, "ERR_RATE_LIMIT"),
    ImmutableLedgerError: (409, "ERR_IMMUTABLE_LEDGER"),
    OverrideJustificationError: (422, "ERR_OVERRIDE_JUSTIFICATION"),
    InvalidFeaturesError: (422, "ERR_INVALID_FEATURES"),
    ShieldResidualPiiError: (422, "ERR_UNSAFE_INPUT"),
    LLMUnavailableError: (503, "ERR_LLM_UNAVAILABLE"),
    AuthenticationError: (401, "ERR_AUTH_INVALID"),
    AuthorizationError: (403, "ERR_FORBIDDEN"),
    AccountLockedError: (423, "ERR_ACCOUNT_LOCKED"),
    WeakPasswordError: (422, "ERR_WEAK_PASSWORD"),
    DuplicateUserError: (409, "ERR_USER_EXISTS"),
}


_NOT_FOUND_CODE: Final[str] = "ERR_NOT_FOUND"  # 404 intencional de handlers RBAC (sin eco)


def _domain_error_handler(_: Request, exc: AduanaError) -> Response[dict[str, str]]:
    status, code = next(
        (_ERROR_TABLE[cls] for cls in type(exc).__mro__ if cls in _ERROR_TABLE),
        (500, "ERR_INTERNAL"),
    )  # MRO: InvalidTokenError hereda el mapeo de AuthenticationError
    headers = {"Retry-After": "60"} if status == 429 else None
    return Response({"error": code}, status_code=status, headers=headers)


def _unhandled_error_handler(_: Request, exc: Exception) -> Response[dict[str, str]]:
    if isinstance(exc, HTTPException):  # 4xx/5xx intencionales
        detail = str(exc.detail)
        if exc.status_code == 404 and detail != _NOT_FOUND_CODE:
            detail = "NOT_FOUND"
        return Response({"error": detail}, status_code=exc.status_code)
    logger.error("unhandled_error type=%s", type(exc).__name__)  # sin traza ni cuerpo
    return Response({"error": "INTERNAL_ERROR"}, status_code=500)


def _shutdown_handler(app: Litestar) -> None:
    state: AppState = app.state.aduana
    state.vault.zeroize_all()
    state.repo.close()
    if state.identity is not None:
        state.identity.close()
    if state.users_repo is not None:
        state.users_repo.close()


def create_app(
    settings: Settings | None = None,
    keys: KeyRing | None = None,
    api_token: str | None = None,
) -> Litestar:
    settings = settings or Settings.from_env()  # antes que load_keys (lee ADUANA_MASTER_KEY)
    keys = keys or load_keys_from_env()
    api_token = api_token or load_api_token_from_env()
    state = build_state(settings, keys, api_token)
    static_dir = settings.static_dir
    static_dir.mkdir(parents=True, exist_ok=True)

    handlers: list = [
        HealthController,
        AuthController,
        GatewayController,
        ShieldController,
        LedgerController,
        MetricsController,
        create_static_files_router(path="/", directories=[static_dir], html_mode=True),
    ]
    if settings.rbac_enabled:
        handlers.extend(
            [
                UsuariosController,
                ExplicaController,
                AuditController,
                ReceiptController,
            ]
        )
    if settings.demo_mode:
        handlers.append(DemoLedgerController)

    allowed_hosts = [
        candidate
        for host in settings.allowed_hosts
        for candidate in (host, f"{host}:{settings.port}")
    ]
    return Litestar(
        route_handlers=handlers,
        exception_handlers={
            AduanaError: _domain_error_handler,
            Exception: _unhandled_error_handler,
        },
        allowed_hosts=AllowedHostsConfig(allowed_hosts=allowed_hosts),
        response_headers=SECURITY_HEADERS,
        # Los estáticos (/ y /assets) y los 404 no pasan por response_headers: sin esto salían
        # sin CSP justo en la página que ejecuta el JavaScript.
        middleware=[DefineMiddleware(security_headers_middleware, headers=SECURITY_HEADERS)],
        request_max_body_size=MAX_BODY_BYTES,
        state=State({"aduana": state}),
        on_shutdown=[_shutdown_handler],
        openapi_config=None,  # la UI de /schema carga JS de CDNs: viola Air-Gapped (RNF-04)
        debug=False,
    )


def main() -> None:
    from granian import Granian

    settings = Settings.from_env()
    Granian(
        "app.server:create_app",
        interface="asgi",
        factory=True,
        workers=1,
        address=settings.host,
        port=settings.port,
    ).serve()


if __name__ == "__main__":
    main()
