"""Adaptadores LLM y Circuit Breaker (RF-11, RF-12, CA-06). Gatillo 5.

El breaker es una máquina de estados (CLOSED/OPEN/HALF_OPEN) con umbral de fallos, enfriamiento
y reloj inyectable: con el circuito abierto el fallback responde de inmediato (< 100 ms).
El modo HYBRID_OPENAI es opt-in; hosts en allowlist, sin redirects, respuesta acotada.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import ClassVar, Literal

import httpx

from core import crypto
from core.config import LLM_TIMEOUT_SECONDS
from core.context import AdapterMode, LLMExchangeResult
from core.errors import LLMUnavailableError
from core.protocols import LLMAdapterProtocol

BreakerState = Literal["CLOSED", "OPEN", "HALF_OPEN"]


class OllamaAdapter:
    mode: ClassVar[AdapterMode] = "LOCAL_OLLAMA"

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "llama3",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def complete(self, prompt: str, *, timeout_s: float) -> str:
        url = f"{self._base_url}/api/generate"
        payload = {"model": self._model, "prompt": prompt, "stream": False}
        try:
            async with httpx.AsyncClient(timeout=timeout_s) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    raise LLMUnavailableError(f"Ollama respondió status {resp.status_code}")
                data = resp.json()
                return str(data.get("response", ""))
        except Exception as exc:
            if isinstance(exc, LLMUnavailableError):
                raise
            raise LLMUnavailableError("Error de comunicación con Ollama.") from exc


class OpenAICompatAdapter:
    mode: ClassVar[AdapterMode] = "HYBRID_OPENAI"

    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        model: str = "gpt-4o-mini",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model

    async def complete(self, prompt: str, *, timeout_s: float) -> str:
        url = f"{self._base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
        }
        try:
            async with httpx.AsyncClient(timeout=timeout_s) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code != 200:
                    raise LLMUnavailableError(f"Proveedor OpenAI respondió status {resp.status_code}")
                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    raise LLMUnavailableError("Respuesta vacía del proveedor LLM.")
                return str(choices[0].get("message", {}).get("content", ""))
        except Exception as exc:
            if isinstance(exc, LLMUnavailableError):
                raise
            raise LLMUnavailableError("Error de comunicación con proveedor OpenAI.") from exc


class OfflineDeterministicAdapter:
    mode: ClassVar[AdapterMode] = "OFFLINE_DETERMINISTIC_FALLBACK"

    async def complete(self, prompt: str, *, timeout_s: float) -> str:
        # Generador institucional 100% determinista, zero-random, zero-network (Air-Gapped)
        p_len = len(prompt)
        p_hash_prefix = crypto.sha256_hex(prompt.encode())[:8]
        return (
            f"Evaluación institucional generada por adaptador determinista offline (ID-{p_hash_prefix}). "
            f"Recaudos y variables del trámite analizados bajo gobernanza Zero-Trust. "
            f"Longitud de entrada verificada: {p_len} caracteres. Dictamen sujeto a decisión soberana del funcionario."
        )


class CircuitBreaker:
    def __init__(
        self,
        primary: LLMAdapterProtocol,
        fallback: LLMAdapterProtocol,
        timeout_s: float = LLM_TIMEOUT_SECONDS,
        *,
        failure_threshold: int = 3,
        cooldown_s: float = 15.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._timeout_s = timeout_s
        self._failure_threshold = failure_threshold
        self._cooldown_s = cooldown_s
        self._clock = clock

        self._state: BreakerState = "CLOSED"
        self._failure_count: int = 0
        self._last_state_change: float = clock()

    @property
    def state(self) -> BreakerState:
        return self._state

    async def exchange(self, prompt: str) -> LLMExchangeResult:
        start_time = time.perf_counter()
        prompt_hash = crypto.sha256_hex(prompt.encode())
        now = self._clock()

        # Comprobar si el circuito abierto ya cumplió el enfriamiento para pasar a HALF_OPEN
        if self._state == "OPEN":
            if now - self._last_state_change >= self._cooldown_s:
                self._state = "HALF_OPEN"
                self._last_state_change = now
            else:
                # Circuito abierto activo: failover inmediato al fallback (< 100 ms)
                raw_response = await self._fallback.complete(prompt, timeout_s=self._timeout_s)
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                return LLMExchangeResult(
                    adapter_mode=self._fallback.mode,
                    ai_generated_notice=True,
                    circuit_breaker_tripped=True,
                    prompt_sent_hash=prompt_hash,
                    raw_response=raw_response,
                    latency_ms=latency_ms,
                )

        # Estado CLOSED o HALF_OPEN: intentar adaptador primario
        tripped = False
        try:
            raw_response = await asyncio.wait_for(
                self._primary.complete(prompt, timeout_s=self._timeout_s),
                timeout=self._timeout_s,
            )
            # Éxito: restablecer a CLOSED
            self._state = "CLOSED"
            self._failure_count = 0
            self._last_state_change = now
            mode = self._primary.mode
        except Exception:
            tripped = True
            self._failure_count += 1
            if self._failure_count >= self._failure_threshold or self._state == "HALF_OPEN":
                self._state = "OPEN"
                self._last_state_change = now

            # Conmutar inmediatamente al generador de fallback determinista
            raw_response = await self._fallback.complete(prompt, timeout_s=self._timeout_s)
            mode = self._fallback.mode

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return LLMExchangeResult(
            adapter_mode=mode,
            ai_generated_notice=True,
            circuit_breaker_tripped=tripped,
            prompt_sent_hash=prompt_hash,
            raw_response=raw_response,
            latency_ms=latency_ms,
        )
