"""Los dos usuarios sembrados con acceso al chat de la IA y al canal seguro entre funcionarios."""

from __future__ import annotations

import dataclasses
from collections.abc import Iterator
from pathlib import Path

import pytest
from litestar.testing import TestClient

from app.server import create_app
from core.config import Settings
from core.keyring import KeyRing
from core.rbac_seed import SEED_USERS, seed_users

API_TOKEN = "t" * 40
CHAT_CODES = ("chat.analista.01", "chat.analista.02")
CHAT_ROLE = "ANALISTA_VALORACION_ADUANERA"
HEADERS = {"X-Aduana-Token": API_TOKEN, "Content-Type": "application/json"}
# Contraseñas de prueba locales (no son las del seeder real, que las genera al sembrar).
TEST_PASSWORD = "Prueba-local-2026-{n}"


def _passwords() -> dict[str, str]:
    return {u.codigo_usuario: TEST_PASSWORD.format(n=i) for i, u in enumerate(SEED_USERS)}


@pytest.fixture
def api(tmp_path: Path) -> Iterator[TestClient]:
    settings = dataclasses.replace(
        Settings(),
        db_path=tmp_path / "ledger.db",
        users_db_path=tmp_path / "usuarios.db",
        ledger_ephemeral=False,
        rbac_enabled=True,
        pbkdf2_iterations=1000,
        allowed_hosts=("testserver.local",),
    )
    app = create_app(settings, KeyRing(bytes(range(32))), API_TOKEN)
    with TestClient(app=app, base_url="http://testserver.local") as client:
        seed_users(client.app.state.aduana.identity, _passwords())
        yield client


def _login(client: TestClient, codigo: str) -> dict[str, str]:
    seed = next(u for u in SEED_USERS if u.codigo_usuario == codigo)
    password = _passwords()[codigo]
    response = client.post(
        "/api/v1/auth/login",
        json={"identificador": seed.identificador, "password": password},
        headers=HEADERS,
    )
    assert response.status_code == 200, response.text
    return {**HEADERS, "Authorization": f"Bearer {response.json()['session_token']}"}


def test_exactly_two_chat_users_are_seeded_with_valuation_role() -> None:
    chat_users = [u for u in SEED_USERS if u.codigo_usuario.startswith("chat.")]
    assert tuple(u.codigo_usuario for u in chat_users) == CHAT_CODES
    assert all(u.rol == CHAT_ROLE for u in chat_users)
    assert len({u.identificador for u in chat_users}) == 2  # cuentas distintas: pueden conversar


@pytest.mark.parametrize("codigo", CHAT_CODES)
def test_chat_user_logs_in_and_has_both_chat_permissions(api: TestClient, codigo: str) -> None:
    headers = _login(api, codigo)
    me = api.get("/api/v1/auth/me", headers=headers).json()
    assert me["codigo_usuario"] == codigo and me["rol"] == CHAT_ROLE
    assert {"chat:ia", "chat:canal"} <= set(me["permisos"])


@pytest.mark.parametrize("codigo", CHAT_CODES)
def test_chat_user_can_use_the_ai_chat_endpoint(api: TestClient, codigo: str) -> None:
    headers = _login(api, codigo)
    response = api.post(
        "/api/v1/shield/inspect", json={"raw_text": "Consulta sobre mi expediente."}, headers=headers
    )
    assert response.status_code == 201, response.text


@pytest.mark.parametrize("codigo", CHAT_CODES)
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/v1/usuarios"),
        ("post", "/api/v1/audit/fiscal"),
        ("get", "/api/v1/ledger/verify"),
        ("get", "/api/v1/metrics/benchmark"),
    ],
)
def test_chat_users_gain_no_other_access(api: TestClient, codigo: str, method: str, path: str) -> None:
    headers = _login(api, codigo)
    kwargs = {"json": {"identificador": "V-12345678"}} if method == "post" else {}
    response = getattr(api, method)(path, headers=headers, **kwargs)
    assert response.status_code == 403 and response.json() == {"error": "ERR_FORBIDDEN"}


def test_chat_users_cannot_submit_tramites(api: TestClient) -> None:
    headers = _login(api, CHAT_CODES[0])
    body = {
        "raw_text": "Solicito constancia.",
        "citizen_cedula": "V-12345678",
        "consent": {"granted": True, "purpose_code": "BECA"},
        "features": {},
    }
    assert api.post("/api/v1/gateway/process", json=body, headers=headers).status_code == 403


def test_other_roles_have_no_chat_access(api: TestClient) -> None:
    """Un agente aduanal (externo) no puede usar el chat de la IA ni el canal seguro."""
    headers = _login(api, "agente.01")
    me = api.get("/api/v1/auth/me", headers=headers).json()
    assert not {"chat:ia", "chat:canal"} & set(me["permisos"])
    response = api.post("/api/v1/shield/inspect", json={"raw_text": "hola"}, headers=headers)
    assert response.status_code == 403
