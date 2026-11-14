"""Variables de EXPLICA inválidas deben responder 422 estable, no 500 genérico."""

from __future__ import annotations

import pytest
from litestar.testing import TestClient

from tests.conftest import TOKEN_HEADERS

VALID_FEATURES = {
    "tiempo_espera_dias": 45.0,
    "vulnerabilidad_socioeconomica": 0.6,
    "completitud_recaudos": 0.9,
    "urgencia_medica": 0.2,
    "complejidad_caso": 0.4,
}


def _body(features: dict[str, float]) -> dict:
    return {
        "raw_text": "Solicito una beca para estudiar ingeniería.",
        "citizen_cedula": "V-12345678",
        "consent": {"granted": True, "purpose_code": "BECA"},
        "features": features,
    }


def test_valid_features_are_accepted(client: TestClient) -> None:
    response = client.post("/api/v1/gateway/process", json=_body(VALID_FEATURES), headers=TOKEN_HEADERS)
    assert response.status_code == 201, response.text
    assert 0.0 <= response.json()["probability_score"] <= 1.0


@pytest.mark.parametrize(
    "features",
    [
        {k: v for k, v in VALID_FEATURES.items() if k != "urgencia_medica"},  # falta una
        {**VALID_FEATURES, "campo_inventado": 1.0},  # sobrante
        {"x": 1.0},  # esquema desconocido
        {},  # vacío
    ],
    ids=["missing", "extra", "unknown_schema", "empty"],
)
def test_invalid_feature_vector_returns_422_with_stable_code(
    client: TestClient, features: dict[str, float]
) -> None:
    response = client.post("/api/v1/gateway/process", json=_body(features), headers=TOKEN_HEADERS)
    assert response.status_code == 422, response.text
    assert response.json() == {"error": "ERR_INVALID_FEATURES"}


def test_invalid_features_response_never_echoes_citizen_text(client: TestClient) -> None:
    response = client.post("/api/v1/gateway/process", json=_body({}), headers=TOKEN_HEADERS)
    assert "V-12345678" not in response.text and "ingeniería" not in response.text
