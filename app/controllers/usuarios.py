"""Gestión de usuarios (``users:manage``): solo campos públicos, nunca sal, hash ni índice ciego."""

from __future__ import annotations

from litestar import Controller, Request, get, post
from litestar.exceptions import HTTPException
from litestar.params import FromPath, JSONBody

from app.dependencies import AppState
from app.rbac_guards import require_permission
from app.schemas import CreateUserRequest, UsuarioPublic
from app.security import api_guard
from core.config import API_PREFIX
from core.context import UsuarioAduana


def _public(user: UsuarioAduana) -> UsuarioPublic:
    return UsuarioPublic(
        codigo_usuario=user.codigo_usuario,
        rol=user.rol,
        estado=user.estado,
        created_utc=user.created_utc,
        last_login_utc=user.last_login_utc,
    )


class UsuariosController(Controller):
    path = f"{API_PREFIX}/usuarios"
    guards = [api_guard, require_permission("users:manage")]

    @get("/", sync_to_thread=True)
    def list_users(self, request: Request) -> list[UsuarioPublic]:
        state: AppState = request.app.state.aduana
        return [_public(u) for u in state.identity.list_users()]  # type: ignore[union-attr]

    @post("/", sync_to_thread=True)  # PBKDF2: fuera del event loop
    def create_user(self, request: Request, data: JSONBody[CreateUserRequest]) -> UsuarioPublic:
        state: AppState = request.app.state.aduana
        try:
            user = state.identity.create_user(  # type: ignore[union-attr]
                codigo_usuario=data.codigo_usuario,
                identificador=data.identificador,
                rol=data.rol,
                password=data.password,
            )
        except ValueError as exc:  # identificador con formato inválido (sin eco)
            raise HTTPException(status_code=422, detail="ERR_INVALID_IDENTIFIER") from exc
        return _public(user)

    @post("/{codigo:str}/suspender", status_code=200, sync_to_thread=True)
    def suspend(self, request: Request, codigo: FromPath[str]) -> UsuarioPublic:
        state: AppState = request.app.state.aduana
        identity = state.identity
        target = next((u for u in identity.list_users() if u.codigo_usuario == codigo), None)  # type: ignore[union-attr]
        if target is None:
            raise HTTPException(status_code=404, detail="ERR_NOT_FOUND")
        return _public(identity.suspend_user(target.user_id))  # type: ignore[union-attr]
