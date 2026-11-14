-- =============================================================================
-- Aduana IA — Esquema SQLite / Cloudflare D1 (Zero-Trust & Zero-Plaintext-PII)
-- Compatible con:
--   1) Nodo Soberano Local (Python SQLite3 WAL + Triggers de Inmutabilidad)
--   2) Demo Edge Cloudflare D1:
--      wrangler d1 execute aduana-db --remote --file=schema.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. LEDGER INMUTABLE (RF-15..RF-17, CA-03, CA-05)
--    Almacena únicamente hashes SHA-256, firmas HMAC-SHA256 e índices ciegos.
--    Cero PII en texto plano.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ledger_blocks (
    block_index INTEGER PRIMARY KEY,
    request_id TEXT NOT NULL UNIQUE,
    timestamp_utc TEXT NOT NULL,
    blind_citizen_id TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    block_hash TEXT NOT NULL,
    hmac_signature TEXT NOT NULL,
    security_verdict TEXT NOT NULL,
    model_recommendation TEXT NOT NULL,
    human_decision TEXT NOT NULL,
    human_override INTEGER NOT NULL DEFAULT 0,
    citizen_receipt_code TEXT NOT NULL UNIQUE,
    key_id TEXT NOT NULL,
    override_justification_hash TEXT
);

CREATE INDEX IF NOT EXISTS idx_ledger_blocks_blind_citizen_id
    ON ledger_blocks (blind_citizen_id);

CREATE INDEX IF NOT EXISTS idx_ledger_blocks_timestamp_utc
    ON ledger_blocks (timestamp_utc);

CREATE INDEX IF NOT EXISTS idx_ledger_blocks_security_verdict
    ON ledger_blocks (security_verdict);

CREATE TRIGGER IF NOT EXISTS prevent_ledger_update
BEFORE UPDATE ON ledger_blocks
BEGIN
    SELECT RAISE(ABORT, 'ERR_IMMUTABLE_LEDGER');
END;

CREATE TRIGGER IF NOT EXISTS prevent_ledger_delete
BEFORE DELETE ON ledger_blocks
BEGIN
    SELECT RAISE(ABORT, 'ERR_IMMUTABLE_LEDGER');
END;

-- -----------------------------------------------------------------------------
-- 2. CONTROL DE ACCESO BASADO EN ROLES — RBAC ADUANERO (usuarios_aduana)
--    6 roles aduaneros institucionales:
--      - admin
--      - auditor
--      - analista
--      - inspector_aforo
--      - oficial_cumplimiento
--      - supervisor_aduana
--    Contraseñas protegidas con PBKDF2-HMAC-SHA256 (310,000 iteraciones)
--    y cédula almacenada exclusivamente como blind_citizen_id (HMAC-SHA256).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios_aduana (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (
        role IN (
            'admin',
            'auditor',
            'analista',
            'inspector_aforo',
            'oficial_cumplimiento',
            'supervisor_aduana'
        )
    ),
    role_label TEXT NOT NULL,
    clearance_level TEXT NOT NULL,
    department TEXT NOT NULL,
    blind_citizen_id TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    permissions_json TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_usuarios_aduana_role
    ON usuarios_aduana (role);

CREATE INDEX IF NOT EXISTS idx_usuarios_aduana_is_active
    ON usuarios_aduana (is_active);
