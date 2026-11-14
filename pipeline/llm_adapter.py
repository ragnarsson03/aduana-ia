"""Adaptadores LLM y Circuit Breaker (RF-11, RF-12, CA-06). Gatillo 5 — pendiente.

El breaker es una máquina de estados (CLOSED/OPEN/HALF_OPEN) con umbral de fallos, enfriamiento
y reloj inyectable: con el circuito abierto el fallback responde de inmediato (< 100 ms).
El modo HYBRID_OPENAI es opt-in; hosts en allowlist, sin redirects, respuesta acotada.
"""

from __future__ import annotations

from typing import ClassVar

from core.config import LLM_TIMEOUT_SECONDS
from core.context import AdapterMode, LLMExchangeResult
from core.protocols import LLMAdapterProtocol


class OllamaAdapter:
    mode: ClassVar[AdapterMode] = "LOCAL_OLLAMA"

    async def complete(self, prompt: str, *, timeout_s: float) -> str:
        raise NotImplementedError("Gatillo 5")


class OpenAICompatAdapter:
    mode: ClassVar[AdapterMode] = "HYBRID_OPENAI"

    async def complete(self, prompt: str, *, timeout_s: float) -> str:
        raise NotImplementedError("Gatillo 5")


class OfflineDeterministicAdapter:
    mode: ClassVar[AdapterMode] = "OFFLINE_DETERMINISTIC_FALLBACK"

    async def complete(self, prompt: str, *, timeout_s: float) -> str:
        raise NotImplementedError("Gatillo 5")


class CircuitBreaker:
    def __init__(
        self,
        primary: LLMAdapterProtocol,
        fallback: LLMAdapterProtocol,
        timeout_s: float = LLM_TIMEOUT_SECONDS,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._timeout_s = timeout_s

    async def exchange(self, prompt: str) -> LLMExchangeResult:
        raise NotImplementedError("Gatillo 5: CircuitBreaker.exchange pendiente")
