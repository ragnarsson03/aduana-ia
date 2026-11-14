"""Consentimiento (RF0) y Rate-Guard. Reloj inyectado: sin dormir."""

from __future__ import annotations

import pytest

from core import crypto
from core.errors import ConsentError, RateLimitError
from pipeline.stage0_consent import RateGuard, validate_consent

TS = "2026-11-13T10:00:00Z"


@pytest.mark.parametrize(("granted", "purpose"), [(False, "BECA"), (True, ""), (True, "   ")])
def test_consent_required(granted: bool, purpose: str) -> None:
    with pytest.raises(ConsentError):
        validate_consent("fixture-001", granted, purpose, TS, "b" * 64)


def test_consent_digest_is_binding() -> None:
    a = validate_consent("fixture-001", True, "BECA", TS, "b" * 64)
    assert a.granted and a.purpose_code == "BECA" and a.timestamp_utc == TS
    assert a.consent_hash == crypto.consent_hash("fixture-001", TS, "BECA", "b" * 64)
    assert a == validate_consent("fixture-001", True, "BECA", TS, "b" * 64)
    assert a.consent_hash != validate_consent("fixture-001", True, "SALUD", TS, "b" * 64).consent_hash
    assert a.consent_hash != validate_consent("fixture-001", True, "BECA", TS, "c" * 64).consent_hash


class Clock:
    now = 100.0

    def __call__(self) -> float:
        return self.now


def test_rate_guard_sliding_window() -> None:
    clock = Clock()
    guard = RateGuard(2, clock=clock)
    guard.check("a")
    guard.check("a")
    with pytest.raises(RateLimitError):
        guard.check("a")
    guard.check("b")  # otro índice, independiente
    clock.now += 59.9
    with pytest.raises(RateLimitError):
        guard.check("a")
    clock.now += 0.2  # 60.1 s después de los primeros accesos
    guard.check("a")


def test_rejected_attempts_do_not_extend_the_block() -> None:
    clock = Clock()
    guard = RateGuard(1, clock=clock)
    guard.check("a")
    for _ in range(10):
        with pytest.raises(RateLimitError):
            guard.check("a")
    clock.now += 60.0
    guard.check("a")


def test_rate_guard_memory_is_bounded_and_fails_closed() -> None:
    clock = Clock()
    guard = RateGuard(5, max_keys=3, clock=clock)
    for key in ("a", "b", "c"):
        guard.check(key)
    with pytest.raises(RateLimitError):
        guard.check("d")  # tabla llena de claves vigentes
    clock.now += 61
    guard.check("d")  # las vencidas se podan


def test_rate_guard_error_does_not_echo_key() -> None:
    guard = RateGuard(1)
    guard.check("secret-key")
    with pytest.raises(RateLimitError) as info:
        guard.check("secret-key")
    assert "secret-key" not in str(info.value)


def test_rate_guard_rejects_non_positive_limit() -> None:
    with pytest.raises(ValueError):
        RateGuard(0)


def test_rate_guard_exact_limit_under_concurrency() -> None:
    from concurrent.futures import ThreadPoolExecutor

    guard = RateGuard(50)
    outcomes: list[bool] = []

    def hit(_: int) -> None:
        for _ in range(20):
            try:
                guard.check("k")
                outcomes.append(True)
            except RateLimitError:
                outcomes.append(False)

    with ThreadPoolExecutor(8) as pool:
        for future in [pool.submit(hit, n) for n in range(8)]:
            future.result()
    assert outcomes.count(True) == 50 and outcomes.count(False) == 110


def test_full_table_prune_is_throttled() -> None:
    clock = Clock()
    guard = RateGuard(5, max_keys=2, clock=clock)
    guard.check("a")
    guard.check("b")
    calls = 0
    original = guard._prune

    def counting(cutoff: float) -> None:
        nonlocal calls
        calls += 1
        original(cutoff)

    guard._prune = counting  # type: ignore[method-assign]
    for i in range(50):
        with pytest.raises(RateLimitError):
            guard.check(f"new{i}")
    assert calls <= 1  # a lo sumo una poda por segundo


def test_rate_guard_thread_safety() -> None:
    from concurrent.futures import ThreadPoolExecutor

    guard = RateGuard(1000)

    def hit(_: int) -> None:
        for _ in range(100):
            guard.check("k")

    with ThreadPoolExecutor(8) as pool:
        for future in [pool.submit(hit, n) for n in range(8)]:
            future.result()  # propaga cualquier excepción
    assert len(guard._hits["k"]) == 800  # sin pérdidas por carreras
    guard.check("k")
