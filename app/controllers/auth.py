"""Login único (RBAC aduanero + soporte institucional Demo/Correo):
``POST /auth/login``, ``POST /auth/logout``, ``GET /auth/me`` y ``GET /auth/session``.

- Con ``rbac_enabled=True`` (modo estricto ``specs/06_rbac_aduanero.spec.md``):
  PBKDF2 600k con sal por usuario, bloqueo por intentos, error uniforme, relectura del usuario en
  cada petición, revocación por ``jti`` y auditoría en el ledger con id opaco por funcionario.
- Con ``demo_mode=True`` (desarrollo local y pruebas de sesión F5 / correo institucional):
  habilita login por correo institucional o cédula demo y persistencia de sesión tras F5 mediante
  cookie ``HttpOnly; SameSite=Strict``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from litestar import Controller, Request, Response, get, post
from litestar.datastructures import Cookie
from litestar.di import NamedDependency, Provide
from litestar.exceptions import HTTPException, NotAuthorizedException
from litestar.params import JSONBody

from app.dependencies import AppState
from app.rbac_guards import extract_bearer, provide_current_user, require_authenticated
from app.schemas import (
    LoginRequest,
    LoginResponse,
    LoginUserOut,
    LogoutResponse,
    MeResponse,
    SessionStatusResponse,
)
from app.security import api_guard
from core.config import API_PREFIX
from core.context import AduanaRoleType, LedgerEntry, LedgerReceipt, UsuarioAduana
from core.crypto import sha256_hex
from core.errors import AuthenticationError
from core.identity import IdentityService
from core.rbac import permissions_of
from core.ui_profile import profile_of
from pipeline.auth import (
    AuthenticatedUser,
    compute_blind_citizen_id,
    dummy_pbkdf2_work,
    normalize_email,
    verify_pbkdf2_password,
)
from pipeline.stage4_ledger import seal_entry

RBAC_DISABLED_DETAIL = "RBAC_DISABLED"
SESSION_COOKIE_NAME = "aduana_session"

_UI_TO_ADUANA_ROLE: dict[str, AduanaRoleType] = {
    "auditor": "INSPECTOR_TRIBUTARIO_SENIAT",
    "analista": "ANALISTA_VALORACION_ADUANERA",
    "administrador": "SUPERVISOR_PUERTO_ADUANERO",
}


def _identity(state: AppState) -> IdentityService:
    if state.identity is None:
        raise HTTPException(status_code=503, detail=RBAC_DISABLED_DETAIL)
    return state.identity


def _to_user_out(user: AuthenticatedUser) -> LoginUserOut:
    return LoginUserOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        short_name=user.short_name,
        avatar_text=user.avatar_text,
        role=user.role,
        role_label=user.role_label,
        aduana_role=_UI_TO_ADUANA_ROLE.get(user.role, "INSPECTOR_TRIBUTARIO_SENIAT"),
        clearance_level=user.clearance_level,
        entity=user.entity,
        department=user.department,
        permissions=user.permissions,
        default_tab=user.default_tab,
        allowed_tabs=user.allowed_tabs,
    )


def _seal_rbac_auth_event(state: AppState, user: UsuarioAduana, outcome: str) -> LedgerReceipt:
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


def _seal_demo_auth_event(
    state: AppState,
    *,
    request_id: str,
    timestamp_utc: str,
    blind_id: str,
    outcome: str,
    success: bool,
) -> LedgerReceipt:
    payload_hash = sha256_hex(f"auth:{request_id}:{blind_id}:{outcome}".encode())
    entry = LedgerEntry(
        request_id=request_id,
        timestamp_utc=timestamp_utc,
        blind_citizen_id=blind_id,
        payload_hash=payload_hash,
        security_verdict="CLEAN" if success else "BLOCKED_NO_CONSENT",
        model_recommendation="REVISION_ESTANDAR" if success else "BLOQUEADO_SEGURIDAD",
        human_decision="REVISION_ESTANDAR" if success else "BLOQUEADO_SEGURIDAD",
        human_override=False,
        citizen_receipt_code=f"AUTH-{request_id[:8].upper()}",
        override_justification_hash=None,
    )
    return seal_entry(entry, state.repo, keys=state.keys)


def _build_rbac_login_response(state: AppState, ident: str, password: str) -> LoginResponse:
    identity = _identity(state)
    token = identity.login(ident, password)
    user = identity.resolve_token(token.token)
    receipt = _seal_rbac_auth_event(state, user, f"AUTH_SUCCESS:{user.rol}")
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


def _login_demo_or_sqlite(
    state: AppState,
    request: Request,
    raw_identifier: str,
    password: str,
) -> Response[LoginResponse]:
    found: tuple[AuthenticatedUser, str] | None
    if "@" in raw_identifier:
        try:
            clean_email = normalize_email(raw_identifier)
        except ValueError:
            raise HTTPException(status_code=422, detail="INVALID_CEDULA") from None
        email_match = state.auth_repo.find_active_by_email(clean_email)
        if email_match is None:
            blind_id = state.keys.hmac_hex("blind-index", clean_email.encode("utf-8"))
            found = None
        else:
            user_obj, pwd_hash, user_blind_id = email_match
            blind_id = user_blind_id
            found = (user_obj, pwd_hash)
    else:
        try:
            blind_id = compute_blind_citizen_id(state.keys, raw_identifier)
        except ValueError:
            raise HTTPException(status_code=422, detail="INVALID_CEDULA") from None
        found = state.auth_repo.find_active_by_blind_id(blind_id)

    state.auth_rate_guard.check(blind_id)

    request_id = uuid.uuid4().hex
    timestamp_utc = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    if found is None:
        dummy_pbkdf2_work(password)
        _seal_demo_auth_event(
            state,
            request_id=request_id,
            timestamp_utc=timestamp_utc,
            blind_id=blind_id,
            outcome="AUTH_USER_NOT_FOUND",
            success=False,
        )
        raise NotAuthorizedException(detail="INVALID_CREDENTIALS")

    user, stored_hash = found
    if not verify_pbkdf2_password(password, stored_hash):
        _seal_demo_auth_event(
            state,
            request_id=request_id,
            timestamp_utc=timestamp_utc,
            blind_id=blind_id,
            outcome="AUTH_INVALID_PASSWORD",
            success=False,
        )
        raise NotAuthorizedException(detail="INVALID_CREDENTIALS")

    session_token, _jti, ttl_seconds = state.session_store.issue(
        state.keys, user.id, user.role
    )
    receipt = _seal_demo_auth_event(
        state,
        request_id=request_id,
        timestamp_utc=timestamp_utc,
        blind_id=blind_id,
        outcome=f"AUTH_SUCCESS:{user.role}",
        success=True,
    )
    now_epoch = int(datetime.now(UTC).timestamp())
    payload = LoginResponse(
        authenticated=True,
        session_token=session_token,
        token_type="Bearer",  # noqa: S106
        expires_in_seconds=ttl_seconds,
        expires_at=now_epoch + ttl_seconds,
        user=_to_user_out(user),
        block_index=receipt.block_index,
        citizen_receipt_code=receipt.citizen_receipt_code,
    )
    return Response(
        content=payload,
        status_code=200,
        cookies=[
            Cookie(
                key=SESSION_COOKIE_NAME,
                value=session_token,
                max_age=ttl_seconds,
                path="/",
                httponly=True,
                samesite="strict",
                secure=request.url.scheme == "https",
            )
        ],
    )


def _extract_session_jwt(request: Request) -> str:
    auth_header = request.headers.get("authorization", "")
    prefix = "Bearer "
    if auth_header.startswith(prefix):
        return auth_header[len(prefix) :].strip()
    cookie_token = request.cookies.get(SESSION_COOKIE_NAME, "")
    if cookie_token:
        return cookie_token.strip()
    raise NotAuthorizedException(detail="INVALID_SESSION")


class AuthController(Controller):
    path = f"{API_PREFIX}/auth"
    guards = [api_guard]
    dependencies = {"current_user": Provide(provide_current_user, sync_to_thread=False)}

    @post("/login", status_code=200, sync_to_thread=True)  # PBKDF2 y ledger: fuera del event loop
    def login(
        self, request: Request, data: JSONBody[LoginRequest]
    ) -> LoginResponse | Response[LoginResponse]:
        state: AppState = request.app.state.aduana
        if not state.settings.demo_mode:
            if not state.settings.rbac_enabled:
                raise HTTPException(status_code=503, detail=RBAC_DISABLED_DETAIL)
            if (
                data.identificador is None
                or data.cedula is not None
                or not (1 <= len(data.identificador) <= 20)
            ):
                raise HTTPException(status_code=422, detail="INVALID_LOGIN_PAYLOAD")
            return _build_rbac_login_response(state, data.identificador, data.password)

        raw_id = (data.identificador or data.cedula or "").strip()
        if not raw_id:
            raise HTTPException(status_code=422, detail="INVALID_CEDULA")

        if state.identity is not None and "@" not in raw_id and len(raw_id) <= 20:
            try:
                return _build_rbac_login_response(state, raw_id, data.password)
            except AuthenticationError:
                pass
        return _login_demo_or_sqlite(state, request, raw_id, data.password)

    @get("/session", status_code=200, sync_to_thread=True)
    def session_status(self, request: Request) -> SessionStatusResponse:
        state: AppState = request.app.state.aduana
        if not state.settings.demo_mode:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        token = _extract_session_jwt(request)
        entry = state.session_store.validate_jwt(state.keys, token)
        if entry is None:
            raise NotAuthorizedException(detail="INVALID_SESSION")
        user = state.auth_repo.find_active_by_id(entry.user_id)
        if user is None:
            raise NotAuthorizedException(detail="INVALID_SESSION")
        return SessionStatusResponse(
            authenticated=True,
            user_id=entry.user_id,
            role=entry.role,
            jti=entry.jti,
            expires_at_epoch=entry.expires_at_epoch,
            user=_to_user_out(user),
        )

    @post("/logout", status_code=200, sync_to_thread=True)
    def logout(self, request: Request) -> LogoutResponse | Response[LogoutResponse]:
        """Revoca el ``jti`` de la sesión actual."""
        state: AppState = request.app.state.aduana
        if not state.settings.demo_mode:
            identity = _identity(state)
            token = extract_bearer(request)
            user, claims = identity.resolve_session(token)
            identity.revoke_token(token)
            _seal_rbac_auth_event(state, user, "AUTH_LOGOUT")
            return LogoutResponse(revoked=True, jti=claims.token_id)

        token = _extract_session_jwt(request)
        if state.identity is not None and token.startswith("v1."):
            user, claims = state.identity.resolve_session(token)
            state.identity.revoke_token(token)
            _seal_rbac_auth_event(state, user, "AUTH_LOGOUT")
            return LogoutResponse(revoked=True, jti=claims.token_id)

        entry = state.session_store.validate_jwt(state.keys, token)
        if entry is None:
            raise NotAuthorizedException(detail="INVALID_SESSION")
        revoked = state.session_store.revoke(entry.jti)
        return Response(
            content=LogoutResponse(revoked=revoked, jti=entry.jti),
            status_code=200,
            cookies=[
                Cookie(
                    key=SESSION_COOKIE_NAME,
                    value="",
                    max_age=0,
                    path="/",
                    httponly=True,
                    samesite="strict",
                    secure=request.url.scheme == "https",
                )
            ],
        )

    @get("/me", guards=[require_authenticated], sync_to_thread=False)
    def me(self, current_user: NamedDependency[UsuarioAduana]) -> MeResponse:
        return MeResponse(
            codigo_usuario=current_user.codigo_usuario,
            rol=current_user.rol,
            permisos=sorted(permissions_of(current_user.rol)),
        )
