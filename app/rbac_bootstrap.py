"""Prepara el entorno local para arrancar con RBAC (login real) en el escritorio.

- Llave maestra: usa ``ADUANA_MASTER_KEY`` si ya viene en el entorno (producción: DPAPI/TPM/vault).
  Si no, lee o crea ``data/dev_master.key`` (hex, 32 bytes aleatorios, permisos restrictivos).
  Es una comodidad de desarrollo local: la llave queda en disco junto a la BD, así que NO sustituye
  a un vault. El archivo está cubierto por ``.gitignore`` (``*.key``).
- Activa ``ADUANA_RBAC=1`` salvo que el entorno ya lo fije a ``0``.
- Siembra los usuarios una sola vez (``scripts/seed_usuarios.py``); las contraseñas se generan al
  sembrar y solo existen en ``data/seed_credenciales.local.json``. Nunca se imprimen.
"""

from __future__ import annotations

import os
import secrets
from collections.abc import MutableMapping
from pathlib import Path
from typing import Final

from core.config import PROJECT_ROOT
from core.keyring import MIN_KEY_BYTES

DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
KEY_FILENAME: Final = "dev_master.key"
CREDENTIALS_FILENAME: Final = "seed_credenciales.local.json"


class BootstrapError(RuntimeError):
    """No se pudo preparar el entorno RBAC (mensaje sin secretos)."""


def _read_key(path: Path) -> str:
    text = path.read_text(encoding="ascii").strip()
    try:
        raw = bytes.fromhex(text)
    except ValueError:
        raise BootstrapError(f"{path.name} no contiene una llave hexadecimal válida.") from None
    if len(raw) < MIN_KEY_BYTES:
        raise BootstrapError(f"{path.name} tiene menos de {MIN_KEY_BYTES} bytes.")
    return text


def _create_key(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    key_hex = secrets.token_bytes(MIN_KEY_BYTES).hex()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)  # nunca pisa una llave
    with os.fdopen(fd, "w", encoding="ascii") as handle:
        handle.write(key_hex + "\n")
    return key_hex


def prepare_rbac_environment(
    env: MutableMapping[str, str] | None = None,
    *,
    data_dir: Path | None = None,
    iterations: int | None = None,
) -> bool:
    """Deja ``env`` listo para RBAC y siembra usuarios. ``False`` si RBAC se apagó a propósito."""
    env = os.environ if env is None else env
    if env.get("ADUANA_RBAC") == "0":
        return False
    data_dir = DATA_DIR if data_dir is None else data_dir

    if not env.get("ADUANA_MASTER_KEY"):
        key_path = data_dir / KEY_FILENAME
        env["ADUANA_MASTER_KEY"] = (
            _read_key(key_path) if key_path.exists() else _create_key(key_path)
        )
    env["ADUANA_RBAC"] = "1"

    from scripts.seed_usuarios import main as seed_main  # import perezoso: solo el escritorio

    argv = ["--output", str(data_dir / CREDENTIALS_FILENAME), "--force"]
    if iterations is not None:
        argv += ["--iterations", str(iterations)]
    # La CLI consume (elimina) ADUANA_MASTER_KEY del mapeo que recibe: se le pasa una copia.
    if seed_main(argv, dict(env)) != 0:
        raise BootstrapError("No se pudieron sembrar los usuarios (ver mensaje anterior).")
    return True
