"""Etapa 4 — LEDGER: SQLite endurecido, encadenado SHA-256 + HMAC (RF-15..RF-17, CA-03).

Reglas de ``verify_chain`` (Gatillo 3): índices contiguos desde 0; primer ``prev_hash`` ==
``GENESIS_PREV_HASH``; hash y firma sobre el payload canónico de TODOS los campos; comparación
con ``KeyRing.verify`` (tolera no ASCII); ancla externa opcional contra truncado de cola.
Orden de comprobación por bloque: INDEX_GAP -> link previo -> HASH_MISMATCH -> HMAC forjado.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path

from core.config import GENESIS_PREV_HASH
from core.context import (
    ChainAnchor,
    ChainVerification,
    LedgerBlock,
    LedgerEntry,
    LedgerReceipt,
)
from core.crypto import block_hash, block_signature, canonical_block_payload
from core.errors import ImmutableLedgerError, StorageError
from core.keyring import KeyRing
from core.protocols import StorageRepositoryProtocol

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS ledger_blocks (
    block_index INTEGER PRIMARY KEY,
    request_id TEXT NOT NULL UNIQUE,
    timestamp_utc TEXT NOT NULL,
    blind_citizen_id TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    block_hash TEXT NOT NULL,
    hmac_signature TEXT NOT NULL,
    security_verdict TEXT NOT NULL,
    model_recommendation TEXT NOT NULL,
    human_decision TEXT NOT NULL,
    human_override INTEGER NOT NULL DEFAULT 0,
    citizen_receipt_code TEXT NOT NULL UNIQUE,
    key_id TEXT NOT NULL,
    override_justification_hash TEXT
);

CREATE TRIGGER IF NOT EXISTS prevent_ledger_update
BEFORE UPDATE ON ledger_blocks
BEGIN
    SELECT RAISE(ABORT, 'ERR_IMMUTABLE_LEDGER');
END;

CREATE TRIGGER IF NOT EXISTS prevent_ledger_delete
BEFORE DELETE ON ledger_blocks
BEGIN
    SELECT RAISE(ABORT, 'ERR_IMMUTABLE_LEDGER');
END;
"""


def _row_to_block(row: tuple) -> LedgerBlock:
    return LedgerBlock(
        block_index=row[0],
        request_id=row[1],
        timestamp_utc=row[2],
        blind_citizen_id=row[3],
        payload_hash=row[4],
        prev_hash=row[5],
        block_hash=row[6],
        hmac_signature=row[7],
        security_verdict=row[8],
        model_recommendation=row[9],
        human_decision=row[10],
        human_override=bool(row[11]),
        citizen_receipt_code=row[12],
        key_id=row[13],
        override_justification_hash=row[14],
    )


