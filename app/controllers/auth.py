"""Controlador de Autenticación Zero-Trust (`POST /api/v1/auth/login`)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from litestar import Controller, Request, get, post
from litestar.exceptions import HTTPException, NotAuthorizedException

from app.dependencies import AppState
from app.schemas import (
    LoginRequest,
    LoginResponse,
    LoginUserOut,
    LogoutResponse,
    SessionStatusResponse,
)
from app.security import api_guard
from core.config import API_PREFIX
from core.context import LedgerEntry, LedgerReceipt
from core.crypto import sha256_hex
from pipeline.auth import (
    compute_blind_citizen_id,
    dummy_pbkdf2_work,
    verify_pbkdf2_password,
)
from pipeline.stage4_ledger import seal_entry


def _seal_auth_event(
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


class AuthController(Controller):
    path = f"{API_PREFIX}/auth"

    @post("/login", guards=[api_guard], status_code=200, sync_to_thread=True)
    def login(self, data: LoginRequest, request: Request) -> LoginResponse:
        state: AppState = request.app.state.aduana
        try:
            blind_id = compute_blind_citizen_id(state.keys, data.cedula)
        except ValueError:
            raise HTTPException(status_code=422, detail="INVALID_CEDULA") from None

        state.auth_rate_guard.check(blind_id)

        request_id = uuid.uuid4().hex
        timestamp_utc = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        found = state.auth_repo.find_active_by_blind_id(blind_id)
        if found is None:
            dummy_pbkdf2_work(data.password)
            _seal_auth_event(
                state,
                request_id=request_id,
                timestamp_utc=timestamp_utc,
                blind_id=blind_id,
                outcome="AUTH_USER_NOT_FOUND",
                success=False,
            )
            raise NotAuthorizedException(detail="INVALID_CREDENTIALS")

        user, stored_hash = found
        if not verify_pbkdf2_password(data.password, stored_hash):
            _seal_auth_event(
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
        receipt = _seal_auth_event(
            state,
            request_id=request_id,
            timestamp_utc=timestamp_utc,
            blind_id=blind_id,
            outcome=f"AUTH_SUCCESS:{user.role}",
            success=True,
        )

        return LoginResponse(
            authenticated=True,
            session_token=session_token,
            token_type="Bearer",  # noqa: S106
            expires_in_seconds=ttl_seconds,
            user=LoginUserOut(
                id=user.id,
                username=user.username,
                full_name=user.full_name,
                short_name=user.short_name,
                avatar_text=user.avatar_text,
                role=user.role,
                role_label=user.role_label,
                clearance_level=user.clearance_level,
                entity=user.entity,
                department=user.department,
                permissions=user.permissions,
                default_tab=user.default_tab,
                allowed_tabs=user.allowed_tabs,
            ),
            block_index=receipt.block_index,
            citizen_receipt_code=receipt.citizen_receipt_code,
        )

    @get("/session", guards=[api_guard], status_code=200, sync_to_thread=False)
    def session_status(self, request: Request) -> SessionStatusResponse:
        state: AppState = request.app.state.aduana
        token = _extract_bearer_token(request)
        entry = state.session_store.validate_jwt(state.keys, token)
        if entry is None:
            raise NotAuthorizedException(detail="INVALID_SESSION")
        return SessionStatusResponse(
            authenticated=True,
            user_id=entry.user_id,
            role=entry.role,
            jti=entry.jti,
            expires_at_epoch=entry.expires_at_epoch,
        )

    @post("/logout", guards=[api_guard], status_code=200, sync_to_thread=False)
    def logout(self, request: Request) -> LogoutResponse:
        state: AppState = request.app.state.aduana
        token = _extract_bearer_token(request)
        entry = state.session_store.validate_jwt(state.keys, token)
        if entry is None:
            raise NotAuthorizedException(detail="INVALID_SESSION")
        revoked = state.session_store.revoke(entry.jti)
        return LogoutResponse(revoked=revoked, jti=entry.jti)


def _extract_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("authorization", "")
    prefix = "Bearer "
    if not auth_header.startswith(prefix):
        raise NotAuthorizedException(detail="INVALID_SESSION")
    return auth_header[len(prefix) :].strip()
