"""POST /api/v1/auth/login y GET /api/v1/auth/me (solo con RBAC activo)."""

from __future__ import annotations

from litestar import Controller, Request, get, post
from litestar.di import NamedDependency, Provide
from litestar.params import JSONBody

from app.dependencies import AppState
from app.rbac_guards import provide_current_user, require_authenticated
from app.schemas import LoginRequest, LoginResponse, MeResponse
from app.security import api_guard
from core.config import API_PREFIX
from core.context import UsuarioAduana
from core.rbac import permissions_of


class AuthController(Controller):
    path = f"{API_PREFIX}/auth"
    guards = [api_guard]
    dependencies = {"current_user": Provide(provide_current_user, sync_to_thread=False)}

    @post("/login", status_code=200, sync_to_thread=True)  # PBKDF2: fuera del event loop
    def login(self, request: Request, data: JSONBody[LoginRequest]) -> LoginResponse:
        state: AppState = request.app.state.aduana
        token = state.identity.login(data.identificador, data.password)  # type: ignore[union-attr]
        return LoginResponse(
            token=token.token,
            codigo_usuario=token.codigo_usuario,
            rol=token.rol,
            expires_at=token.expires_at,
        )

    @get("/me", guards=[require_authenticated], sync_to_thread=False)
    def me(self, current_user: NamedDependency[UsuarioAduana]) -> MeResponse:
        return MeResponse(
            codigo_usuario=current_user.codigo_usuario,
            rol=current_user.rol,
            permisos=sorted(permissions_of(current_user.rol)),
        )
