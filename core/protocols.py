"""Interfaces (typing.Protocol) que desacoplan el pipeline de sus implementaciones."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import ClassVar, Protocol, runtime_checkable

from core.context import AdapterMode, LedgerBlock


@runtime_checkable
class StorageRepositoryProtocol(Protocol):
    """Persistencia append-only del ledger. SQLite endurecido hoy, PostgreSQL mañana."""

    def append_chained(self, build: Callable[[int, str], LedgerBlock]) -> LedgerBlock:
        """Atómico: dentro de una transacción exclusiva lee (próximo índice, prev_hash),
        construye el bloque con ``build`` e inserta. Evita bifurcaciones por concurrencia."""

    def get_block(self, block_index: int) -> LedgerBlock | None: ...

    def last_block(self) -> LedgerBlock | None: ...

    def iter_blocks(self, start: int = 0, end: int | None = None) -> Iterator[LedgerBlock]: ...

    def find_by_receipt_code(self, code: str) -> LedgerBlock | None: ...

    def iter_blocks_by_blind_id(self, blind_id: str) -> Iterator[LedgerBlock]: ...

    def count(self) -> int: ...

    def close(self) -> None: ...


@runtime_checkable
class LLMAdapterProtocol(Protocol):
    """Conector agnóstico de proveedor. Solo recibe texto ya anonimizado (RF-11)."""

    mode: ClassVar[AdapterMode]

    async def complete(self, prompt: str, *, timeout_s: float) -> str:
        """Devuelve la respuesta o lanza ``LLMUnavailableError``."""


class RateGuardProtocol(Protocol):
    def check(self, blind_citizen_id: str) -> None:
        """Lanza ``RateLimitError`` si se excede la tasa."""


class LLMGatewayProtocol(Protocol):
    """Lo que el orquestador necesita del conmutador LLM (Circuit Breaker o doble de test)."""

    async def exchange(self, prompt: str): ...  # -> LLMExchangeResult
