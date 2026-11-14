"""Autenticación Zero-Trust y RBAC Aduanero (PBKDF2-HMAC-SHA256 + SessionStore en RAM).

Reglas de seguridad:
- Zero-Plaintext-PII: la cédula se normaliza (NFKC + ``normalize_cedula``) y se convierte
  inmediatamente a ``blind_citizen_id`` vía HMAC-SHA256 (dominio ``blind-index``).
- Contraseñas verificadas con ``hashlib.pbkdf2_hmac('sha256', ..., 310_000)`` y
  ``hmac.compare_digest`` (tiempo constante, cero ``random()``).
- Tokens de sesión efímeros generados con ``secrets.token_urlsafe(32)`` en RAM (TTL corto).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

from core.crypto import blind_citizen_id, normalize_cedula
from core.keyring import KeyRing

OfficialRole = Literal["analista", "administrador", "auditor"]
DefaultTab = Literal["pasarela", "ledger"]

PBKDF2_ITERATIONS: Final[int] = 310_000
SESSION_TTL_SECONDS: Final[int] = 1800
_DUMMY_SALT: Final[bytes] = b"\x00" * 16
_DUMMY_DK: Final[bytes] = b"\x00" * 32

_AUTH_SCHEMA_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS roles_aduana (
    role_id TEXT PRIMARY KEY CHECK (
        role_id IN ('analista', 'administrador', 'auditor')
    ),
    role_name TEXT NOT NULL,
    description TEXT NOT NULL,
    allowed_tabs_json TEXT NOT NULL,
    default_tab TEXT NOT NULL CHECK (
        default_tab IN ('pasarela', 'chat', 'ledger', 'explicabilidad', 'canal')
    )
);

CREATE TABLE IF NOT EXISTS usuarios_aduana (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    avatar_text TEXT NOT NULL,
    role TEXT NOT NULL REFERENCES roles_aduana(role_id),
    role_label TEXT NOT NULL,
    clearance_level TEXT NOT NULL,
    entity TEXT NOT NULL,
    department TEXT NOT NULL,
    ed25519_key TEXT NOT NULL,
    ed25519_status TEXT NOT NULL,
    blind_citizen_id TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    permissions_json TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_usuarios_aduana_role
    ON usuarios_aduana (role);

CREATE INDEX IF NOT EXISTS idx_usuarios_aduana_is_active
    ON usuarios_aduana (is_active);

CREATE TABLE IF NOT EXISTS canal_seguro_channels (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
);
"""


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """Perfil RBAC hidratado desde ``usuarios_aduana`` + ``roles_aduana``."""

    id: str
    username: str
    full_name: str
    short_name: str
    avatar_text: str
    role: OfficialRole
    role_label: str
    clearance_level: str
    entity: str
    department: str
    permissions: tuple[str, ...]
    default_tab: DefaultTab
    allowed_tabs: tuple[str, ...]


