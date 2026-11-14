"""Endurecimiento de la API: auth, content-type, hosts, cabeceras, tamper-sim, Zero-Leak."""

from __future__ import annotations

import logging

import pytest
from litestar.testing import TestClient

from app.schemas import ConsentIn, GatewayProcessRequest, ShieldInspectRequest
from pipeline.orchestrator import GatewayInput
from tests.conftest import API_TOKEN, TOKEN_HEADERS

SECRET = "V-12345678"


def test_api_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/ledger/verify")
    assert response.status_code == 401


def test_wrong_token_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/ledger/verify", headers={"X-Aduana-Token": "x" * 40})
    assert response.status_code == 401


def test_text_plain_post_rejected_even_with_token(client: TestClient) -> None:
    response = client.post(
        "/api/v1/shield/inspect",
        content=f'{{"raw_text": "{SECRET}"}}',
        headers={"X-Aduana-Token": API_TOKEN, "Content-Type": "text/plain"},
    )
    assert response.status_code == 415


def test_unknown_host_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/health/system", headers={"Host": "evil.example"})
    assert response.status_code == 400


def test_security_headers_present(client: TestClient) -> None:
    response = client.get("/api/v1/health/system")
    assert "default-src 'self'" in response.headers["content-security-policy"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"


def test_openapi_ui_not_exposed(client: TestClient) -> None:
    for path in ("/schema", "/schema/swagger", "/schema/redoc"):
        assert client.get(path).status_code == 404


def test_tamper_sim_absent_without_demo_mode(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ledger/tamper-sim",
        json={"scenario": "flip_override", "block_index": 1},
        headers=TOKEN_HEADERS,
    )
    assert response.status_code in (404, 405)


def test_tamper_sim_registered_in_demo_mode(demo_client: TestClient) -> None:
    response = demo_client.post(
        "/api/v1/ledger/tamper-sim",
        json={"scenario": "flip_override", "block_index": 1},
        headers=TOKEN_HEADERS,
    )
    # Ruta registrada y activa: valida parámetros (400 si índice fuera de rango, 200 si simula)
    assert response.status_code in (200, 400)


@pytest.mark.parametrize(
    "body",
    [
        {"raw_text": SECRET, "extra": 1},  # campo desconocido
        {"raw_text": ""},  # vacío
        {"raw_text": "x" * 20_001},  # excede el máximo
    ],
)
def test_shield_dto_is_strict_and_never_echoes_input(client: TestClient, body: dict) -> None:
    response = client.post("/api/v1/shield/inspect", json=body, headers=TOKEN_HEADERS)
    assert response.status_code == 400
    assert SECRET not in response.text


def test_shield_inspect_masks_and_leaves_no_vault_session(client: TestClient) -> None:
    text = "Solicitante V-00000001, tel 0412-0000001, J-12345678-4"
    response = client.post("/api/v1/shield/inspect", json={"raw_text": text}, headers=TOKEN_HEADERS)
    assert response.status_code == 201
    body = response.json()
    assert body["masked_text"].count("[") == 3 and "V-00000001" not in response.text
    assert body["pii_count"] == 3 and body["rif_mod11_verified"] is True
    assert client.app.state.aduana.vault.active_sessions == 0


def test_shield_inspect_never_logs_input(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG):
        client.post("/api/v1/shield/inspect", json={"raw_text": SECRET}, headers=TOKEN_HEADERS)
    assert SECRET not in caplog.text


def test_oversized_body_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/shield/inspect", content="x" * 70_000, headers=TOKEN_HEADERS
    )
    assert response.status_code == 413


def test_validation_failure_does_not_leak_to_logs(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.DEBUG):
        client.post(
            "/api/v1/gateway/process",
            json={
                "raw_text": SECRET,
                "citizen_cedula": SECRET,
                "consent": {"granted": True, "purpose_code": "BECA"},
                "features": {},
                "human_decision": f"CEDULA {SECRET}",  # enum inválido con PII
            },
            headers=TOKEN_HEADERS,
        )
    assert SECRET not in caplog.text


def test_dto_and_input_reprs_are_redacted() -> None:
    dto = GatewayProcessRequest(
        raw_text=SECRET,
        citizen_cedula=SECRET,
        consent=ConsentIn(granted=True, purpose_code="BECA"),
        features={},
    )
    assert SECRET not in repr(ShieldInspectRequest(raw_text=SECRET))
    assert SECRET not in repr(dto)
    gateway = GatewayInput(SECRET, SECRET, True, "BECA", {})
    assert SECRET not in repr(gateway)
