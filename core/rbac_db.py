"""Persistencia de usuarios (``usuarios_aduana``): SQLite endurecido. Ver specs/06 §6.

Base distinta del ledger: el ledger es inmutable; aquí se actualizan contadores y estado. La baja
es lógica (trigger ``ERR_NO_DELETE_USUARIOS``). Los métodos públicos NUNCA devuelven sal ni hash
salvo ``get_credentials``. Los mensajes de error no incluyen valores (códigos, índices, hashes).
"""

from __future__ import annotations

import os
import secrets
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final, cast

from core.auth import PasswordRecord
from core.context import AduanaRoleType, UserStatus, UsuarioAduana
from core.errors import DuplicateUserError, StorageError

_TS_FORMAT: Final = "%Y-%m-%dT%H:%M:%SZ"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS usuarios_aduana (
    user_id          TEXT PRIMARY KEY,
    codigo_usuario   TEXT NOT NULL UNIQUE,
    blind_identifier TEXT NOT NULL UNIQUE,
    rol              TEXT NOT NULL CHECK (rol IN (
        'INSPECTOR_TRIBUTARIO_SENIAT', 'AGENTE_ADUANAL_CERTIFICADO',
        'FISCAL_ANTI_CONTRABANDO', 'OPERADOR_LOGISTICO_ALMACEN',
        'SUPERVISOR_PUERTO_ADUANERO', 'ANALISTA_VALORACION_ADUANERA')),
    estado           TEXT NOT NULL CHECK (estado IN ('ACTIVO', 'SUSPENDIDO')),
    password_salt    BLOB NOT NULL CHECK (length(password_salt) = 32),
    password_hash    BLOB NOT NULL CHECK (length(password_hash) = 32),
    kdf_iterations   INTEGER NOT NULL CHECK (kdf_iterations >= 1),
    failed_attempts  INTEGER NOT NULL DEFAULT 0,
    locked_until_utc TEXT,
    created_utc      TEXT NOT NULL,
    last_login_utc   TEXT
);

CREATE TRIGGER IF NOT EXISTS prevent_usuarios_delete
BEFORE DELETE ON usuarios_aduana
BEGIN
    SELECT RAISE(ABORT, 'ERR_NO_DELETE_USUARIOS');
