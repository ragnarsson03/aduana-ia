"""Login único: respuesta rica para el front, logout con revocación y auditoría en el ledger."""

from __future__ import annotations

import dataclasses
from collections.abc import Iterator
from pathlib import Path

import pytest
from litestar.testing import TestClient

from app.server import create_app
from core.auth import blind_identifier
from core.config import Settings
from core.keyring import KeyRing
from core.rbac_seed import SEED_USERS, seed_users

API = "/api/v1"
API_TOKEN = "t" * 40
HEADERS = {"X-Aduana-Token": API_TOKEN, "Content-Type": "application/json"}
KEYS = KeyRing(bytes(range(32)))
TEST_PASSWORD = "Prueba-local-2026-{n}"  # noqa: S105 - contraseña de prueba local


def _passwords() -> dict[str, str]:
    return {u.codigo_usuario: TEST_PASSWORD.format(n=i) for i, u in enumerate(SEED_USERS)}


def _settings(tmp_path: Path, *, rbac: bool) -> Settings:
    return dataclasses.replace(
        Settings(),
        db_path=tmp_path / "ledger.db",
        users_db_path=tmp_path / "usuarios.db",
        ledger_ephemeral=not rbac,
        rbac_enabled=rbac,
        pbkdf2_iterations=1000,
        allowed_hosts=("testserver.local",),
    )


@pytest.fixture
def api(tmp_path: Path) -> Iterator[TestClient]:
    app = create_app(_settings(tmp_path, rbac=True), KEYS, API_TOKEN)
    with TestClient(app=app, base_url="http://testserver.local") as client:
        seed_users(client.app.state.aduana.identity, _passwords())
        yield client


@pytest.fixture
def api_without_rbac(tmp_path: Path) -> Iterator[TestClient]:
    app = create_app(_settings(tmp_path, rbac=False), KEYS, API_TOKEN)
    with TestClient(app=app, base_url="http://testserver.local") as client:
        yield client


def _login(client: TestClient, codigo: str):
    seed = next(u for u in SEED_USERS if u.codigo_usuario == codigo)
    return client.post(
        f"{API}/auth/login",
        json={"identificador": seed.identificador, "password": _passwords()[codigo]},
        headers=HEADERS,
    )


def _bearer(token: str) -> dict[str, str]:
    return {**HEADERS, "Authorization": f"Bearer {token}"}


