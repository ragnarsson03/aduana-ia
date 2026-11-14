"""Pruebas de aceptación de Gatillo 7: Granian + PyWebView desktop, scripts y static Air-Gapped."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from app import desktop
from core.config import PROJECT_ROOT

_W3C_XML_NAMESPACES = frozenset(
    {
        "http://www.w3.org/1999/xhtml",
        "http://www.w3.org/2000/svg",
        "http://www.w3.org/1998/Math/MathML",
        "http://www.w3.org/1999/xlink",
        "http://www.w3.org/XML/1998/namespace",
    }
)
_URL_RE = re.compile(r"https?://[^\s\"'<>`)]+")
_INPUT_TAG_RE = re.compile(r"<(?:input|textarea)\b.*?(?:/>|(?<!=)>)", re.DOTALL)


@pytest.mark.unit
def test_static_and_index_have_no_external_urls_or_cdns() -> None:
    index_html = (PROJECT_ROOT / "index.html").read_text(encoding="utf-8")
    assert _URL_RE.findall(index_html) == []

    static_dir = PROJECT_ROOT / "static"
    html_css_files = list(static_dir.rglob("*.html")) + list(static_dir.rglob("*.css"))
    assert html_css_files, "static/ debe contener index.html y hojas de estilo compiladas"

    for path in html_css_files:
        content = path.read_text(encoding="utf-8")
        urls = _URL_RE.findall(content)
        assert urls == [], f"URL externa prohibida en {path.relative_to(PROJECT_ROOT)}: {urls}"

    for js_path in static_dir.rglob("*.js"):
        content = js_path.read_text(encoding="utf-8")
        urls = [u.rstrip(".,;:") for u in _URL_RE.findall(content)]
        non_w3c = [u for u in urls if u not in _W3C_XML_NAMESPACES]
        assert non_w3c == [], (
            f"URL externa en bundle JS {js_path.relative_to(PROJECT_ROOT)}: {non_w3c}"
        )


@pytest.mark.unit
def test_frontend_source_no_innerhtml_and_autocomplete_off() -> None:
    src_dir = PROJECT_ROOT / "src"
    source_files = list(src_dir.rglob("*.ts")) + list(src_dir.rglob("*.tsx"))
    assert source_files

    for path in source_files:
        if path.name.endswith(".test.ts"):
            continue
        content = path.read_text(encoding="utf-8")
        assert "innerHTML" not in content, f"innerHTML prohibido en {path}"
        assert "dangerouslySetInnerHTML" not in content, (
            f"dangerouslySetInnerHTML prohibido en {path}"
        )
        for match in _INPUT_TAG_RE.finditer(content):
            tag = match.group(0)
            assert 'autoComplete="off"' in tag or "autoComplete='off'" in tag, (
                f"Falta autoComplete='off' en {path.relative_to(PROJECT_ROOT)}: {tag}"
            )


@pytest.mark.unit
def test_launcher_scripts_exist() -> None:
    bat_path = PROJECT_ROOT / "iniciar_escritorio.bat"
    sh_path = PROJECT_ROOT / "iniciar_escritorio.sh"

    assert bat_path.is_file(), "Falta iniciar_escritorio.bat"
    assert sh_path.is_file(), "Falta iniciar_escritorio.sh"

    bat_content = bat_path.read_text(encoding="utf-8")
    sh_content = sh_path.read_text(encoding="utf-8")

    assert "app.desktop" in bat_content
    assert sh_content.startswith("#!/usr/bin/env bash")
    assert "app.desktop" in sh_content


@pytest.mark.integration
def test_granian_subprocess_real_execution_and_token_auth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Aislado de data/: el ledger local persistente (llave de desarrollo) no debe contaminarlo.
    monkeypatch.setenv("ADUANA_DB_PATH", str(tmp_path / "ledger.db"))
    for name in ("ADUANA_MASTER_KEY", "ADUANA_RBAC", "ADUANA_USERS_DB_PATH"):
        monkeypatch.delenv(name, raising=False)
    port = desktop._free_port()
    token = "d" * 40
    proc = desktop.start_server_process(port, token)
    try:
        desktop._wait_ready(port)

        # 1. Health check responde 200 con cabeceras de seguridad CSP
        with urllib.request.urlopen(  # noqa: S310
            f"http://127.0.0.1:{port}/api/v1/health/system", timeout=3
        ) as resp:
            assert resp.status == 200
            assert "default-src 'self'" in (resp.headers.get("Content-Security-Policy") or "")
            body = json.loads(resp.read().decode("utf-8"))
            assert body["status"] == "ok"

        # 2. Raíz sirve static/index.html sin CDNs
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=3) as resp:  # noqa: S310
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            assert '<div id="root"></div>' in html
            assert "https://" not in html

        # 3. Ruta protegida sin token -> 401
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(  # noqa: S310
                f"http://127.0.0.1:{port}/api/v1/ledger/verify", timeout=3
            )
        assert exc_info.value.code == 401

        # 4. Ruta protegida con el token inyectado -> 200
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/v1/ledger/verify",
            headers={"X-Aduana-Token": token},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:  # noqa: S310
            assert resp.status == 200
            verify_body = json.loads(resp.read().decode("utf-8"))
            assert verify_body["is_valid"] is True
    finally:
        desktop.stop_server_process(proc)

    assert not proc.is_alive()


@pytest.mark.unit
def test_desktop_main_wires_webview_private_mode_and_evaluate_js(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    loaded_callbacks: list[Any] = []

    class _FakeEvents:
        def __init__(self) -> None:
            self.loaded = self

        def __iadd__(self, cb: Any) -> _FakeEvents:
            loaded_callbacks.append(cb)
            return self

    fake_window = MagicMock()
    fake_window.events = _FakeEvents()

    fake_webview = MagicMock()
    fake_webview.create_window.return_value = fake_window

    def _fake_start(**kwargs: Any) -> None:
        for cb in loaded_callbacks:
            cb()

    fake_webview.start.side_effect = _fake_start

    fake_proc = MagicMock()
    freeze_called = False

    def _fake_freeze() -> None:
        nonlocal freeze_called
        freeze_called = True

    monkeypatch.setattr(desktop.multiprocessing, "freeze_support", _fake_freeze)
    monkeypatch.setattr(desktop, "_free_port", lambda: 54321)
    monkeypatch.setattr(desktop, "start_server_process", lambda p, t: fake_proc)
    monkeypatch.setattr(desktop, "_wait_ready", lambda p: None)
    monkeypatch.setattr(desktop, "stop_server_process", lambda proc: proc.terminate())
    monkeypatch.setitem(__import__("sys").modules, "webview", fake_webview)

    desktop.main()

    assert freeze_called is True
    create_args = fake_webview.create_window.call_args[0]
    assert create_args[1] == "http://127.0.0.1:54321"
    assert "token" not in create_args[1].lower()

    js_arg = fake_window.evaluate_js.call_args[0][0]
    assert js_arg.startswith("window.__ADUANA_TOKEN__=")

    start_kwargs = fake_webview.start.call_args[1]
    assert start_kwargs["private_mode"] is True
    assert start_kwargs["debug"] is False
    assert start_kwargs["storage_path"]
    fake_proc.terminate.assert_called_once()
