"""CA-03 — LEDGER Criptográfico (RF-15..RF-17, CA-03).

Verifica inmutabilidad SQLite (triggers BEFORE UPDATE/DELETE), encadenamiento SHA-256 + HMAC,
detección de alteración de bit en < 50 ms y simulación en memoria (specs/03_ledger.spec.md).
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import replace
from pathlib import Path

import pytest
from litestar.testing import TestClient

from core.config import GENESIS_PREV_HASH
from core.context import ChainAnchor, LedgerEntry
from core.crypto import block_hash, canonical_block_payload
from core.errors import ImmutableLedgerError, StorageError
from core.keyring import KeyRing
from pipeline.stage4_ledger import SQLiteLedgerRepository, seal_entry, verify_chain

KEYS = KeyRing(bytes(range(32)))
FORGED_KEYS = KeyRing(bytes(range(1, 33)))


def _make_entry(
    rid: str,
    index: int = 0,
    override: bool = False,
    justification: str | None = None,
) -> LedgerEntry:
    just_hash = KEYS.hmac_hex("justification", justification.encode()) if justification else None
    return LedgerEntry(
        request_id=f"req-{rid}",
        timestamp_utc=f"2026-11-13T10:0{index}:00Z",
        blind_citizen_id="b" * 64,
        payload_hash=f"p{index}" * 32,
        security_verdict="CLEAN",
        model_recommendation="REVISION_ESTANDAR",
        human_decision="REVISION_ESTANDAR",
        human_override=override,
        citizen_receipt_code=f"REC-{rid}-{index}",
        override_justification_hash=just_hash,
    )


def test_sqlite_hardening(tmp_path: Path) -> None:
    """Verifica PRAGMAs obligatorios y que triggers aborten UPDATE y DELETE."""
    db_file = str(tmp_path / "hardened.db")
    repo = SQLiteLedgerRepository(db_file)

    # Verificar PRAGMAs en la conexión activa del repositorio
    repo_cur = repo._conn.cursor()
    repo_cur.execute("PRAGMA journal_mode;")
    assert repo_cur.fetchone()[0].lower() == "wal"

    repo_cur.execute("PRAGMA synchronous;")
    assert repo_cur.fetchone()[0] == 2  # FULL

    repo_cur.execute("PRAGMA secure_delete;")
    assert repo_cur.fetchone()[0] == 1  # ON

    repo_cur.execute("PRAGMA trusted_schema;")
    assert repo_cur.fetchone()[0] == 0  # OFF

    # Sellar un bloque
    seal_entry(_make_entry("t1", 0), repo, keys=KEYS)

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    # Intentar UPDATE directo debe ser abortado por el trigger
    with pytest.raises(
        (sqlite3.IntegrityError, sqlite3.OperationalError, ImmutableLedgerError)
    ) as exc_info:
        cur.execute("UPDATE ledger_blocks SET security_verdict = 'ALTERED' WHERE block_index = 0")
    assert "ERR_IMMUTABLE_LEDGER" in str(exc_info.value)

    # Intentar DELETE directo debe ser abortado por el trigger
    with pytest.raises(
        (sqlite3.IntegrityError, sqlite3.OperationalError, ImmutableLedgerError)
    ) as exc_info:
        cur.execute("DELETE FROM ledger_blocks WHERE block_index = 0")
    assert "ERR_IMMUTABLE_LEDGER" in str(exc_info.value)

    cur.close()
    conn.close()
    repo.close()


def test_schema_uniqueness(tmp_path: Path) -> None:
    """request_id y citizen_receipt_code repetidos deben ser rechazados."""
    repo = SQLiteLedgerRepository(str(tmp_path / "unique.db"))
    entry1 = _make_entry("dup", 0)
    seal_entry(entry1, repo, keys=KEYS)

    # Mismo request_id
    with pytest.raises((StorageError, sqlite3.IntegrityError)):
        seal_entry(entry1, repo, keys=KEYS)

    repo.close()


def test_append_and_receipt(tmp_path: Path) -> None:
    """Verifica secuencialidad, generación de recibos e integridad de cadena."""
    repo = SQLiteLedgerRepository(str(tmp_path / "chain.db"))
    assert repo.count() == 0

    receipt0 = seal_entry(_make_entry("seq1", 0), repo, keys=KEYS)
    assert receipt0.block_index == 0
    assert receipt0.prev_hash == GENESIS_PREV_HASH
    assert receipt0.chain_verified

    receipt1 = seal_entry(_make_entry("seq2", 1), repo, keys=KEYS)
    assert receipt1.block_index == 1
    assert receipt1.prev_hash == receipt0.block_hash
    assert receipt1.chain_verified

    assert repo.count() == 2

    # Verificación pura de la cadena
    blocks = list(repo.iter_blocks())
    verif = verify_chain(blocks, keys=KEYS)
    assert verif.is_valid
    assert verif.blocks_checked == 2
    assert verif.corrupted_block_index is None
    assert verif.failure_reason is None

    repo.close()


def test_payload_bit_flip(tmp_path: Path) -> None:
    """Alterar un bit del payload_hash debe resultar en HASH_MISMATCH."""
    repo = SQLiteLedgerRepository(str(tmp_path / "bitflip.db"))
    seal_entry(_make_entry("a0", 0), repo, keys=KEYS)
    seal_entry(_make_entry("a1", 1), repo, keys=KEYS)
    seal_entry(_make_entry("a2", 2), repo, keys=KEYS)

    blocks = list(repo.iter_blocks())
    b1 = blocks[1]
    flipped_hash = ("1" if b1.payload_hash[0] == "0" else "0") + b1.payload_hash[1:]
    blocks[1] = replace(b1, payload_hash=flipped_hash)

    verif = verify_chain(blocks, keys=KEYS)
    assert not verif.is_valid
    assert verif.corrupted_block_index == 1
    assert verif.failure_reason == "HASH_MISMATCH"
    assert verif.blocks_checked == 1

    repo.close()


def test_prev_link_only(tmp_path: Path) -> None:
    """Alterar prev_hash del bloque debe detectarse como PREV_HASH_LINK_BROKEN."""
    repo = SQLiteLedgerRepository(str(tmp_path / "link.db"))
    seal_entry(_make_entry("l0", 0), repo, keys=KEYS)
    seal_entry(_make_entry("l1", 1), repo, keys=KEYS)

    blocks = list(repo.iter_blocks())
    blocks[1] = replace(blocks[1], prev_hash="f" * 64)

    verif = verify_chain(blocks, keys=KEYS)
    assert not verif.is_valid
    assert verif.corrupted_block_index == 1
    assert verif.failure_reason == "PREV_HASH_LINK_BROKEN"

    repo.close()


def test_genesis_link_broken(tmp_path: Path) -> None:
    """Bloque 0 con prev_hash distinto a GENESIS_PREV_HASH falla con GENESIS_LINK_BROKEN."""
    repo = SQLiteLedgerRepository(str(tmp_path / "genesis.db"))
    seal_entry(_make_entry("g0", 0), repo, keys=KEYS)

    blocks = list(repo.iter_blocks())
    blocks[0] = replace(blocks[0], prev_hash="1" * 64)

    verif = verify_chain(blocks, keys=KEYS)
    assert not verif.is_valid
    assert verif.corrupted_block_index == 0
    assert verif.failure_reason == "GENESIS_LINK_BROKEN"

    repo.close()


def test_rehashed_without_hmac(tmp_path: Path) -> None:
    """Recalcular SHA-256 sin la clave HMAC debe detectarse como HMAC_SIGNATURE_FORGED."""
    repo = SQLiteLedgerRepository(str(tmp_path / "rehash.db"))
    seal_entry(_make_entry("r0", 0), repo, keys=KEYS)
    seal_entry(_make_entry("r1", 1), repo, keys=KEYS)

    blocks = list(repo.iter_blocks())
    b1 = blocks[1]
    new_payload_h = "a" * 64
    temp_block = replace(b1, payload_hash=new_payload_h)
    new_b_hash = block_hash(
        canonical_block_payload(
            temp_block,
            index=temp_block.block_index,
            prev_hash=temp_block.prev_hash,
            key_id=temp_block.key_id,
        )
    )
    # Conserva la firma antigua
    blocks[1] = replace(temp_block, block_hash=new_b_hash)

    verif = verify_chain(blocks, keys=KEYS)
    assert not verif.is_valid
    assert verif.corrupted_block_index == 1
    assert verif.failure_reason == "HMAC_SIGNATURE_FORGED"

    repo.close()


def test_forged_signature(tmp_path: Path) -> None:
    """Firma HMAC alterada o calculada con clave distinta genera HMAC_SIGNATURE_FORGED."""
    repo = SQLiteLedgerRepository(str(tmp_path / "forged.db"))
    seal_entry(_make_entry("f0", 0), repo, keys=KEYS)

    blocks = list(repo.iter_blocks())
    forged_sig = ("1" if blocks[0].hmac_signature[0] == "0" else "0") + blocks[0].hmac_signature[1:]
    blocks[0] = replace(blocks[0], hmac_signature=forged_sig)

    verif = verify_chain(blocks, keys=KEYS)
    assert not verif.is_valid
    assert verif.corrupted_block_index == 0
    assert verif.failure_reason == "HMAC_SIGNATURE_FORGED"

    repo.close()


def test_index_gap(tmp_path: Path) -> None:
    """Discontinuidad en la secuencia de índices produce INDEX_GAP."""
    repo = SQLiteLedgerRepository(str(tmp_path / "gap.db"))
    seal_entry(_make_entry("i0", 0), repo, keys=KEYS)
    seal_entry(_make_entry("i1", 1), repo, keys=KEYS)
    seal_entry(_make_entry("i2", 2), repo, keys=KEYS)

    blocks = list(repo.iter_blocks())
    # Omitir el bloque 1
    broken_blocks = [blocks[0], blocks[2]]

    verif = verify_chain(broken_blocks, keys=KEYS)
    assert not verif.is_valid
    assert verif.corrupted_block_index == 2
    assert verif.failure_reason == "INDEX_GAP"

    repo.close()


def test_anchor_tail_truncated(tmp_path: Path) -> None:
    """Si la cadena fue truncada respecto al ancla externa, detecta TAIL_TRUNCATED."""
    repo = SQLiteLedgerRepository(str(tmp_path / "anchor.db"))
    seal_entry(_make_entry("an0", 0), repo, keys=KEYS)
    seal_entry(_make_entry("an1", 1), repo, keys=KEYS)
    seal_entry(_make_entry("an2", 2), repo, keys=KEYS)

    blocks = list(repo.iter_blocks())
    anchor = ChainAnchor(count=3, head_hash=blocks[-1].block_hash)

    # Pasar solo 2 bloques con ancla de 3
    verif = verify_chain(blocks[:2], keys=KEYS, anchor=anchor)
    assert not verif.is_valid
    assert verif.failure_reason == "TAIL_TRUNCATED"

    # Pasar los 3 bloques íntegros con ancla correcta
    verif_ok = verify_chain(blocks, keys=KEYS, anchor=anchor)
    assert verif_ok.is_valid

    repo.close()


def test_verify_endpoint_and_latency(demo_client: TestClient) -> None:
    """GET /api/v1/ledger/verify responde en < 50 ms y detecta estado íntegro."""
    from tests.conftest import TOKEN_HEADERS

    state = demo_client.app.state.aduana
    seal_entry(_make_entry("endp0", 0), state.repo, keys=state.keys)
    seal_entry(_make_entry("endp1", 1), state.repo, keys=state.keys)

    t0 = time.perf_counter()
    resp = demo_client.get("/api/v1/ledger/verify", headers=TOKEN_HEADERS)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["blocks_checked"] == 2
    assert data["head_hash"] is not None
    assert data["latency_ms"] < 50.0
    assert elapsed_ms < 50.0, f"Latencia total excedida: {elapsed_ms:.2f} ms"


def test_tamper_sim_scenarios(demo_client: TestClient) -> None:
    """POST /api/v1/ledger/tamper-sim ejecuta los 4 escenarios en RAM sin tocar disco en < 50 ms."""
    from tests.conftest import TOKEN_HEADERS

    state = demo_client.app.state.aduana
    # Sembrar 2 bloques si no existen
    if state.repo.count() < 2:
        seal_entry(_make_entry("demo0", 0), state.repo, keys=state.keys)
        seal_entry(_make_entry("demo1", 1), state.repo, keys=state.keys)

    scenarios = [
        ("flip_payload_bit", "HASH_MISMATCH"),
        ("recompute_sha_without_key", "HMAC_SIGNATURE_FORGED"),
        ("break_prev_link", "PREV_HASH_LINK_BROKEN"),
        ("flip_override", "HASH_MISMATCH"),
    ]

    for scn, expected_reason in scenarios:
        t0 = time.perf_counter()
        resp = demo_client.post(
            "/api/v1/ledger/tamper-sim",
            json={"scenario": scn, "block_index": 1},
            headers=TOKEN_HEADERS,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        assert resp.status_code == 200, f"Fallo en escenario {scn}: {resp.text}"
        data = resp.json()
        assert data["simulated"] is True
        assert data["scenario"] == scn
        assert data["tampered_block_index"] == 1

        det = data["detection"]
        assert det["is_valid"] is False
        assert det["corrupted_block_index"] == 1
        assert det["failure_reason"] == expected_reason
        assert elapsed_ms < 50.0, f"Escenario {scn} tardó {elapsed_ms:.2f} ms >= 50 ms"

    # Verificar que el ledger real en disco sigue completamente intacto y válido
    check_resp = demo_client.get("/api/v1/ledger/verify", headers=TOKEN_HEADERS)
    assert check_resp.status_code == 200
    assert check_resp.json()["is_valid"] is True
