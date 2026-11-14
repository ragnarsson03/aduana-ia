"""Bóveda efímera en RAM (Anillo 1). Gatillo 0.

Decisiones tras revisión:
- NO se guarda ``raw_input``: solo el mapa token -> valor, como ``bytearray`` (sobrescribible).
- ``zeroize`` es mitigación de mejor esfuerzo; CPython no garantiza borrado de copias previas, y
  el ``Mapping`` que devuelve ``get_map`` contiene ``str`` inmutables: el llamador debe soltarlo
  cuanto antes (no persistirlo ni loguearlo).
- TTL con reloj monotónico inyectable; expira cuando edad > TTL (180 s exactos siguen vigentes).
- Tope de sesiones; la purga oportunista de expiradas libera cupo.
- Seguro entre hilos (``RLock``). Sin I/O ni logging: jamás toca disco.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Mapping
from types import MappingProxyType

from core.config import VAULT_MAX_SESSIONS, VAULT_TTL_SECONDS
from core.errors import VaultError, VaultExpiredError, VaultSessionNotFoundError

_Buffers = dict[str, bytearray]
_Session = tuple[float, _Buffers]


def _wipe(buffers: _Buffers) -> None:
    for buffer in buffers.values():
        buffer[:] = bytes(len(buffer))
    buffers.clear()


def _encode(token_map: Mapping[str, str]) -> _Buffers:
    """Construye los buffers; ante valor inválido borra lo parcial y falla sin eco del valor."""
    buffers: _Buffers = {}
    try:
        for token, value in token_map.items():
            buffers[token] = bytearray(value.encode())
    except (AttributeError, UnicodeError):
        _wipe(buffers)
        raise VaultError("Valor de mapa inválido.") from None
    return buffers


class EphemeralVault:
    def __init__(
        self,
        ttl_seconds: int = VAULT_TTL_SECONDS,
        max_sessions: int = VAULT_MAX_SESSIONS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if ttl_seconds <= 0 or max_sessions < 1:
            raise ValueError("ttl_seconds debe ser > 0 y max_sessions >= 1.")
        self._ttl_seconds = ttl_seconds
        self._max_sessions = max_sessions
        self._clock = clock  # debe ser monotónico
        self._lock = threading.RLock()
        self._sessions: dict[str, _Session] = {}

    def _is_expired(self, created_at: float) -> bool:
        return self._clock() - created_at > self._ttl_seconds

    @property
    def active_sessions(self) -> int:
        """Sesiones vigentes (excluye expiradas, que se purgan)."""
        with self._lock:
            self.purge_expired()
            return len(self._sessions)

    def put(self, request_id: str, token_map: Mapping[str, str]) -> None:
        with self._lock:
            self.purge_expired()
            buffers = _encode(token_map)  # antes de tocar la sesión previa: put es atómico
            previous = self._sessions.pop(request_id, None)
            if previous is not None:
                _wipe(previous[1])
            if len(self._sessions) >= self._max_sessions:
                _wipe(buffers)
                raise VaultError("Capacidad de la bóveda agotada.")
            self._sessions[request_id] = (self._clock(), buffers)

    def get_map(self, request_id: str) -> Mapping[str, str]:
        with self._lock:
            session = self._sessions.get(request_id)
            if session is None:
                raise VaultSessionNotFoundError("Sesión inexistente en la bóveda.")
            if self._is_expired(session[0]):
                self.zeroize(request_id)
                raise VaultExpiredError("Sesión expirada y purgada.")
            return MappingProxyType({t: bytes(b).decode() for t, b in session[1].items()})

    def purge_expired(self) -> int:
        with self._lock:
            expired = [
                rid for rid, (created, _) in list(self._sessions.items()) if self._is_expired(created)
            ]
            for request_id in expired:
                self.zeroize(request_id)
            return len(expired)

    def zeroize(self, request_id: str) -> None:
        """Idempotente: sobrescribe con 0x00 los buffers y elimina la sesión."""
        with self._lock:
            session = self._sessions.pop(request_id, None)
            if session is not None:
                _wipe(session[1])

    def zeroize_all(self) -> None:
        with self._lock:
            for request_id in list(self._sessions):
                self.zeroize(request_id)
