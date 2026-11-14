"""Pruebas de autenticación Zero-Trust (POST /api/v1/auth/login)."""

from __future__ import annotations

from pathlib import Path

import msgspec
import pytest
from litestar.testing import TestClient

from app.schemas import LoginRequest, LoginResponse, LoginUserOut
from app.server import create_app
from core.config import Settings
from core.keyring import KeyRing

AUTH_HEADERS = {
    "X-Aduana-Token": "t" * 40,
    "Content-Type": "application/json",
}


def _make_client(tmp_path: Path) -> tuple[TestClient, Path]:
    db_path = tmp_path / "auth_test.db"
    settings = Settings(
        db_path=db_path,
        demo_mode=True,
        allowed_hosts=("testserver.local",),
    )
    app = create_app(
        settings=settings,
        keys=KeyRing(bytes(range(32))),
        api_token="t" * 40,
    )
    return TestClient(app=app), db_path


@pytest.mark.parametrize(
    ("cedula", "password", "expected_role", "expected_tab"),
    [
        ("V-14220101", "auditor2026", "auditor", "ledger"),
        ("v-14.220.101", "auditor2026", "auditor", "ledger"),
        ("Ｖ-18660505", "analista2026", "analista", "pasarela"),
        ("V-12110909", "admin2026", "administrador", "pasarela"),
    ],
)
def test_login_success_three_roles_and_normalization(
    tmp_path: Path,
    cedula: str,
    password: str,
    expected_role: str,
    expected_tab: str,
) -> None:
    client, db_path = _make_client(tmp_path)
    with client:
        resp = client.post(
            "/api/v1/auth/login",
            headers=AUTH_HEADERS,
            json={"cedula": cedula, "password": password},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["authenticated"] is True
        assert body["token_type"] == "Bearer"  # noqa: S105
        assert len(body["session_token"].split(".")) == 3  # JWT HS256 header.payload.sig
        assert body["expires_in_seconds"] == 1800
        assert body["user"]["role"] == expected_role
        assert body["user"]["default_tab"] == expected_tab
        assert body["citizen_receipt_code"].startswith("AUTH-")

        # Validar sesión JWT activa
        session_headers = {**AUTH_HEADERS, "Authorization": f"Bearer {body['session_token']}"}
        sess = client.get("/api/v1/auth/session", headers=session_headers)
        assert sess.status_code == 200
        assert sess.json()["authenticated"] is True
        assert sess.json()["role"] == expected_role

        verify = client.get("/api/v1/ledger/verify", headers=AUTH_HEADERS)
        assert verify.status_code == 200
        assert verify.json()["is_valid"] is True
        assert verify.json()["blocks_checked"] == 1

    # Auditoría binaria Zero-Plaintext-PII en SQLite
    raw_bytes = db_path.read_bytes()
    for needle in (b"14220101", b"18660505", b"12110909", b"auditor2026", b"analista2026"):
        assert needle not in raw_bytes


def test_login_invalid_password_and_unknown_user_seal_ledger(tmp_path: Path) -> None:
    client, _ = _make_client(tmp_path)
    with client:
        bad_pass = client.post(
            "/api/v1/auth/login",
            headers=AUTH_HEADERS,
            json={"cedula": "V-14220101", "password": "wrong-password"},
        )
        assert bad_pass.status_code == 401

        unknown = client.post(
            "/api/v1/auth/login",
            headers=AUTH_HEADERS,
            json={"cedula": "V-99887766", "password": "wrong-password"},
        )
        assert unknown.status_code == 401

        verify = client.get("/api/v1/ledger/verify", headers=AUTH_HEADERS)
        assert verify.status_code == 200
        vdata = verify.json()
        assert vdata["is_valid"] is True
        assert vdata["blocks_checked"] == 2


def test_login_rate_limit_five_per_minute(tmp_path: Path) -> None:
    client, _ = _make_client(tmp_path)
    with client:
        for _ in range(5):
            resp = client.post(
                "/api/v1/auth/login",
                headers=AUTH_HEADERS,
                json={"cedula": "V-14220101", "password": "bad"},
            )
            assert resp.status_code == 401

        blocked = client.post(
            "/api/v1/auth/login",
            headers=AUTH_HEADERS,
            json={"cedula": "V-14220101", "password": "auditor2026"},
        )
        assert blocked.status_code == 429
        assert blocked.json()["error"] == "ERR_RATE_LIMIT"


def test_login_requires_api_token(tmp_path: Path) -> None:
    client, _ = _make_client(tmp_path)
    with client:
        resp = client.post(
            "/api/v1/auth/login",
            headers={"Content-Type": "application/json"},
            json={"cedula": "V-14220101", "password": "auditor2026"},
        )
        assert resp.status_code == 401


def test_login_dtos_repr_redacted_and_forbid_unknown_fields() -> None:
    req = LoginRequest(cedula="V-14220101", password="secret")  # noqa: S106
    assert repr(req) == "LoginRequest([REDACTED])"
    assert "14220101" not in repr(req)
    assert "secret" not in repr(req)

    res = LoginResponse(
        authenticated=True,
        session_token="tok-123",  # noqa: S106
        token_type="Bearer",  # noqa: S106
        expires_in_seconds=1800,
        user=LoginUserOut(
            id="usr-1",
            username="u",
            full_name="Test",
            short_name="T.",
            avatar_text="TT",
            role="auditor",
            role_label="Auditor",
            clearance_level="Nivel 4",
            entity="Aduana",
            department="Audit",
            permissions=("ledger:read",),
            default_tab="ledger",
            allowed_tabs=("ledger",),
        ),
        block_index=0,
        citizen_receipt_code="AUTH-1234",
    )
    assert repr(res) == "LoginResponse([REDACTED])"
    assert "tok-123" not in repr(res)

    with pytest.raises(msgspec.ValidationError):
        msgspec.json.decode(
            b'{"cedula":"V-14220101","password":"x","extra":1}',
            type=LoginRequest,
        )


def test_session_jwt_logout_and_tamper_rejection(tmp_path: Path) -> None:
    client, _ = _make_client(tmp_path)
    with client:
        login = client.post(
            "/api/v1/auth/login",
            headers=AUTH_HEADERS,
            json={"cedula": "V-14220101", "password": "auditor2026"},
        )
        assert login.status_code == 200
        jwt_token = login.json()["session_token"]

        # JWT manipulado -> 401
        tampered = jwt_token[:-4] + "AAAA"
        bad_sess = client.get(
            "/api/v1/auth/session",
            headers={**AUTH_HEADERS, "Authorization": f"Bearer {tampered}"},
        )
        assert bad_sess.status_code == 401

        # Logout revoca la sesión en RAM
        auth_hdrs = {**AUTH_HEADERS, "Authorization": f"Bearer {jwt_token}"}
        out = client.post("/api/v1/auth/logout", headers=auth_hdrs)
        assert out.status_code == 200
        assert out.json()["revoked"] is True

        # Reutilizar el JWT revocado -> 401
        after_logout = client.get("/api/v1/auth/session", headers=auth_hdrs)
        assert after_logout.status_code == 401


def test_session_cookie_survives_f5_and_logout_clears_it(tmp_path: Path) -> None:
    client, _ = _make_client(tmp_path)
    with client:
        login = client.post(
            "/api/v1/auth/login",
            headers=AUTH_HEADERS,
            json={"cedula": "V-18660505", "password": "analista2026"},
        )
        assert login.status_code == 200
        set_cookie = login.headers.get("set-cookie", "")
        assert "aduana_session=" in set_cookie
        assert "httponly" in set_cookie.lower()
        assert "samesite=strict" in set_cookie.lower()

        # Simular F5: GET /api/v1/auth/session sin header Authorization (solo cookie HttpOnly)
        f5_sess = client.get("/api/v1/auth/session", headers=AUTH_HEADERS)
        assert f5_sess.status_code == 200
        sdata = f5_sess.json()
        assert sdata["authenticated"] is True
        assert sdata["role"] == "analista"
        assert sdata["user"]["full_name"] == "Elena Salazar"
        assert sdata["user"]["default_tab"] == "pasarela"

        # Logout usando únicamente la cookie HttpOnly
        out = client.post("/api/v1/auth/logout", headers=AUTH_HEADERS)
        assert out.status_code == 200
        assert out.json()["revoked"] is True

        # F5 después de logout -> 401
        after_logout_f5 = client.get("/api/v1/auth/session", headers=AUTH_HEADERS)
        assert after_logout_f5.status_code == 401
