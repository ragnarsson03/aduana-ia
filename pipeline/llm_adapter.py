"""Adaptadores LLM y Circuit Breaker (RF-11, RF-12, CA-06). Gatillo 5.

El breaker es una máquina de estados (CLOSED/OPEN/HALF_OPEN) con umbral de fallos, enfriamiento
y reloj inyectable: con el circuito abierto el fallback responde de inmediato (< 100 ms).
El modo HYBRID_OPENAI es opt-in; hosts en allowlist, sin redirects, respuesta acotada.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from collections.abc import Callable
from typing import Any, ClassVar, Final, Literal
from urllib.parse import urlparse

import httpx

from core.config import LLM_TIMEOUT_SECONDS, LOOPBACK_HOSTS
from core.context import AdapterMode, LLMExchangeResult
from core.crypto import sha256_hex
from core.errors import LLMUnavailableError
from core.protocols import LLMAdapterProtocol

BreakerState = Literal["CLOSED", "OPEN", "HALF_OPEN"]

_DEFAULT_MAX_RESPONSE_BYTES: Final[int] = 32 * 1024
_CANARY_TAG_RE: Final = re.compile(r"\[\[CANARY-HMAC-[0-9A-Fa-f]+\]\]")
_XML_TAG_RE: Final = re.compile(r"<[^>]+>")
_SHIELD_TOKEN_RE: Final = re.compile(r"\[[A-Z]+_[0-9]+\]")


def _validate_endpoint(
    base_url: str,
    *,
    allowed_hosts: tuple[str, ...],
    require_https_remote: bool,
) -> str:
    """Valida esquema y host contra allowlist para evitar SSRF y fugas en claro."""
    parsed = urlparse(base_url.strip())
    host = (parsed.hostname or "").lower()
    allowed = {h.lower() for h in allowed_hosts}
    if not host or host not in allowed:
        raise ValueError("Host de adaptador LLM fuera de allowlist.")
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Esquema de URL LLM inválido (solo http/https).")
    if require_https_remote and host not in LOOPBACK_HOSTS and parsed.scheme != "https":
        raise ValueError("Adaptador remoto requiere HTTPS.")
    return base_url.rstrip("/")


async def _post_json_bounded(
    *,
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout_s: float,
    max_response_bytes: int,
    transport: httpx.AsyncBaseTransport | None,
) -> dict[str, Any]:
    """Ejecuta POST JSON sin redirects, con timeout y tope de tamaño de respuesta."""
    try:
        async with httpx.AsyncClient(
            timeout=timeout_s,
            follow_redirects=False,
            transport=transport,
        ) as client:
            response = await client.post(url, json=payload, headers=headers)
    except (httpx.TimeoutException, httpx.HTTPError) as exc:
        raise LLMUnavailableError("Fallo de comunicación con el proveedor LLM.") from exc

    if response.status_code != 200:
        raise LLMUnavailableError(f"Proveedor LLM respondió HTTP {response.status_code}.")

    raw_bytes = response.content
    if len(raw_bytes) > max_response_bytes:
        raise LLMUnavailableError("Respuesta LLM excede el límite permitido.")

    try:
        data = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LLMUnavailableError("Respuesta LLM con JSON inválido.") from exc

    if not isinstance(data, dict):
        raise LLMUnavailableError("Respuesta LLM con estructura inesperada.")
    return data


class OllamaAdapter:
    """Adaptador local para Ollama (solo hosts en allowlist, por defecto loopback)."""

    mode: ClassVar[AdapterMode] = "LOCAL_OLLAMA"

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "llama3.2:3b",
        allowed_hosts: tuple[str, ...] = ("127.0.0.1", "localhost", "::1"),
        max_response_bytes: int = _DEFAULT_MAX_RESPONSE_BYTES,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = _validate_endpoint(
            base_url, allowed_hosts=allowed_hosts, require_https_remote=False
        )
        self._model = model
        self._max_response_bytes = max_response_bytes
        self._transport = transport

    async def complete(self, prompt: str, *, timeout_s: float) -> str:
        data = await _post_json_bounded(
            url=f"{self._base_url}/api/generate",
            payload={"model": self._model, "prompt": prompt, "stream": False},
            headers={"Content-Type": "application/json"},
            timeout_s=timeout_s,
            max_response_bytes=self._max_response_bytes,
            transport=self._transport,
        )
        text = data.get("response")
        if not isinstance(text, str) or not text.strip():
            raise LLMUnavailableError("Respuesta vacía de Ollama.")
        return text


class OpenAICompatAdapter:
    """Adaptador híbrido OpenAI-compatible (opt-in estricto, TLS remoto, repr redactado)."""

    mode: ClassVar[AdapterMode] = "HYBRID_OPENAI"

    def __init__(
        self,
        *,
        base_url: str = "",
        api_key: str = "",
        model: str = "",
        enabled: bool = False,
        allowed_hosts: tuple[str, ...] = (),
        max_response_bytes: int = _DEFAULT_MAX_RESPONSE_BYTES,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._enabled = enabled
        self._api_key = api_key
        self._model = model
        self._max_response_bytes = max_response_bytes
        self._transport = transport
        self._base_url = (
            _validate_endpoint(base_url, allowed_hosts=allowed_hosts, require_https_remote=True)
            if enabled
            else ""
        )

    def __repr__(self) -> str:
        return (
            f"OpenAICompatAdapter(enabled={self._enabled!r}, "
            f"base_url={self._base_url!r}, model={self._model!r}, api_key='<redacted>')"
        )

    async def complete(self, prompt: str, *, timeout_s: float) -> str:
        if not self._enabled:
            raise LLMUnavailableError("Adaptador híbrido deshabilitado (opt-in requerido).")

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        data = await _post_json_bounded(
            url=f"{self._base_url}/v1/chat/completions",
            payload={
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            headers=headers,
            timeout_s=timeout_s,
            max_response_bytes=self._max_response_bytes,
            transport=self._transport,
        )
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMUnavailableError("Respuesta sin opciones en proveedor híbrido.")
        first = choices[0]
        message = first.get("message") if isinstance(first, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise LLMUnavailableError("Respuesta vacía en proveedor híbrido.")
        return content


class OfflineDeterministicAdapter:
    """Generador institucional determinista sin red ni descargas (CA-06)."""

    mode: ClassVar[AdapterMode] = "OFFLINE_DETERMINISTIC_FALLBACK"

    async def complete(self, prompt: str, *, timeout_s: float) -> str:
        del timeout_s  # Ejecución local síncrona/inmediata sin espera de red.
        without_canary = _CANARY_TAG_RE.sub("", prompt)
        clean_text = _XML_TAG_RE.sub(" ", without_canary)
        clean_text = " ".join(clean_text.split())
        tokens = list(dict.fromkeys(_SHIELD_TOKEN_RE.findall(clean_text)))
        digest = sha256_hex(clean_text.encode("utf-8"))[:12]
        token_note = ", ".join(tokens[:6]) if tokens else "sin identificadores enmascarados"
        return (
            "[AVISO IA - MODO INSTITUCIONAL OFFLINE] "
            f"Resumen orientativo determinista (ref=0x{digest}): "
            f"trámite recibido para revisión funcional ({token_note}). "
            "Este resumen no sustituye la decisión humana ni el motor EXPLICA."
        )


class CircuitBreaker:
    """Máquina de estados CLOSED/OPEN/HALF_OPEN para conmutación resiliente al fallback."""

    def __init__(
        self,
        primary: LLMAdapterProtocol,
        fallback: LLMAdapterProtocol,
        timeout_s: float = LLM_TIMEOUT_SECONDS,
        *,
        failure_threshold: int = 3,
        cooldown_s: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if timeout_s <= 0:
            raise ValueError("timeout_s debe ser positivo.")
        if failure_threshold < 1:
            raise ValueError("failure_threshold debe ser >= 1.")
        if cooldown_s < 0:
            raise ValueError("cooldown_s no puede ser negativo.")
        self._primary = primary
        self._fallback = fallback
        self._timeout_s = timeout_s
        self._failure_threshold = failure_threshold
        self._cooldown_s = cooldown_s
        self._clock = clock
        self._state: BreakerState = "CLOSED"
        self._failure_count = 0
        self._opened_at = 0.0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> BreakerState:
        return self._state

    async def _call_fallback(
        self, prompt: str, *, prompt_hash: str, started: float
    ) -> LLMExchangeResult:
        raw_fb = await self._fallback.complete(prompt, timeout_s=self._timeout_s)
        latency_ms = (time.perf_counter() - started) * 1000.0
        return LLMExchangeResult(
            adapter_mode=self._fallback.mode,
            ai_generated_notice=True,
            circuit_breaker_tripped=True,
            prompt_sent_hash=prompt_hash,
            raw_response=raw_fb,
            latency_ms=latency_ms,
        )

    async def exchange(self, prompt: str) -> LLMExchangeResult:
        started = time.perf_counter()
        prompt_hash = sha256_hex(prompt.encode("utf-8"))

        async with self._lock:
            if self._state == "OPEN":
                if (self._clock() - self._opened_at) < self._cooldown_s:
                    return await self._call_fallback(
                        prompt, prompt_hash=prompt_hash, started=started
                    )
                self._state = "HALF_OPEN"

            try:
                raw = await asyncio.wait_for(
                    self._primary.complete(prompt, timeout_s=self._timeout_s),
                    timeout=self._timeout_s,
                )
            except (LLMUnavailableError, TimeoutError):
                self._failure_count += 1
                if self._state == "HALF_OPEN" or self._failure_count >= self._failure_threshold:
                    self._state = "OPEN"
                    self._opened_at = self._clock()
                return await self._call_fallback(prompt, prompt_hash=prompt_hash, started=started)

            self._failure_count = 0
            self._state = "CLOSED"
            latency_ms = (time.perf_counter() - started) * 1000.0
            return LLMExchangeResult(
                adapter_mode=self._primary.mode,
                ai_generated_notice=True,
                circuit_breaker_tripped=False,
                prompt_sent_hash=prompt_hash,
                raw_response=raw,
                latency_ms=latency_ms,
            )