END;
"""

_PUBLIC_COLUMNS = (
    "user_id, codigo_usuario, blind_identifier, rol, estado, created_utc, "
    "last_login_utc, failed_attempts, locked_until_utc"
)


def _row_to_user(row: tuple[object, ...]) -> UsuarioAduana:
    return UsuarioAduana(
        user_id=cast(str, row[0]),
        codigo_usuario=cast(str, row[1]),
        blind_identifier=cast(str, row[2]),
        rol=cast(AduanaRoleType, row[3]),
        estado=cast(UserStatus, row[4]),
        created_utc=cast(str, row[5]),
        last_login_utc=cast("str | None", row[6]),
        failed_attempts=cast(int, row[7]),
        locked_until_utc=cast("str | None", row[8]),
    )


def _format_utc(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime(_TS_FORMAT)


def _parse_utc(text: str) -> datetime:
    return datetime.strptime(text, _TS_FORMAT).replace(tzinfo=UTC)


class UsuariosRepository:
    """SQLite con WAL, synchronous=FULL, secure_delete=ON, trusted_schema=OFF, foreign_keys=ON."""

    def __init__(self, db_path: str) -> None:
        self._lock = threading.RLock()
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL;")
            cur.execute("PRAGMA synchronous=FULL;")
            cur.execute("PRAGMA secure_delete=ON;")
            cur.execute("PRAGMA trusted_schema=OFF;")
            cur.execute("PRAGMA foreign_keys=ON;")
            cur.executescript(_SCHEMA_SQL)
            cur.close()
        try:
            os.chmod(db_path, 0o600)
        except OSError:
            pass  # mejor esfuerzo: depende del SO

    # --- infraestructura ----------------------------------------------------------------------

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Cursor]:
        """Transacción explícita BEGIN IMMEDIATE bajo el RLock; errores SQL -> StorageError."""
        with self._lock:
            cur = self._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                yield cur
                cur.execute("COMMIT")
            except DuplicateUserError:
                self._rollback(cur)
                raise
            except sqlite3.Error:
                self._rollback(cur)
                raise StorageError("Fallo de persistencia de usuarios.") from None
            except BaseException:
                self._rollback(cur)
                raise
            finally:
                cur.close()

    @staticmethod
    def _rollback(cur: sqlite3.Cursor) -> None:
        try:
            cur.execute("ROLLBACK")
        except sqlite3.Error:
            pass

    def _fetch_user(self, cur: sqlite3.Cursor, user_id: str) -> UsuarioAduana:
        cur.execute(f"SELECT {_PUBLIC_COLUMNS} FROM usuarios_aduana WHERE user_id = ?", (user_id,))  # noqa: S608
        row = cur.fetchone()
        if row is None:
            raise StorageError("Usuario inexistente.")
        return _row_to_user(row)

    # --- escritura ----------------------------------------------------------------------------

    def create_user(
        self,
        *,
        codigo_usuario: str,
        blind_identifier: str,
        rol: AduanaRoleType,
        password: PasswordRecord,
        now_utc: str,
    ) -> UsuarioAduana:
        user_id = secrets.token_hex(16)
        with self._transaction() as cur:
            try:
                cur.execute(
                    "INSERT INTO usuarios_aduana (user_id, codigo_usuario, blind_identifier, rol, "
                    "estado, password_salt, password_hash, kdf_iterations, failed_attempts, "
                    "created_utc) VALUES (?, ?, ?, ?, 'ACTIVO', ?, ?, ?, 0, ?)",
                    (
                        user_id,
                        codigo_usuario,
                        blind_identifier,
                        rol,
                        password.salt,
                        password.hash,
                        password.iterations,
                        now_utc,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                if "UNIQUE" in str(exc):
                    raise DuplicateUserError(
                        "Ya existe un usuario con ese código o identificador."
                    ) from None
                raise
            return self._fetch_user(cur, user_id)

    def register_failed_attempt(
        self, user_id: str, *, max_attempts: int, lockout_seconds: int, now: datetime
    ) -> UsuarioAduana:
        """Incrementa el contador de forma atómica; al alcanzar ``max_attempts`` fija el bloqueo.

        Un bloqueo ya vencido reinicia el contador antes de contar el nuevo fallo.
        """
        with self._transaction() as cur:
            current = self._fetch_user(cur, user_id)
            failed = current.failed_attempts
            if current.locked_until_utc is not None and _parse_utc(
                current.locked_until_utc
            ) <= now.astimezone(UTC):
                failed = 0
            failed += 1
            locked_until = (
                _format_utc(now + timedelta(seconds=lockout_seconds))
                if failed >= max_attempts
                else None
            )
            cur.execute(
                "UPDATE usuarios_aduana SET failed_attempts = ?, locked_until_utc = ? "
                "WHERE user_id = ?",
                (failed, locked_until, user_id),
            )
            return self._fetch_user(cur, user_id)

    def register_successful_login(self, user_id: str, *, now_utc: str) -> UsuarioAduana:
        return self._update(
            user_id,
            "failed_attempts = 0, locked_until_utc = NULL, last_login_utc = ?",
            (now_utc,),
        )

    def set_estado(self, user_id: str, estado: UserStatus) -> UsuarioAduana:
        return self._update(user_id, "estado = ?", (estado,))

    def set_rol(self, user_id: str, rol: AduanaRoleType) -> UsuarioAduana:
        return self._update(user_id, "rol = ?", (rol,))

    def _update(self, user_id: str, assignment: str, params: tuple[object, ...]) -> UsuarioAduana:
        with self._transaction() as cur:
            cur.execute(
                f"UPDATE usuarios_aduana SET {assignment} WHERE user_id = ?",  # noqa: S608
                (*params, user_id),
            )
            if cur.rowcount != 1:
                raise StorageError("Usuario inexistente.")
            return self._fetch_user(cur, user_id)

    # --- lectura ------------------------------------------------------------------------------

    def get_by_id(self, user_id: str) -> UsuarioAduana | None:
        with self._lock:
            row = self._conn.execute(
                f"SELECT {_PUBLIC_COLUMNS} FROM usuarios_aduana WHERE user_id = ?",  # noqa: S608
                (user_id,),
            ).fetchone()
        return None if row is None else _row_to_user(row)

    def get_credentials(self, blind_identifier: str) -> tuple[UsuarioAduana, PasswordRecord] | None:
        with self._lock:
            row = self._conn.execute(
                f"SELECT {_PUBLIC_COLUMNS}, password_salt, password_hash, kdf_iterations "  # noqa: S608
                "FROM usuarios_aduana WHERE blind_identifier = ?",
                (blind_identifier,),
            ).fetchone()
        if row is None:
            return None
        record = PasswordRecord(salt=bytes(row[9]), hash=bytes(row[10]), iterations=int(row[11]))
        return _row_to_user(row[:9]), record

    def list_users(self) -> list[UsuarioAduana]:
        with self._lock:
            rows = self._conn.execute(
                f"SELECT {_PUBLIC_COLUMNS} FROM usuarios_aduana ORDER BY rowid"  # noqa: S608
            ).fetchall()
        return [_row_to_user(r) for r in rows]

    def count(self) -> int:
        with self._lock:
            return int(self._conn.execute("SELECT COUNT(*) FROM usuarios_aduana").fetchone()[0])

    def close(self) -> None:
        with self._lock:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
