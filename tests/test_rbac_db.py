"""Repositorio SQLite de usuarios (specs/06 §6): endurecimiento, bloqueos, zero-leak."""

from __future__ import annotations

import os
import sqlite3
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from core.auth import PasswordRecord, hash_password
from core.errors import DuplicateUserError, StorageError
from core.rbac_db import UsuariosRepository

NOW_UTC = "2026-01-01T00:00:00Z"
NOW = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
BLIND_A = "a" * 64
BLIND_B = "b" * 64
ROL = "AGENTE_ADUANAL_CERTIFICADO"


@pytest.fixture
def password() -> PasswordRecord:
    return hash_password("Clave-De-Prueba-42", iterations=1000)


@pytest.fixture
def repo(tmp_path: Path) -> UsuariosRepository:
    r = UsuariosRepository(str(tmp_path / "sub" / "usuarios.db"))
    yield r  # type: ignore[misc]
    r.close()


def _create(
    repo: UsuariosRepository,
    pw: PasswordRecord,
    code: str = "agente.01",
    blind: str = BLIND_A,
    rol: str = ROL,
):  # type: ignore[no-untyped-def]
    return repo.create_user(
        codigo_usuario=code,
        blind_identifier=blind,
        rol=rol,  # type: ignore[arg-type]
        password=pw,
        now_utc=NOW_UTC,
    )


def test_pragmas_applied(repo: UsuariosRepository, tmp_path: Path) -> None:
    conn = repo._conn  # noqa: SLF001
    assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    assert conn.execute("PRAGMA synchronous").fetchone()[0] == 2  # FULL
    assert conn.execute("PRAGMA secure_delete").fetchone()[0] == 1
    assert conn.execute("PRAGMA trusted_schema").fetchone()[0] == 0
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_create_and_get(repo: UsuariosRepository, password: PasswordRecord) -> None:
    user = _create(repo, password)
    assert len(user.user_id) == 32 and int(user.user_id, 16) >= 0
    assert user.estado == "ACTIVO" and user.rol == ROL
    assert user.failed_attempts == 0 and user.locked_until_utc is None
    assert user.created_utc == NOW_UTC and user.last_login_utc is None
    assert repo.get_by_id(user.user_id) == user
    assert repo.get_by_id("nope") is None
    assert repo.count() == 1


def test_user_ids_are_random(repo: UsuariosRepository, password: PasswordRecord) -> None:
    a = _create(repo, password, "a.01", BLIND_A)
    b = _create(repo, password, "a.02", BLIND_B)
    assert a.user_id != b.user_id


def test_duplicate_codigo_and_blind_raise_without_values(
    repo: UsuariosRepository, password: PasswordRecord
) -> None:
    _create(repo, password)
    with pytest.raises(DuplicateUserError) as e1:
        _create(repo, password, "agente.01", BLIND_B)
    with pytest.raises(DuplicateUserError) as e2:
        _create(repo, password, "otro.01", BLIND_A)
    for exc in (e1, e2):
        assert "agente.01" not in str(exc.value) and BLIND_A not in str(exc.value)
    assert repo.count() == 1


def test_invalid_role_and_state_rejected_by_check(
    repo: UsuariosRepository, password: PasswordRecord
) -> None:
    with pytest.raises(StorageError):
        _create(repo, password, rol="ROOT")
    user = _create(repo, password)
    with pytest.raises(StorageError):
        repo.set_estado(user.user_id, "BORRADO")  # type: ignore[arg-type]
    with pytest.raises(StorageError):
        repo.set_rol(user.user_id, "ROOT")  # type: ignore[arg-type]


def test_salt_and_hash_length_checks(repo: UsuariosRepository) -> None:
    with pytest.raises(StorageError):
        _create(repo, PasswordRecord(salt=b"short", hash=b"h" * 32, iterations=10))
    with pytest.raises(StorageError):
        _create(repo, PasswordRecord(salt=b"s" * 32, hash=b"short", iterations=10))
    with pytest.raises(StorageError):
        _create(repo, PasswordRecord(salt=b"s" * 32, hash=b"h" * 32, iterations=0))


def test_get_credentials_returns_record(repo: UsuariosRepository, password: PasswordRecord) -> None:
    user = _create(repo, password)
    got = repo.get_credentials(BLIND_A)
    assert got is not None
    found, rec = got
    assert found == user and rec == password
    assert repo.get_credentials(BLIND_B) is None


def test_public_methods_never_return_salt_or_hash(
    repo: UsuariosRepository, password: PasswordRecord
) -> None:
    user = _create(repo, password)
    haystack = repr(user) + repr(repo.list_users()) + repr(repo.get_by_id(user.user_id))
    assert password.hash.hex() not in haystack and password.salt.hex() not in haystack
    assert not hasattr(user, "password_hash") and not hasattr(user, "password_salt")