@dataclass(slots=True)
class SessionEntry:
    user_id: str
    role: OfficialRole
    jti: str
    expires_at_monotonic: float
    expires_at_epoch: int


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def issue_jwt_hs256(
    keys: KeyRing,
    *,
    user_id: str,
    role: OfficialRole,
    jti: str,
    ttl_seconds: int = SESSION_TTL_SECONDS,
) -> tuple[str, int]:
    """Emite un JWT HS256 (RFC 7519) firmado con HMAC-SHA256 en dominio ``jwt-session``."""
    now_epoch = int(time.time())
    exp_epoch = now_epoch + ttl_seconds
    header = _b64url_encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":"), sort_keys=True).encode()
    )
    payload = _b64url_encode(
        json.dumps(
            {
                "sub": user_id,
                "role": role,
                "jti": jti,
                "iat": now_epoch,
                "exp": exp_epoch,
                "iss": "aduana-ia",
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    )
    signing_input = f"{header}.{payload}".encode("ascii")
    sig_bytes = bytes.fromhex(keys.hmac_hex("jwt-session", signing_input))
    signature = _b64url_encode(sig_bytes)
    return f"{header}.{payload}.{signature}", exp_epoch


def verify_jwt_hs256(keys: KeyRing, token: str) -> dict[str, object] | None:
    """Verifica firma HMAC-SHA256 en tiempo constante y expiración ``exp`` del JWT."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    header_b64, payload_b64, sig_b64 = parts
    try:
        header = json.loads(_b64url_decode(header_b64))
        if header.get("alg") != "HS256" or header.get("typ") != "JWT":
            return None
        supplied_sig = _b64url_decode(sig_b64)
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = bytes.fromhex(keys.hmac_hex("jwt-session", signing_input))
        if not hmac.compare_digest(supplied_sig, expected_sig):
            return None
        claims = json.loads(_b64url_decode(payload_b64))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None

    if not isinstance(claims, dict):
        return None
    exp = claims.get("exp")
    if not isinstance(exp, int) or exp <= int(time.time()):
        return None
    if claims.get("iss") != "aduana-ia":
        return None
    return claims


class SessionStore:
    """Almacén efímero en RAM para sesiones activas y revocación inmediata de JWT (``jti``)."""

    def __init__(self, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._sessions: dict[str, SessionEntry] = {}

    def issue(self, keys: KeyRing, user_id: str, role: OfficialRole) -> tuple[str, str, int]:
        jti = secrets.token_urlsafe(32)
        token, exp_epoch = issue_jwt_hs256(
            keys,
            user_id=user_id,
            role=role,
            jti=jti,
            ttl_seconds=self._ttl,
        )
        now = time.monotonic()
        with self._lock:
            self._purge_expired_locked(now)
            self._sessions[jti] = SessionEntry(
                user_id=user_id,
                role=role,
                jti=jti,
                expires_at_monotonic=now + self._ttl,
                expires_at_epoch=exp_epoch,
            )
        return token, jti, self._ttl

    def validate_jwt(self, keys: KeyRing, token: str) -> SessionEntry | None:
        claims = verify_jwt_hs256(keys, token)
        if claims is None:
            return None
        jti = claims.get("jti")
        if not isinstance(jti, str):
            return None
        now = time.monotonic()
        with self._lock:
            self._purge_expired_locked(now)
            entry = self._sessions.get(jti)
            if entry is None or entry.expires_at_monotonic <= now:
                return None
            return entry

    def revoke(self, jti: str) -> bool:
        with self._lock:
            return self._sessions.pop(jti, None) is not None

    def zeroize_all(self) -> None:
        with self._lock:
            self._sessions.clear()

    def _purge_expired_locked(self, now: float) -> None:
        expired = [k for k, v in self._sessions.items() if v.expires_at_monotonic <= now]
        for key in expired:
            del self._sessions[key]


def verify_pbkdf2_password(password: str, stored_hash: str) -> bool:
    """Verifica ``pbkdf2_sha256$<iter>$<salt_hex>$<dk_hex>`` en tiempo constante."""
    try:
        scheme, iter_raw, salt_hex, dk_hex = stored_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iter_raw)
        if iterations < PBKDF2_ITERATIONS:
            return False
        salt = bytes.fromhex(salt_hex)
        expected_dk = bytes.fromhex(dk_hex)
    except (ValueError, TypeError):
        return False

    computed_dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(computed_dk, expected_dk)


def dummy_pbkdf2_work(password: str) -> None:
    """Equilibra el costo CPU cuando el usuario no existe (mitiga timing oracle)."""
    computed = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), _DUMMY_SALT, PBKDF2_ITERATIONS
    )
    hmac.compare_digest(computed, _DUMMY_DK)


def compute_blind_citizen_id(keys: KeyRing, cedula: str) -> str:
    """Normaliza la cédula (NFKC + V/E canónica) y retorna ``blind_citizen_id`` HMAC."""
    canonical = normalize_cedula(cedula)
    return blind_citizen_id(keys, canonical)


class SQLiteAuthRepository:
    """Repositorio SQLite para ``roles_aduana`` y ``usuarios_aduana`` (Zero-Plaintext-PII)."""

    def __init__(self, db_path: str, keys: KeyRing | None = None) -> None:
        self._db_path = db_path
        self._keys = keys
        self._seeded = False
        self._lock = threading.RLock()
        p = Path(db_path)
        if not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("PRAGMA foreign_keys = ON;")
            cur.executescript(_AUTH_SCHEMA_SQL)
            self._conn.commit()
            cur.close()

    def _seed_if_empty_locked(self, cur: sqlite3.Cursor) -> None:
        if self._seeded or self._keys is None:
            return
        cur.execute("SELECT COUNT(*) FROM usuarios_aduana")
        count = cur.fetchone()[0]
        if count == 0:
            from scripts.generate_d1_seed import build_seed_sql

            cur.executescript(build_seed_sql(self._keys))
        self._seeded = True

    def find_active_by_blind_id(self, blind_id: str) -> tuple[AuthenticatedUser, str] | None:
        """Busca un funcionario activo exclusivamente por su ``blind_citizen_id``."""
        with self._lock:
            cur = self._conn.cursor()
            self._seed_if_empty_locked(cur)
            cur.execute(
                """
                SELECT
                    u.id,
                    u.username,
                    u.full_name,
                    u.short_name,
                    u.avatar_text,
                    u.role,
                    u.role_label,
                    u.clearance_level,
                    u.entity,
                    u.department,
                    u.permissions_json,
                    r.default_tab,
                    r.allowed_tabs_json,
                    u.password_hash
                FROM usuarios_aduana AS u
                INNER JOIN roles_aduana AS r ON r.role_id = u.role
                WHERE u.blind_citizen_id = ? AND u.is_active = 1
                LIMIT 1
                """,
                (blind_id,),
            )
            row = cur.fetchone()
            cur.close()

        if row is None:
            return None

        role: OfficialRole = row[5]
        default_tab: DefaultTab = "ledger" if role == "auditor" else "pasarela"
        permissions = tuple(str(p) for p in json.loads(row[10]))
        allowed_tabs = tuple(str(t) for t in json.loads(row[12]))
        user = AuthenticatedUser(
            id=row[0],
            username=row[1],
            full_name=row[2],
            short_name=row[3],
            avatar_text=row[4],
            role=role,
            role_label=row[6],
            clearance_level=row[7],
            entity=row[8],
            department=row[9],
            permissions=permissions,
            default_tab=default_tab,
            allowed_tabs=allowed_tabs,
        )
        return user, str(row[13])

    def close(self) -> None:
        with self._lock:
            self._conn.close()
