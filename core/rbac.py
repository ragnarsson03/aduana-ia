"""Política de control de acceso por rol aduanero (puro, sin I/O). Ver specs/06_rbac_aduanero.

Mínimo privilegio y segregación de funciones (SoD): quien envía trámites no decide sobre ellos,
quien administra identidades no opera trámites, y los roles de solo lectura no tienen escritura.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, Literal, get_args

from core.context import AduanaRoleType

Permission = Literal[
    "tramite:submit",
    "tramite:override",
    "shield:inspect",
    "explica:read",
    "ledger:receipt",
    "ledger:audit",
    "audit:fiscal",
    "metrics:read",
    "users:manage",
]

ALL_ROLES: Final[tuple[str, ...]] = get_args(AduanaRoleType)
ALL_PERMISSIONS: Final[tuple[str, ...]] = get_args(Permission)

ROLE_PERMISSIONS: Final[Mapping[AduanaRoleType, frozenset[Permission]]] = MappingProxyType(
    {
        "INSPECTOR_TRIBUTARIO_SENIAT": frozenset(
            {
                "tramite:override",
                "shield:inspect",
                "explica:read",
                "ledger:receipt",
                "ledger:audit",
                "audit:fiscal",
                "metrics:read",
            }
        ),
        "AGENTE_ADUANAL_CERTIFICADO": frozenset({"tramite:submit"}),
        "FISCAL_ANTI_CONTRABANDO": frozenset({"explica:read"}),
        "OPERADOR_LOGISTICO_ALMACEN": frozenset({"ledger:receipt"}),
        "SUPERVISOR_PUERTO_ADUANERO": frozenset({"users:manage", "ledger:audit", "metrics:read"}),
        "ANALISTA_VALORACION_ADUANERA": frozenset({"explica:read", "shield:inspect"}),
    }
)

WRITE_PERMISSIONS: Final[frozenset[Permission]] = frozenset(
    {"tramite:submit", "tramite:override", "users:manage"}
)
READ_ONLY_ROLES: Final[frozenset[AduanaRoleType]] = frozenset(
    {"FISCAL_ANTI_CONTRABANDO", "ANALISTA_VALORACION_ADUANERA"}
)


def permissions_of(role: AduanaRoleType) -> frozenset[Permission]:
    """Permisos efectivos del rol; un rol desconocido no tiene ninguno (fail-closed)."""
    return ROLE_PERMISSIONS.get(role, frozenset())


def has_permission(role: AduanaRoleType, permission: Permission) -> bool:
    return permission in permissions_of(role)
