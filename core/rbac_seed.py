"""Usuarios sintéticos de demostración (specs/06 §8). Sin contraseñas: se reciben por parámetro.

Los identificadores son obviamente ficticios (prefijo 99xxxxxx) y existen aquí solo para poder
sembrar; en la base de datos únicamente se guarda su índice ciego.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from core.auth import validate_password_policy
from core.context import AduanaRoleType, UsuarioAduana
from core.identity import IdentityService


@dataclass(frozen=True, slots=True)
class SeedUser:
    codigo_usuario: str
    identificador: str  # cédula sintética; nunca se persiste en claro
    rol: AduanaRoleType


SEED_USERS: Final[tuple[SeedUser, ...]] = (
    SeedUser("insp.seniat.01", "V-99000001", "INSPECTOR_TRIBUTARIO_SENIAT"),
    SeedUser("agente.01", "V-99000002", "AGENTE_ADUANAL_CERTIFICADO"),
    SeedUser("fiscal.01", "V-99000003", "FISCAL_ANTI_CONTRABANDO"),
    SeedUser("almacen.01", "V-99000004", "OPERADOR_LOGISTICO_ALMACEN"),
    SeedUser("supervisor.01", "V-99000005", "SUPERVISOR_PUERTO_ADUANERO"),
    SeedUser("valoracion.01", "V-99000006", "ANALISTA_VALORACION_ADUANERA"),
    # Usuarios "normales" de mínimo privilegio
    SeedUser("agente.02", "V-99000007", "AGENTE_ADUANAL_CERTIFICADO"),
    SeedUser("agente.03", "E-99000008", "AGENTE_ADUANAL_CERTIFICADO"),
    SeedUser("almacen.02", "V-99000009", "OPERADOR_LOGISTICO_ALMACEN"),
    SeedUser("almacen.03", "E-99000010", "OPERADOR_LOGISTICO_ALMACEN"),
)


def seed_users(service: IdentityService, passwords: Mapping[str, str]) -> list[UsuarioAduana]:
    """Siembra los usuarios que aún no existen (por ``codigo_usuario``); idempotente.

    Valida antes de escribir: una contraseña ausente (``KeyError`` con el código, nunca un valor
    por defecto) o débil (``WeakPasswordError``) aborta sin crear ningún usuario.
    """
    existing = {user.codigo_usuario for user in service.list_users()}
    pending = [seed for seed in SEED_USERS if seed.codigo_usuario not in existing]
    for seed in pending:
        if seed.codigo_usuario not in passwords:
            raise KeyError(f"Falta la contraseña del usuario {seed.codigo_usuario}.")
        validate_password_policy(passwords[seed.codigo_usuario])
    return [
        service.create_user(
            codigo_usuario=seed.codigo_usuario,
            identificador=seed.identificador,
            rol=seed.rol,
            password=passwords[seed.codigo_usuario],
        )
        for seed in pending
    ]
