"""CA-07c (API) y Zero-PII del RBAC aduanero: aislamiento de permisos entre los 6 roles.

Contrato: ``specs/06_rbac_aduanero.spec.md`` (§3 matriz, §4 endpoints/errores, §5, §9).
Las importaciones del código nuevo (core.auth, core.rbac_db, core.identity) se hacen DENTRO de
fixtures y funciones para que ``pytest --collect-only`` funcione antes de la implementación.
Todos los identificadores y contraseñas de este archivo son sintéticos y locales.
"""

from __future__ import annotations

import itertools
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Final

import pytest
from litestar.testing import TestClient

from app.server import create_app
from core.config import PROJECT_ROOT, Settings
from core.keyring import KeyRing
from tests.conftest import API_TOKEN, TOKEN_HEADERS

API: Final[str] = "/api/v1"
CITIZEN_CEDULA: Final[str] = "V-12345678"
OTHER_CEDULA: Final[str] = "V-87654321"
RAW_TEXT: Final[str] = f"Solicitud de importación de insumos médicos, solicitante {CITIZEN_CEDULA}."
FEATURES: Final[dict[str, float]] = {
    "tiempo_espera_dias": 90.0,
    "vulnerabilidad_socioeconomica": 0.8,
    "completitud_recaudos": 0.9,
    "urgencia_medica": 1.0,
    "complejidad_caso": 0.3,
}
JUSTIFICATION: Final[str] = "Falso positivo confirmado tras revisión documental presencial."

AGENTE: Final = "AGENTE_ADUANAL_CERTIFICADO"
INSPECTOR: Final = "INSPECTOR_TRIBUTARIO_SENIAT"
FISCAL: Final = "FISCAL_ANTI_CONTRABANDO"
OPERADOR: Final = "OPERADOR_LOGISTICO_ALMACEN"
SUPERVISOR: Final = "SUPERVISOR_PUERTO_ADUANERO"
ANALISTA: Final = "ANALISTA_VALORACION_ADUANERA"
ALL_ROLES: Final[tuple[str, ...]] = (AGENTE, INSPECTOR, FISCAL, OPERADOR, SUPERVISOR, ANALISTA)

# rol -> (identificador sintético, codigo_usuario, contraseña de prueba)
ROLE_ACCOUNTS: Final[dict[str, tuple[str, str, str]]] = {
    INSPECTOR: ("V-90000001", "t.insp.01", "Inspector-Test-2024x"),
    AGENTE: ("V-90000002", "t.agente.01", "Agente-Test-2024x"),
    FISCAL: ("V-90000003", "t.fiscal.01", "Fiscal-Test-2024x"),
    OPERADOR: ("V-90000004", "t.oper.01", "Operador-Test-2024x"),
    SUPERVISOR: ("V-90000005", "t.superv.01", "Supervisor-Test-2024x"),
    ANALISTA: ("V-90000006", "t.analista.01", "Analista-Test-2024x"),
}
VICTIM: Final = ("V-90000007", "t.victima.01", "Victima-Test-2024x", AGENTE)
LOCKOUT_USER: Final = ("V-90000008", "t.bloqueo.01", "Bloqueo-Test-2024x", AGENTE)
UNKNOWN_IDENTIFIER: Final[str] = "V-90999999"
FORBIDDEN_BODY: Final[dict[str, str]] = {"error": "ERR_FORBIDDEN"}
UNAUTHORIZED_BODY: Final[dict[str, str]] = {"error": "ERR_AUTH_INVALID"}
SECRET_FIELDS: Final[tuple[str, ...]] = ("password_salt", "password_hash", "blind_identifier")
_counter = itertools.count(1)


