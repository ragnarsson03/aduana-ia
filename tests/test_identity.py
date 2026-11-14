"""IdentityService (specs/06 §5-§7): login uniforme, bloqueo, tokens Zero-Trust, autorización."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from core import identity as identity_module
from core.errors import (
    AccountLockedError,
    AuthenticationError,
    AuthorizationError,
    DuplicateUserError,
    InvalidTokenError,
    WeakPasswordError,
)
from core.identity import IdentityService
from core.keyring import KeyRing
from core.rbac import ALL_PERMISSIONS, has_permission
from core.rbac_db import UsuariosRepository

PW = "Clave-De-Prueba-42"  # noqa: S105
CED = "V-12.345.678"
START = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self) -> None:
        self.now = START

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kwargs: float) -> None:
        self.now += timedelta(**kwargs)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def repo(tmp_path: Path) -> Iterator[UsuariosRepository]:
    r = UsuariosRepository(str(tmp_path / "u.db"))
    yield r
    r.close()


@pytest.fixture
def svc(repo: UsuariosRepository, keys: KeyRing, clock: FakeClock) -> IdentityService:
    return IdentityService(
        repo,
        keys,
        iterations=1000,
        token_ttl_seconds=1800,
        max_failed_attempts=5,
        lockout_seconds=900,
        clock=clock,
    )


@pytest.fixture
def agente(svc: IdentityService):  # type: ignore[no-untyped-def]
    return svc.create_user(
        codigo_usuario="agente.01", identificador=CED, rol="AGENTE_ADUANAL_CERTIFICADO", password=PW
    )


def test_create_user_stores_blind_index_only(svc: IdentityService, agente, keys: KeyRing) -> None:  # type: ignore[no-untyped-def]
    from core.crypto import blind_citizen_id

    assert agente.blind_identifier == blind_citizen_id(keys, CED)
    assert "12345678" not in repr(agente) and "12.345" not in repr(agente)


def test_create_user_policy_and_identifier_errors(svc: IdentityService) -> None:
    with pytest.raises(WeakPasswordError) as exc:
        svc.create_user(
            codigo_usuario="a.01",
            identificador=CED,
            rol="AGENTE_ADUANAL_CERTIFICADO",
            password="corta1",  # noqa: S106
        )
    assert "corta1" not in str(exc.value)
    with pytest.raises(ValueError) as exc2:
        svc.create_user(
            codigo_usuario="a.01",
            identificador="basura",
            rol="AGENTE_ADUANAL_CERTIFICADO",
            password=PW,
        )
    assert "basura" not in str(exc2.value)
    assert svc.list_users() == []


def test_create_user_duplicate_by_formatting_variants(svc: IdentityService, agente) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(DuplicateUserError):
        svc.create_user(
            codigo_usuario="otro.01",
            identificador="12345678",
            rol="AGENTE_ADUANAL_CERTIFICADO",
            password=PW,
        )


def test_login_success_returns_token_and_resets_state(
    svc: IdentityService, agente, clock: FakeClock
) -> None:  # type: ignore[no-untyped-def]
    for _ in range(3):
        with pytest.raises(AuthenticationError):
            svc.login(CED, "mala-clave-123")
    token = svc.login("V12345678", PW)  # otro formato del mismo identificador
    assert token.codigo_usuario == "agente.01" and token.rol == agente.rol
    assert token.expires_at - token.issued_at == 1800
    assert token.issued_at == int(START.timestamp())
    user = svc.resolve_token(token.token)
    assert user.failed_attempts == 0 and user.locked_until_utc is None
    assert user.last_login_utc == "2026-03-01T12:00:00Z"


def test_login_errors_are_uniform(svc: IdentityService, agente) -> None:  # type: ignore[no-untyped-def]
    svc.create_user(
        codigo_usuario="s.01",
        identificador="V-23456789",
        rol="AGENTE_ADUANAL_CERTIFICADO",
        password=PW,
    )
    suspended = svc.list_users()[1]
    svc.suspend_user(suspended.user_id)
    attempts = [
        (CED, "mala-clave-123"),  # contraseña errónea
        ("V-99999999", PW),  # usuario inexistente
        ("V-23456789", PW),  # suspendido con clave correcta
        ("basura", PW),  # identificador inválido
        ("", ""),
    ]
    messages = set()
    for ident, pw in attempts:
        with pytest.raises(AuthenticationError) as exc:
            svc.login(ident, pw)
        assert not isinstance(exc.value, AccountLockedError)
        messages.add((type(exc.value), str(exc.value)))
        assert pw not in str(exc.value) or pw == ""
    assert len(messages) == 1


def test_non_string_inputs_are_uniform_errors(svc: IdentityService) -> None:
    with pytest.raises(AuthenticationError):
        svc.login(None, None)  # type: ignore[arg-type]


def test_missing_user_still_runs_a_kdf(
    svc: IdentityService, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[int] = []
    real = identity_module.derive_key

    def spy(password: str, salt: bytes, iterations: int) -> bytes:
        calls.append(iterations)
        return real(password, salt, iterations)

    monkeypatch.setattr(identity_module, "derive_key", spy)
    with pytest.raises(AuthenticationError):
        svc.login("V-99999999", PW)
    with pytest.raises(AuthenticationError):
        svc.login("basura", PW)
    assert calls == [1000, 1000]


def test_suspended_user_still_runs_a_kdf(
    svc: IdentityService,
    agente,
    monkeypatch: pytest.MonkeyPatch,  # type: ignore[no-untyped-def]
) -> None:
    svc.suspend_user(agente.user_id)
    calls: list[int] = []
    real = identity_module.derive_key
    monkeypatch.setattr(
        identity_module, "derive_key", lambda p, s, i: (calls.append(i), real(p, s, i))[1]
    )
    with pytest.raises(AuthenticationError):
        svc.login(CED, PW)
    assert calls == [1000]


def test_lockout_after_five_failures_even_with_correct_password(
    svc: IdentityService,
    agente,
    clock: FakeClock,  # type: ignore[no-untyped-def]
) -> None:
    for _ in range(5):
        with pytest.raises(AuthenticationError):
            svc.login(CED, "mala-clave-123")
    with pytest.raises(AccountLockedError):
        svc.login(CED, PW)
    clock.advance(seconds=899)
    with pytest.raises(AccountLockedError):
        svc.login(CED, PW)
    clock.advance(seconds=2)  # 901 s > 900 s
    assert svc.login(CED, PW).token


def test_failures_after_lock_expiry_restart_the_count(
    svc: IdentityService,
    agente,
    clock: FakeClock,  # type: ignore[no-untyped-def]
) -> None:
    for _ in range(5):
        with pytest.raises(AuthenticationError):
            svc.login(CED, "mala-clave-123")
    clock.advance(seconds=901)
    with pytest.raises(AuthenticationError):
        svc.login(CED, "mala-clave-123")
    assert svc.login(CED, PW).token  # un solo fallo nuevo no vuelve a bloquear


def test_success_resets_counter(svc: IdentityService, agente) -> None:  # type: ignore[no-untyped-def]
    for _ in range(4):
        with pytest.raises(AuthenticationError):
            svc.login(CED, "mala-clave-123")
    svc.login(CED, PW)
    for _ in range(4):
        with pytest.raises(AuthenticationError):
            svc.login(CED, "mala-clave-123")
    assert svc.login(CED, PW).token  # sigue sin bloquear: el contador se reinició


def test_resolve_token_returns_current_db_state(svc: IdentityService, agente) -> None:  # type: ignore[no-untyped-def]
    token = svc.login(CED, PW)
    svc.change_role(agente.user_id, "FISCAL_ANTI_CONTRABANDO")
    assert svc.resolve_token(token.token).rol == "FISCAL_ANTI_CONTRABANDO"  # no el del token


def test_resolve_token_after_suspension_fails_immediately(svc: IdentityService, agente) -> None:  # type: ignore[no-untyped-def]
    token = svc.login(CED, PW)
    svc.suspend_user(agente.user_id)
    with pytest.raises(AuthenticationError):
        svc.resolve_token(token.token)
    svc.reactivate_user(agente.user_id)
    assert svc.resolve_token(token.token).estado == "ACTIVO"


def test_resolve_token_expiry_and_garbage(svc: IdentityService, agente, clock: FakeClock) -> None:  # type: ignore[no-untyped-def]
    token = svc.login(CED, PW)
    clock.advance(seconds=1799)
    svc.resolve_token(token.token)
    clock.advance(seconds=1)
    with pytest.raises(InvalidTokenError):
        svc.resolve_token(token.token)
    with pytest.raises(AuthenticationError):
        svc.resolve_token("v1.x.y")


def test_resolve_token_unknown_user(
    svc: IdentityService, keys: KeyRing, clock: FakeClock, tmp_path: Path
) -> None:
    other_repo = UsuariosRepository(str(tmp_path / "other.db"))
    other = IdentityService(
        other_repo,
        keys,
        iterations=1000,
        token_ttl_seconds=60,
        max_failed_attempts=5,
        lockout_seconds=60,
        clock=clock,
    )
    other.create_user(
        codigo_usuario="x.01", identificador=CED, rol="AGENTE_ADUANAL_CERTIFICADO", password=PW
    )
    token = other.login(CED, PW)
    other_repo.close()
    with pytest.raises(AuthenticationError):
        svc.resolve_token(token.token)  # firma válida (misma llave) pero el usuario no existe aquí


def test_authorize_matches_policy_with_fixed_message(svc: IdentityService, agente) -> None:  # type: ignore[no-untyped-def]
    messages = set()
    for perm in ALL_PERMISSIONS:
        if has_permission(agente.rol, perm):  # type: ignore[arg-type]
            svc.authorize(agente, perm)  # type: ignore[arg-type]
        else:
            with pytest.raises(AuthorizationError) as exc:
                svc.authorize(agente, perm)  # type: ignore[arg-type]
            messages.add(str(exc.value))
            assert perm not in str(exc.value)
    assert len(messages) == 1


def test_default_clock_is_utc_aware() -> None:
    now = identity_module.utcnow()
    assert now.tzinfo is not None and now.utcoffset() == timedelta(0)


def test_service_with_default_clock(repo: UsuariosRepository, keys: KeyRing) -> None:
    s = IdentityService(
        repo, keys, iterations=1000, token_ttl_seconds=60, max_failed_attempts=3, lockout_seconds=60
    )
    s.create_user(
        codigo_usuario="d.01", identificador=CED, rol="OPERADOR_LOGISTICO_ALMACEN", password=PW
    )
    assert s.resolve_token(s.login(CED, PW).token).codigo_usuario == "d.01"


def test_rif_login(svc: IdentityService) -> None:
    from core.crypto import rif_mod11_valid

    rif = next(f"J30123456{d}" for d in range(10) if rif_mod11_valid(f"J30123456{d}"))
    svc.create_user(
        codigo_usuario="rif.01", identificador=rif, rol="AGENTE_ADUANAL_CERTIFICADO", password=PW
    )
    dashed = f"{rif[0]}-{rif[1:9]}-{rif[9]}"
    assert svc.login(dashed, PW).codigo_usuario == "rif.01"


def test_invalid_constructor_params(repo: UsuariosRepository, keys: KeyRing) -> None:
    with pytest.raises(ValueError):
        IdentityService(
            repo,
            keys,
            iterations=0,
            token_ttl_seconds=60,
            max_failed_attempts=5,
            lockout_seconds=60,
        )
