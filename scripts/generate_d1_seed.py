"""Genera ``seed_d1.sql`` con 10 usuarios RBAC (6 roles aduaneros) para Cloudflare D1.

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
class SeedUser:
    id: str
    username: str
    email: str
    full_name: str
    role: str
    role_label: str
    clearance_level: str
    department: str
    synthetic_cedula: str
    demo_clave: str
    permissions: tuple[str, ...]


SEED_USERS: tuple[SeedUser, ...] = (
    SeedUser(
        id="usr-auditor-01",
        username="dgonzalez",
        email="auditor@aduana.gob.ve",
        full_name="Deykary González",
        role="auditor",
        role_label="Auditora Principal",
        clearance_level="Nivel 4 — Confidencial Estatal",
        department="Dirección de Auditoría Algorítmica y Cumplimiento",
        synthetic_cedula="V-14220101",
        demo_clave="auditor2026",
        permissions=(
            "ledger:read",
            "ledger:verify",
            "explica:inspect",
            "canal:read",
        ),
    ),
    SeedUser(
        id="usr-auditor-02",
        username="cmendez",
        email="cmendez@aduana.gob.ve",
        full_name="Carlos Méndez",
        role="auditor",
        role_label="Auditor Forense SHA-256",
        clearance_level="Nivel 4 — Confidencial Estatal",
        department="Contraloría Interna Aduanera",
        synthetic_cedula="V-15330202",
        demo_clave="auditor2026",
        permissions=(
            "ledger:read",
            "ledger:verify",
            "explica:inspect",
        ),
    ),
    SeedUser(
        id="usr-analista-01",
        username="esalazar",
        email="analista@aduana.gob.ve",
        full_name="Elena Salazar",
        role="analista",
        role_label="Analista de Operaciones & Solvencias",
        clearance_level="Nivel 2 — Operativo Aduanero",
        department="Departamento de Solvencias Fiscales y Aforo",
        synthetic_cedula="V-18440303",
        demo_clave="analista2026",
        permissions=(
            "gateway:process",
            "shield:sanitize",
            "chat:use",
            "canal:write",
        ),
    ),
    SeedUser(
        id="usr-analista-02",
        username="lparedes",
        email="lparedes@aduana.gob.ve",
        full_name="Luisana Paredes",
        role="analista",
        role_label="Analista de Expedientes",
        clearance_level="Nivel 2 — Operativo Aduanero",
        department="División de Trámites y Encomiendas",
        synthetic_cedula="V-19550404",
        demo_clave="analista2026",
        permissions=(
            "gateway:process",
            "shield:sanitize",
            "chat:use",
        ),
    ),
    SeedUser(
        id="usr-admin-01",
        username="mvivas",
        email="admin@aduana.gob.ve",
        full_name="Marcos Vivas",
        role="admin",
        role_label="Administrador de Infraestructura & Ciberseguridad",
        clearance_level="Nivel 5 — Soberanía Crítica GovTech",
        department="Coordinación Nacional de Infraestructura Soberana",
        synthetic_cedula="V-12660505",
        demo_clave="admin2026",
        permissions=(
            "admin:all",
            "gateway:process",
            "ledger:verify",
            "ledger:tamper_sim",
            "users:manage",
        ),
    ),
    SeedUser(
        id="usr-admin-02",
        username="rbriceno",
        email="rbriceno@aduana.gob.ve",
        full_name="Rafael Briceño",
        role="admin",
        role_label="Custodio de Llaves y Enclaves",
        clearance_level="Nivel 5 — Soberanía Crítica GovTech",
        department="Centro Nacional de Ciberseguridad Aduanera",
        synthetic_cedula="V-13770606",
        demo_clave="admin2026",
        permissions=(
            "admin:all",
            "keyring:rotate",
            "ledger:verify",
            "users:manage",
        ),
    ),
    SeedUser(
        id="usr-inspector-01",
        username="vmarquez",
        email="vmarquez@aduana.gob.ve",
        full_name="Valeria Márquez",
        role="inspector_aforo",
        role_label="Inspectora de Aforo Físico y Documental",
        clearance_level="Nivel 3 — Control Primario Aduanero",
        department="Gerencia de Aduana Principal La Guaira",
        synthetic_cedula="V-20880707",
        demo_clave="inspector2026",
        permissions=(
            "gateway:process",
            "explica:inspect",
            "explica:override",
            "aforo:validate",
        ),
    ),
    SeedUser(
        id="usr-inspector-02",
        username="aquintero",
        email="aquintero@aduana.gob.ve",
        full_name="Andrés Quintero",
        role="inspector_aforo",
        role_label="Inspector de Aforo Marítimo",
        clearance_level="Nivel 3 — Control Primario Aduanero",
        department="Gerencia de Aduana Principal Puerto Cabello",
        synthetic_cedula="V-21990808",
        demo_clave="inspector2026",
        permissions=(
            "gateway:process",
            "explica:inspect",
            "aforo:validate",
        ),
    ),
    SeedUser(
        id="usr-cumplimiento-01",
        username="sherrera",
        email="cumplimiento@aduana.gob.ve",
        full_name="Sofía Herrera",
        role="oficial_cumplimiento",
        role_label="Oficial de Cumplimiento y Habeas Data",
        clearance_level="Nivel 4 — Protección de Datos CRBV",
        department="Unidad de Cumplimiento Ley de Infogobierno",
        synthetic_cedula="V-16110909",
        demo_clave="cumplimiento2026",
        permissions=(
            "guardian:audit",
            "consent:audit",
            "ledger:read",
            "explica:inspect",
        ),
    ),
    SeedUser(
        id="usr-supervisor-01",
        username="rzambrano",
        email="supervisor@aduana.gob.ve",
        full_name="Ricardo Zambrano",
        role="supervisor_aduana",
        role_label="Supervisor Nacional de Operaciones Aduaneras",
        clearance_level="Nivel 4 — Supervisión Regional",
        department="Intendencia Nacional de Aduanas",
        synthetic_cedula="V-11221010",
        demo_clave="supervisor2026",
        permissions=(
            "gateway:process",
            "explica:override",
            "ledger:read",
            "ledger:verify",
            "canal:write",
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
        "-- Aduana IA — Seed RBAC para Cloudflare D1 (10 usuarios / 6 roles aduaneros)",
        "-- Generado automáticamente por scripts/generate_d1_seed.py",
        "-- Zero-Plaintext-PII: las cédulas están transformadas vía HMAC (blind_citizen_id)",
        "-- Contraseñas protegidas con PBKDF2-HMAC-SHA256 (310,000 iteraciones)",
        "-- Ejecutar:",
        "--   wrangler d1 execute aduana-db --remote --file=seed_d1.sql",
        "-- =============================================================================",
        "",
    ]

    for user in SEED_USERS:
        blind_id = blind_citizen_id(keys, user.synthetic_cedula)
        pwd_hash = hash_password_pbkdf2(user.demo_clave)
        perms_json = json.dumps(list(user.permissions), ensure_ascii=False)
        cols = (
            "id, username, email, full_name, role, role_label, clearance_level, "
            "department, blind_citizen_id, password_hash, permissions_json, "
            "is_active, created_at_utc, updated_at_utc"
        )
        vals = ", ".join(
            [
                sql_quote(user.id),
                sql_quote(user.username),
                sql_quote(user.email),
                sql_quote(user.full_name),
                sql_quote(user.role),
                sql_quote(user.role_label),
                sql_quote(user.clearance_level),
                sql_quote(user.department),
                sql_quote(blind_id),
                sql_quote(pwd_hash),
                sql_quote(perms_json),
                "1",
                sql_quote(timestamp),
                sql_quote(timestamp),
            ]
        )
        stmt = (
            f"INSERT INTO usuarios_aduana ({cols})\n"
            f"VALUES ({vals})\n"
            f"ON CONFLICT(id) DO NOTHING;\n"
        )
        lines.append(stmt)

    return "\n".join(lines)


def main() -> None:
    keys = resolve_keyring()
    sql_content = build_seed_sql(keys)
    output_path = PROJECT_ROOT / "seed_d1.sql"
    output_path.write_text(sql_content, encoding="utf-8", newline="\n")
    roles = sorted({u.role for u in SEED_USERS})
    sys.stdout.write(
        f"Generado {output_path} con {len(SEED_USERS)} usuarios "
        f"y {len(roles)} roles: {', '.join(roles)}\n"
    )


if __name__ == "__main__":
    main()
