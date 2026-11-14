"""Humo de estructura: el esqueleto importa, arranca y respeta contratos base."""

from __future__ import annotations

import dataclasses
import importlib
from pathlib import Path

import pytest
from litestar.testing import TestClient

from core.context import CitizenConsent, ExplicaResult
from core.protocols import LLMAdapterProtocol, StorageRepositoryProtocol
from pipeline.llm_adapter import OfflineDeterministicAdapter
from pipeline.stage4_ledger import SQLiteLedgerRepository
from tests.conftest import TOKEN_HEADERS

MODULES = [
    "core.context", "core.config", "core.errors", "core.crypto", "core.keyring",
    "core.ephemeral_vault", "core.protocols", "core.text_normalizer", "core.pii_patterns",
    "pipeline.stage0_consent", "pipeline.stage1_shield", "pipeline.stage2_guard_in",
    "pipeline.stage3_guard_out", "pipeline.stage4_ledger", "pipeline.stage5_explica",
    "pipeline.llm_adapter", "pipeline.orchestrator",
    "app.server", "app.schemas", "app.dependencies", "app.desktop", "app.security",
]

GATEWAY_BODY = {
    "raw_text": "x",
    "citizen_cedula": "V-12345678",
    "consent": {"granted": True, "purpose_code": "BECA"},
    "features": {},
}


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name: str) -> None:
    assert importlib.import_module(name)


def test_importing_server_has_no_side_effects() -> None:
    server = importlib.import_module("app.server")
    assert not hasattr(server, "app")


def test_context_dataclasses_are_frozen() -> None:
    consent = CitizenConsent(True, "BECA", "2026-11-13T10:00:00Z", "h")
    with pytest.raises(dataclasses.FrozenInstanceError):
        consent.granted = False  # type: ignore[misc]


def test_explica_mappings_are_deeply_immutable() -> None:
    source = {"a": 1.0}
    result = ExplicaResult(
        "m", 0.0, 0.5, 0.0, source, source, source, 0.0, "REVISION_ESTANDAR", "REVISION_ESTANDAR",
        False,
    )
    source["a"] = 99.0
    assert result.feature_values["a"] == 1.0
    with pytest.raises(TypeError):
        result.feature_values["a"] = 2.0  # type: ignore[index]


def test_implementations_satisfy_protocols(tmp_path: Path) -> None:
    assert isinstance(OfflineDeterministicAdapter(), LLMAdapterProtocol)
    assert isinstance(SQLiteLedgerRepository(str(tmp_path / "x.db")), StorageRepositoryProtocol)


def test_health_is_public_and_minimal(client: TestClient) -> None:
    response = client.get("/api/v1/health/system")
    assert response.status_code == 200
    assert set(response.json()) == {"status", "ledger_mode", "implemented_stages"}


def test_gateway_process_endpoint_is_implemented(client: TestClient) -> None:
    body = {
        "raw_text": "Solicitud institucional de prueba",
        "citizen_cedula": "V-12345678",
        "consent": {"granted": True, "purpose_code": "BECA"},
        "features": {"f1": 0.0, "f2": 0.0, "f3": 0.0, "f4": 0.0, "f5": 0.0},
    }
    response = client.post("/api/v1/gateway/process", headers=TOKEN_HEADERS, json=body)
    assert response.status_code == 201