class SQLiteLedgerRepository:
    """Implementa ``StorageRepositoryProtocol`` con WAL, synchronous=FULL, secure_delete=ON,
    trusted_schema=OFF y triggers BEFORE UPDATE/DELETE -> RAISE(ABORT, 'ERR_IMMUTABLE_LEDGER').
    Los triggers previenen errores; el control de integridad real es el HMAC. Gatillo 3."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._lock = threading.RLock()
        p = Path(db_path)
        if not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(
            db_path,
            check_same_thread=False,
            isolation_level=None,  # Manejo manual de transacciones explícitas
        )

        with self._lock:
            cur = self._conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL;")
            cur.execute("PRAGMA synchronous=FULL;")
            cur.execute("PRAGMA secure_delete=ON;")
            cur.execute("PRAGMA trusted_schema=OFF;")
            cur.executescript(_SCHEMA_SQL)
            cur.close()

        try:
            os.chmod(db_path, 0o600)
        except OSError:
            pass

    def append_chained(self, build: Callable[[int, str], LedgerBlock]) -> LedgerBlock:
        with self._lock:
            cur = self._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                cur.execute(
                    "SELECT block_index, block_hash FROM ledger_blocks "
                    "ORDER BY block_index DESC LIMIT 1"
                )
                row = cur.fetchone()
                if row is None:
                    next_index = 0
                    prev_hash = GENESIS_PREV_HASH
                else:
                    next_index = row[0] + 1
                    prev_hash = row[1]

                block = build(next_index, prev_hash)

                cur.execute(
                    """
                    INSERT INTO ledger_blocks (
                        block_index, request_id, timestamp_utc, blind_citizen_id,
                        payload_hash, prev_hash, block_hash, hmac_signature,
                        security_verdict, model_recommendation, human_decision,
                        human_override, citizen_receipt_code, key_id,
                        override_justification_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        block.block_index,
                        block.request_id,
                        block.timestamp_utc,
                        block.blind_citizen_id,
                        block.payload_hash,
                        block.prev_hash,
                        block.block_hash,
                        block.hmac_signature,
                        block.security_verdict,
                        block.model_recommendation,
                        block.human_decision,
                        1 if block.human_override else 0,
                        block.citizen_receipt_code,
                        block.key_id,
                        block.override_justification_hash,
                    ),
                )
                cur.execute("COMMIT")
                return block
            except sqlite3.OperationalError as e:
                cur.execute("ROLLBACK")
                if "ERR_IMMUTABLE_LEDGER" in str(e):
                    raise ImmutableLedgerError(str(e)) from e
                raise StorageError(str(e)) from e
            except Exception as e:
                cur.execute("ROLLBACK")
                raise StorageError(str(e)) from e
            finally:
                cur.close()

    def get_block(self, block_index: int) -> LedgerBlock | None:
        with self._lock:
            cur = self._conn.cursor()
            try:
                cur.execute("SELECT * FROM ledger_blocks WHERE block_index = ?", (block_index,))
                row = cur.fetchone()
                return _row_to_block(row) if row else None
            finally:
                cur.close()

    def last_block(self) -> LedgerBlock | None:
        with self._lock:
            cur = self._conn.cursor()
            try:
                cur.execute("SELECT * FROM ledger_blocks ORDER BY block_index DESC LIMIT 1")
                row = cur.fetchone()
                return _row_to_block(row) if row else None
            finally:
                cur.close()

    def iter_blocks(self, start: int = 0, end: int | None = None) -> Iterator[LedgerBlock]:
        with self._lock:
            cur = self._conn.cursor()
            try:
                if end is None:
                    cur.execute(
                        "SELECT * FROM ledger_blocks WHERE block_index >= ? "
                        "ORDER BY block_index ASC",
                        (start,),
                    )
                else:
                    cur.execute(
                        "SELECT * FROM ledger_blocks WHERE block_index >= ? "
                        "AND block_index <= ? ORDER BY block_index ASC",
                        (start, end),
                    )
                rows = cur.fetchall()
            finally:
                cur.close()
        for row in rows:
            yield _row_to_block(row)

    def count(self) -> int:
        with self._lock:
            cur = self._conn.cursor()
            try:
                cur.execute("SELECT COUNT(*) FROM ledger_blocks")
                row = cur.fetchone()
                return int(row[0]) if row else 0
            finally:
                cur.close()

    def close(self) -> None:
        with self._lock:
            self._conn.close()


