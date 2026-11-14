from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from litestar.testing import TestClient

from app.server import create_app
from core.config import PROJECT_ROOT, Settings
from core.keyring import KeyRing
from tests.e2e_harness.support import IndexReferences, assert_asset_type


@pytest.fixture
def static_client(tmp_path: Path) -> Iterator[TestClient]:
    # Settings only accepts static_dir inside PROJECT_ROOT; keep this copy in our allowed area.
    with tempfile.TemporaryDirectory(
        prefix="static-copy-", dir=PROJECT_ROOT / "tests/e2e_harness"
    ) as directory:
        static_dir = Path(directory) / "static"
        shutil.copytree(PROJECT_ROOT / "static", static_dir)
        settings = Settings(
            db_path=tmp_path / "ledger.db",
            static_dir=static_dir,
            allowed_hosts=("testserver.local",),
        )
        with TestClient(
            create_app(settings, KeyRing(bytes(range(32))), "e2e-token-" + "0" * 32),
            base_url="http://testserver.local",
            raise_server_exceptions=False,
        ) as client:
            yield client


def test_static_index(static_client: TestClient) -> None:
    response = static_client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert '<div id="root">' in response.text


def test_static_assets(static_client: TestClient) -> None:
    response = static_client.get("/")
    assert response.status_code == 200
    assets = IndexReferences(response.text).local_assets("http://testserver.local/")
    assert assets
    for asset in assets:
        result = static_client.get(asset)
        assert result.status_code == 200, f"Asset unavailable: {asset}"
        assert_asset_type(asset, result.headers.get("content-type", ""))


@pytest.mark.parametrize("route", ["/tramites/e2e", "/auditoria/e2e"])
def test_unknown_front_route_never_returns_500(static_client: TestClient, route: str) -> None:
    response = static_client.get(route)
    assert response.status_code in {200, 404}, (
        "Unknown frontend route must not produce a server error"
    )


def test_spa_deep_link_returns_controlled_404(static_client: TestClient) -> None:
    """El front navega por estado interno (sin router de URLs): una ruta desconocida no existe.

    Se fija el comportamiento correcto: 404 controlado y nunca 500. Si algún día se añade un
    router con rutas profundas, este test debe cambiar a exigir el fallback a index.html.
    """
    response = static_client.get("/tramites/e2e")
    assert response.status_code == 404
    assert "tramites" not in response.text  # sin eco de la ruta pedida
