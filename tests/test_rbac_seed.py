"""Seeders (specs/06 §8) y Zero-PII del archivo .db, más el CLI scripts/seed_usuarios.py."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

from core.auth import normalize_identifier
from core.context import AuthToken
from core.errors import WeakPasswordError
from core.identity import IdentityService
from core.keyring import KeyRing
from core.rbac import ALL_ROLES
from core.rbac_db import UsuariosRepository
from core.rbac_seed import SEED_USERS, seed_users

ROOT = Path(__file__).resolve().parent.parent
HEX_KEY = bytes(range(32)).hex()


def _passwords() -> dict[str, str]:
    return {u.codigo_usuario: f"Semilla-Test-{i:02d}-xyz" for i, u in enumerate(SEED_USERS)}


@pytest.fixture
def repo(tmp_path: Path) -> Iterator[UsuariosRepository]:
    r = UsuariosRepository(str(tmp_path / "u.db"))
    yield r
    r.close()


@pytest.fixture
def svc(repo: UsuariosRepository, keys: KeyRing) -> IdentityService:
    return IdentityService(
        repo, keys, iterations=1000, token_ttl_seconds=60, max_failed_attempts=5, lockout_seconds=60
    )


# 6 roles (uno por rol) + 4 usuarios normales de mínimo privilegio + 2 con acceso a los chats.
EXPECTED_USERS = 12


def test_seed_users_shape() -> None:
    assert isinstance(SEED_USERS, tuple) and len(SEED_USERS) == EXPECTED_USERS
    codes = [u.codigo_usuario for u in SEED_USERS]
    assert len(set(codes)) == EXPECTED_USERS
    roles = Counter(u.rol for u in SEED_USERS)
    assert set(roles) == set(ALL_ROLES)
    assert roles["AGENTE_ADUANAL_CERTIFICADO"] == 3
    assert roles["OPERADOR_LOGISTICO_ALMACEN"] == 3
    for code in (
        "insp.seniat.01",
        "agente.01",
        "fiscal.01",
        "almacen.01",
        "supervisor.01",
        "valoracion.01",
        "agente.02",
        "agente.03",
        "almacen.02",
        "almacen.03",
        "chat.analista.01",
        "chat.analista.02",
    ):
        assert code in codes
    idents = {normalize_identifier(u.identificador) for u in SEED_USERS}
    assert len(idents) == EXPECTED_USERS


def test_seed_identifiers_are_obviously_fictitious() -> None:
    for u in SEED_USERS:
        assert re.search(r"99\d{6}", u.identificador), "prefijo ficticio 99xxxxxx"


def test_seed_users_is_immutable() -> None:
    with pytest.raises(AttributeError):
        SEED_USERS[0].rol = "FISCAL_ANTI_CONTRABANDO"  # type: ignore[misc]


def test_seed_creates_all_and_is_idempotent(svc: IdentityService) -> None:
    created = seed_users(svc, _passwords())
    assert len(created) == EXPECTED_USERS and len(svc.list_users()) == EXPECTED_USERS
    assert seed_users(svc, _passwords()) == []
    assert len(svc.list_users()) == EXPECTED_USERS


def test_seed_skips_existing_by_codigo(svc: IdentityService) -> None:
    first = SEED_USERS[0]
    svc.create_user(
        codigo_usuario=first.codigo_usuario,
        identificador="V-55555555",
        rol=first.rol,
        password="Otra-Clave-12345",  # noqa: S106
    )
    created = seed_users(svc, _passwords())
    assert {u.codigo_usuario for u in created} == {u.codigo_usuario for u in SEED_USERS[1:]}


def test_seed_missing_password_raises_and_creates_nothing(svc: IdentityService) -> None:
    passwords = _passwords()
    del passwords[SEED_USERS[3].codigo_usuario]
    with pytest.raises(KeyError) as exc:
        seed_users(svc, passwords)
    assert SEED_USERS[3].codigo_usuario in str(exc.value)  # el código no es secreto
    assert svc.list_users() == []


def test_seed_weak_password_creates_nothing(svc: IdentityService) -> None:
    passwords = _passwords()
    passwords[SEED_USERS[5].codigo_usuario] = "debil"
    with pytest.raises(WeakPasswordError):
        seed_users(svc, passwords)
    assert svc.list_users() == []


def test_seeded_users_can_login_with_their_password(svc: IdentityService) -> None:
    seed_users(svc, _passwords())
    pws = _passwords()
    for u in SEED_USERS[:3]:
        token = svc.login(u.identificador, pws[u.codigo_usuario])
        assert token.codigo_usuario == u.codigo_usuario and token.rol == u.rol


def test_zero_pii_in_db_wal_and_shm(
    svc: IdentityService, repo: UsuariosRepository, tmp_path: Path
) -> None:
    pws = _passwords()
    seed_users(svc, pws)
    svc.login(SEED_USERS[0].identificador, pws[SEED_USERS[0].codigo_usuario])  # fuerza escrituras
    blobs = b""
    for suffix in ("", "-wal", "-shm"):
        f = tmp_path / f"u.db{suffix}"
        if f.exists():
            blobs += f.read_bytes()
    assert blobs, "el archivo .db debe existir"
    forbidden: list[str] = []
    for u in SEED_USERS:
        digits = re.sub(r"\D", "", u.identificador)
        canon = normalize_identifier(u.identificador)
        forbidden += [
            u.identificador,
            canon,
            digits,
            canon.lower(),
            f"{canon[0]}-{digits}",
            f"{digits[:2]}.{digits[2:5]}.{digits[5:]}",
            f"{canon[0]}-{digits[:2]}.{digits[2:5]}.{digits[5:]}",
        ]
    forbidden += list(pws.values())
    for needle in forbidden:
        assert needle.encode() not in blobs, "PII o contraseña en claro en el .db"
    # El esquema sí debe estar (sanidad del test)
    assert b"usuarios_aduana" in blobs


def test_repr_does_not_leak(svc: IdentityService, repo: UsuariosRepository) -> None:
    pws = _passwords()
    users = seed_users(svc, pws)
    token: AuthToken = svc.login(SEED_USERS[0].identificador, pws[SEED_USERS[0].codigo_usuario])
    creds = repo.get_credentials(users[0].blind_identifier)
    assert creds is not None
    user, record = creds
    for text in (repr(record), str(record)):
        assert record.hash.hex() not in text and record.salt.hex() not in text
    assert token.token not in repr(token) and token.token not in str(token)
    for text in (repr(user), str(user)):
        assert record.hash.hex() not in text and token.token not in text


# --- CLI ---------------------------------------------------------------------------------------


@pytest.fixture
def cli() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "seed_usuarios", ROOT / "scripts" / "seed_usuarios.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["seed_usuarios"] = module
    spec.loader.exec_module(module)
    return module


def _env(tmp_path: Path) -> dict[str, str]:
    return {"ADUANA_MASTER_KEY": HEX_KEY, "ADUANA_USERS_DB_PATH": str(tmp_path / "cli.db")}


def test_cli_requires_master_key(
    cli: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "cred.json"
    code = cli.main(
        ["--output", str(out), "--iterations", "1000"],
        {"ADUANA_USERS_DB_PATH": str(tmp_path / "cli.db")},
    )
    assert code != 0 and not out.exists() and not (tmp_path / "cli.db").exists()
    assert "ADUANA_MASTER_KEY" in capsys.readouterr().err


def test_generated_password_always_meets_policy_even_if_csprng_yields_no_digit(
    cli: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regresión: token_urlsafe puede salir sin dígitos (~1,7 %) y hacía fallar la siembra."""
    candidates = iter(
        ["abcdefghijklmnopqrstuvwx", "ABCDEFGHIJKLMNOPQRSTUVWX", "abcdefghijk-Z_1234567890"]
    )
    monkeypatch.setattr(cli.secrets, "token_urlsafe", lambda _n: next(candidates))
    password = cli.generate_password()
    assert password == "abcdefghijk-Z_1234567890"  # noqa: S105  # descartó los dos sin dígito y reintentó


