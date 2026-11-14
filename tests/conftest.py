from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest
from litestar.testing import TestClient

from app.server import create_app
from core.config import PROJECT_ROOT, Settings
from core.keyring import KeyRing

API_TOKEN = "t" * 40
TOKEN_HEADERS = {"X-Aduana-Token": API_TOKEN, "Content-Type": "application/json"}


@pytest.fixture
def keys() -> KeyRing:
    return KeyRing(bytes(range(32)))


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    static = PROJECT_ROOT / "static"
    return replace(
        Settings(),
        db_path=tmp_path / "ledger.db",
        static_dir=static,
        allowed_hosts=("testserver.local",),
    )


@pytest.fixture
def client(settings: Settings, keys: KeyRing) -> Iterator[TestClient]:
    app = create_app(settings, keys, API_TOKEN)
    with TestClient(app=app, base_url="http://testserver.local") as test_client:
        yield test_client


@pytest.fixture
def demo_client(settings: Settings, keys: KeyRing) -> Iterator[TestClient]:
    app = create_app(replace(settings, demo_mode=True), keys, API_TOKEN)
    with TestClient(app=app, base_url="http://testserver.local") as test_client:
        yield test_client
