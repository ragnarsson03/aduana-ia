-- =============================================================================
-- Aduana IA — Seed RBAC para Cloudflare D1 (10 usuarios / 6 roles aduaneros)
-- Generado automáticamente por scripts/generate_d1_seed.py
-- Zero-Plaintext-PII: las cédulas están transformadas vía HMAC (blind_citizen_id)
-- Contraseñas protegidas con PBKDF2-HMAC-SHA256 (310,000 iteraciones)
-- Ejecutar:
--   wrangler d1 execute aduana-db --remote --file=seed_d1.sql
-- =============================================================================

INSERT INTO usuarios_aduana (id, username, email, full_name, role, role_label, clearance_level, department, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-auditor-01', 'dgonzalez', 'auditor@aduana.gob.ve', 'Deykary González', 'auditor', 'Auditora Principal', 'Nivel 4 — Confidencial Estatal', 'Dirección de Auditoría Algorítmica y Cumplimiento', '580f475264bb6597910d1799be12bd0f2b729afd8e35d2e873a8d64c0ba397f9', 'pbkdf2_sha256$310000$c973517f146af141f220e5db6b9d2767$c76e49f56a28db5e1f4977af62caba1397454334307d923685972695b6b93fc3', '["ledger:read", "ledger:verify", "explica:inspect", "canal:read"]', 1, '2026-11-14T06:28:07Z', '2026-11-14T06:28:07Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, role, role_label, clearance_level, department, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-auditor-02', 'cmendez', 'cmendez@aduana.gob.ve', 'Carlos Méndez', 'auditor', 'Auditor Forense SHA-256', 'Nivel 4 — Confidencial Estatal', 'Contraloría Interna Aduanera', '792e7027d469e9f39bbd412c3244d671e93d0032abeb79523c068c29e1751107', 'pbkdf2_sha256$310000$7bb6a786662ac715e8c130d3af5d54dc$ac51c255dfd69ae4efe71634be1e4fa74a752b5e600e0318f72ea207f633b4e9', '["ledger:read", "ledger:verify", "explica:inspect"]', 1, '2026-11-14T06:28:07Z', '2026-11-14T06:28:07Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, role, role_label, clearance_level, department, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-analista-01', 'esalazar', 'analista@aduana.gob.ve', 'Elena Salazar', 'analista', 'Analista de Operaciones & Solvencias', 'Nivel 2 — Operativo Aduanero', 'Departamento de Solvencias Fiscales y Aforo', '6fde69c3e0c4b8c74de40c55fb9e4a9d52af28defcd7974906a649edcbe587c2', 'pbkdf2_sha256$310000$d0b9f7379d8a8f229541be5582f702e1$c966b8037fa40d2f954ab0d649058b32913c26a2004db1a7aade8c10bae8f327', '["gateway:process", "shield:sanitize", "chat:use", "canal:write"]', 1, '2026-11-14T06:28:07Z', '2026-11-14T06:28:07Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, role, role_label, clearance_level, department, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-analista-02', 'lparedes', 'lparedes@aduana.gob.ve', 'Luisana Paredes', 'analista', 'Analista de Expedientes', 'Nivel 2 — Operativo Aduanero', 'División de Trámites y Encomiendas', '33c19ee292ba231c75a4bb8ae846c3529c5e453b1f86c9a2667c2ca0bbe19ebb', 'pbkdf2_sha256$310000$3c1664ed4f401dcf46391c8f70dca66b$03c6842e4b4cfbeaf87d0db4859d393a1c48e50e1855b91ca34aeb2fb7fa9e11', '["gateway:process", "shield:sanitize", "chat:use"]', 1, '2026-11-14T06:28:07Z', '2026-11-14T06:28:07Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, role, role_label, clearance_level, department, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-admin-01', 'mvivas', 'admin@aduana.gob.ve', 'Marcos Vivas', 'admin', 'Administrador de Infraestructura & Ciberseguridad', 'Nivel 5 — Soberanía Crítica GovTech', 'Coordinación Nacional de Infraestructura Soberana', 'ea45b9fe264f45014c7ab004283c3b8437d1c112b6c97a36b91f731c83ebb108', 'pbkdf2_sha256$310000$84587d9be873271c360e2c1237030bc1$a80dfa1ee6c699241fde6cb769f0fb68cec84a0fd14d22cd2c51319d4def49aa', '["admin:all", "gateway:process", "ledger:verify", "ledger:tamper_sim", "users:manage"]', 1, '2026-11-14T06:28:07Z', '2026-11-14T06:28:07Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, role, role_label, clearance_level, department, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-admin-02', 'rbriceno', 'rbriceno@aduana.gob.ve', 'Rafael Briceño', 'admin', 'Custodio de Llaves y Enclaves', 'Nivel 5 — Soberanía Crítica GovTech', 'Centro Nacional de Ciberseguridad Aduanera', '6f7e853697bc7e41815c5912c892497ed81abc2edd09d9beb15274a1d18f71aa', 'pbkdf2_sha256$310000$dae9f4562f3f4e62b777fb12ab0eda3c$3433dba2ace0709485ef1bffaa4817a23eb4211a8b33fd4dad199eb5a2d0d23b', '["admin:all", "keyring:rotate", "ledger:verify", "users:manage"]', 1, '2026-11-14T06:28:07Z', '2026-11-14T06:28:07Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, role, role_label, clearance_level, department, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-inspector-01', 'vmarquez', 'vmarquez@aduana.gob.ve', 'Valeria Márquez', 'inspector_aforo', 'Inspectora de Aforo Físico y Documental', 'Nivel 3 — Control Primario Aduanero', 'Gerencia de Aduana Principal La Guaira', 'a36b5fb0747b424c0660977950d73321c72472ffc7234bb2794441c7768d7d36', 'pbkdf2_sha256$310000$c22b3d0d49d7c6fb8563121289530498$6793e2a686adab31806f025fac641333ef5159737826cda2622f440b4d9e6171', '["gateway:process", "explica:inspect", "explica:override", "aforo:validate"]', 1, '2026-11-14T06:28:07Z', '2026-11-14T06:28:07Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, role, role_label, clearance_level, department, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-inspector-02', 'aquintero', 'aquintero@aduana.gob.ve', 'Andrés Quintero', 'inspector_aforo', 'Inspector de Aforo Marítimo', 'Nivel 3 — Control Primario Aduanero', 'Gerencia de Aduana Principal Puerto Cabello', '84bcb4dfd9300888580164b3a286e5793b8ee54e1030391d5a2b8a7ca9fb28a2', 'pbkdf2_sha256$310000$7bf2642ac281154a7f1b64211f9175bb$26a74dfd01c8120ae45f11f3c6eff32c2816ac37c5de1a25bd4a0a46fe03f836', '["gateway:process", "explica:inspect", "aforo:validate"]', 1, '2026-11-14T06:28:07Z', '2026-11-14T06:28:07Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, role, role_label, clearance_level, department, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-cumplimiento-01', 'sherrera', 'cumplimiento@aduana.gob.ve', 'Sofía Herrera', 'oficial_cumplimiento', 'Oficial de Cumplimiento y Habeas Data', 'Nivel 4 — Protección de Datos CRBV', 'Unidad de Cumplimiento Ley de Infogobierno', '48ed613668ab2fa6ec5f13ad4c402ad150b3da6aca939847432892f7d2d892eb', 'pbkdf2_sha256$310000$dad5bd05f14df191832b3e7f71eabdfa$80ed0e4fdf6c81f4c0098ef0e5abdbfc43fd18dd365499f4a8613c09f0d8cbc1', '["guardian:audit", "consent:audit", "ledger:read", "explica:inspect"]', 1, '2026-11-14T06:28:07Z', '2026-11-14T06:28:07Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, role, role_label, clearance_level, department, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-supervisor-01', 'rzambrano', 'supervisor@aduana.gob.ve', 'Ricardo Zambrano', 'supervisor_aduana', 'Supervisor Nacional de Operaciones Aduaneras', 'Nivel 4 — Supervisión Regional', 'Intendencia Nacional de Aduanas', '839982a926b5e67b57ff3e923c99b7a318c2d11b8251807c1aa5336951e93f65', 'pbkdf2_sha256$310000$87aec9988be4e88aad8b573fc017c301$b313826ccdf565686e29f90f646e997efb4b7df22ce0caa9e03375ebbe990e40', '["gateway:process", "explica:override", "ledger:read", "ledger:verify", "canal:write"]', 1, '2026-11-14T06:28:07Z', '2026-11-14T06:28:07Z')
ON CONFLICT(id) DO NOTHING;
