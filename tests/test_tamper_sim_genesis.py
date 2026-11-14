"""La simulación de sabotaje debe poder apuntar al bloque génesis (índice 0)."""

from __future__ import annotations

import pytest
from litestar.testing import TestClient

from tests.conftest import TOKEN_HEADERS

BODY = {
    "raw_text": "Solicito constancia de residencia.",
    "citizen_cedula": "V-12345678",
    "consent": {"granted": True, "purpose_code": "TRAMITE_GENERAL"},
    "features": {
        "tiempo_espera_dias": 10.0,
        "vulnerabilidad_socioeconomica": 0.2,
        "completitud_recaudos": 0.9,
        "urgencia_medica": 0.0,
        "complejidad_caso": 0.3,
    },
}


def _seal_one(client: TestClient) -> None:
    response = client.post("/api/v1/gateway/process", json=BODY, headers=TOKEN_HEADERS)
    assert response.status_code == 201, response.text


@pytest.mark.parametrize("scenario", ["flip_payload_bit", "recompute_sha_without_key", "flip_override"])
def test_tamper_on_genesis_block_is_detected(demo_client: TestClient, scenario: str) -> None:
    _seal_one(demo_client)
    response = demo_client.post(
        "/api/v1/ledger/tamper-sim",
        json={"scenario": scenario, "block_index": 0},
        headers=TOKEN_HEADERS,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["simulated"] is True and body["tampered_block_index"] == 0
    assert body["detection"]["is_valid"] is False
    assert body["detection"]["corrupted_block_index"] == 0


def test_tamper_simulation_never_corrupts_the_real_ledger(demo_client: TestClient) -> None:
    _seal_one(demo_client)
    demo_client.post(
        "/api/v1/ledger/tamper-sim",
        json={"scenario": "flip_payload_bit", "block_index": 0},
        headers=TOKEN_HEADERS,
    )
    verify = demo_client.get("/api/v1/ledger/verify", headers=TOKEN_HEADERS).json()
    assert verify["is_valid"] is True and verify["blocks_checked"] == 1


def test_negative_block_index_is_rejected(demo_client: TestClient) -> None:
    response = demo_client.post(
        "/api/v1/ledger/tamper-sim",
        json={"scenario": "flip_override", "block_index": -1},
        headers=TOKEN_HEADERS,
    )
    assert response.status_code == 400
