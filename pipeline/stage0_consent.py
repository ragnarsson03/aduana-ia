"""Etapa 0 — Consentimiento y Rate-Guard (RF-01..RF-03). Gatillo 1.

Orden: la etapa 0 calcula ``blind_citizen_id`` (``core.crypto.blind_citizen_id``) y se lo pasa a
SHIELD; así el rate-guard actúa antes de cualquier procesamiento costoso.
El exceso de tasa es ``RateLimitError`` (HTTP 429); ``PolicyStatus`` no tiene un estado de tasa.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable

from core import crypto
from core.context import CitizenConsent
from core.errors import ConsentError, RateLimitError

RATE_WINDOW_SECONDS = 60.0
RATE_MAX_KEYS = 10_000


class RateGuard:
    """Ventana deslizante en RAM por ``blind_citizen_id``: acotada, segura entre hilos, con reloj
    inyectable. Solo se registran los intentos aceptados (los rechazados no prolongan el bloqueo).
    Con la tabla llena de claves vigentes rechaza claves nuevas (falla cerrado)."""

    def __init__(
        self,
        limit_per_minute: int,
        *,
        window_s: float = RATE_WINDOW_SECONDS,
        max_keys: int = RATE_MAX_KEYS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if limit_per_minute < 1:
            raise ValueError("limit_per_minute debe ser >= 1.")
        self._limit = limit_per_minute
        self._window_s = window_s
        self._max_keys = max_keys
        self._clock = clock
        self._lock = threading.Lock()
        self._hits: dict[str, deque[float]] = {}
        self._last_prune = float("-inf")

    def _prune(self, cutoff: float) -> None:
        """Poda O(n) de claves vencidas; ``check`` la limita a una vez por segundo."""
        for key in list(self._hits):
            hits = self._hits[key]
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if not hits:
                del self._hits[key]

    def check(self, blind_citizen_id: str) -> None:
        """Lanza ``RateLimitError`` si se excede la tasa."""
        with self._lock:
            now = self._clock()
            cutoff = now - self._window_s
            hits = self._hits.get(blind_citizen_id)
            if hits is None:
                if len(self._hits) >= self._max_keys and now - self._last_prune >= 1.0:
                    self._last_prune = now
                    self._prune(cutoff)
                if len(self._hits) >= self._max_keys:
                    raise RateLimitError("Límite de tasa excedido.")
                hits = deque()
                self._hits[blind_citizen_id] = hits
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= self._limit:
                raise RateLimitError("Límite de tasa excedido.")
            hits.append(now)


def validate_consent(
    request_id: str,
    granted: bool,
    purpose_code: str,
    timestamp_utc: str,
    blind_citizen_id: str,
) -> CitizenConsent:
    """Lanza ``ConsentError`` (BLOCKED_NO_CONSENT) sin consentimiento o propósito."""
    purpose = purpose_code.strip() if isinstance(purpose_code, str) else ""
    if granted is not True or not purpose:
        raise ConsentError("Consentimiento explícito y propósito requeridos.")
    digest = crypto.consent_hash(request_id, timestamp_utc, purpose, blind_citizen_id)
    return CitizenConsent(True, purpose, timestamp_utc, digest)
