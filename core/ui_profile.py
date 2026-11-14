"""Perfil de presentación derivado del rol aduanero (sin PII: no hay nombres ni correos).

El servidor es la fuente de verdad: las pestañas permitidas se calculan a partir de los permisos
reales del rol (``core.rbac``), de modo que el front no mantiene su propia tabla de privilegios.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from core.context import AduanaRoleType, UsuarioAduana
from core.rbac import Permission, permissions_of

UiRole = Literal["analista", "administrador", "auditor"]
TabId = Literal["pasarela", "chat", "ledger", "explicabilidad", "canal"]

# Orden de presentación de las pestañas + permisos que dan acceso a cada una (cualquiera basta).
_TAB_PERMISSIONS: Final[tuple[tuple[TabId, frozenset[Permission]], ...]] = (
    ("pasarela", frozenset({"tramite:submit", "shield:inspect"})),
    ("chat", frozenset({"chat:ia"})),
    ("ledger", frozenset({"ledger:audit", "ledger:receipt"})),
    ("explicabilidad", frozenset({"explica:read"})),
    ("canal", frozenset({"chat:canal"})),
)


@dataclass(frozen=True, slots=True)
class _RoleLabels:
    ui_role: UiRole
    label: str
    clearance: str
    entity: str
    department: str


_LABELS: Final[dict[AduanaRoleType, _RoleLabels]] = {
    "INSPECTOR_TRIBUTARIO_SENIAT": _RoleLabels(
        "auditor",
        "Inspector Tributario SENIAT",
        "Nivel 4 — Confidencial Estatal",
        "SENIAT",
        "Inspección Tributaria",
    ),
    "AGENTE_ADUANAL_CERTIFICADO": _RoleLabels(
        "analista",
        "Agente Aduanal Certificado",
        "Nivel 2 — Restringido",
        "Agente aduanal externo",
        "Trámites Aduanales",
    ),
    "FISCAL_ANTI_CONTRABANDO": _RoleLabels(
        "auditor",
        "Fiscal Anti-Contrabando",
        "Nivel 3 — Reservado",
        "Fiscalía Aduanera",
        "Anti-Contrabando",
    ),
    "OPERADOR_LOGISTICO_ALMACEN": _RoleLabels(
        "auditor",
        "Operador Logístico de Almacén",
        "Nivel 1 — Operativo",
        "Almacén aduanero",
        "Logística",
    ),
    "SUPERVISOR_PUERTO_ADUANERO": _RoleLabels(
        "administrador",
        "Supervisor de Puerto Aduanero",
        "Nivel 5 — Soberanía Crítica",
        "Puerto aduanero",
        "Administración de Usuarios",
    ),
    "ANALISTA_VALORACION_ADUANERA": _RoleLabels(
        "analista",
        "Analista de Valoración Aduanera",
        "Nivel 3 — Reservado",
        "Valoración aduanera",
        "Valoración",
    ),
}

_FALLBACK: Final = _RoleLabels("auditor", "Sin perfil", "Sin acceso", "—", "—")


@dataclass(frozen=True, slots=True)
class UiProfile:
    id: str
    username: str
    full_name: str
    short_name: str
    avatar_text: str
    role: UiRole
    role_label: str
    clearance_level: str
    entity: str
    department: str
    permissions: tuple[str, ...]
    default_tab: TabId
    allowed_tabs: tuple[TabId, ...]


def allowed_tabs_for(role: AduanaRoleType) -> tuple[TabId, ...]:
    granted = permissions_of(role)
    return tuple(tab for tab, needed in _TAB_PERMISSIONS if granted & needed)


def _avatar(codigo_usuario: str) -> str:
    letters = [c for c in codigo_usuario if c.isalpha()]
    return "".join(letters[:2]).upper() or "US"


def profile_of(user: UsuarioAduana) -> UiProfile:
    labels = _LABELS.get(user.rol, _FALLBACK)
    tabs = allowed_tabs_for(user.rol)
    return UiProfile(
        id=user.user_id,
        username=user.codigo_usuario,
        full_name=labels.label,
        short_name=user.codigo_usuario,
        avatar_text=_avatar(user.codigo_usuario),
        role=labels.ui_role,
        role_label=labels.label,
        clearance_level=labels.clearance,
        entity=labels.entity,
        department=labels.department,
        permissions=tuple(sorted(permissions_of(user.rol))),
        default_tab=tabs[0] if tabs else "ledger",
        allowed_tabs=tabs,
    )
