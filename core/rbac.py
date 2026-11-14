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
    "chat:ia",
    "chat:canal",
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
        # Chat con la IA institucional y canal seguro con otros funcionarios (no son de escritura).
        "ANALISTA_VALORACION_ADUANERA": frozenset(
            {"explica:read", "shield:inspect", "chat:ia", "chat:canal"}
        ),
    }
)

WRITE_PERMISSIONS: Final[frozenset[Permission]] = frozenset(
    {"tramite:submit", "tramite:override", "users:manage"}
)
READ_ONLY_ROLES: Final[frozenset[AduanaRoleType]] = frozenset(
    {"FISCAL_ANTI_CONTRABANDO", "ANALISTA_VALORACION_ADUANERA"}
)


# Anti-escalada: quien tiene ``users:manage`` solo puede crear y gestionar roles OPERATIVOS. Las
# cuentas de inspector y de supervisor (las que sobreescriben, auditan o administran) no se crean
# ni se modifican por la API: se siembran o se dan de alta fuera de banda. Sin esto, un supervisor
# podría fabricarse un inspector y anular la segregación de funciones.
MANAGEABLE_ROLES: Final[Mapping[AduanaRoleType, frozenset[AduanaRoleType]]] = MappingProxyType(
    {
        "SUPERVISOR_PUERTO_ADUANERO": frozenset(
            {
                "AGENTE_ADUANAL_CERTIFICADO",
                "FISCAL_ANTI_CONTRABANDO",
                "OPERADOR_LOGISTICO_ALMACEN",
                "ANALISTA_VALORACION_ADUANERA",
            }
        ),
    }
)


def can_manage_role(actor_role: AduanaRoleType, target_role: AduanaRoleType) -> bool:
    """¿Puede un usuario con ``actor_role`` crear o gestionar cuentas de ``target_role``?
    Exige ``users:manage`` y que el rol destino sea operativo; un actor desconocido no gestiona."""
    return has_permission(actor_role, "users:manage") and target_role in MANAGEABLE_ROLES.get(
        actor_role, frozenset()
    )


def permissions_of(role: AduanaRoleType) -> frozenset[Permission]:
    """Permisos efectivos del rol; un rol desconocido no tiene ninguno (fail-closed)."""
    return ROLE_PERMISSIONS.get(role, frozenset())


def has_permission(role: AduanaRoleType, permission: Permission) -> bool:
    return permission in permissions_of(role)
