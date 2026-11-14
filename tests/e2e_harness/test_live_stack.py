from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from tests.e2e_harness.conftest import LiveStack
from tests.e2e_harness.support import IndexReferences, assert_asset_type, assert_no_cedula

ROOT = Path(__file__).resolve().parents[2]


def synthetic_tramite() -> dict[str, object]:
    return {
        "raw_text": "Solicitud sintetica de beca. Cedula V-12345678.",
        "citizen_cedula": "V-12345678",
        "consent": {"granted": True, "purpose_code": "BECA"},
        "features": {
            "tiempo_espera_dias": 30.0,
            "vulnerabilidad_socioeconomica": 0.6,
            "completitud_recaudos": 1.0,
            "urgencia_medica": 0.0,
            "complejidad_caso": 0.2,
        },
    }


def test_serves_front_index(live_http: httpx.Client) -> None:
    response = live_http.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.content == (ROOT / "static/index.html").read_bytes()


def test_index_has_no_external_hosts(live_http: httpx.Client) -> None:
    response = live_http.get("/")
    assert response.status_code == 200
    external = IndexReferences(response.text).external(str(live_http.base_url))
    assert not external, (
        f"FINDING: index.html references external hosts: {external}. "
        "External fonts (fonts.googleapis.com/fonts.gstatic.com) violate offline use and CSP."
    )


def test_referenced_assets(live_http: httpx.Client) -> None:
    response = live_http.get("/")
    assert response.status_code == 200
    assets = IndexReferences(response.text).local_assets(str(live_http.base_url))
    assert assets, "index.html must reference compiled frontend assets"
    for asset in assets:
        result = live_http.get(asset)
        assert result.status_code == 200, f"Referenced asset unavailable: {asset}"
        assert_asset_type(asset, result.headers.get("content-type", ""))


@pytest.mark.parametrize("route", ["/", "/api/v1/health/system", "/api/v1/ledger/verify"])
@pytest.mark.parametrize(
    "header,expected",
    [
        ("content-security-policy", "default-src 'self'"),
        ("x-content-type-options", "nosniff"),
    ],
)
def test_security_headers(live_http: httpx.Client, route: str, header: str, expected: str) -> None:
    response = live_http.get(route)
    assert response.status_code == 200
    assert expected in response.headers.get(header, ""), f"FINDING: {header} missing on {route}"
    if route.startswith("/api/"):
        assert "no-store" in response.headers.get("cache-control", "")


@pytest.mark.parametrize("route", ["/api/v1/ledger/verify", "/api/v1/shield/inspect"])
def test_rejects_missing_token(live_stack: LiveStack, route: str) -> None:
    with httpx.Client(base_url=live_stack.url, trust_env=False) as client:
        response = (
            client.get(route)
            if "/ledger/" in route
            else client.post(route, json={"raw_text": "Sintetico"})
        )
        assert response.status_code == 401


def test_rejects_plain_text(live_http: httpx.Client) -> None:
    response = live_http.post(
        "/api/v1/shield/inspect",
        content="Sintetico",
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 415


def test_full_api_flow_and_disk_privacy(live_http: httpx.Client, live_stack: LiveStack) -> None:
    health = live_http.get("/api/v1/health/system")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["ledger_mode"] == "persistent"
    payload = synthetic_tramite()
    shield = live_http.post("/api/v1/shield/inspect", json={"raw_text": payload["raw_text"]})
    assert shield.status_code == 201
    assert shield.json()["pii_count"] >= 1
    assert_no_cedula(shield.content, "Shield response")
    # The redacted text is safe to forward, unlike the mandatory raw ingress DTO.
    masked_json = json.dumps({"raw_text": shield.json()["masked_text"]}).encode()
    assert_no_cedula(masked_json, "masked request")
    processed = live_http.post("/api/v1/gateway/process", json=payload)
    assert processed.status_code == 201
    assert_no_cedula(processed.content, "Gateway response")
    result = processed.json()
    assert result["chain_verified"] is True
    assert result["policy_status"] != "BLOCKED"
    assert result["probability_score"] is not None
    assert set(result["linear_shap_values"]) == set(payload["features"])
    # The first ledger block is 0, but TamperSimRequest requires block_index >= 1.
    second = live_http.post("/api/v1/gateway/process", json=payload)
    assert second.status_code == 201
    assert_no_cedula(second.content, "second Gateway response")
    result = second.json()
    assert result["block_index"] >= 1
    verification = live_http.get("/api/v1/ledger/verify")
    assert verification.status_code == 200
    assert verification.json()["is_valid"] is True
    assert verification.json()["blocks_checked"] >= 1
    for scenario in (
        "flip_payload_bit",
        "recompute_sha_without_key",
        "break_prev_link",
        "flip_override",
    ):
        simulation = live_http.post(
            "/api/v1/ledger/tamper-sim",
            json={"scenario": scenario, "block_index": result["block_index"]},
        )
        assert simulation.status_code == 200, f"Tamper scenario failed: {scenario}"
        assert simulation.json()["simulated"] is True
        assert simulation.json()["detection"]["is_valid"] is False
        assert_no_cedula(simulation.request.content, "tamper request")
        assert_no_cedula(simulation.content, "tamper response")
    assert live_http.get("/api/v1/ledger/verify").json()["is_valid"] is True
    for response in (health, verification):
        assert_no_cedula(response.content, "API response")
    assert live_stack.db_path.is_file()
    assert live_stack.db_path.resolve() != (ROOT / "data/ledger.db").resolve()
    for path in live_stack.db_path.parent.glob("ledger.db*"):
        assert_no_cedula(path.read_bytes(), "temporary SQLite/WAL/SHM")


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Diseño: la cédula y el texto llegan EN CLARO al ingreso (loopback/TLS) porque SHIELD debe "
        "verlos para enmascararlos y calcular el índice ciego. Lo que se exige es que no se "
        "persistan ni se registren (ver los tests de .db y respuestas)."
    ),
)
@pytest.mark.parametrize("route", ["/api/v1/shield/inspect", "/api/v1/gateway/process"])
def test_ingress_request_bodies_do_not_expose_cedula(live_http: httpx.Client, route: str) -> None:
    payload = synthetic_tramite()
    body = {"raw_text": payload["raw_text"]} if "/shield/" in route else payload
    response = live_http.post(route, json=body)
    assert response.status_code == 201
    assert_no_cedula(response.content, "API response")
    ingress_msg = "ingress body (FINDING: API requires clear synthetic cedula)"
    assert_no_cedula(response.request.content, ingress_msg)


def test_duration_shuts_down_and_removes_temporary_db() -> None:
    completed = subprocess.run(  # noqa: S603
        [sys.executable, str(ROOT / "scripts/run_e2e_stack.py"), "--duration", "0.2"],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert completed.returncode == 0, "Duration shutdown failed; output redacted"
    lines = completed.stdout.splitlines()
    assert len(lines) == 1, "Harness must emit exactly one startup JSON line"
    info = json.loads(lines[0])
    assert set(info) == {"url", "token", "db_path", "pid"}
    assert not Path(info["db_path"]).parent.exists(), "Temporary storage survived shutdown"
    with httpx.Client(trust_env=False, timeout=1) as client:
        with pytest.raises((httpx.ConnectError, httpx.ConnectTimeout)):
            client.get(info["url"] + "/api/v1/health/system")