def _verify(client: TestClient, headers: dict[str, str]) -> dict:
    response = client.get(f"{API}/ledger/verify", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


# --- respuesta única que consume el front ----------------------------------------------------


def test_login_returns_the_shape_the_front_consumes(api: TestClient) -> None:
    response = _login(api, "chat.analista.01")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["authenticated"] is True and body["token_type"] == "Bearer"  # noqa: S105
    assert body["session_token"].startswith("v1.") and body["expires_in_seconds"] > 0
    assert isinstance(body["block_index"], int) and body["citizen_receipt_code"].startswith("AUTH-")
    user = body["user"]
    assert user["username"] == "chat.analista.01"
    assert user["aduana_role"] == "ANALISTA_VALORACION_ADUANERA" and user["role"] == "analista"
    assert user["allowed_tabs"] == ["pasarela", "chat", "explicabilidad", "canal"]
    assert user["default_tab"] == "pasarela"
    assert {"chat:ia", "chat:canal"} <= set(user["permissions"])


@pytest.mark.parametrize(
    ("codigo", "ui_role", "tabs"),
    [
        ("insp.seniat.01", "auditor", ["pasarela", "ledger", "explicabilidad"]),
        ("agente.01", "analista", ["pasarela"]),
        ("almacen.01", "auditor", ["ledger"]),
        ("supervisor.01", "administrador", ["ledger"]),
    ],
)
def test_tabs_follow_real_permissions_not_a_client_table(
    api: TestClient, codigo: str, ui_role: str, tabs: list[str]
) -> None:
    user = _login(api, codigo).json()["user"]
    assert user["role"] == ui_role and user["allowed_tabs"] == tabs
    assert user["default_tab"] == tabs[0]


def test_login_response_never_carries_secrets_or_identifiers(api: TestClient) -> None:
    seed = next(u for u in SEED_USERS if u.codigo_usuario == "insp.seniat.01")
    text = _login(api, "insp.seniat.01").text
    for forbidden in (seed.identificador, _passwords()[seed.codigo_usuario], "salt", "hash"):
        assert forbidden not in text


def test_old_session_endpoint_and_cedula_field_are_gone(api: TestClient) -> None:
    assert api.get(f"{API}/auth/session", headers=HEADERS).status_code in (404, 405)
    seed = SEED_USERS[0]
    legacy = api.post(
        f"{API}/auth/login",
        json={"cedula": seed.identificador, "password": _passwords()[seed.codigo_usuario]},
        headers=HEADERS,
    )
    assert legacy.status_code in (400, 422)


# --- logout con revocación --------------------------------------------------------------------


def test_logout_revokes_the_token_everywhere(api: TestClient) -> None:
    token = _login(api, "supervisor.01").json()["session_token"]
    headers = _bearer(token)
    assert api.get(f"{API}/auth/me", headers=headers).status_code == 200
    out = api.post(f"{API}/auth/logout", headers=headers)
    assert out.status_code == 200 and out.json()["revoked"] is True and out.json()["jti"]
    assert api.get(f"{API}/auth/me", headers=headers).status_code == 401
    assert api.get(f"{API}/ledger/verify", headers=headers).status_code == 401
    assert api.post(f"{API}/auth/logout", headers=headers).status_code == 401  # ya revocado


def test_logout_only_revokes_that_session(api: TestClient) -> None:
    first = _bearer(_login(api, "supervisor.01").json()["session_token"])
    second = _bearer(_login(api, "supervisor.01").json()["session_token"])
    assert api.post(f"{API}/auth/logout", headers=first).status_code == 200
    assert api.get(f"{API}/auth/me", headers=second).status_code == 200


@pytest.mark.parametrize("authorization", [None, "Bearer", "Bearer basura", "Token abc"])
def test_logout_requires_a_valid_bearer(api: TestClient, authorization: str | None) -> None:
    headers = (
        dict(HEADERS) if authorization is None else {**HEADERS, "Authorization": authorization}
    )
    assert api.post(f"{API}/auth/logout", headers=headers).status_code == 401


# --- auditoría en el ledger -------------------------------------------------------------------


def test_successful_login_and_logout_are_sealed_but_failures_are_not(api: TestClient) -> None:
    bad = api.post(
        f"{API}/auth/login",
        json={"identificador": SEED_USERS[0].identificador, "password": "incorrecta-1234"},
        headers=HEADERS,
    )
    unknown = api.post(
        f"{API}/auth/login",
        json={"identificador": "V-77777777", "password": "incorrecta-1234"},
        headers=HEADERS,
    )
    assert bad.status_code == unknown.status_code == 401 and bad.json() == unknown.json()

    login = _login(api, "supervisor.01").json()
    headers = _bearer(login["session_token"])
    assert _verify(api, headers)["blocks_checked"] == 1  # solo el login exitoso
    assert api.post(f"{API}/auth/logout", headers=headers).status_code == 200
    again = _bearer(_login(api, "supervisor.01").json()["session_token"])
    assert _verify(api, again)["blocks_checked"] == 3  # login + logout + segundo login
    assert _verify(api, again)["is_valid"] is True


def test_audit_subject_is_not_the_citizen_blind_index(api: TestClient) -> None:
    """El funcionario no se correlaciona con un ciudadano que tenga el mismo número de cédula."""
    seed = next(u for u in SEED_USERS if u.codigo_usuario == "supervisor.01")
    assert _login(api, "supervisor.01").status_code == 200
    state = api.app.state.aduana
    assert state.repo.count() == 1
    citizen_style_id = blind_identifier(KEYS, seed.identificador)
    assert list(state.repo.iter_blocks_by_blind_id(citizen_style_id)) == []


# --- RBAC apagado -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path"), [("POST", "/auth/login"), ("POST", "/auth/logout"), ("GET", "/auth/me")]
)
def test_auth_endpoints_report_rbac_disabled(
    api_without_rbac: TestClient, method: str, path: str
) -> None:
    response = api_without_rbac.request(
        method, f"{API}{path}", headers=HEADERS, json={"identificador": "V-1", "password": "x"}
    )
    assert response.status_code == 503 and response.json() == {"error": "RBAC_DISABLED"}