def test_generated_passwords_are_policy_compliant_and_unique(cli: ModuleType) -> None:
    from core.auth import validate_password_policy

    passwords = [cli.generate_password() for _ in range(500)]
    for password in passwords:
        validate_password_policy(password)
    assert len(set(passwords)) == len(passwords)


def test_cli_seeds_and_writes_credentials_once(
    cli: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "data" / "seed_credenciales.local.json"
    env = _env(tmp_path)
    assert cli.main(["--output", str(out), "--iterations", "1000"], env) == 0
    captured = capsys.readouterr()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert set(data) == {u.codigo_usuario for u in SEED_USERS}
    for entry in data.values():
        assert set(entry) == {"identificador", "password", "rol"}
        assert len(entry["password"]) >= 12
        assert entry["password"] not in captured.out + captured.err
        assert entry["identificador"] not in captured.out + captured.err
    assert str(out) in captured.out and str(EXPECTED_USERS) in captured.out
    if os.name != "nt":
        assert (out.stat().st_mode & 0o777) == 0o600
    # las credenciales escritas permiten iniciar sesión realmente
    keys = KeyRing(bytes.fromhex(HEX_KEY))
    repo = UsuariosRepository(env["ADUANA_USERS_DB_PATH"])
    try:
        svc = IdentityService(
            repo,
            keys,
            iterations=1000,
            token_ttl_seconds=60,
            max_failed_attempts=5,
            lockout_seconds=60,
        )
        entry = data["agente.01"]
        assert svc.login(entry["identificador"], entry["password"]).rol == entry["rol"]
    finally:
        repo.close()


def test_cli_refuses_overwrite_without_force(
    cli: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "cred.json"
    out.write_text("{}", encoding="utf-8")
    code = cli.main(["--output", str(out), "--iterations", "1000"], _env(tmp_path))
    assert code != 0 and out.read_text(encoding="utf-8") == "{}"
    assert not (tmp_path / "cli.db").exists()  # falla antes de sembrar
    assert "--force" in capsys.readouterr().err


def test_cli_force_overwrites(cli: ModuleType, tmp_path: Path) -> None:
    out = tmp_path / "cred.json"
    out.write_text("{}", encoding="utf-8")
    assert cli.main(["--output", str(out), "--iterations", "1000", "--force"], _env(tmp_path)) == 0
    assert len(json.loads(out.read_text(encoding="utf-8"))) == EXPECTED_USERS


def test_cli_rerun_on_seeded_db_creates_nothing_and_keeps_file(
    cli: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "cred.json"
    env = _env(tmp_path)
    assert cli.main(["--output", str(out), "--iterations", "1000"], env) == 0
    before = out.read_text(encoding="utf-8")
    capsys.readouterr()
    # la CLI consume (elimina) ADUANA_MASTER_KEY del entorno, como load_keys_from_env
    assert cli.main(["--output", str(out), "--iterations", "1000", "--force"], _env(tmp_path)) == 0
    assert out.read_text(encoding="utf-8") == before  # no se pierden credenciales previas
    assert "0 usuarios" in capsys.readouterr().out


def test_gitignore_covers_credentials_file() -> None:
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "data/seed_credenciales*.json" in text.splitlines()
