"""CA-07b — matriz de permisos e invariantes de segregación de funciones (specs/06 §3)."""

from __future__ import annotations

import pytest

from core.rbac import (
    ALL_PERMISSIONS,
    ALL_ROLES,
    READ_ONLY_ROLES,
    ROLE_PERMISSIONS,
    WRITE_PERMISSIONS,
    has_permission,
    permissions_of,
)

INSPECTOR = "INSPECTOR_TRIBUTARIO_SENIAT"
AGENTE = "AGENTE_ADUANAL_CERTIFICADO"
FISCAL = "FISCAL_ANTI_CONTRABANDO"
OPERADOR = "OPERADOR_LOGISTICO_ALMACEN"
SUPERVISOR = "SUPERVISOR_PUERTO_ADUANERO"
ANALISTA = "ANALISTA_VALORACION_ADUANERA"


def test_every_role_is_defined_and_has_at_least_one_permission() -> None:
    assert set(ROLE_PERMISSIONS) == set(ALL_ROLES)
    assert len(ALL_ROLES) == 6
    assert all(ROLE_PERMISSIONS[role] for role in ALL_ROLES)


def test_every_permission_is_granted_to_some_role() -> None:
    granted = set().union(*ROLE_PERMISSIONS.values())
    assert granted == set(ALL_PERMISSIONS)


def test_matrix_is_immutable() -> None:
    with pytest.raises(TypeError):
        ROLE_PERMISSIONS[AGENTE] = frozenset(ALL_PERMISSIONS)  # type: ignore[index]
    assert isinstance(ROLE_PERMISSIONS[AGENTE], frozenset)


def test_unknown_role_has_no_permissions_fail_closed() -> None:
    assert permissions_of("ADMIN_DE_SISTEMAS") == frozenset()  # type: ignore[arg-type]
    assert not has_permission("ADMIN_DE_SISTEMAS", "tramite:submit")  # type: ignore[arg-type]


def test_sod_user_admin_cannot_operate_tramites() -> None:
    for role, perms in ROLE_PERMISSIONS.items():
        if "users:manage" in perms:
            assert not perms & {"tramite:submit", "tramite:override"}, role


def test_sod_submitter_cannot_decide_or_audit() -> None:
    for role, perms in ROLE_PERMISSIONS.items():
        if "tramite:submit" in perms:
            assert "tramite:override" not in perms, role
            assert "audit:fiscal" not in perms, role


def test_read_only_roles_have_no_write_permissions() -> None:
    for role in READ_ONLY_ROLES:
        assert not ROLE_PERMISSIONS[role] & WRITE_PERMISSIONS, role


def test_logistics_operator_sees_neither_pii_nor_payload() -> None:
    perms = ROLE_PERMISSIONS[OPERADOR]
    assert perms == {"ledger:receipt"}
    assert not perms & {"explica:read", "shield:inspect", "audit:fiscal", "ledger:audit"}


def test_agent_and_inspector_are_isolated() -> None:
    """Núcleo de CA-07: el agente aduanal y el inspector del SENIAT no comparten ningún permiso."""
    assert not ROLE_PERMISSIONS[AGENTE] & ROLE_PERMISSIONS[INSPECTOR]
    assert has_permission(AGENTE, "tramite:submit") and not has_permission(
        INSPECTOR, "tramite:submit"
    )
    assert has_permission(INSPECTOR, "audit:fiscal") and not has_permission(AGENTE, "audit:fiscal")
    assert has_permission(INSPECTOR, "tramite:override") and not has_permission(
        AGENTE, "tramite:override"
    )


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        (FISCAL, {"explica:read"}),
        (AGENTE, {"tramite:submit"}),
        (OPERADOR, {"ledger:receipt"}),
        (SUPERVISOR, {"users:manage", "ledger:audit", "metrics:read"}),
        (ANALISTA, {"explica:read", "shield:inspect", "chat:ia", "chat:canal"}),
    ],
)
def test_least_privilege_sets(role: str, expected: set[str]) -> None:
    assert permissions_of(role) == expected  # type: ignore[arg-type]


def test_only_inspector_can_audit_importers_and_only_supervisor_manages_users() -> None:
    assert [r for r in ALL_ROLES if has_permission(r, "audit:fiscal")] == [INSPECTOR]  # type: ignore[arg-type]
    assert [r for r in ALL_ROLES if has_permission(r, "users:manage")] == [SUPERVISOR]  # type: ignore[arg-type]


def test_only_the_valuation_analyst_can_use_both_chats() -> None:
    """Chat con la IA (chat:ia) y canal seguro entre funcionarios (chat:canal)."""
    assert [r for r in ALL_ROLES if has_permission(r, "chat:ia")] == [ANALISTA]  # type: ignore[arg-type]
    assert [r for r in ALL_ROLES if has_permission(r, "chat:canal")] == [ANALISTA]  # type: ignore[arg-type]


def test_chat_permissions_are_not_write_permissions() -> None:
    assert not {"chat:ia", "chat:canal"} & WRITE_PERMISSIONS
    assert not ROLE_PERMISSIONS[ANALISTA] & WRITE_PERMISSIONS  # sigue siendo de solo lectura
