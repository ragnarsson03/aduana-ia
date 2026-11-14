"""Anti-escalada de privilegios: quien administra identidades no puede crear cuentas con más
atribuciones que las suyas (specs/06 §3, SoD). Reproduce el hueco hallado en la revisión: un
supervisor podía crear un inspector del SENIAT y suspenderse a sí mismo."""

from __future__ import annotations

import dataclasses
from collections.abc import Iterator
from pathlib import Path

import pytest
from litestar.testing import TestClient

from app.server import create_app
from core.config import Settings
from core.errors import AuthorizationError
from core.identity import IdentityService
from core.keyring import KeyRing
from core.rbac import MANAGEABLE_ROLES, can_manage_role
from core.rbac_db import UsuariosRepository

INSPECTOR = "INSPECTOR_TRIBUTARIO_SENIAT"
AGENTE = "AGENTE_ADUANAL_CERTIFICADO"
FISCAL = "FISCAL_ANTI_CONTRABANDO"
OPERADOR = "OPERADOR_LOGISTICO_ALMACEN"
SUPERVISOR = "SUPERVISOR_PUERTO_ADUANERO"
ANALISTA = "ANALISTA_VALORACION_ADUANERA"
PASSWORD = "Clave-de-prueba-1234"  # noqa: S105
API_TOKEN = "t" * 40
HEADERS = {"X-Aduana-Token": API_TOKEN, "Content-Type": "application/json"}


# --- política pura ------------------------------------------------------------------------------
def test_supervisor_manages_only_operational_roles() -> None:
    assert MANAGEABLE_ROLES[SUPERVISOR] == {AGENTE, FISCAL, OPERADOR, ANALISTA}
    for forbidden in (INSPECTOR, SUPERVISOR):
        assert not can_manage_role(SUPERVISOR, forbidden)  # type: ignore[arg-type]


@pytest.mark.parametrize("actor", [INSPECTOR, AGENTE, FISCAL, OPERADOR, ANALISTA])
def test_roles_without_user_management_manage_nobody(actor: str) -> None:
    assert not any(can_manage_role(actor, target) for target in MANAGEABLE_ROLES[SUPERVISOR])  # type: ignore[arg-type]


def test_unknown_actor_manages_nobody() -> None:
    assert not can_manage_role("ADMIN_DE_SISTEMAS", AGENTE)  # type: ignore[arg-type]


# --- IdentityService ------------------------------------------------------------------------------
@pytest.fixture
def service(tmp_path: Path) -> Iterator[IdentityService]:
    repo = UsuariosRepository(str(tmp_path / "u.db"))
    svc = IdentityService(
        repo,
        KeyRing(bytes(range(32))),
        iterations=1000,
        token_ttl_seconds=600,
        max_failed_attempts=5,
        lockout_seconds=900,
    )
    yield svc
    repo.close()


def _make(service: IdentityService, codigo: str, ident: str, rol: str):  # type: ignore[no-untyped-def]
    return service.create_user(
        codigo_usuario=codigo, identificador=ident, rol=rol, password=PASSWORD
    )  # type: ignore[arg-type]


@pytest.mark.parametrize("rol", [INSPECTOR, SUPERVISOR])
def test_supervisor_cannot_create_privileged_accounts(service: IdentityService, rol: str) -> None:
    sup = _make(service, "sup.01", "V-90000001", SUPERVISOR)
    with pytest.raises(AuthorizationError):
        service.create_user_as(
            sup, codigo_usuario="x.01", identificador="V-90000002", rol=rol, password=PASSWORD
        )  # type: ignore[arg-type]
    assert [u.codigo_usuario for u in service.list_users()] == ["sup.01"]


@pytest.mark.parametrize("rol", [AGENTE, FISCAL, OPERADOR, ANALISTA])
def test_supervisor_can_create_operational_accounts(service: IdentityService, rol: str) -> None:
    sup = _make(service, "sup.01", "V-90000001", SUPERVISOR)
    created = service.create_user_as(
        sup, codigo_usuario="op.01", identificador="V-90000003", rol=rol, password=PASSWORD
    )  # type: ignore[arg-type]
    assert created.rol == rol


@pytest.mark.parametrize("actor_rol", [INSPECTOR, AGENTE, FISCAL, OPERADOR, ANALISTA])
def test_roles_without_users_manage_cannot_create_anyone(
    service: IdentityService, actor_rol: str
) -> None:
    actor = _make(service, "act.01", "V-90000004", actor_rol)
    with pytest.raises(AuthorizationError):
        service.create_user_as(
            actor, codigo_usuario="op.01", identificador="V-90000005", rol=AGENTE, password=PASSWORD
        )  # type: ignore[arg-type]


