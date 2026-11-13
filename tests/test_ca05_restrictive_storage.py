"""CA-05 (parte Gatillo 0): la bóveda jamás toca disco ni emite logs.

La auditoría binaria del ``.db`` tras 20 trámites queda en rojo esperado hasta el Gatillo 3.
"""

from __future__ import annotations

import ast
import inspect
import logging
from pathlib import Path

import pytest

from core import ephemeral_vault
from core.ephemeral_vault import EphemeralVault
from pipeline.stage4_ledger import SQLiteLedgerRepository

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


@pytest.mark.xfail(strict=True, raises=NotImplementedError, reason="Gatillo 3: ledger SQLite")
def test_ca05_db_and_wal_hold_zero_plaintext_pii_after_20_requests(tmp_path: Path) -> None:
    SQLiteLedgerRepository(str(tmp_path / "ledger.db")).count()
