-- =============================================================================
-- Aduana IA — Esquema SQLite / Cloudflare D1 (Zero-Trust & Zero-Plaintext-PII)
-- Basado en el contexto completo del proyecto:
--   * RBAC (src/types/auth.ts, src/constants/mockAuth.ts):
--       3 roles oficiales: 'analista', 'administrador', 'auditor'
--   * Pipeline Soberano (core/context.py, pipeline/stage0..stage5, app/schemas.py)
--   * Ledger Inmutable (pipeline/stage4_ledger.py)
--   * Canal Seguro E2EE (src/types/secure-channel.ts)
--
-- Despliegue en Cloudflare D1:
--   wrangler d1 execute aduana-db --remote --file=schema.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. CATÁLOGO DE ROLES RBAC (roles_aduana)
--    Roles oficiales del sistema: analista, administrador, auditor
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles_aduana (
    role_id TEXT PRIMARY KEY CHECK (
        role_id IN ('analista', 'administrador', 'auditor')
    ),
    role_name TEXT NOT NULL,
    description TEXT NOT NULL,
    allowed_tabs_json TEXT NOT NULL,
    default_tab TEXT NOT NULL CHECK (
        default_tab IN ('pasarela', 'chat', 'ledger', 'explicabilidad', 'canal')
    )
);

-- -----------------------------------------------------------------------------
-- 2. USUARIOS ADUANEROS RBAC (usuarios_aduana)
--    Zero-Plaintext-PII: cédula almacenada como blind_citizen_id (HMAC-SHA256).
--    Contraseñas protegidas con PBKDF2-HMAC-SHA256 (310,000 iteraciones).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios_aduana (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    avatar_text TEXT NOT NULL,
    role TEXT NOT NULL REFERENCES roles_aduana(role_id),
    role_label TEXT NOT NULL,
    clearance_level TEXT NOT NULL,
    entity TEXT NOT NULL,
    department TEXT NOT NULL,
    ed25519_key TEXT NOT NULL,
    ed25519_status TEXT NOT NULL,
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

-- -----------------------------------------------------------------------------
-- 3. LEDGER INMUTABLE (ledger_blocks — pipeline/stage4_ledger.py, CA-03, CA-05)
--    Almacena únicamente hashes SHA-256, firmas HMAC-SHA256 e índices ciegos.
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
    human_override INTEGER NOT NULL DEFAULT 0 CHECK (human_override IN (0, 1)),
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
-- 4. REGISTRO DE CONSENTIMIENTO CIUDADANO (consent_records — RF0 / stage0_consent)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS consent_records (
    request_id TEXT PRIMARY KEY,
    blind_citizen_id TEXT NOT NULL,
    purpose_code TEXT NOT NULL,
    granted INTEGER NOT NULL CHECK (granted IN (0, 1)),
    consent_hash TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_consent_records_blind_citizen_id
    ON consent_records (blind_citizen_id);

-- -----------------------------------------------------------------------------
-- 5. EVALUACIONES DEL PIPELINE (tramite_evaluations — SHIELD + GUARDIÁN + EXPLICA)
--    Trazabilidad analítica Zero-PII vinculada a ledger_blocks y usuarios_aduana.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tramite_evaluations (
    request_id TEXT PRIMARY KEY,
    operator_user_id TEXT REFERENCES usuarios_aduana(id),
    timestamp_utc TEXT NOT NULL,
    blind_citizen_id TEXT NOT NULL,
    policy_status TEXT NOT NULL CHECK (
        policy_status IN (
            'CLEAN',
            'BLOCKED_INJECTION',
            'BLOCKED_CANARY_LEAK',
            'BLOCKED_NO_CONSENT',
            'BLOCKED_PII_LEAK'
        )
    ),
    pii_count INTEGER NOT NULL DEFAULT 0,
    detected_types_json TEXT NOT NULL DEFAULT '[]',
    rif_mod11_verified INTEGER CHECK (rif_mod11_verified IN (0, 1)),
    risk_score REAL NOT NULL DEFAULT 0.0,
    adapter_mode TEXT NOT NULL CHECK (
        adapter_mode IN (
            'LOCAL_OLLAMA',
            'HYBRID_OPENAI',
            'OFFLINE_DETERMINISTIC_FALLBACK',
            'CLOUDFLARE_WORKERS_AI'
        )
    ),
    circuit_breaker_tripped INTEGER NOT NULL DEFAULT 0 CHECK (
        circuit_breaker_tripped IN (0, 1)
    ),
    model_type TEXT,
    logit_z REAL,
    probability_score REAL,
    linear_shap_json TEXT,
    model_recommendation TEXT NOT NULL CHECK (
        model_recommendation IN (
            'PRIORIDAD_ALTA',
            'REVISION_ESTANDAR',
            'RECAUDOS_INCOMPLETOS',
            'BLOQUEADO_SEGURIDAD'
        )
    ),
    human_decision TEXT NOT NULL CHECK (
        human_decision IN (
            'PRIORIDAD_ALTA',
            'REVISION_ESTANDAR',
            'RECAUDOS_INCOMPLETOS',
            'BLOQUEADO_SEGURIDAD'
        )
    ),
    human_override INTEGER NOT NULL DEFAULT 0 CHECK (human_override IN (0, 1)),
    latency_ms REAL NOT NULL,
    block_index INTEGER REFERENCES ledger_blocks(block_index)
);

CREATE INDEX IF NOT EXISTS idx_tramite_evaluations_policy_status
    ON tramite_evaluations (policy_status);

CREATE INDEX IF NOT EXISTS idx_tramite_evaluations_operator
    ON tramite_evaluations (operator_user_id);

CREATE INDEX IF NOT EXISTS idx_tramite_evaluations_block_index
    ON tramite_evaluations (block_index);

-- -----------------------------------------------------------------------------
-- 6. CANAL SEGURO INSTITUCIONAL E2EE (canal_seguro_channels / messages)
--    Mensajería sanitizada entre funcionarios (cero PII en texto plano).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS canal_seguro_channels (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS canal_seguro_messages (
    id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL REFERENCES canal_seguro_channels(id),
    sender_user_id TEXT NOT NULL REFERENCES usuarios_aduana(id),
    sender_role TEXT NOT NULL,
    sanitized_content TEXT NOT NULL,
    pii_masked INTEGER NOT NULL DEFAULT 0 CHECK (pii_masked IN (0, 1)),
    pii_hash TEXT,
    verified_delivery INTEGER NOT NULL DEFAULT 1 CHECK (verified_delivery IN (0, 1)),
    timestamp_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_canal_seguro_messages_channel
    ON canal_seguro_messages (channel_id, timestamp_utc);