def seal_entry(
    entry: LedgerEntry, repo: StorageRepositoryProtocol, *, keys: KeyRing
) -> LedgerReceipt:
    """Sella una entrada en el ledger calculando hash canónico y firma HMAC con la clave maestra."""
    key_id = keys.key_id

    def build(index: int, prev_hash: str) -> LedgerBlock:
        payload = canonical_block_payload(
            entry,
            index=index,
            prev_hash=prev_hash,
            key_id=key_id,
        )
        b_hash = block_hash(payload)
        sig = block_signature(keys, b_hash)
        return LedgerBlock(
            block_index=index,
            request_id=entry.request_id,
            timestamp_utc=entry.timestamp_utc,
            blind_citizen_id=entry.blind_citizen_id,
            payload_hash=entry.payload_hash,
            prev_hash=prev_hash,
            block_hash=b_hash,
            hmac_signature=sig,
            security_verdict=entry.security_verdict,
            model_recommendation=entry.model_recommendation,
            human_decision=entry.human_decision,
            human_override=entry.human_override,
            citizen_receipt_code=entry.citizen_receipt_code,
            key_id=key_id,
            override_justification_hash=entry.override_justification_hash,
        )

    block = repo.append_chained(build)

    return LedgerReceipt(
        block_index=block.block_index,
        prev_hash=block.prev_hash,
        payload_hash=block.payload_hash,
        block_hash=block.block_hash,
        hmac_signature=block.hmac_signature,
        citizen_receipt_code=block.citizen_receipt_code,
        chain_verified=True,
    )


def verify_chain(
    blocks: Iterable[LedgerBlock], *, keys: KeyRing, anchor: ChainAnchor | None = None
) -> ChainVerification:
    """Verifica secuencialmente la integridad de una cadena de bloques del ledger.

    Orden de verificación por bloque:
    1. INDEX_GAP: índices contiguos comenzando en 0.
    2. PREV_HASH_LINK_BROKEN / GENESIS_LINK_BROKEN: enlace al bloque anterior o al génesis.
    3. HASH_MISMATCH: hash canónico recalculado coincide con block_hash.
    4. HMAC_SIGNATURE_FORGED: firma HMAC válida con la clave maestra.
    5. Ancla externa opcional: detecta truncado de cola (TAIL_TRUNCATED).
    """
    expected_index = 0
    prev_hash = GENESIS_PREV_HASH
    count = 0

    for block in blocks:
        # 1. Verificación de índice contiguo
        if block.block_index != expected_index:
            return ChainVerification(
                is_valid=False,
                blocks_checked=count,
                corrupted_block_index=block.block_index,
                failure_reason="INDEX_GAP",
            )

        # 2. Verificación de enlace previo
        if expected_index == 0:
            if block.prev_hash != GENESIS_PREV_HASH:
                return ChainVerification(
                    is_valid=False,
                    blocks_checked=count,
                    corrupted_block_index=0,
                    failure_reason="GENESIS_LINK_BROKEN",
                )
        else:
            if block.prev_hash != prev_hash:
                return ChainVerification(
                    is_valid=False,
                    blocks_checked=count,
                    corrupted_block_index=block.block_index,
                    failure_reason="PREV_HASH_LINK_BROKEN",
                )

        # 3. Verificación de hash del payload canónico
        expected_payload = canonical_block_payload(
            block,
            index=block.block_index,
            prev_hash=block.prev_hash,
            key_id=block.key_id,
        )
        expected_hash = block_hash(expected_payload)
        if block.block_hash != expected_hash:
            return ChainVerification(
                is_valid=False,
                blocks_checked=count,
                corrupted_block_index=block.block_index,
                failure_reason="HASH_MISMATCH",
            )

        # 4. Verificación de firma HMAC
        if not keys.verify("ledger-sign", block.block_hash.encode(), block.hmac_signature):
            return ChainVerification(
                is_valid=False,
                blocks_checked=count,
                corrupted_block_index=block.block_index,
                failure_reason="HMAC_SIGNATURE_FORGED",
            )

        prev_hash = block.block_hash
        expected_index += 1
        count += 1

    # 5. Comprobación de ancla contra truncado de cola
    if anchor is not None:
        if count < anchor.count:
            return ChainVerification(
                is_valid=False,
                blocks_checked=count,
                corrupted_block_index=count,
                failure_reason="TAIL_TRUNCATED",
            )
        if count > 0 and prev_hash != anchor.head_hash:
            return ChainVerification(
                is_valid=False,
                blocks_checked=count,
                corrupted_block_index=count - 1,
                failure_reason="HASH_MISMATCH",
            )

    return ChainVerification(
        is_valid=True,
        blocks_checked=count,
    )
