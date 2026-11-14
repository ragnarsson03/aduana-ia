"""Gatillo 0 — EphemeralVault: TTL, zeroize, tope de sesiones, sin raw_input."""

from __future__ import annotations

import pytest

from core.ephemeral_vault import EphemeralVault
from core.errors import VaultError, VaultExpiredError, VaultSessionNotFoundError

PII = {"[CEDULA_1]": "V-12345678", "[PHONE_1]": "0414-1234567"}


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def vault(clock: FakeClock) -> EphemeralVault:
    return EphemeralVault(ttl_seconds=180, max_sessions=3, clock=clock)


def test_put_and_get_roundtrip(vault: EphemeralVault) -> None:
    vault.put("r1", PII)
    assert dict(vault.get_map("r1")) == PII
    assert vault.active_sessions == 1


def test_get_map_is_read_only_copy(vault: EphemeralVault) -> None:
    vault.put("r1", PII)
    view = vault.get_map("r1")
    with pytest.raises(TypeError):
        view["[CEDULA_1]"] = "x"  # type: ignore[index]


def test_unknown_session_raises(vault: EphemeralVault) -> None:
    with pytest.raises(VaultSessionNotFoundError):
        vault.get_map("nope")


def test_ttl_boundary_is_strictly_greater_than_180s(
    vault: EphemeralVault, clock: FakeClock
) -> None:
    vault.put("r1", PII)
    clock.now += 180.0
    assert dict(vault.get_map("r1")) == PII  # exactamente 180 s: vigente
    clock.now += 0.001
    with pytest.raises(VaultExpiredError):
        vault.get_map("r1")


def test_expired_session_is_purged_after_failed_get(
    vault: EphemeralVault, clock: FakeClock
) -> None:
    vault.put("r1", PII)
    clock.now += 181
    with pytest.raises(VaultExpiredError):
        vault.get_map("r1")
    assert vault.active_sessions == 0
    with pytest.raises(VaultSessionNotFoundError):
        vault.get_map("r1")


def test_active_sessions_excludes_expired(vault: EphemeralVault, clock: FakeClock) -> None:
    vault.put("old", PII)
    clock.now += 100
    vault.put("new", PII)
    clock.now += 81  # old: 181 s, new: 81 s
    assert vault.active_sessions == 1


def test_purge_expired_returns_count(vault: EphemeralVault, clock: FakeClock) -> None:
    vault.put("a", PII)
    vault.put("b", PII)
    clock.now += 181
    assert vault.purge_expired() == 2
    assert vault.purge_expired() == 0


def test_zeroize_overwrites_buffers_before_removal(vault: EphemeralVault) -> None:
    vault.put("r1", PII)
    _, buffers = vault._sessions["r1"]  # white-box: referencias a los bytearray reales
    held = list(buffers.values())
    assert any(any(b) for b in held)
    vault.zeroize("r1")
    assert all(not any(b) for b in held)  # todos a 0x00
    assert vault.active_sessions == 0
    with pytest.raises(VaultSessionNotFoundError):
        vault.get_map("r1")


def test_zeroize_is_idempotent(vault: EphemeralVault) -> None:
    vault.zeroize("never-existed")
    vault.put("r1", PII)
    vault.zeroize("r1")
    vault.zeroize("r1")


def test_zeroize_all_wipes_everything(vault: EphemeralVault) -> None:
    vault.put("a", PII)
    vault.put("b", PII)
    held = [list(buf.values()) for _, buf in vault._sessions.values()]
    vault.zeroize_all()
    assert vault.active_sessions == 0
    assert all(not any(b) for group in held for b in group)


def test_capacity_limit_raises_but_expired_sessions_free_space(
    vault: EphemeralVault, clock: FakeClock
) -> None:
    for rid in ("a", "b", "c"):
        vault.put(rid, PII)
    with pytest.raises(VaultError):
        vault.put("d", PII)
    clock.now += 181
    vault.put("d", PII)  # purga oportunista libera cupo
    assert vault.active_sessions == 1


def test_put_same_request_id_replaces_and_wipes_previous(vault: EphemeralVault) -> None:
    vault.put("r1", {"[CEDULA_1]": "V-11111111"})
    old_buffers = list(vault._sessions["r1"][1].values())
    vault.put("r1", {"[CEDULA_1]": "V-22222222"})
    assert all(not any(b) for b in old_buffers)
    assert dict(vault.get_map("r1")) == {"[CEDULA_1]": "V-22222222"}


def test_put_with_invalid_value_keeps_previous_session_and_does_not_echo(
    vault: EphemeralVault,
) -> None:
    vault.put("r1", {"[CEDULA_1]": "V-11111111"})
    for bad in ({"[CEDULA_1]": 5}, {"[CEDULA_1]": "V-\ud800"}):
        with pytest.raises(VaultError) as info:
            vault.put("r1", bad)  # type: ignore[arg-type]
        assert "V-" not in str(info.value)
    assert dict(vault.get_map("r1")) == {"[CEDULA_1]": "V-11111111"}


@pytest.mark.parametrize("kwargs", [{"ttl_seconds": 0}, {"ttl_seconds": -1}, {"max_sessions": 0}])
def test_constructor_validates_parameters(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        EphemeralVault(**kwargs)


def test_default_ttl_is_180_seconds() -> None:
    from core.config import VAULT_TTL_SECONDS

    assert VAULT_TTL_SECONDS == 180
    assert EphemeralVault()._ttl_seconds == 180


def test_returned_map_is_independent_copy(vault: EphemeralVault) -> None:
    vault.put("r1", PII)
    view = vault.get_map("r1")
    vault.zeroize("r1")
    assert dict(view) == PII  # la copia sobrevive (limitación de CPython documentada)
    assert not vault._sessions


def test_concurrent_use_is_safe_and_respects_capacity() -> None:
    from concurrent.futures import ThreadPoolExecutor

    shared = EphemeralVault(ttl_seconds=180, max_sessions=50)

    def worker(n: int) -> None:
        for i in range(200):
            rid = f"r{n}-{i % 5}"
            try:
                shared.put(rid, PII)
                shared.get_map(rid)
            except (VaultError, VaultSessionNotFoundError):
                pass
            shared.purge_expired()
            shared.zeroize(rid)
            assert len(shared._sessions) <= 50

    with ThreadPoolExecutor(max_workers=8) as pool:
        for future in [pool.submit(worker, n) for n in range(8)]:
            future.result()  # propaga cualquier excepción
    shared.zeroize_all()
    assert shared.active_sessions == 0


def test_vault_does_not_store_raw_input_api() -> None:
    import inspect

    assert list(inspect.signature(EphemeralVault.put).parameters) == [
        "self",
        "request_id",
        "token_map",
    ]
