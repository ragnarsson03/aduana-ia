"""Servicio de identidad (dominio, sin Litestar). Ver specs/06_rbac_aduanero §5-§7.

Zero-Trust: cada petición resuelve el token y vuelve a consultar al usuario en BD (estado ACTIVO y
rol ACTUAL). El login responde con un error uniforme y con coste de KDF comparable exista o no el
usuario, para impedir la enumeración por contenido o por tiempo.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Final

from core.auth import (
    PasswordRecord,
    blind_identifier,
    derive_key,
    hash_password,
    issue_token,
    validate_password_policy,
    verify_password,
    verify_token,
)
from core.context import AduanaRoleType, AuthToken, UsuarioAduana
from core.errors import AccountLockedError, AuthenticationError, AuthorizationError
from core.keyring import KeyRing
from core.rbac import Permission, has_permission
from core.rbac_db import UsuariosRepository

AUTH_ERROR_MESSAGE: Final = "Credenciales inválidas."
LOCKED_MESSAGE: Final = "Cuenta bloqueada temporalmente."
FORBIDDEN_MESSAGE: Final = "Permiso insuficiente para esta operación."
_TS_FORMAT: Final = "%Y-%m-%dT%H:%M:%SZ"
_DUMMY_SALT: Final = bytes(32)


def utcnow() -> datetime:
    return datetime.now(UTC)


def _format_utc(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime(_TS_FORMAT)


def _parse_utc(text: str) -> datetime:
    return datetime.strptime(text, _TS_FORMAT).replace(tzinfo=UTC)


class IdentityService:
    def __init__(
        self,
        repo: UsuariosRepository,
        keys: KeyRing,
        *,
        iterations: int,
        token_ttl_seconds: int,
        max_failed_attempts: int,
        lockout_seconds: int,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        if min(iterations, token_ttl_seconds, max_failed_attempts, lockout_seconds) < 1:
            raise ValueError("Parámetros de identidad fuera de rango.")
        self._repo = repo
        self._keys = keys
        self._iterations = iterations
        self._ttl = token_ttl_seconds
        self._max_attempts = max_failed_attempts
        self._lockout = lockout_seconds
        self._clock = clock

    # --- autenticación ------------------------------------------------------------------------

    def _dummy_verify(self, password: str) -> None:
        """Gasta un PBKDF2 con las mismas iteraciones cuando no hay hash real que comprobar."""
        derive_key(password, _DUMMY_SALT, self._iterations)

    def login(self, identificador: str, password: str) -> AuthToken:
        password = password if isinstance(password, str) else ""
        credentials = self._lookup(identificador)
        if credentials is None or credentials[0].estado != "ACTIVO":
            self._dummy_verify(password)
            raise AuthenticationError(AUTH_ERROR_MESSAGE)
        user, record = credentials
        now = self._clock()
        if user.locked_until_utc is not None and _parse_utc(user.locked_until_utc) > now:
            raise AccountLockedError(LOCKED_MESSAGE)
        if not verify_password(password, record):
            self._repo.register_failed_attempt(
                user.user_id,
                max_attempts=self._max_attempts,
                lockout_seconds=self._lockout,
                now=now,
            )
            raise AuthenticationError(AUTH_ERROR_MESSAGE)
        updated = self._repo.register_successful_login(user.user_id, now_utc=_format_utc(now))
        return issue_token(self._keys, updated, now=int(now.timestamp()), ttl_seconds=self._ttl)

    def _lookup(self, identificador: str) -> tuple[UsuarioAduana, PasswordRecord] | None:
        try:
            blind = blind_identifier(self._keys, identificador)
        except ValueError:
            return None
        return self._repo.get_credentials(blind)

    def resolve_token(self, token: str) -> UsuarioAduana:
        """Firma, expiración y relectura del usuario (ACTIVO); devuelve el rol actual de la BD."""
        claims = verify_token(self._keys, token, now=int(self._clock().timestamp()))
        user = self._repo.get_by_id(claims.user_id)
        if user is None or user.estado != "ACTIVO":
            raise AuthenticationError(AUTH_ERROR_MESSAGE)
        return user

    # --- administración -----------------------------------------------------------------------

    def create_user(
        self, *, codigo_usuario: str, identificador: str, rol: AduanaRoleType, password: str
    ) -> UsuarioAduana:
        validate_password_policy(password)
        blind = blind_identifier(self._keys, identificador)  # ValueError sin eco
        record = hash_password(password, iterations=self._iterations)
        return self._repo.create_user(
            codigo_usuario=codigo_usuario,
            blind_identifier=blind,
            rol=rol,
            password=record,
            now_utc=_format_utc(self._clock()),
        )

    def list_users(self) -> list[UsuarioAduana]:
        return self._repo.list_users()

    def suspend_user(self, user_id: str) -> UsuarioAduana:
        return self._repo.set_estado(user_id, "SUSPENDIDO")

    def reactivate_user(self, user_id: str) -> UsuarioAduana:
        return self._repo.set_estado(user_id, "ACTIVO")

    def change_role(self, user_id: str, rol: AduanaRoleType) -> UsuarioAduana:
        return self._repo.set_rol(user_id, rol)

    # --- autorización -------------------------------------------------------------------------

    def authorize(self, user: UsuarioAduana, permission: Permission) -> None:
        if not has_permission(user.rol, permission):
            raise AuthorizationError(FORBIDDEN_MESSAGE)
