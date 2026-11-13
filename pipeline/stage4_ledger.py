"""Etapa 4 — LEDGER: SQLite endurecido, encadenado SHA-256 + HMAC (RF-15..RF-17, CA-03).

Reglas de ``verify_chain`` (Gatillo 3): índices contiguos desde 0; primer ``prev_hash`` ==
``GENESIS_PREV_HASH``; hash y firma sobre el payload canónico de TODOS los campos; comparación
con ``KeyRing.verify`` (tolera no ASCII); ancla externa opcional contra truncado de cola.
Orden de comprobación por bloque: INDEX_GAP -> link previo -> HASH_MISMATCH -> HMAC forjado.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator

from core.context import (
    ChainAnchor,
    ChainVerification,
    LedgerBlock,
    LedgerEntry,
    LedgerReceipt,
)
from core.keyring import KeyRing
from core.protocols import StorageRepositoryProtocol


class SQLiteLedgerRepository:
    """Implementa ``StorageRepositoryProtocol`` con WAL, synchronous=FULL, secure_delete=ON,
    trusted_schema=OFF y triggers BEFORE UPDATE/DELETE -> RAISE(ABORT, 'ERR_IMMUTABLE_LEDGER').
    Los triggers previenen errores; el control de integridad real es el HMAC. Gatillo 3."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def append_chained(self, build: Callable[[int, str], LedgerBlock]) -> LedgerBlock:
        raise NotImplementedError("Gatillo 3: SQLiteLedgerRepository pendiente")

    def get_block(self, block_index: int) -> LedgerBlock | None:
        raise NotImplementedError("Gatillo 3")

    def last_block(self) -> LedgerBlock | None:
        raise NotImplementedError("Gatillo 3")

    def iter_blocks(self, start: int = 0, end: int | None = None) -> Iterator[LedgerBlock]:
        raise NotImplementedError("Gatillo 3")

    def count(self) -> int:
        raise NotImplementedError("Gatillo 3")

    def close(self) -> None:
        raise NotImplementedError("Gatillo 3")


def seal_entry(
    entry: LedgerEntry, repo: StorageRepositoryProtocol, *, keys: KeyRing
) -> LedgerReceipt:
    raise NotImplementedError("Gatillo 3: seal_entry pendiente (specs/03_ledger.spec.md)")


def verify_chain(
    blocks: Iterable[LedgerBlock], *, keys: KeyRing, anchor: ChainAnchor | None = None
) -> ChainVerification:
    raise NotImplementedError("Gatillo 3: verify_chain pendiente (specs/03_ledger.spec.md)")
