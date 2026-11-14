"""Primitivas de autenticación (puras, solo stdlib). Ver specs/06_rbac_aduanero §5 y §7.

- Contraseñas: PBKDF2-HMAC-SHA256 con sal única de 32 bytes e iteraciones guardadas por usuario.
- Índice ciego (Anillo 2): cédula -> exactamente ``blind_citizen_id`` del ledger; RIF -> HMAC con
  prefijo ``RIF:`` para no colisionar jamás con una cédula.
- Token de sesión: ``v1.<base64url(JSON)>.<hmac hex>`` firmado con la subllave ``auth-token``.

Ningún mensaje de error incluye la contraseña, el identificador ni el token recibidos.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import re
import secrets
from dataclasses import dataclass, field
from typing import Final, cast, get_args

from core.context import AduanaRoleType, AuthToken, UsuarioAduana
from core.crypto import normalize_cedula, rif_mod11_valid
from core.errors import InvalidTokenError, WeakPasswordError
from core.keyring import KeyRing
from core.text_normalizer import normalize_text

PBKDF2_ITERATIONS: Final = 600_000
SALT_BYTES: Final = 32
KEY_BYTES: Final = 32
MIN_PASSWORD_CHARS: Final = 12
MAX_PASSWORD_CHARS: Final = 1024  # tope anti-DoS del KDF
TOKEN_VERSION: Final = "v1"  # noqa: S105
INVALID_TOKEN_MESSAGE: Final = "Token inválido o expirado."  # noqa: S105 - mensaje, no secreto

_ROLES: Final[frozenset[str]] = frozenset(get_args(AduanaRoleType))
_RIF_ONLY_LETTERS: Final = frozenset("JPGC")
_RIF_RE: Final = re.compile(r"([VEJPGC])([0-9]{9})", re.ASCII)
_B64_PAD: Final = "="


@dataclass(frozen=True, slots=True)
class PasswordRecord:
    salt: bytes
    hash: bytes = field(repr=False)
    iterations: int


@dataclass(frozen=True, slots=True)
class TokenClaims:
    user_id: str
    rol: AduanaRoleType
    issued_at: int
    expires_at: int
    token_id: str


# --- contraseñas ------------------------------------------------------------------------------


def validate_password_policy(password: str) -> None:
    """>= 12 caracteres, al menos una letra y un dígito, no todos iguales. Sin eco."""
    ok = (
        isinstance(password, str)
        and MIN_PASSWORD_CHARS <= len(password) <= MAX_PASSWORD_CHARS
        and any(ch.isalpha() for ch in password)
        and any(ch.isdigit() for ch in password)
        and len(set(password)) > 1
    )
    if not ok:
        raise WeakPasswordError(
            "La contraseña no cumple la política (mínimo 12 caracteres, letra y dígito)."
        )


def derive_key(password: str, salt: bytes, iterations: int) -> bytes:
    if iterations < 1:
        raise ValueError("Iteraciones del KDF fuera de rango.")
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations, dklen=KEY_BYTES)


def hash_password(password: str, *, iterations: int = PBKDF2_ITERATIONS) -> PasswordRecord:
    salt = secrets.token_bytes(SALT_BYTES)
    return PasswordRecord(
        salt=salt, hash=derive_key(password, salt, iterations), iterations=iterations
    )


def verify_password(password: str, record: PasswordRecord) -> bool:
    """Comparación en tiempo constante; una entrada no codificable no verifica (sin excepción)."""
    try:
        candidate = derive_key(password, record.salt, record.iterations)
    except (AttributeError, UnicodeError):
        return False
    return hmac.compare_digest(candidate, record.hash)


# --- identificadores --------------------------------------------------------------------------


def _compact(identifier: str) -> str:
    return "".join(
        ch for ch in normalize_text(identifier).upper() if ch not in "-." and not ch.isspace()
    )


def _is_rif(compact: str) -> bool:
    match = _RIF_RE.fullmatch(compact)
    if match is None:
        return False
    return match.group(1) in _RIF_ONLY_LETTERS or rif_mod11_valid(compact)


def normalize_identifier(identifier: str) -> str:
    """Forma canónica de cédula (``V12345678``) o RIF (letra + 9 dígitos). ``ValueError`` sin eco.

    Letras J|P|G|C + 9 dígitos son siempre RIF; V|E + 9 dígitos son RIF solo si el módulo 11 lo
    valida (si no, cédula de 9 dígitos).
    """
    if not isinstance(identifier, str):
        raise ValueError("Identificador con formato inválido.")
    compact = _compact(identifier)
    if _is_rif(compact):
        return compact
    try:
        return normalize_cedula(compact)
    except ValueError:
        raise ValueError("Identificador con formato inválido.") from None


def blind_identifier(keys: KeyRing, identifier: str) -> str:
    canonical = normalize_identifier(identifier)
    if _RIF_RE.fullmatch(canonical) and _is_rif(canonical):
        return keys.hmac_hex("blind-index", b"RIF:" + canonical.encode())
    # Cédula: debe coincidir EXACTAMENTE con el blind_citizen_id del ledger.
    return keys.hmac_hex("blind-index", canonical.encode())


# --- token ------------------------------------------------------------------------------------


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + _B64_PAD * (-len(text) % 4))


def issue_token(keys: KeyRing, user: UsuarioAduana, *, now: int, ttl_seconds: int) -> AuthToken:
    if ttl_seconds < 1:
        raise ValueError("ttl_seconds debe ser >= 1.")
    token_id = secrets.token_hex(16)
    expires_at = now + ttl_seconds
    payload = _b64e(
        json.dumps(
            {"sub": user.user_id, "rol": user.rol, "iat": now, "exp": expires_at, "jti": token_id},
            separators=(",", ":"),
        ).encode()
    )
    signature = keys.hmac_hex("auth-token", payload.encode())
    return AuthToken(
        token=f"{TOKEN_VERSION}.{payload}.{signature}",
        user_id=user.user_id,
        codigo_usuario=user.codigo_usuario,
        rol=user.rol,
        issued_at=now,
        expires_at=expires_at,
        token_id=token_id,
    )


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _reject() -> InvalidTokenError:
    return InvalidTokenError(INVALID_TOKEN_MESSAGE)


def verify_token(keys: KeyRing, token: str, *, now: int) -> TokenClaims:
    """Verifica formato, versión, firma (tiempo constante), payload, rol y ``exp``."""
    if not isinstance(token, str):
        raise _reject()
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != TOKEN_VERSION:
        raise _reject()
    _, payload, signature = parts
    if not keys.verify("auth-token", payload.encode(), signature):
        raise _reject()
    try:
        data = json.loads(_b64d(payload))
    except (ValueError, binascii.Error, UnicodeError):
        raise _reject() from None
    if not isinstance(data, dict):
        raise _reject()
    sub, rol, iat, exp, jti = (data.get(k) for k in ("sub", "rol", "iat", "exp", "jti"))
    valid = (
        isinstance(sub, str)
        and sub != ""
        and isinstance(jti, str)
        and jti != ""
        and isinstance(rol, str)
        and rol in _ROLES
        and _is_int(iat)
        and _is_int(exp)
    )
    if not valid:
        raise _reject()
    assert isinstance(iat, int) and isinstance(exp, int)  # noqa: S101 - estrechamiento de tipos
    if exp <= now:
        raise _reject()
    return TokenClaims(
        user_id=cast(str, sub),
        rol=cast(AduanaRoleType, rol),
        issued_at=iat,
        expires_at=exp,
        token_id=cast(str, jti),
    )
