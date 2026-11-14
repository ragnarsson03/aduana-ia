"""Arranque local con RBAC: llave persistente, ADUANA_RBAC=1 y siembra única de usuarios."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from app.rbac_bootstrap import (
    CREDENTIALS_FILENAME,
    KEY_FILENAME,
    BootstrapError,
    prepare_rbac_environment,
)
from core.identity import IdentityService
from core.keyring import KeyRing
from core.rbac_db import UsuariosRepository
from core.rbac_seed import SEED_USERS

ITERATIONS = 1000


def _env(tmp_path: Path) -> dict[str, str]:
    return {"ADUANA_USERS_DB_PATH": str(tmp_path / "usuarios.db")}


def _prepare(tmp_path: Path, env: dict[str, str]) -> bool:
    return prepare_rbac_environment(env, data_dir=tmp_path, iterations=ITERATIONS)


def test_first_run_creates_key_enables_rbac_and_seeds_users(tmp_path: Path) -> None:
    env = _env(tmp_path)
    assert _prepare(tmp_path, env) is True
    key_text = (tmp_path / KEY_FILENAME).read_text(encoding="ascii").strip()
    assert len(bytes.fromhex(key_text)) >= 32
    assert env["ADUANA_MASTER_KEY"] == key_text and env["ADUANA_RBAC"] == "1"
    credentials = json.loads((tmp_path / CREDENTIALS_FILENAME).read_text(encoding="utf-8"))
    assert set(credentials) == {u.codigo_usuario for u in SEED_USERS}


def test_seeded_credentials_can_really_log_in(tmp_path: Path) -> None:
    env = _env(tmp_path)
    _prepare(tmp_path, env)
    credentials = json.loads((tmp_path / CREDENTIALS_FILENAME).read_text(encoding="utf-8"))
    repo = UsuariosRepository(env["ADUANA_USERS_DB_PATH"])
    try:
        service = IdentityService(
            repo,
            KeyRing(bytes.fromhex(env["ADUANA_MASTER_KEY"])),
            iterations=ITERATIONS,
            token_ttl_seconds=60,
            max_failed_attempts=5,
            lockout_seconds=60,
        )
        entry = credentials["chat.analista.01"]
        token = service.login(entry["identificador"], entry["password"])
        assert token.rol == "ANALISTA_VALORACION_ADUANERA"
    finally:
        repo.close()


def test_second_run_reuses_key_and_does_not_reseed_or_touch_credentials(tmp_path: Path) -> None:
    first = _env(tmp_path)
    _prepare(tmp_path, first)
    key_before = (tmp_path / KEY_FILENAME).read_text(encoding="ascii")
    creds_before = (tmp_path / CREDENTIALS_FILENAME).read_text(encoding="utf-8")

    second = _env(tmp_path)
    assert _prepare(tmp_path, second) is True
    assert (tmp_path / KEY_FILENAME).read_text(encoding="ascii") == key_before
    assert second["ADUANA_MASTER_KEY"] == key_before.strip()
    assert (tmp_path / CREDENTIALS_FILENAME).read_text(encoding="utf-8") == creds_before


def test_key_from_environment_wins_and_no_key_file_is_written(tmp_path: Path) -> None:
    env = {**_env(tmp_path), "ADUANA_MASTER_KEY": bytes(range(32)).hex()}
    _prepare(tmp_path, env)
    assert not (tmp_path / KEY_FILENAME).exists()
    assert env["ADUANA_MASTER_KEY"] == bytes(range(32)).hex()


def test_explicitly_disabled_rbac_changes_nothing(tmp_path: Path) -> None:
    env = {**_env(tmp_path), "ADUANA_RBAC": "0"}
    assert _prepare(tmp_path, env) is False
    assert env == {**_env(tmp_path), "ADUANA_RBAC": "0"}
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("content", ["no-es-hex", "abcd", ""])
def test_invalid_key_file_fails_without_leaking_its_content(tmp_path: Path, content: str) -> None:
    (tmp_path / KEY_FILENAME).write_text(content, encoding="ascii")
    with pytest.raises(BootstrapError) as exc:
        _prepare(tmp_path, _env(tmp_path))
    assert content not in str(exc.value) or content == ""
    assert not (tmp_path / CREDENTIALS_FILENAME).exists()


def test_key_and_passwords_are_never_printed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    env = _env(tmp_path)
    _prepare(tmp_path, env)
    output = capsys.readouterr()
    secrets_text = output.out + output.err
    assert env["ADUANA_MASTER_KEY"] not in secrets_text
    credentials = json.loads((tmp_path / CREDENTIALS_FILENAME).read_text(encoding="utf-8"))
    for entry in credentials.values():
        assert entry["password"] not in secrets_text


@pytest.mark.skipif(os.name == "nt", reason="los permisos POSIX no aplican en Windows")
def test_key_file_is_private_on_posix(tmp_path: Path) -> None:
    _prepare(tmp_path, _env(tmp_path))
    assert ((tmp_path / KEY_FILENAME).stat().st_mode & 0o777) == 0o600
