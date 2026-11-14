"""CA-05 (parte Gatillo 0): la bóveda jamás toca disco ni emite logs.

La auditoría binaria del ``.db`` tras 20 trámites queda en rojo esperado hasta el Gatillo 3.
"""

from __future__ import annotations

import ast
import inspect
import logging
from pathlib import Path

import pytest

from core import crypto, ephemeral_vault
from core.context import LedgerEntry
from core.ephemeral_vault import EphemeralVault
from core.keyring import KeyRing
from pipeline.stage4_ledger import SQLiteLedgerRepository, seal_entry

SECRET = "V-12345678"
FORBIDDEN_MODULES = {"sqlite3", "pickle", "shelve", "tempfile", "logging", "os", "pathlib", "io"}
FORBIDDEN_CALLS = {"open", "print"}


def test_vault_lifecycle_writes_no_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    vault = EphemeralVault()
    for i in range(20):
        vault.put(f"r{i}", {"[CEDULA_1]": SECRET})
        vault.get_map(f"r{i}")
        vault.zeroize(f"r{i}")
    assert list(tmp_path.iterdir()) == []


def test_vault_emits_no_logs(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG):
        vault = EphemeralVault()
        vault.put("r1", {"[CEDULA_1]": SECRET})
        vault.zeroize("r1")
    assert SECRET not in caplog.text


def test_vault_module_has_no_io_primitives() -> None:
    tree = ast.parse(inspect.getsource(ephemeral_vault))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    called = {
        node.func.id for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert imported.isdisjoint(FORBIDDEN_MODULES), imported & FORBIDDEN_MODULES
    assert called.isdisjoint(FORBIDDEN_CALLS), called & FORBIDDEN_CALLS


def test_vault_error_messages_never_contain_pii() -> None:
    vault = EphemeralVault()
    vault.put("r1", {"[CEDULA_1]": SECRET})
    vault.zeroize("r1")
    with pytest.raises(Exception) as info:  # noqa: PT011
        vault.get_map("r1")
    assert SECRET not in str(info.value)


def test_ca05_db_and_wal_hold_zero_plaintext_pii_after_20_requests(tmp_path: Path) -> None:
    """CA-05: tras 20 trámites, auditoría binaria de .db, -wal y -shm comprueba 0 bytes de PII."""
    keys = KeyRing(bytes(range(32)))
    db_path = tmp_path / "ledger.db"
    repo = SQLiteLedgerRepository(str(db_path))

    cedulas = [f"V-{10000000 + i}" for i in range(20)]
    rifs = [f"J-{12345670 + i}-4" for i in range(20)]
    phones = [f"0412-00000{i:02d}" for i in range(20)]
    justifications = [f"Solicitante {c} aprobado con {r}" for c, r in zip(cedulas, rifs, strict=True)]

    for i in range(20):
        blind_id = crypto.blind_citizen_id(keys, cedulas[i])
        payload_h = crypto.sha256_hex(f"sanitized_payload_{i}".encode())
        just_h = keys.hmac_hex("justification", justifications[i].encode())

        entry = LedgerEntry(
            request_id=f"req-audit-{i:03d}",
            timestamp_utc=f"2026-11-13T12:{i:02d}:00Z",
            blind_citizen_id=blind_id,
            payload_hash=payload_h,
            security_verdict="CLEAN",
            model_recommendation="PRIORIDAD_ALTA",
            human_decision="PRIORIDAD_ALTA",
            human_override=True,
            citizen_receipt_code=f"REC-AUDIT-{i:03d}",
            override_justification_hash=just_h,
        )
        seal_entry(entry, repo, keys=keys)

    assert repo.count() == 20
    repo.close()

    # Auditoría binaria forense de los archivos de base de datos en disco
    db_bytes = bytearray()
    for ext in ("", "-wal", "-shm"):
        fpath = tmp_path / f"ledger.db{ext}"
        if fpath.exists():
            db_bytes.extend(fpath.read_bytes())

    raw_bytes = bytes(db_bytes)

    # Verificar que NINGUNA cédula, número de cédula, RIF, teléfono ni texto de justificación aparece
    for c in cedulas:
        assert c.encode() not in raw_bytes, f"Cédula {c} encontrada en disco"
        digits = c.replace("V-", "")
        assert digits.encode() not in raw_bytes, f"Dígitos de cédula {digits} encontrados en disco"

    for r in rifs:
        assert r.encode() not in raw_bytes, f"RIF {r} encontrado en disco"

    for p in phones:
        assert p.encode() not in raw_bytes, f"Teléfono {p} encontrado en disco"

    for j in justifications:
        assert j.encode() not in raw_bytes, f"Texto de justificación encontrado en disco"

