"""Login único (RBAC aduanero): ``POST /auth/login``, ``POST /auth/logout`` y ``GET /auth/me``.

Un solo sistema de identidad (``core.identity``): PBKDF2 con sal por usuario, bloqueo por intentos,
error uniforme y relectura del usuario en cada petición. Esta capa añade la auditoría en el ledger
y la revocación de sesión (logout).

Auditoría: solo se sellan login exitoso y logout. Los intentos fallidos NO se sellan: cualquiera
sin credenciales podría inflar el ledger inmutable y el coste extra de sellar solo para cuentas
existentes delataría cuáles existen. El sujeto sellado es un id opaco por usuario (HMAC del
``user_id``), nunca el índice ciego de la cédula, para no correlacionar funcionarios con ciudadanos.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from litestar import Controller, Request, get, post
from litestar.di import NamedDependency, Provide
from litestar.exceptions import HTTPException
from litestar.params import JSONBody

from app.dependencies import AppState
from app.rbac_guards import extract_bearer, provide_current_user, require_authenticated
from app.schemas import LoginRequest, LoginResponse, LoginUserOut, LogoutResponse, MeResponse
from app.security import api_guard
from core.config import API_PREFIX
from core.context import LedgerEntry, LedgerReceipt, UsuarioAduana
from core.crypto import sha256_hex
from core.identity import IdentityService
from core.rbac import permissions_of
from core.ui_profile import profile_of
from pipeline.stage4_ledger import seal_entry

RBAC_DISABLED_DETAIL = "RBAC_DISABLED"


def _identity(state: AppState) -> IdentityService:
    if state.identity is None:
        raise HTTPException(status_code=503, detail=RBAC_DISABLED_DETAIL)
    return state.identity


def _seal_auth_event(state: AppState, user: UsuarioAduana, outcome: str) -> LedgerReceipt:
    request_id = uuid.uuid4().hex
    subject = state.keys.hmac_hex("auth-token", f"audit-subject:{user.user_id}".encode())
    entry = LedgerEntry(
        request_id=request_id,
        timestamp_utc=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        blind_citizen_id=subject,
        payload_hash=sha256_hex(f"auth:{request_id}:{subject}:{outcome}".encode()),
        security_verdict="CLEAN",
        model_recommendation="REVISION_ESTANDAR",
        human_decision="REVISION_ESTANDAR",
        human_override=False,
        citizen_receipt_code=f"AUTH-{request_id[:8].upper()}",
        override_justification_hash=None,
    )
    return seal_entry(entry, state.repo, keys=state.keys)


class AuthController(Controller):
    path = f"{API_PREFIX}/auth"
    guards = [api_guard]
    dependencies = {"current_user": Provide(provide_current_user, sync_to_thread=False)}

    @post("/login", status_code=200, sync_to_thread=True)  # PBKDF2 y ledger: fuera del event loop
    def login(self, request: Request, data: JSONBody[LoginRequest]) -> LoginResponse:
        state: AppState = request.app.state.aduana
        identity = _identity(state)
        token = identity.login(data.identificador, data.password)
        user = identity.resolve_token(token.token)
        receipt = _seal_auth_event(state, user, f"AUTH_SUCCESS:{user.rol}")
        profile = profile_of(user)
        return LoginResponse(
            authenticated=True,
            session_token=token.token,
            token_type="Bearer",  # noqa: S106 - esquema HTTP, no es un secreto
            expires_in_seconds=token.expires_at - token.issued_at,
            expires_at=token.expires_at,
            user=LoginUserOut(
                id=profile.id,
                username=profile.username,
                full_name=profile.full_name,
                short_name=profile.short_name,
                avatar_text=profile.avatar_text,
                role=profile.role,
                role_label=profile.role_label,
                aduana_role=user.rol,
                clearance_level=profile.clearance_level,
                entity=profile.entity,
                department=profile.department,
                permissions=profile.permissions,
                default_tab=profile.default_tab,
                allowed_tabs=profile.allowed_tabs,
            ),
            block_index=receipt.block_index,
            citizen_receipt_code=receipt.citizen_receipt_code,
        )

    @post("/logout", status_code=200, sync_to_thread=True)
    def logout(self, request: Request) -> LogoutResponse:
        """Revoca el ``jti`` de la sesión actual. Con RBAC activo exige un Bearer válido."""
        state: AppState = request.app.state.aduana
        identity = _identity(state)
        token = extract_bearer(request)
        user, claims = identity.resolve_session(token)
        identity.revoke_token(token)
        _seal_auth_event(state, user, "AUTH_LOGOUT")
        return LogoutResponse(revoked=True, jti=claims.token_id)

    @get("/me", guards=[require_authenticated], sync_to_thread=False)
    def me(self, current_user: NamedDependency[UsuarioAduana]) -> MeResponse:
        return MeResponse(
            codigo_usuario=current_user.codigo_usuario,
            rol=current_user.rol,
            permisos=sorted(permissions_of(current_user.rol)),
        )