def test_supervisor_cannot_suspend_self_or_other_supervisors_or_inspectors(
    service: IdentityService,
) -> None:
    sup = _make(service, "sup.01", "V-90000001", SUPERVISOR)
    other = _make(service, "sup.02", "V-90000006", SUPERVISOR)
    insp = _make(service, "insp.01", "V-90000007", INSPECTOR)
    for target in (sup, other, insp):
        with pytest.raises(AuthorizationError):
            service.suspend_user_as(sup, target.codigo_usuario)
    assert all(u.estado == "ACTIVO" for u in service.list_users())


def test_supervisor_can_suspend_operational_user(service: IdentityService) -> None:
    sup = _make(service, "sup.01", "V-90000001", SUPERVISOR)
    agente = _make(service, "ag.01", "V-90000008", AGENTE)
    assert service.suspend_user_as(sup, agente.codigo_usuario).estado == "SUSPENDIDO"


def test_supervisor_cannot_promote_anyone_to_privileged_role_or_change_own_role(
    service: IdentityService,
) -> None:
    sup = _make(service, "sup.01", "V-90000001", SUPERVISOR)
    agente = _make(service, "ag.01", "V-90000008", AGENTE)
    for target, new_rol in ((agente, INSPECTOR), (agente, SUPERVISOR), (sup, INSPECTOR)):
        with pytest.raises(AuthorizationError):
            service.change_role_as(sup, target.codigo_usuario, new_rol)  # type: ignore[arg-type]
    assert service.change_role_as(sup, agente.codigo_usuario, FISCAL).rol == FISCAL  # type: ignore[arg-type]


def test_suspended_actor_cannot_manage(service: IdentityService) -> None:
    sup = _make(service, "sup.01", "V-90000001", SUPERVISOR)
    service.suspend_user(sup.user_id)
    stale = dataclasses.replace(sup)  # copia con estado viejo ACTIVO: el servicio debe reconsultar
    with pytest.raises(AuthorizationError):
        service.create_user_as(
            stale, codigo_usuario="op.01", identificador="V-90000009", rol=AGENTE, password=PASSWORD
        )  # type: ignore[arg-type]


def test_authorization_error_message_is_fixed(service: IdentityService) -> None:
    sup = _make(service, "sup.01", "V-90000001", SUPERVISOR)
    with pytest.raises(AuthorizationError) as info:
        service.create_user_as(
            sup, codigo_usuario="x.01", identificador="V-90000010", rol=INSPECTOR, password=PASSWORD
        )  # type: ignore[arg-type]
    assert "V-90000010" not in str(info.value) and PASSWORD not in str(info.value)


# --- API ---------------------------------------------------------------------------------------
@pytest.fixture
def api(tmp_path: Path) -> Iterator[tuple[TestClient, dict[str, str]]]:
    settings = dataclasses.replace(
        Settings(),
        db_path=tmp_path / "l.db",
        users_db_path=tmp_path / "u.db",
        ledger_ephemeral=False,
        rbac_enabled=True,
        pbkdf2_iterations=1000,
        allowed_hosts=("testserver.local",),
    )
    with TestClient(
        app=create_app(settings, KeyRing(bytes(range(32))), API_TOKEN),
        base_url="http://testserver.local",
    ) as client:
        _make(client.app.state.aduana.identity, "sup.01", "V-90000101", SUPERVISOR)
        token = client.post(
            "/api/v1/auth/login",
            json={"identificador": "V-90000101", "password": PASSWORD},
            headers=HEADERS,
        ).json()["session_token"]
        yield client, {**HEADERS, "Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("rol", [INSPECTOR, SUPERVISOR])
def test_api_supervisor_cannot_mint_privileged_accounts(
    api: tuple[TestClient, dict[str, str]], rol: str
) -> None:
    client, headers = api
    response = client.post(
        "/api/v1/usuarios",
        json={
            "codigo_usuario": "mint.01",
            "identificador": "V-90000201",
            "rol": rol,
            "password": PASSWORD,
        },
        headers=headers,
    )
    assert response.status_code == 403 and response.json() == {"error": "ERR_FORBIDDEN"}
    codes = [u["codigo_usuario"] for u in client.get("/api/v1/usuarios", headers=headers).json()]
    assert "mint.01" not in codes


def test_api_supervisor_cannot_suspend_self(api: tuple[TestClient, dict[str, str]]) -> None:
    client, headers = api
    response = client.post("/api/v1/usuarios/sup.01/suspender", headers=headers)
    assert response.status_code == 403
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200  # sigue activo


def test_api_supervisor_can_manage_operational_roles(
    api: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = api
    created = client.post(
        "/api/v1/usuarios",
        json={
            "codigo_usuario": "ag.nuevo",
            "identificador": "V-90000202",
            "rol": AGENTE,
            "password": PASSWORD,
        },
        headers=headers,
    )
    assert created.status_code == 201
    assert client.post("/api/v1/usuarios/ag.nuevo/suspender", headers=headers).status_code == 200
