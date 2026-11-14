"""Pruebas de resiliencia del Circuit Breaker y adaptadores LLM (CA-06, RF-11, RF-12)."""

from __future__ import annotations

import asyncio
import time
from typing import ClassVar

from core.context import AdapterMode
from core.errors import LLMUnavailableError
from pipeline.llm_adapter import (
    CircuitBreaker,
    OfflineDeterministicAdapter,
)


class MockLLMAdapter:
    mode: ClassVar[AdapterMode] = "LOCAL_OLLAMA"

    def __init__(self, response: str = "OK", should_fail: bool = False, delay_s: float = 0.0) -> None:
        self.response = response
        self.should_fail = should_fail
        self.delay_s = delay_s
        self.call_count = 0

    async def complete(self, prompt: str, *, timeout_s: float) -> str:
        self.call_count += 1
        if self.delay_s > 0:
            await asyncio.sleep(self.delay_s)
        if self.should_fail:
            raise LLMUnavailableError("Error de conexión simulado con LLM.")
        return self.response


def test_circuit_breaker_primary_success() -> None:
    async def _run() -> None:
        primary = MockLLMAdapter(response="Respuesta exitosa de Ollama")
        fallback = OfflineDeterministicAdapter()
        breaker = CircuitBreaker(primary, fallback, timeout_s=1.0)

        res = await breaker.exchange("<prompt seguro>")

        assert res.adapter_mode == "LOCAL_OLLAMA"
        assert res.circuit_breaker_tripped is False
        assert res.ai_generated_notice is True
        assert res.raw_response == "Respuesta exitosa de Ollama"
        assert primary.call_count == 1
        assert len(res.prompt_sent_hash) == 64

    asyncio.run(_run())


def test_ca06_llm_failover_under_100ms() -> None:
    """CA-06: Con circuito abierto el failover al generador determinista responde en < 100 ms."""
    async def _run() -> None:
        primary = MockLLMAdapter(should_fail=True)
        fallback = OfflineDeterministicAdapter()
        clock_time = 1000.0

        def mock_clock() -> float:
            return clock_time

        breaker = CircuitBreaker(
            primary,
            fallback,
            timeout_s=0.05,
            failure_threshold=1,
            cooldown_s=30.0,
            clock=mock_clock,
        )

        # Primer fallo: abre el circuito
        res1 = await breaker.exchange("prompt 1")
        assert res1.circuit_breaker_tripped is True
        assert res1.adapter_mode == "OFFLINE_DETERMINISTIC_FALLBACK"

        # Segundo intento con circuito abierto: failover inmediato (< 100 ms)
        start = time.perf_counter()
        res2 = await breaker.exchange("prompt 2")
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        assert elapsed_ms < 100.0, f"Failover tardó {elapsed_ms:.2f} ms (debe ser < 100 ms)"
        assert res2.circuit_breaker_tripped is True
        assert res2.adapter_mode == "OFFLINE_DETERMINISTIC_FALLBACK"
        assert "determinista" in res2.raw_response.lower()
        # No debió llamar a primary la segunda vez porque el circuito está abierto
        assert primary.call_count == 1

    asyncio.run(_run())


def test_circuit_breaker_half_open_recovery() -> None:
    async def _run() -> None:
        primary = MockLLMAdapter(should_fail=True)
        fallback = OfflineDeterministicAdapter()
        current_time = [100.0]

        def clock() -> float:
            return current_time[0]

        breaker = CircuitBreaker(
            primary,
            fallback,
            timeout_s=0.05,
            failure_threshold=1,
            cooldown_s=10.0,
            clock=clock,
        )

        await breaker.exchange("p1")
        assert breaker.state == "OPEN"

        # Avanzar el reloj más allá del cooldown: pasa a HALF_OPEN
        current_time[0] = 115.0
        primary.should_fail = False
        primary.response = "Recuperado"

        res = await breaker.exchange("p2")
        assert res.circuit_breaker_tripped is False
        assert res.raw_response == "Recuperado"
        assert breaker.state == "CLOSED"

    asyncio.run(_run())


def test_offline_deterministic_adapter_zero_random() -> None:
    async def _run() -> None:
        adapter = OfflineDeterministicAdapter()
        r1 = await adapter.complete("expediente 1", timeout_s=1.0)
        r2 = await adapter.complete("expediente 1", timeout_s=1.0)

        assert r1 == r2
        assert len(r1) > 20

    asyncio.run(_run())
