"""Genera ``seed_d1.sql`` alineado al contexto real de Aduana IA para Cloudflare D1.

Roles oficiales del proyecto: ``analista``, ``administrador`` y ``auditor``.
Calcula hashes PBKDF2-HMAC-SHA256 (310,000 iteraciones) y ``blind_citizen_id``
mediante ``core.crypto.blind_citizen_id`` sin escribir cédulas en texto plano en SQL.

Uso:
    python scripts/generate_d1_seed.py
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.crypto import blind_citizen_id  # noqa: E402
from core.keyring import KeyRing  # noqa: E402

PBKDF2_ITERATIONS = 310_000
DEMO_SEED_KEY_HEX = hashlib.sha256(b"aduana-ia-uneti-2026-demo-seed").hexdigest()


@dataclass(frozen=True, slots=True)
class SeedRole:
    role_id: str
    role_name: str
    description: str
    allowed_tabs: tuple[str, ...]
    default_tab: str


@dataclass(frozen=True, slots=True)
class SeedUser:
    id: str
    username: str
    email: str
    full_name: str
    short_name: str
    avatar_text: str
    role: str
    role_label: str
    clearance_level: str
    entity: str
    department: str
    ed25519_key: str
    ed25519_status: str
    synthetic_cedula: str
    demo_clave: str
    permissions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SeedChannel:
    id: str
    name: str
    description: str


SEED_ROLES: tuple[SeedRole, ...] = (
    SeedRole(
        role_id="analista",
        role_name="Analista",
        description="Módulos asignados: Pasarela, Chat IA y Canal Seguro E2EE.",
        allowed_tabs=("pasarela", "chat", "canal"),
        default_tab="pasarela",
    ),
    SeedRole(
        role_id="administrador",
        role_name="Administrador de Infraestructura",
        description="Módulos asignados: Control total perimetral (Todos los módulos).",
        allowed_tabs=("pasarela", "chat", "ledger", "explicabilidad", "canal"),
        default_tab="pasarela",
    ),
    SeedRole(
        role_id="auditor",
        role_name="Auditor",
        description="Módulos asignados: Explicabilidad y Ledger inalterable SHA-256.",
        allowed_tabs=("ledger", "explicabilidad"),
        default_tab="ledger",
    ),
)

SEED_USERS: tuple[SeedUser, ...] = (
    SeedUser(
        id="usr-auditor-01",
        username="dgonzalez",
        email="auditor@aduana.gob.ve",
        full_name="Deykary González",
        short_name="Deykary G.",
        avatar_text="DG",
        role="auditor",
        role_label="Auditora Principal",
        clearance_level="Nivel 4 — Confidencial Estatal",
        entity="Superintendencia Nacional Aduanera / Contraloría GovTech",
        department="Dirección de Auditoría Algorítmica y Cumplimiento",
        ed25519_key="0x8F9a...3B42",
        ed25519_status="Validada y Activa",
        synthetic_cedula="V-14220101",
        demo_clave="auditor2026",
        permissions=(
            "Desencriptación de PII autorizada",
            "Auditoría de Ledger SHA-256",
            "Inspección de Inferencia GovEval",
            "Canal E2EE Enclave Seguro",
        ),
    ),
    SeedUser(
        id="usr-auditor-02",
        username="cmendez",
        email="cmendez@aduana.gob.ve",
        full_name="Carlos Méndez",
        short_name="Carlos M.",
        avatar_text="CM",
        role="auditor",
        role_label="Auditor Principal",
        clearance_level="Nivel 4 — Confidencial Estatal",
        entity="Ministerio de Tecnología e Innovación / UNETI",
        department="División de Auditoría Forense y Ciberseguridad",
        ed25519_key="0x8F9...3B",
        ed25519_status="Validada y Activa",
        synthetic_cedula="V-15330202",
        demo_clave="auditor2026",
        permissions=(
            "Desencriptación de PII autorizada",
            "Auditoría de Ledger SHA-256",
            "Emisión de Dictámenes Vinculantes",
            "Inspección de Pasarela Local",
        ),
    ),
    SeedUser(
        id="usr-auditor-03",
        username="lsantander",
        email="lsantander@aduana.gob.ve",
        full_name="Lucía Santander",
        short_name="Lucía S.",
        avatar_text="LS",
        role="auditor",
        role_label="Auditora Legal Gov-AI",
        clearance_level="Nivel 3 — Dictamen Jurídico",
        entity="Consultoría Jurídica de Inteligencia Artificial Gubernamental",
        department="Marco Regulatorio y Transparencia Pública",
        ed25519_key="0x71D...5E",
        ed25519_status="Validada y Activa",
        synthetic_cedula="V-16440303",
        demo_clave="auditor2026",
        permissions=(
            "Validación de Concordancia Legal ENISA",
            "Supervisión del Artículo 14 Ley IA",
            "Firma de Dictamen Vinculante",
        ),
    ),
    SeedUser(
        id="usr-auditor-04",
        username="cramirez",
        email="cramirez@aduana.gob.ve",
        full_name="Dra. Carmen Ramírez",
        short_name="Carmen R.",
        avatar_text="CR",
        role="auditor",
        role_label="Auditora de Cumplimiento y Confidencialidad",
        clearance_level="Nivel 4 — Confidencial Estatal",
        entity="SENIAT / Gerencia de Fiscalización Nacional",
        department="Departamento de Cumplimiento Normativo",
        ed25519_key="0xA92...F1",
        ed25519_status="Validada y Activa",
        synthetic_cedula="V-13550404",
        demo_clave="auditor2026",
        permissions=(
            "Desencriptación Selectiva Homomórfica",
            "Custodia de Datos Ciudadanos",
            "Auditoría de Ledger SHA-256",
        ),
    ),
    SeedUser(
        id="usr-analista-01",
        username="esalazar",
        email="analista@aduana.gob.ve",
        full_name="Elena Salazar",
        short_name="Elena S.",
        avatar_text="ES",
        role="analista",
        role_label="Analista de Operaciones & Solvencias",
        clearance_level="Nivel 2 — Operativo Aduanero",
        entity="Intendencia Nacional de Aduanas / División de Trámites",
        department="Departamento de Solvencias Fiscales y Aforo",
        ed25519_key="0x3C4b...9F11",
        ed25519_status="Validada y Activa",
        synthetic_cedula="V-18660505",
        demo_clave="analista2026",
        permissions=(
            "Consulta de Pasarela en Tiempo Real",
            "Sanitización Homomórfica de PII",
            "Evaluación de Explicabilidad y Equidad",
            "Revisión de Declaraciones Aduaneras",
        ),
    ),
    SeedUser(
        id="usr-analista-02",
        username="lparedes",
        email="lparedes@aduana.gob.ve",
        full_name="Luisana Paredes",
        short_name="Luisana P.",
        avatar_text="LP",
        role="analista",
        role_label="Analista de Aforo Documental",
        clearance_level="Nivel 2 — Operativo Aduanero",
        entity="Intendencia Nacional de Aduanas / Aduana La Guaira",
        department="División de Trámites y Encomiendas",
        ed25519_key="0x4D2a...8E01",
        ed25519_status="Validada y Activa",
        synthetic_cedula="V-19770606",
        demo_clave="analista2026",
        permissions=(
            "Consulta de Pasarela en Tiempo Real",
            "Sanitización Homomórfica de PII",
            "Gestión de Peticiones Ciudadanas",
        ),
    ),
    SeedUser(
        id="usr-analista-03",
        username="aquintero",
        email="aquintero@aduana.gob.ve",
        full_name="Andrés Quintero",
        short_name="Andrés Q.",
        avatar_text="AQ",
        role="analista",
        role_label="Analista de Guardia Aduanera",
        clearance_level="Nivel 2 — Operativo Aduanero",
        entity="Intendencia Nacional de Aduanas / Puerto Cabello",
        department="Centro de Comando Operativo Aduanero",
        ed25519_key="0x5B1c...7D22",
        ed25519_status="Validada y Activa",
        synthetic_cedula="V-20880707",
        demo_clave="analista2026",
        permissions=(
            "Consulta de Pasarela en Tiempo Real",
            "Sanitización de PII con Shield",
            "Consulta de Constancias de Solvencia",
        ),
    ),
    SeedUser(
        id="usr-analista-04",
        username="vmarquez",
        email="vmarquez@aduana.gob.ve",
        full_name="Valeria Márquez",
        short_name="Valeria M.",
        avatar_text="VM",
        role="analista",
        role_label="Analista de Exoneraciones y Becas",
        clearance_level="Nivel 2 — Operativo Aduanero",
        entity="Intendencia Nacional de Aduanas / Operaciones",
        department="Coordinación de Beneficios Institucionales",
        ed25519_key="0x6E3d...4A19",
        ed25519_status="Validada y Activa",
        synthetic_cedula="V-21990808",
        demo_clave="analista2026",
        permissions=(
            "Consulta de Pasarela en Tiempo Real",
            "Sanitización Homomórfica de PII",
            "Revisión de Declaraciones Aduaneras",
        ),
    ),
    SeedUser(
        id="usr-admin-01",
        username="mvivas",
        email="admin@aduana.gob.ve",
        full_name="Marcos Vivas",
        short_name="Marcos V.",
        avatar_text="MV",
        role="administrador",
        role_label="Administrador de Infraestructura & Ciberseguridad",
        clearance_level="Nivel 5 — Soberanía Crítica GovTech",
        entity="Centro Nacional de Ciberseguridad / Red Nacional de Integridad",
        department="Coordinación Nacional de Infraestructura Soberana",
        ed25519_key="0xE4A1...77C0",
        ed25519_status="Custodio Maestro Gov-Ed25519",
        synthetic_cedula="V-12110909",
        demo_clave="admin2026",
        permissions=(
            "Control Total de Nodos y Consenso",
            "Simulación de Manipulación y Cuarentena",
            "Gestión de Claves Criptográficas y Enclaves",
            "Supervisión Perimetral ISO/IEC 27001",
        ),
    ),
    SeedUser(
        id="usr-admin-02",
        username="rbriceno",
        email="rbriceno@aduana.gob.ve",
        full_name="Rafael Briceño",
        short_name="Rafael B.",
        avatar_text="RB",
        role="administrador",
        role_label="Administrador de Enclaves y KeyRing",
        clearance_level="Nivel 5 — Soberanía Crítica GovTech",
        entity="Centro Nacional de Ciberseguridad / Red de Integridad",
        department="Seguridad Ofensiva y Enclaves Confinados",
        ed25519_key="0xF109...2B88",
        ed25519_status="Custodio Maestro Gov-Ed25519",
        synthetic_cedula="V-11221010",
        demo_clave="admin2026",
        permissions=(
            "Control de Nodos Perimetrales",
            "Simulación de Manipulación Criptográfica",
            "Aislamiento Preventivo de Memoria",
            "Gestión de Certificados Homomórficos",
        ),
    ),
)

SEED_CHANNELS: tuple[SeedChannel, ...] = (
    SeedChannel(
        id="auditoria-general",
        name="auditoria-general",
        description=(
            "Canal general de trazabilidad, concordancia de expedientes y dictámenes soberanos."
        ),
    ),
    SeedChannel(
        id="alertas-ledger",
        name="alertas-ledger",
        description=(
            "Monitoreo de desajustes hash SHA-256, firmas no concordantes y aislamiento de nodos."
        ),
    ),
)


def hash_password_pbkdf2(password: str, iterations: int = PBKDF2_ITERATIONS) -> str:
    """Genera hash PBKDF2-HMAC-SHA256 con sal criptográfica de 16 bytes."""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}"


def sql_quote(value: str) -> str:
    """Escapa comillas simples para literales SQL estándar."""
    return "'" + value.replace("'", "''") + "'"


def resolve_keyring() -> KeyRing:
    """Obtiene KeyRing desde ADUANA_MASTER_KEY o llave determinista de seed demo."""
    raw = os.environ.get("ADUANA_MASTER_KEY", "").strip()
    if raw:
        return KeyRing(bytes.fromhex(raw))
    return KeyRing(bytes.fromhex(DEMO_SEED_KEY_HEX))


def build_seed_sql(keys: KeyRing, now_utc: str | None = None) -> str:
    """Construye el contenido completo de ``seed_d1.sql``."""
    timestamp = now_utc or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = [
        "-- =============================================================================",
        "-- Aduana IA — Seed RBAC y Canales para Cloudflare D1",
        "-- Roles oficiales: analista, administrador, auditor (10 usuarios)",
        "-- Generado automáticamente por scripts/generate_d1_seed.py",
        "-- Zero-Plaintext-PII: cédulas transformadas vía HMAC (blind_citizen_id)",
        "-- Contraseñas protegidas con PBKDF2-HMAC-SHA256 (310,000 iteraciones)",
        "-- Ejecutar:",
        "--   wrangler d1 execute aduana-db --remote --file=seed_d1.sql",
        "-- =============================================================================",
        "",
        "-- 1. Roles oficiales RBAC",
    ]

    for role in SEED_ROLES:
        tabs_json = json.dumps(list(role.allowed_tabs), ensure_ascii=False)
        cols = "role_id, role_name, description, allowed_tabs_json, default_tab"
        vals = ", ".join(
            [
                sql_quote(role.role_id),
                sql_quote(role.role_name),
                sql_quote(role.description),
                sql_quote(tabs_json),
                sql_quote(role.default_tab),
            ]
        )
        lines.append(
            f"INSERT INTO roles_aduana ({cols})\n"
            f"VALUES ({vals})\n"
            "ON CONFLICT(role_id) DO NOTHING;\n"
        )

    lines.append("-- 2. Usuarios RBAC (10 funcionarios)")
    for user in SEED_USERS:
        blind_id = blind_citizen_id(keys, user.synthetic_cedula)
        pwd_hash = hash_password_pbkdf2(user.demo_clave)
        perms_json = json.dumps(list(user.permissions), ensure_ascii=False)
        cols = (
            "id, username, email, full_name, short_name, avatar_text, role, "
            "role_label, clearance_level, entity, department, ed25519_key, "
            "ed25519_status, blind_citizen_id, password_hash, permissions_json, "
            "is_active, created_at_utc, updated_at_utc"
        )
        vals = ", ".join(
            [
                sql_quote(user.id),
                sql_quote(user.username),
                sql_quote(user.email),
                sql_quote(user.full_name),
                sql_quote(user.short_name),
                sql_quote(user.avatar_text),
                sql_quote(user.role),
                sql_quote(user.role_label),
                sql_quote(user.clearance_level),
                sql_quote(user.entity),
                sql_quote(user.department),
                sql_quote(user.ed25519_key),
                sql_quote(user.ed25519_status),
                sql_quote(blind_id),
                sql_quote(pwd_hash),
                sql_quote(perms_json),
                "1",
                sql_quote(timestamp),
                sql_quote(timestamp),
            ]
        )
        lines.append(
            f"INSERT INTO usuarios_aduana ({cols})\n"
            f"VALUES ({vals})\n"
            "ON CONFLICT(id) DO NOTHING;\n"
        )

    lines.append("-- 3. Canales institucionales del Canal Seguro E2EE")
    for ch in SEED_CHANNELS:
        cols = "id, name, description, created_at_utc"
        vals = ", ".join(
            [
                sql_quote(ch.id),
                sql_quote(ch.name),
                sql_quote(ch.description),
                sql_quote(timestamp),
            ]
        )
        lines.append(
            f"INSERT INTO canal_seguro_channels ({cols})\n"
            f"VALUES ({vals})\n"
            "ON CONFLICT(id) DO NOTHING;\n"
        )

    return "\n".join(lines)


def main() -> None:
    keys = resolve_keyring()
    sql_content = build_seed_sql(keys)
    output_path = PROJECT_ROOT / "seed_d1.sql"
    output_path.write_text(sql_content, encoding="utf-8", newline="\n")
    roles = sorted({u.role for u in SEED_USERS})
    sys.stdout.write(
        f"Generado {output_path} con {len(SEED_USERS)} usuarios, "
        f"{len(roles)} roles ({', '.join(roles)}) y {len(SEED_CHANNELS)} canales\n"
    )


if __name__ == "__main__":
    main()
