"""Pruebas de aceptación CA-06 y resiliencia LLM (Gatillo 5, specs/05_interconnect.spec.md)."""

from __future__ import annotations

import asyncio
import json
import socket
import time
from typing import ClassVar

import httpx
import pytest

from core.config import LLM_TIMEOUT_SECONDS
from core.context import AdapterMode, LLMExchangeResult
from core.crypto import sha256_hex
from core.errors import LLMUnavailableError
from pipeline.llm_adapter import (
    CircuitBreaker,
    OfflineDeterministicAdapter,
    OllamaAdapter,
    OpenAICompatAdapter,
)
from pipeline.stage3_guard_out import guard_out


class _FakeClock:
    def __init__(self, start: float = 100.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class _SuccessAdapter:
    mode: ClassVar[AdapterMode] = "LOCAL_OLLAMA"

    def __init__(self, response: str = "Resumen orientativo [CEDULA_1]") -> None:
        self.response = response
        self.calls: list[tuple[str, float]] = []

    async def complete(self, prompt: str, *, timeout_s: float) -> str:
        self.calls.append((prompt, timeout_s))
        return self.response


class _UnsafeFallbackAdapter:
    mode: ClassVar[AdapterMode] = "OFFLINE_DETERMINISTIC_FALLBACK"

    def __init__(self, response: str) -> None:
        self.response = response

    async def complete(self, prompt: str, *, timeout_s: float) -> str:
        return self.response


class _FailingAdapter:
    mode: ClassVar[AdapterMode] = "LOCAL_OLLAMA"

    def __init__(self, message: str = "servicio no disponible") -> None:
        self.message = message
        self.calls: list[tuple[str, float]] = []

    async def complete(self, prompt: str, *, timeout_s: float) -> str:
        self.calls.append((prompt, timeout_s))
        raise LLMUnavailableError(self.message)


class _SlowAdapter:
    mode: ClassVar[AdapterMode] = "LOCAL_OLLAMA"

    def __init__(self, delay_s: float) -> None:
        self.delay_s = delay_s
        self.calls: list[tuple[str, float]] = []

    async def complete(self, prompt: str, *, timeout_s: float) -> str:
        self.calls.append((prompt, timeout_s))
        await asyncio.sleep(self.delay_s)
        return "tardío"


@pytest.mark.unit
def test_primary_success() -> None:
    primary = _SuccessAdapter("Resumen orientativo [CEDULA_1]")
    fallback = OfflineDeterministicAdapter()
    breaker = CircuitBreaker(primary, fallback)

    prompt = "Solicitud de [CEDULA_1] para beca."
    result = asyncio.run(breaker.exchange(prompt))

    assert isinstance(result, LLMExchangeResult)
    assert result.adapter_mode == "LOCAL_OLLAMA"
    assert result.ai_generated_notice is True
    assert result.circuit_breaker_tripped is False
    assert result.raw_response == "Resumen orientativo [CEDULA_1]"
    assert result.prompt_sent_hash == sha256_hex(prompt.encode("utf-8"))
    assert len(primary.calls) == 1
    assert primary.calls[0][1] == LLM_TIMEOUT_SECONDS


@pytest.mark.unit
def test_immediate_failure_failover_under_100ms() -> None:
    primary = _FailingAdapter()
    fallback = OfflineDeterministicAdapter()
    breaker = CircuitBreaker(primary, fallback)

    t0 = time.perf_counter()
    result = asyncio.run(breaker.exchange("Trámite de [CEDULA_1]"))
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert result.adapter_mode == "OFFLINE_DETERMINISTIC_FALLBACK"
    assert result.ai_generated_notice is True
    assert result.circuit_breaker_tripped is True
    assert elapsed_ms < 100.0


@pytest.mark.unit
def test_timeout_triggers_fallback_with_fast_transition() -> None:
    # Timeout corto en test para validar el mecanismo sin esperar 3.5 s reales.
    primary = _SlowAdapter(delay_s=0.5)
    fallback = OfflineDeterministicAdapter()
    breaker = CircuitBreaker(primary, fallback, timeout_s=0.05)

    t0 = time.perf_counter()
    result = asyncio.run(breaker.exchange("Trámite de [CEDULA_1]"))
    total_ms = (time.perf_counter() - t0) * 1000.0

    assert result.adapter_mode == "OFFLINE_DETERMINISTIC_FALLBACK"
    assert result.circuit_breaker_tripped is True
    assert result.ai_generated_notice is True
    assert len(primary.calls) == 1
    assert primary.calls[0][1] == 0.05
    # El timeout fue 50 ms y la transición + fallback debe quedar muy por debajo de 100 ms extra.
    assert total_ms < 150.0


@pytest.mark.unit
def test_timeout_propagation_default_3_5s() -> None:
    primary = _SuccessAdapter()
    fallback = OfflineDeterministicAdapter()
    breaker = CircuitBreaker(primary, fallback)

    asyncio.run(breaker.exchange("Prueba"))
    assert primary.calls[0][1] == 3.5


@pytest.mark.unit
def test_circuit_breaker_state_machine_open_and_half_open() -> None:
    clock = _FakeClock(1000.0)
    primary = _FailingAdapter()
    fallback = OfflineDeterministicAdapter()
    breaker = CircuitBreaker(
        primary,
        fallback,
        failure_threshold=3,
        cooldown_s=30.0,
        clock=clock,
    )

    assert breaker.state == "CLOSED"

    for _ in range(3):
        res = asyncio.run(breaker.exchange("Consulta"))
        assert res.circuit_breaker_tripped is True
    assert breaker.state == "OPEN"
    assert len(primary.calls) == 3

    # Con circuito abierto: no llama al primario y responde < 100 ms
    clock.advance(10.0)
    t0 = time.perf_counter()
    res_open = asyncio.run(breaker.exchange("Consulta en abierto"))
    open_ms = (time.perf_counter() - t0) * 1000.0
    assert res_open.adapter_mode == "OFFLINE_DETERMINISTIC_FALLBACK"
    assert res_open.circuit_breaker_tripped is True
    assert len(primary.calls) == 3  # no se invocó al primario
    assert open_ms < 100.0

    # Tras enfriamiento: pasa a HALF_OPEN, prueba el primario; si tiene éxito cierra.
    clock.advance(25.0)
    healthy = _SuccessAdapter("Recuperado")
    breaker._primary = healthy  # noqa: SLF001
    res_recovered = asyncio.run(breaker.exchange("Consulta recuperación"))
    assert res_recovered.adapter_mode == "LOCAL_OLLAMA"
    assert res_recovered.circuit_breaker_tripped is False
    assert breaker.state == "CLOSED"


@pytest.mark.unit
def test_circuit_breaker_half_open_failure_reopens() -> None:
    clock = _FakeClock(500.0)
    primary = _FailingAdapter()
    fallback = OfflineDeterministicAdapter()
    breaker = CircuitBreaker(
        primary,
        fallback,
        failure_threshold=2,
        cooldown_s=15.0,
        clock=clock,
    )

    asyncio.run(breaker.exchange("1"))
    asyncio.run(breaker.exchange("2"))
    assert breaker.state == "OPEN"

    clock.advance(16.0)
    res = asyncio.run(breaker.exchange("3"))
    assert res.circuit_breaker_tripped is True
    assert breaker.state == "OPEN"
    assert len(primary.calls) == 3


@pytest.mark.unit
def test_offline_repeatability_no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _no_socket(*args: object, **kwargs: object) -> object:
        raise AssertionError("Red prohibida en OfflineDeterministicAdapter")

    monkeypatch.setattr(socket, "create_connection", _no_socket)

    adapter = OfflineDeterministicAdapter()
    prompt = "<tramite>Solicitud de [CEDULA_1] por [RIF_1]</tramite>"
    out1 = asyncio.run(adapter.complete(prompt, timeout_s=3.5))
    out2 = asyncio.run(adapter.complete(prompt, timeout_s=3.5))

    assert out1 == out2
    assert len(out1) > 0
    assert "[CEDULA_1]" in out1


@pytest.mark.unit
def test_offline_adapter_never_echoes_canary() -> None:
    adapter = OfflineDeterministicAdapter()
    canary = "[[CANARY-HMAC-ABCDEF0123456789]]"
    prompt = f"{canary}\n<user_input>Trámite de [CEDULA_1]</user_input>"
    out = asyncio.run(adapter.complete(prompt, timeout_s=3.5))
    assert "CANARY-HMAC" not in out
    assert "ABCDEF0123456789" not in out


@pytest.mark.unit
def test_guard_after_fallback_blocks_unsafe_output() -> None:
    canary = "[[CANARY-HMAC-0011223344556677]]"
    unsafe_fallback = _UnsafeFallbackAdapter("<script>alert(1)</script> V-12345678")
    breaker = CircuitBreaker(_FailingAdapter(), unsafe_fallback)

    exchange = asyncio.run(breaker.exchange("Consulta"))
    guard_res = guard_out(exchange.raw_response, canary_token=canary)

    assert guard_res.allowed is False
    assert guard_res.xss_or_code_injected is True
    assert guard_res.residual_pii_detected is True
    assert "<script>" not in guard_res.sanitized_response


@pytest.mark.unit
def test_ollama_adapter_mock_transport_and_allowlist() -> None:
    with pytest.raises(ValueError):
        OllamaAdapter(base_url="http://evil.example.com:11434")

    def _handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/generate"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload["stream"] is False
        return httpx.Response(200, json={"response": "Orientación para [CEDULA_1]"})

    adapter = OllamaAdapter(transport=httpx.MockTransport(_handler))
    out = asyncio.run(adapter.complete("Trámite [CEDULA_1]", timeout_s=3.5))
    assert out == "Orientación para [CEDULA_1]"


@pytest.mark.unit
def test_ollama_adapter_rejects_oversized_or_error_response() -> None:
    def _oversized(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": "x" * 200})

    adapter = OllamaAdapter(max_response_bytes=64, transport=httpx.MockTransport(_oversized))
    with pytest.raises(LLMUnavailableError):
        asyncio.run(adapter.complete("hola", timeout_s=3.5))

    def _server_error(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="down")

    adapter_err = OllamaAdapter(transport=httpx.MockTransport(_server_error))
    with pytest.raises(LLMUnavailableError):
        asyncio.run(adapter_err.complete("hola", timeout_s=3.5))


@pytest.mark.unit
def test_openai_compat_adapter_opt_in_and_redacted_repr() -> None:
    disabled = OpenAICompatAdapter()
    with pytest.raises(LLMUnavailableError):
        asyncio.run(disabled.complete("hola", timeout_s=3.5))

    with pytest.raises(ValueError):
        OpenAICompatAdapter(
            enabled=True,
            base_url="http://api.openai.com/v1",  # http sin TLS para host no loopback
            allowed_hosts=("api.openai.com",),
        )

    def _handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer sk-secret-test-key"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Respuesta híbrida [CEDULA_1]"}}]},
        )

    enabled = OpenAICompatAdapter(
        enabled=True,
        base_url="https://api.example.local",
        api_key="sk-secret-test-key",
        model="gpt-test",
        allowed_hosts=("api.example.local",),
        transport=httpx.MockTransport(_handler),
    )
    assert "sk-secret-test-key" not in repr(enabled)
    out = asyncio.run(enabled.complete("Trámite [CEDULA_1]", timeout_s=3.5))
    assert out == "Respuesta híbrida [CEDULA_1]"