def test_delete_blocked_by_trigger(repo: UsuariosRepository, password: PasswordRecord) -> None:
    _create(repo, password)
    with pytest.raises(sqlite3.DatabaseError, match="ERR_NO_DELETE_USUARIOS"):
        repo._conn.execute("DELETE FROM usuarios_aduana")  # noqa: SLF001
    assert repo.count() == 1


def test_set_estado_and_rol(repo: UsuariosRepository, password: PasswordRecord) -> None:
    user = _create(repo, password)
    assert repo.set_estado(user.user_id, "SUSPENDIDO").estado == "SUSPENDIDO"
    assert repo.set_rol(user.user_id, "FISCAL_ANTI_CONTRABANDO").rol == "FISCAL_ANTI_CONTRABANDO"
    assert repo.get_by_id(user.user_id).estado == "SUSPENDIDO"  # type: ignore[union-attr]


def test_updates_on_unknown_user_raise_storage_error(repo: UsuariosRepository) -> None:
    with pytest.raises(StorageError):
        repo.set_estado("x", "ACTIVO")
    with pytest.raises(StorageError):
        repo.set_rol("x", ROL)  # type: ignore[arg-type]
    with pytest.raises(StorageError):
        repo.register_successful_login("x", now_utc=NOW_UTC)
    with pytest.raises(StorageError):
        repo.register_failed_attempt("x", max_attempts=5, lockout_seconds=60, now=NOW)


def test_failed_attempts_lock_at_threshold(
    repo: UsuariosRepository, password: PasswordRecord
) -> None:
    user = _create(repo, password)
    for expected in (1, 2, 3, 4):
        u = repo.register_failed_attempt(user.user_id, max_attempts=5, lockout_seconds=900, now=NOW)
        assert u.failed_attempts == expected and u.locked_until_utc is None
    locked = repo.register_failed_attempt(
        user.user_id, max_attempts=5, lockout_seconds=900, now=NOW
    )
    assert locked.failed_attempts == 5
    assert locked.locked_until_utc == "2026-01-01T00:15:00Z"


def test_expired_lock_restarts_the_counter(
    repo: UsuariosRepository, password: PasswordRecord
) -> None:
    user = _create(repo, password)
    for _ in range(3):
        repo.register_failed_attempt(user.user_id, max_attempts=3, lockout_seconds=60, now=NOW)
    later = NOW + timedelta(seconds=61)
    u = repo.register_failed_attempt(user.user_id, max_attempts=3, lockout_seconds=60, now=later)
    assert u.failed_attempts == 1 and u.locked_until_utc is None


def test_successful_login_resets_counter_and_lock(
    repo: UsuariosRepository, password: PasswordRecord
) -> None:
    user = _create(repo, password)
    for _ in range(3):
        repo.register_failed_attempt(user.user_id, max_attempts=3, lockout_seconds=60, now=NOW)
    ok = repo.register_successful_login(user.user_id, now_utc="2026-01-02T00:00:00Z")
    assert ok.failed_attempts == 0 and ok.locked_until_utc is None
    assert ok.last_login_utc == "2026-01-02T00:00:00Z"


def test_list_users_ordered_by_creation(repo: UsuariosRepository, password: PasswordRecord) -> None:
    _create(repo, password, "a.01", BLIND_A)
    _create(repo, password, "a.02", BLIND_B)
    assert [u.codigo_usuario for u in repo.list_users()] == ["a.01", "a.02"]


def test_concurrent_failed_attempts_lose_no_counts(
    repo: UsuariosRepository, password: PasswordRecord
) -> None:
    user = _create(repo, password)
    threads_n, per_thread = 8, 5
    errors: list[BaseException] = []

    def work() -> None:
        try:
            for _ in range(per_thread):
                repo.register_failed_attempt(
                    user.user_id, max_attempts=10_000, lockout_seconds=60, now=NOW
                )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=work) for _ in range(threads_n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert repo.get_by_id(user.user_id).failed_attempts == threads_n * per_thread  # type: ignore[union-attr]


def test_persistence_across_reopen(tmp_path: Path, password: PasswordRecord) -> None:
    path = str(tmp_path / "u.db")
    first = UsuariosRepository(path)
    user = _create(first, password)
    first.close()
    second = UsuariosRepository(path)
    try:
        assert second.get_by_id(user.user_id) == user
        assert second.get_credentials(BLIND_A) is not None
    finally:
        second.close()


@pytest.mark.skipif(os.name == "nt", reason="chmod POSIX")
def test_file_permissions_0600(tmp_path: Path) -> None:
    path = tmp_path / "u.db"
    UsuariosRepository(str(path)).close()
    assert (path.stat().st_mode & 0o777) == 0o600


def test_close_is_idempotent(tmp_path: Path) -> None:
    r = UsuariosRepository(str(tmp_path / "u.db"))
    r.close()
    r.close()
