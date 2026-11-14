#!/usr/bin/env python3
"""Siembra los 10 usuarios sintéticos del RBAC aduanero (specs/06 §8).

Requiere ``ADUANA_MASTER_KEY`` (el índice ciego depende de ella). Lee ``ADUANA_USERS_DB_PATH``.
Genera una contraseña aleatoria por usuario y escribe UNA sola vez
``data/seed_credenciales.local.json`` (permisos restrictivos, ignorado por git) con
``{codigo: {identificador, password, rol}}``: es el único lugar donde existen en claro.
Solo imprime la ruta y la cantidad; jamás las contraseñas. No sobrescribe sin ``--force``.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from collections.abc import MutableMapping, Sequence
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.auth import validate_password_policy  # noqa: E402
from core.config import PROJECT_ROOT, Settings, load_keys_from_env  # noqa: E402
from core.errors import WeakPasswordError  # noqa: E402
from core.identity import IdentityService  # noqa: E402
from core.rbac_db import UsuariosRepository  # noqa: E402
from core.rbac_seed import SEED_USERS, seed_users  # noqa: E402

DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "seed_credenciales.local.json"
PASSWORD_BYTES = 18  # token_urlsafe(18) -> 24 caracteres


def generate_password() -> str:
    """Contraseña aleatoria que SIEMPRE cumple la política (letra y dígito).

    ``token_urlsafe`` puede salir sin ningún dígito (~1,7 % de las veces con 24 caracteres), lo que
    hacía fallar la siembra de forma intermitente. Se regenera hasta cumplir; es CSPRNG puro y la
    condición solo descarta una fracción pequeña del espacio, sin sesgo apreciable.
    """
    while True:
        candidate = secrets.token_urlsafe(PASSWORD_BYTES)
        try:
            validate_password_policy(candidate)
        except WeakPasswordError:
            continue
        return candidate


def _parse(argv: Sequence[str] | None, defaults: Settings) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Siembra usuarios sintéticos del RBAC aduanero.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="archivo de credenciales locales (por defecto data/seed_credenciales.local.json)",
    )
    parser.add_argument(
        "--force", action="store_true", help="sobrescribir el archivo de credenciales"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=defaults.pbkdf2_iterations,
        help="iteraciones PBKDF2 (por defecto el valor de Settings)",
    )
    return parser.parse_args(argv)


def _fail(message: str) -> int:
    sys.stderr.write(message + "\n")
    return 2


def _write_private(path: Path, content: str, *, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | (os.O_TRUNC if force else os.O_EXCL)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(content)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass  # mejor esfuerzo según el SO


def main(argv: Sequence[str] | None = None, env: MutableMapping[str, str] | None = None) -> int:
    env = os.environ if env is None else env
    defaults = Settings()
    args = _parse(argv, defaults)
    if not env.get("ADUANA_MASTER_KEY"):
        return _fail("Falta ADUANA_MASTER_KEY: sin llave persistente el índice ciego no sirve.")
    if args.iterations < 1:
        return _fail("--iterations debe ser >= 1.")
    if args.output.exists() and not args.force:
        return _fail("El archivo de credenciales ya existe; usa --force para sobrescribirlo.")
    db_path = env.get("ADUANA_USERS_DB_PATH", str(defaults.users_db_path))
    try:
        keys = load_keys_from_env(env)
    except ValueError:
        return _fail("ADUANA_MASTER_KEY inválida (hex de al menos 32 bytes).")

    passwords = {u.codigo_usuario: generate_password() for u in SEED_USERS}
    repo = UsuariosRepository(db_path)
    try:
        service = IdentityService(
            repo,
            keys,
            iterations=args.iterations,
            token_ttl_seconds=defaults.token_ttl_seconds,
            max_failed_attempts=defaults.max_failed_attempts,
            lockout_seconds=defaults.lockout_seconds,
        )
        created = seed_users(service, passwords)
    finally:
        repo.close()
        keys.wipe()

    if created:
        by_code = {u.codigo_usuario: u for u in SEED_USERS}
        credentials = {
            user.codigo_usuario: {
                "identificador": by_code[user.codigo_usuario].identificador,
                "password": passwords[user.codigo_usuario],
                "rol": user.rol,
            }
            for user in created
        }
        _write_private(args.output, json.dumps(credentials, indent=2) + "\n", force=args.force)
        sys.stdout.write(f"{len(created)} usuarios creados. Credenciales en: {args.output}\n")
    else:
        sys.stdout.write("0 usuarios creados (ya existían); no se escribió ningún archivo.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
