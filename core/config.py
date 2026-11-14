"""Configuración inmutable y carga de secretos.

Política de llaves (decisión de diseño):
- ``ADUANA_MASTER_KEY`` (hex, >= 32 bytes) presente  -> ledger persistente verificable
  entre reinicios. La variable se elimina del entorno del proceso tras leerla.
- Ausente -> llave efímera en RAM y ledger efímero (``ledger_ephemeral=True``):
  la cadena solo es verificable durante la vida del proceso (modo demo).
Las llaves NO viven en ``Settings`` (se entregan como ``KeyRing``).
"""

from __future__ import annotations

import os
import secrets
import sys
from collections.abc import MutableMapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from core.keyring import MIN_KEY_BYTES, KeyRing

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
DEFAULT_GEMINI_MODEL: Final[str] = "gemini-3.5-flash-lite"

VAULT_TTL_SECONDS: Final[int] = 180
VAULT_MAX_SESSIONS: Final[int] = 1000
LLM_TIMEOUT_SECONDS: Final[float] = 3.5
RISK_BLOCK_THRESHOLD: Final[float] = 0.65
OVERRIDE_MIN_JUSTIFICATION_CHARS: Final[int] = 20
OVERRIDE_MAX_JUSTIFICATION_CHARS: Final[int] = 500
LOGIT_RECONSTRUCTION_TOLERANCE: Final[float] = 1e-9
GENESIS_PREV_HASH: Final[str] = "0" * 64
API_PREFIX: Final[str] = "/api/v1"
MAX_BODY_BYTES: Final[int] = 64 * 1024
MAX_RAW_TEXT_CHARS: Final[int] = 20_000
LOOPBACK_HOSTS: Final[frozenset[str]] = frozenset({"127.0.0.1", "localhost", "::1"})


@dataclass(frozen=True, slots=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8000
    db_path: Path = PROJECT_ROOT / "data" / "ledger.db"
    static_dir: Path = PROJECT_ROOT / "static"
    benchmark_path: Path = PROJECT_ROOT / "data" / "attack_benchmark.json"
    tramites_path: Path = PROJECT_ROOT / "data" / "synthetic_tramites.csv"
    rate_limit_per_minute: int = 30
    demo_mode: bool = False
    allow_remote: bool = False
    ledger_ephemeral: bool = True
    allowed_hosts: tuple[str, ...] = ("127.0.0.1", "localhost", "[::1]")

    def __post_init__(self) -> None:
        if self.host not in LOOPBACK_HOSTS and not self.allow_remote:
            raise ValueError("Host no loopback: exige ADUANA_ALLOW_REMOTE=1 (y TLS + auth).")
        if not 1024 <= self.port <= 65535:
            raise ValueError("Puerto fuera de rango (1024-65535).")
        if not 1 <= self.rate_limit_per_minute <= 600:
            raise ValueError("rate_limit_per_minute fuera de rango (1-600).")
        resolved = self.static_dir.resolve()
        if not resolved.is_relative_to(PROJECT_ROOT):
            raise ValueError("static_dir debe estar dentro del proyecto.")

    @classmethod
    def from_env(cls, env: MutableMapping[str, str] | None = None) -> Settings:
        """Construye Settings desde ``ADUANA_*``. Llamar ANTES de ``load_keys_from_env``."""
        env = os.environ if env is None else env
        defaults = cls()
        return cls(
            host=env.get("ADUANA_HOST", defaults.host),
            port=int(env.get("ADUANA_PORT", defaults.port)),
            db_path=Path(env.get("ADUANA_DB_PATH", str(defaults.db_path))),
            static_dir=Path(env.get("ADUANA_STATIC_DIR", str(defaults.static_dir))),
            rate_limit_per_minute=int(
                env.get("ADUANA_RATE_LIMIT_PER_MINUTE", defaults.rate_limit_per_minute)
            ),
            demo_mode=env.get("ADUANA_DEMO_MODE", "0") == "1",
            allow_remote=env.get("ADUANA_ALLOW_REMOTE", "0") == "1",
            ledger_ephemeral=not env.get("ADUANA_MASTER_KEY"),
        )


def load_keys_from_env(env: MutableMapping[str, str] | None = None) -> KeyRing:
    """Lee y ELIMINA ``ADUANA_MASTER_KEY`` del entorno; sin ella genera llave efímera."""
    env = os.environ if env is None else env
    raw = env.pop("ADUANA_MASTER_KEY", None)
    if not raw:
        return KeyRing(secrets.token_bytes(MIN_KEY_BYTES))
    return KeyRing(bytes.fromhex(raw.strip()))


def load_api_token_from_env(env: MutableMapping[str, str] | None = None) -> str:
    """Token de API por proceso (``X-Aduana-Token``). Se elimina del entorno tras leerlo."""
    env = os.environ if env is None else env
    token = env.pop("ADUANA_API_TOKEN", None)
    return token if token and len(token) >= 32 else secrets.token_urlsafe(32)


def _parse_dotenv_file(dotenv_path: Path) -> dict[str, str]:
    """Lee un archivo .env local soportando tanto KEY=VALUE como una clave cruda en una línea."""
    if not dotenv_path.is_file():
        return {}
    parsed: dict[str, str] = {}
    try:
        content = dotenv_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            key_name = k.strip()
            val = v.strip().strip("'").strip('"')
            if key_name and val:
                parsed[key_name] = val
        elif (line.startswith("AQ.") or line.startswith("AIza")) and "GEMINI_API_KEY" not in parsed:
            parsed["GEMINI_API_KEY"] = line
    return parsed


def load_gemini_from_env(
    env: MutableMapping[str, str] | None = None,
    *,
    dotenv_path: Path | None = None,
) -> tuple[str, str]:
    """Obtiene ``(api_key, model)`` para Gemini y purga ``GEMINI_API_KEY`` del entorno."""
    active_env = os.environ if env is None else env
    api_key = (
        active_env.pop("GEMINI_API_KEY", None)
        or active_env.pop("GOOGLE_API_KEY", None)
        or active_env.pop("ADUANA_GEMINI_API_KEY", None)
        or ""
    ).strip()
    model = (
        active_env.get("GEMINI_MODEL")
        or active_env.get("ADUANA_GEMINI_MODEL")
        or ""
    ).strip()

    # Si no estamos en pytest (o si se pasó dotenv_path explícito), leer .env del proyecto
    in_pytest = "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ
    if not api_key and (dotenv_path is not None or (env is None and not in_pytest)):
        target_dotenv = dotenv_path if dotenv_path is not None else (PROJECT_ROOT / ".env")
        file_vars = _parse_dotenv_file(target_dotenv)
        api_key = (
            file_vars.get("GEMINI_API_KEY")
            or file_vars.get("GOOGLE_API_KEY")
            or file_vars.get("ADUANA_GEMINI_API_KEY")
            or ""
        ).strip()
        if not model:
            model = (
                file_vars.get("GEMINI_MODEL")
                or file_vars.get("ADUANA_GEMINI_MODEL")
                or ""
            ).strip()

    return api_key, (model or DEFAULT_GEMINI_MODEL)