@dataclass(frozen=True)
class Env:
    client: TestClient
    settings: Settings
    keys: KeyRing
    headers: dict[str, dict[str, str]]  # rol -> cabeceras con Bearer
    receipt_code: str  # recibo de un trámite real enviado por el agente con CITIZEN_CEDULA

    def call(
        self, method: str, path: str, role: str | None = None, body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        chosen = headers if headers is not None else (
            self.headers[role] if role else dict(TOKEN_HEADERS)
        )
        return self.client.request(method, f"{API}{path}", headers=chosen, json=body)


def _bearer(token: str) -> dict[str, str]:
    return {**TOKEN_HEADERS, "Authorization": f"Bearer {token}"}


def _login(client: TestClient, identificador: str, password: str) -> Any:
    return client.post(
        f"{API}/auth/login",
        json={"identificador": identificador, "password": password},
        headers=TOKEN_HEADERS,
    )


def gateway_body(cedula: str = CITIZEN_CEDULA, **extra: Any) -> dict[str, Any]:
    return {
        "raw_text": RAW_TEXT.replace(CITIZEN_CEDULA, cedula),
        "citizen_cedula": cedula,
        "consent": {"granted": True, "purpose_code": "BECA"},
        "features": dict(FEATURES),
        **extra,
    }


@pytest.fixture
def rbac_settings(tmp_path: Path) -> Settings:
    return replace(
        Settings(),
        rbac_enabled=True,
        ledger_ephemeral=False,
        db_path=tmp_path / "ledger.db",
        users_db_path=tmp_path / "usuarios.db",
        pbkdf2_iterations=1000,
        allowed_hosts=("testserver.local",),
        static_dir=PROJECT_ROOT / "static",
    )


@pytest.fixture
def env(rbac_settings: Settings) -> Iterator[Env]:
    keys = KeyRing(bytes(range(32)))
    app = create_app(rbac_settings, keys, API_TOKEN)
    with TestClient(app=app, base_url="http://testserver.local") as client:
        identity = client.app.state.aduana.identity
        for role, (ident, codigo, password) in ROLE_ACCOUNTS.items():
            identity.create_user(
                codigo_usuario=codigo, identificador=ident, rol=role, password=password
            )
        for ident, codigo, password, role in (VICTIM, LOCKOUT_USER):
            identity.create_user(
                codigo_usuario=codigo, identificador=ident, rol=role, password=password
            )
        headers: dict[str, dict[str, str]] = {}
        for role, (ident, _codigo, password) in ROLE_ACCOUNTS.items():
            response = _login(client, ident, password)
            assert response.status_code in (200, 201), role
            headers[role] = _bearer(response.json()["session_token"])
        sent = client.post(f"{API}/gateway/process", json=gateway_body(), headers=headers[AGENTE])
        assert sent.status_code == 201
        yield Env(client, rbac_settings, keys, headers, sent.json()["citizen_receipt_code"])


# --------------------------------------------------------------------------------------------
# Tabla ruta x rol -> permitido. "ok" = 2xx; el resto = 403 ERR_FORBIDDEN.
# --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Route:
    route_id: str
    method: str
    path: str  # admite {receipt} y {victim}
    body: Callable[[], Any] | None
    allowed: frozenset[str]


def _new_user_body() -> dict[str, str]:
    n = next(_counter)
    return {
        "codigo_usuario": f"t.nuevo.{n:02d}",
        "identificador": f"V-9100{n:04d}",
        "rol": OPERADOR,
        "password": "Nuevo-Usuario-2024x",
    }


ROUTES: Final[tuple[Route, ...]] = (
    Route("auth_me", "GET", "/auth/me", None, frozenset(ALL_ROLES)),
    Route("gateway_process", "POST", "/gateway/process", gateway_body, frozenset({AGENTE})),
    Route("shield_inspect", "POST", "/shield/inspect", lambda: {"raw_text": "Texto sin PII"},
          frozenset({INSPECTOR, ANALISTA})),
    Route("explica_evaluate", "POST", "/explica/evaluate", lambda: {"features": dict(FEATURES)},
          frozenset({INSPECTOR, FISCAL, ANALISTA})),
    Route("ledger_verify", "GET", "/ledger/verify", None, frozenset({INSPECTOR, SUPERVISOR})),
    Route("ledger_receipt", "GET", "/ledger/receipt/{receipt}", None,
          frozenset({INSPECTOR, OPERADOR})),
    Route("audit_fiscal", "POST", "/audit/fiscal", lambda: {"identificador": CITIZEN_CEDULA},
          frozenset({INSPECTOR})),
    Route("metrics_benchmark", "GET", "/metrics/benchmark", None,
          frozenset({INSPECTOR, SUPERVISOR})),
    Route("usuarios_list", "GET", "/usuarios", None, frozenset({SUPERVISOR})),
    Route("usuarios_create", "POST", "/usuarios", _new_user_body, frozenset({SUPERVISOR})),
    Route("usuarios_suspend", "POST", "/usuarios/{victim}/suspender", None,
          frozenset({SUPERVISOR})),
)
# Rutas protegidas por RBAC (todas; /auth/me exige solo usuario activo).
MATRIX_CASES: Final[list[Any]] = [
    pytest.param(route, role, id=f"{route.route_id}-{role.split('_')[0].lower()}")
    for route in ROUTES
    for role in ALL_ROLES
]


def _fire(env: Env, route: Route, role: str | None, headers: dict[str, str] | None = None) -> Any:
    path = route.path.format(receipt=env.receipt_code, victim=VICTIM[1])
    body = route.body() if route.body else None
    return env.call(route.method, path, role, body, headers)


@pytest.mark.parametrize(("route", "role"), MATRIX_CASES)
def test_route_role_matrix(env: Env, route: Route, role: str) -> None:
    # Arrange / Act
    response = _fire(env, route, role)

    # Assert
    if role in route.allowed:
        assert 200 <= response.status_code < 300, response.text
    else:
        assert response.status_code == 403
        assert response.json() == FORBIDDEN_BODY


def test_matrix_covers_every_route_with_at_least_one_allowed_role() -> None:
    assert all(route.allowed <= set(ALL_ROLES) and route.allowed for route in ROUTES)


# (a) Autenticación -------------------------------------------------------------------------
@pytest.mark.parametrize("route", ROUTES, ids=lambda r: r.route_id)
def test_missing_bearer_is_401_on_every_protected_route(env: Env, route: Route) -> None:
    response = _fire(env, route, None)  # solo X-Aduana-Token

    assert response.status_code == 401
    assert response.json() == UNAUTHORIZED_BODY


def test_login_requires_app_token_even_though_public(env: Env) -> None:
    ident, _codigo, password = ROLE_ACCOUNTS[AGENTE]
    response = env.client.post(
        f"{API}/auth/login",
        json={"identificador": ident, "password": password},
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 401


def test_valid_bearer_without_app_token_is_rejected(env: Env) -> None:
    headers = {k: v for k, v in env.headers[INSPECTOR].items() if k != "X-Aduana-Token"}

    response = env.client.get(f"{API}/ledger/verify", headers=headers)

    assert response.status_code == 401


def _tampered(token: str) -> str:
    head, payload, signature = token.split(".")
    flipped = ("A" if signature[0] != "A" else "B") + signature[1:]
    return ".".join((head, payload, flipped))


def _expired(env: Env, role: str) -> str:
    from core.auth import issue_token

    identity = env.client.app.state.aduana.identity
    user = identity.resolve_token(env.headers[role]["Authorization"].removeprefix("Bearer "))
    now = int(time.time())
    return issue_token(env.keys, user, now=now - 7200, ttl_seconds=60).token


@pytest.mark.parametrize(
    "variant",
    ["firma_manipulada", "basura", "vacio", "vencido", "esquema_basic"],
)
def test_invalid_tokens_are_401_uniform(env: Env, variant: str) -> None:
    good = env.headers[INSPECTOR]["Authorization"].removeprefix("Bearer ")
    authorization = {
        "firma_manipulada": f"Bearer {_tampered(good)}",
        "basura": "Bearer not-a-token",
        "vacio": "Bearer ",
        "vencido": f"Bearer {_expired(env, INSPECTOR)}",
        "esquema_basic": f"Basic {good}",
    }[variant]

    response = env.client.get(
        f"{API}/ledger/verify", headers={**TOKEN_HEADERS, "Authorization": authorization}
    )

    assert response.status_code == 401
    assert response.json() == UNAUTHORIZED_BODY


def test_payload_manipulation_to_escalate_role_is_rejected(env: Env) -> None:
    import base64
    import json

    good = env.headers[AGENTE]["Authorization"].removeprefix("Bearer ")
    head, payload, signature = good.split(".")
    padded = payload + "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(padded))
    claims["rol"] = INSPECTOR
    forged = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()

    response = env.client.get(
        f"{API}/ledger/verify",
        headers=_bearer(f"{head}.{forged}.{signature}"),
    )

    assert response.status_code == 401


# (b) AGENTE_ADUANAL ------------------------------------------------------------------------
def test_agent_gets_201_and_sanitized_package(env: Env) -> None:
    response = env.call("POST", "/gateway/process", AGENTE, gateway_body())

    assert response.status_code == 201
    assert CITIZEN_CEDULA not in response.text


@pytest.mark.parametrize(
    "extra",
    [
        {"human_decision": "REVISION_ESTANDAR"},
        {"override_justification": JUSTIFICATION},
        {"human_decision": "PRIORIDAD_ALTA", "override_justification": JUSTIFICATION},
    ],
    ids=["human_decision", "justificacion", "ambos"],
)
def test_agent_cannot_send_override_fields(env: Env, extra: dict[str, str]) -> None:
    response = env.call("POST", "/gateway/process", AGENTE, gateway_body(**extra))

    assert response.status_code == 403
    assert response.json() == FORBIDDEN_BODY


# (c) INSPECTOR -----------------------------------------------------------------------------
def test_inspector_cannot_submit_without_override(env: Env) -> None:
    response = env.call("POST", "/gateway/process", INSPECTOR, gateway_body())

    assert response.status_code == 403
    assert response.json() == FORBIDDEN_BODY


def test_inspector_override_is_the_only_gateway_access(env: Env) -> None:
    body = gateway_body(human_decision="REVISION_ESTANDAR", override_justification=JUSTIFICATION)

    response = env.call("POST", "/gateway/process", INSPECTOR, body)

    assert 200 <= response.status_code < 300, response.text


def _blocks(body: Any) -> list[Any]:
    """Acepta lista directa o ``{"blocks": [...]}`` (forma exacta no fijada por la spec)."""
    blocks = body if isinstance(body, list) else body.get("blocks")
    assert isinstance(blocks, list), body
    return blocks


def test_inspector_audit_returns_only_blocks_of_that_importer(env: Env) -> None:
    other = env.call("POST", "/gateway/process", AGENTE, gateway_body(cedula=OTHER_CEDULA))
    assert other.status_code == 201

    mine = env.call("POST", "/audit/fiscal", INSPECTOR, {"identificador": CITIZEN_CEDULA})
    theirs = env.call("POST", "/audit/fiscal", INSPECTOR, {"identificador": OTHER_CEDULA})
    nobody = env.call("POST", "/audit/fiscal", INSPECTOR, {"identificador": "V-11111111"})

    assert all(r.status_code == 200 for r in (mine, theirs, nobody)), mine.text
    assert len(_blocks(mine.json())) == 1
    assert len(_blocks(theirs.json())) == 1
    assert _blocks(nobody.json()) == []
    assert CITIZEN_CEDULA not in mine.text and OTHER_CEDULA not in theirs.text
    assert env.receipt_code in mine.text and env.receipt_code not in theirs.text


def test_inspector_can_read_receipt_and_benchmark(env: Env) -> None:
    receipt = env.call("GET", f"/ledger/receipt/{env.receipt_code}", INSPECTOR)
    benchmark = env.call("GET", "/metrics/benchmark", INSPECTOR)

    assert receipt.status_code == 200 and benchmark.status_code == 200


# (d) FISCAL --------------------------------------------------------------------------------
def test_fiscal_evaluate_returns_explainability_and_seals_nothing(env: Env) -> None:
    before = env.call("GET", "/ledger/verify", INSPECTOR).json()["blocks_checked"]

    response = env.call("POST", "/explica/evaluate", FISCAL, {"features": dict(FEATURES)})
    after = env.call("GET", "/ledger/verify", INSPECTOR).json()["blocks_checked"]

    assert 200 <= response.status_code < 300, response.text
    body = response.json()
    assert 0.0 <= body["probability_score"] <= 1.0
    assert set(body["linear_shap_values"]) == set(FEATURES)
    assert after == before


# (e) OPERADOR ------------------------------------------------------------------------------
def test_operator_receipt_has_no_pii_or_payload(env: Env) -> None:
    response = env.call("GET", f"/ledger/receipt/{env.receipt_code}", OPERADOR)

    assert 200 <= response.status_code < 300, response.text
    body = response.json()
    assert body["codigo"] == env.receipt_code
    assert isinstance(body["block_index"], int) and body["block_hash"]
    assert isinstance(body["cadena_valida"], bool)
    assert isinstance(body["liberacion_autorizada"], bool)
    for forbidden in (CITIZEN_CEDULA, "12345678", "masked_text", "payload_hash",
                      "citizen_cedula", "insumos"):
        assert forbidden not in response.text
    assert not {"masked_text", "payload_hash", "citizen_cedula", "raw_text"} & set(body)


def test_unknown_receipt_is_404_without_echo(env: Env) -> None:
    code = "REC-inexistente-secreto-123"

    response = env.call("GET", f"/ledger/receipt/{code}", OPERADOR)

    assert response.status_code == 404
    assert "secreto" not in response.text and code not in response.text


# (f) SUPERVISOR ----------------------------------------------------------------------------
def test_supervisor_user_list_never_exposes_secrets_or_identifiers(env: Env) -> None:
    response = env.call("GET", "/usuarios", SUPERVISOR)

    assert response.status_code == 200
    assert len(response.json()) >= len(ALL_ROLES)
    for field in SECRET_FIELDS:
        assert field not in response.text
    for ident, _codigo, password in ROLE_ACCOUNTS.values():
        assert ident not in response.text and ident.removeprefix("V-") not in response.text
        assert password not in response.text


def test_supervisor_creates_user_who_can_login_and_response_has_no_secrets(env: Env) -> None:
    body = _new_user_body()

    created = env.call("POST", "/usuarios", SUPERVISOR, body)
    login = _login(env.client, body["identificador"], body["password"])

    assert 200 <= created.status_code < 300, created.text
    assert body["password"] not in created.text and body["identificador"] not in created.text
    assert all(field not in created.text for field in SECRET_FIELDS)
    assert login.status_code in (200, 201)


@pytest.mark.parametrize(
    ("mutation", "status", "code"),
    [
        ({"password": "corta1"}, 422, "ERR_WEAK_PASSWORD"),
        ({"codigo_usuario": ROLE_ACCOUNTS[AGENTE][1]}, 409, "ERR_USER_EXISTS"),
    ],
    ids=["password_debil", "usuario_duplicado"],
)
def test_user_creation_errors_use_stable_codes(
    env: Env, mutation: dict[str, str], status: int, code: str
) -> None:
    body = {**_new_user_body(), **mutation}

    response = env.call("POST", "/usuarios", SUPERVISOR, body)

    assert response.status_code == status
    assert response.json() == {"error": code}
    assert body["password"] not in response.text


# (h) Suspensión y cambio de rol inmediatos -------------------------------------------------
def test_suspended_user_loses_access_on_next_request_with_valid_token(env: Env) -> None:
    ident, codigo, password, _role = VICTIM
    token = _login(env.client, ident, password).json()["session_token"]
    victim_headers = _bearer(token)
    assert env.client.get(f"{API}/auth/me", headers=victim_headers).status_code == 200

    suspended = env.call("POST", f"/usuarios/{codigo}/suspender", SUPERVISOR)
    after = env.client.get(f"{API}/auth/me", headers=victim_headers)

    assert 200 <= suspended.status_code < 300
    assert after.status_code == 401
    assert after.json() == UNAUTHORIZED_BODY
    sent = env.client.post(f"{API}/gateway/process", json=gateway_body(), headers=victim_headers)
    assert sent.status_code == 401


def test_suspended_users_token_is_rejected_everywhere(env: Env) -> None:
    ident, codigo, password, _role = VICTIM
    victim_headers = _bearer(_login(env.client, ident, password).json()["session_token"])
    env.call("POST", f"/usuarios/{codigo}/suspender", SUPERVISOR)

    statuses = {
        route.route_id: _fire(env, route, None, headers=victim_headers).status_code
        for route in ROUTES
    }

    assert set(statuses.values()) == {401}, statuses


def test_role_change_takes_effect_immediately(env: Env) -> None:
    from core.rbac_db import UsuariosRepository

    repo = UsuariosRepository(str(env.settings.users_db_path))
    try:
        user = next(u for u in repo.list_users() if u.codigo_usuario == ROLE_ACCOUNTS[AGENTE][1])
        assert env.call("POST", "/gateway/process", AGENTE, gateway_body()).status_code == 201

        repo.set_rol(user.user_id, FISCAL)
    finally:
        repo.close()

    assert env.call("POST", "/gateway/process", AGENTE, gateway_body()).status_code == 403
    evaluate = env.call("POST", "/explica/evaluate", AGENTE, {"features": dict(FEATURES)})
    assert 200 <= evaluate.status_code < 300


# (i) Login ---------------------------------------------------------------------------------
def test_login_error_is_uniform_for_unknown_user_and_wrong_password(env: Env) -> None:
    ident, _codigo, _password = ROLE_ACCOUNTS[AGENTE]

    unknown = _login(env.client, UNKNOWN_IDENTIFIER, "Cualquier-Clave-2024x")
    wrong = _login(env.client, ident, "Clave-Equivocada-2024x")

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json() == UNAUTHORIZED_BODY


def test_successful_login_has_token_but_no_hash_or_salt(env: Env) -> None:
    ident, _codigo, password = ROLE_ACCOUNTS[AGENTE]

    response = _login(env.client, ident, password)

    assert response.status_code in (200, 201)
    assert response.json()["session_token"].startswith("v1.")
    assert all(field not in response.text for field in SECRET_FIELDS)
    assert password not in response.text and ident not in response.text


def test_account_locks_after_five_failures_even_for_correct_password(env: Env) -> None:
    ident, _codigo, password, _role = LOCKOUT_USER

    first_four = [_login(env.client, ident, "Mala-Clave-2024x").status_code for _ in range(4)]
    _login(env.client, ident, "Mala-Clave-2024x")  # quinto fallo
    locked_wrong = _login(env.client, ident, "Mala-Clave-2024x")
    locked_correct = _login(env.client, ident, password)

    assert first_four == [401] * 4
    for response in (locked_wrong, locked_correct):
        assert response.status_code == 423
        assert response.json() == {"error": "ERR_ACCOUNT_LOCKED"}


def test_successful_login_resets_failure_counter(env: Env) -> None:
    ident, _codigo, password, _role = LOCKOUT_USER
    for _ in range(4):
        _login(env.client, ident, "Mala-Clave-2024x")
    assert _login(env.client, ident, password).status_code in (200, 201)

    for _ in range(4):
        assert _login(env.client, ident, "Mala-Clave-2024x").status_code == 401

    assert _login(env.client, ident, password).status_code in (200, 201)


# Zero-Leak de cuerpos de error (técnica de test_api_hardening) ------------------------------
@pytest.mark.parametrize("role", [r for r in ALL_ROLES if r != AGENTE])
def test_forbidden_gateway_error_never_echoes_citizen_data(env: Env, role: str) -> None:
    response = env.call("POST", "/gateway/process", role, gateway_body())

    assert response.status_code == 403
    assert response.json() == FORBIDDEN_BODY
    assert CITIZEN_CEDULA not in response.text and "insumos" not in response.text


def test_denied_and_unauthenticated_requests_never_log_citizen_data(
    env: Env, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    with caplog.at_level(logging.DEBUG):
        env.call("POST", "/gateway/process", FISCAL, gateway_body())
        env.call("POST", "/gateway/process", None, gateway_body())
        env.call("POST", "/audit/fiscal", AGENTE, {"identificador": CITIZEN_CEDULA})

    assert CITIZEN_CEDULA not in caplog.text and "12345678" not in caplog.text


# (j) Zero-PII ------------------------------------------------------------------------------
def test_no_response_nor_users_db_bytes_contain_identifiers_or_passwords(env: Env) -> None:
    texts: list[str] = []
    for route in ROUTES:
        for role in ALL_ROLES:
            texts.append(_fire(env, route, role).text)
    for ident, _codigo, password in ROLE_ACCOUNTS.values():
        texts.append(_login(env.client, ident, password).text)
        texts.append(_login(env.client, ident, "Clave-Equivocada-2024x").text)
    texts.append(_login(env.client, UNKNOWN_IDENTIFIER, "Clave-Equivocada-2024x").text)
    secrets_clear = [
        value
        for ident, _codigo, password in (*ROLE_ACCOUNTS.values(), VICTIM[:3], LOCKOUT_USER[:3])
        for value in (ident, ident.removeprefix("V-"), password)
    ]

    blob = "\n".join(texts)
    leaked_response = [s for s in secrets_clear if s in blob]
    db = env.settings.users_db_path
    db_bytes = b"".join(
        p.read_bytes()
        for p in (db, db.with_name(db.name + "-wal"), db.with_name(db.name + "-shm"))
        if p.exists()
    )
    leaked_db = [s for s in secrets_clear if s.encode() in db_bytes]

    assert db_bytes, "usuarios.db no existe o está vacío"
    assert leaked_response == []
    assert leaked_db == []


# (k) RBAC apagado: compatibilidad ----------------------------------------------------------
@pytest.fixture
def legacy_client(tmp_path: Path) -> Iterator[TestClient]:
    settings = replace(
        Settings(),
        db_path=tmp_path / "ledger.db",
        static_dir=PROJECT_ROOT / "static",
        allowed_hosts=("testserver.local",),
    )
    app = create_app(settings, KeyRing(bytes(range(32))), API_TOKEN)
    with TestClient(app=app, base_url="http://testserver.local") as client:
        yield client


@pytest.mark.parametrize(
    ("method", "path", "body", "expected"),
    [
        ("POST", "/gateway/process", gateway_body(), 201),
        ("POST", "/shield/inspect", {"raw_text": "Texto sin PII"}, 201),
        ("GET", "/ledger/verify", None, 200),
        ("GET", "/metrics/benchmark", None, 200),
    ],
    ids=["gateway", "shield", "verify", "benchmark"],
)
def test_legacy_routes_work_with_app_token_only_when_rbac_disabled(
    legacy_client: TestClient, method: str, path: str, body: Any, expected: int
) -> None:
    response = legacy_client.request(method, f"{API}{path}", headers=TOKEN_HEADERS, json=body)

    assert response.status_code == expected, response.text


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/usuarios"),
        ("POST", "/usuarios"),
        ("POST", "/usuarios/x/suspender"),
        ("POST", "/audit/fiscal"),
        ("POST", "/explica/evaluate"),
        ("GET", "/ledger/receipt/REC-x"),
    ],
)
def test_new_routes_do_not_exist_when_rbac_disabled(
    legacy_client: TestClient, method: str, path: str
) -> None:
    response = legacy_client.request(method, f"{API}{path}", headers=TOKEN_HEADERS, json={})

    # 404 (o 405 si el router estático captura la ruta para otros métodos, como tamper-sim).
    assert response.status_code in ((404,) if method == "GET" else (404, 405))
