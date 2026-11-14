-- =============================================================================
-- Aduana IA — Seed RBAC y Canales para Cloudflare D1
-- Roles oficiales: analista, administrador, auditor (10 usuarios)
-- Generado automáticamente por scripts/generate_d1_seed.py
-- Zero-Plaintext-PII: cédulas transformadas vía HMAC (blind_citizen_id)
-- Contraseñas protegidas con PBKDF2-HMAC-SHA256 (310,000 iteraciones)
-- Ejecutar:
--   wrangler d1 execute aduana-db --remote --file=seed_d1.sql
-- =============================================================================

-- 1. Roles oficiales RBAC
INSERT INTO roles_aduana (role_id, role_name, description, allowed_tabs_json, default_tab)
VALUES ('analista', 'Analista', 'Módulos asignados: Pasarela, Chat IA y Canal Seguro E2EE.', '["pasarela", "chat", "canal"]', 'pasarela')
ON CONFLICT(role_id) DO NOTHING;

INSERT INTO roles_aduana (role_id, role_name, description, allowed_tabs_json, default_tab)
VALUES ('administrador', 'Administrador de Infraestructura', 'Módulos asignados: Control total perimetral (Todos los módulos).', '["pasarela", "chat", "ledger", "explicabilidad", "canal"]', 'pasarela')
ON CONFLICT(role_id) DO NOTHING;

INSERT INTO roles_aduana (role_id, role_name, description, allowed_tabs_json, default_tab)
VALUES ('auditor', 'Auditor', 'Módulos asignados: Explicabilidad y Ledger inalterable SHA-256.', '["ledger", "explicabilidad"]', 'ledger')
ON CONFLICT(role_id) DO NOTHING;

-- 2. Usuarios RBAC (10 funcionarios)
INSERT INTO usuarios_aduana (id, username, email, full_name, short_name, avatar_text, role, role_label, clearance_level, entity, department, ed25519_key, ed25519_status, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-auditor-01', 'dgonzalez', 'auditor@aduana.gob.ve', 'Deykary González', 'Deykary G.', 'DG', 'auditor', 'Auditora Principal', 'Nivel 4 — Confidencial Estatal', 'Superintendencia Nacional Aduanera / Contraloría GovTech', 'Dirección de Auditoría Algorítmica y Cumplimiento', '0x8F9a...3B42', 'Validada y Activa', '580f475264bb6597910d1799be12bd0f2b729afd8e35d2e873a8d64c0ba397f9', 'pbkdf2_sha256$310000$ebfcd3d69c38b3ee732ba7b2d5fb2a94$91119477f71100796dbcd52c74eb2da000c41432b47d242f245f15df4f1066df', '["Desencriptación de PII autorizada", "Auditoría de Ledger SHA-256", "Inspección de Inferencia GovEval", "Canal E2EE Enclave Seguro"]', 1, '2026-11-14T07:11:31Z', '2026-11-14T07:11:31Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, short_name, avatar_text, role, role_label, clearance_level, entity, department, ed25519_key, ed25519_status, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-auditor-02', 'cmendez', 'cmendez@aduana.gob.ve', 'Carlos Méndez', 'Carlos M.', 'CM', 'auditor', 'Auditor Principal', 'Nivel 4 — Confidencial Estatal', 'Ministerio de Tecnología e Innovación / UNETI', 'División de Auditoría Forense y Ciberseguridad', '0x8F9...3B', 'Validada y Activa', '792e7027d469e9f39bbd412c3244d671e93d0032abeb79523c068c29e1751107', 'pbkdf2_sha256$310000$0a5d9cf9aa6c29a0b4089dbd8a6a2b91$fe44246c081bda1fea354ac567c0e01fe164c793982b7bf6f26ecd1cecfc4233', '["Desencriptación de PII autorizada", "Auditoría de Ledger SHA-256", "Emisión de Dictámenes Vinculantes", "Inspección de Pasarela Local"]', 1, '2026-11-14T07:11:31Z', '2026-11-14T07:11:31Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, short_name, avatar_text, role, role_label, clearance_level, entity, department, ed25519_key, ed25519_status, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-auditor-03', 'lsantander', 'lsantander@aduana.gob.ve', 'Lucía Santander', 'Lucía S.', 'LS', 'auditor', 'Auditora Legal Gov-AI', 'Nivel 3 — Dictamen Jurídico', 'Consultoría Jurídica de Inteligencia Artificial Gubernamental', 'Marco Regulatorio y Transparencia Pública', '0x71D...5E', 'Validada y Activa', 'b0a6502012780e5c01b9574e23dd4863c8c118471f997a0a1530a316370d043b', 'pbkdf2_sha256$310000$0894c8b16e8418def43203b50a24b662$8a4fabdc82c26a3f8f563ee4071ef86eab2e7baa58113b55f3fa312882a2a658', '["Validación de Concordancia Legal ENISA", "Supervisión del Artículo 14 Ley IA", "Firma de Dictamen Vinculante"]', 1, '2026-11-14T07:11:31Z', '2026-11-14T07:11:31Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, short_name, avatar_text, role, role_label, clearance_level, entity, department, ed25519_key, ed25519_status, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-auditor-04', 'cramirez', 'cramirez@aduana.gob.ve', 'Dra. Carmen Ramírez', 'Carmen R.', 'CR', 'auditor', 'Auditora de Cumplimiento y Confidencialidad', 'Nivel 4 — Confidencial Estatal', 'SENIAT / Gerencia de Fiscalización Nacional', 'Departamento de Cumplimiento Normativo', '0xA92...F1', 'Validada y Activa', '9cbe59b0add927c187f6bfa500668f7fa65d29183496c5e1963a64148585b91d', 'pbkdf2_sha256$310000$a09259f48629992c8559845561ec0561$818b7dbbe3f7ccd185e919181af820dfb11ff47c9175e5174be01ae9248eaa83', '["Desencriptación Selectiva Homomórfica", "Custodia de Datos Ciudadanos", "Auditoría de Ledger SHA-256"]', 1, '2026-11-14T07:11:31Z', '2026-11-14T07:11:31Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, short_name, avatar_text, role, role_label, clearance_level, entity, department, ed25519_key, ed25519_status, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-analista-01', 'esalazar', 'analista@aduana.gob.ve', 'Elena Salazar', 'Elena S.', 'ES', 'analista', 'Analista de Operaciones & Solvencias', 'Nivel 2 — Operativo Aduanero', 'Intendencia Nacional de Aduanas / División de Trámites', 'Departamento de Solvencias Fiscales y Aforo', '0x3C4b...9F11', 'Validada y Activa', '17aebaa69ffc1b9b45a90e34c3a4c99a1e71f72ce78a18c7831a3c4dbbebf84d', 'pbkdf2_sha256$310000$d9f2acf6e0e12063840c6f80d5aa68ce$9ac0789a72b1a0737cb7019f4769370a70e505e97543e438a0fb77f2bfb7e915', '["Consulta de Pasarela en Tiempo Real", "Sanitización Homomórfica de PII", "Evaluación de Explicabilidad y Equidad", "Revisión de Declaraciones Aduaneras"]', 1, '2026-11-14T07:11:31Z', '2026-11-14T07:11:31Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, short_name, avatar_text, role, role_label, clearance_level, entity, department, ed25519_key, ed25519_status, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-analista-02', 'lparedes', 'lparedes@aduana.gob.ve', 'Luisana Paredes', 'Luisana P.', 'LP', 'analista', 'Analista de Aforo Documental', 'Nivel 2 — Operativo Aduanero', 'Intendencia Nacional de Aduanas / Aduana La Guaira', 'División de Trámites y Encomiendas', '0x4D2a...8E01', 'Validada y Activa', '31a9639ef47fe0fb32bde1437d25e2c70b7091d7212b4f7cbf96e64799f1d9b0', 'pbkdf2_sha256$310000$0c4a1cd3ac00ef9bcb7f9a1c82f3b58a$e67fe8dec00660855f5d76b6a8681d8f7c4a41f35aaecd8284c818de96ce8800', '["Consulta de Pasarela en Tiempo Real", "Sanitización Homomórfica de PII", "Gestión de Peticiones Ciudadanas"]', 1, '2026-11-14T07:11:31Z', '2026-11-14T07:11:31Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, short_name, avatar_text, role, role_label, clearance_level, entity, department, ed25519_key, ed25519_status, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-analista-03', 'aquintero', 'aquintero@aduana.gob.ve', 'Andrés Quintero', 'Andrés Q.', 'AQ', 'analista', 'Analista de Guardia Aduanera', 'Nivel 2 — Operativo Aduanero', 'Intendencia Nacional de Aduanas / Puerto Cabello', 'Centro de Comando Operativo Aduanero', '0x5B1c...7D22', 'Validada y Activa', 'a36b5fb0747b424c0660977950d73321c72472ffc7234bb2794441c7768d7d36', 'pbkdf2_sha256$310000$ef5f7d381a7121cd6b0991d49d451d7d$c3dd7c16e38d13df9d89fcad0c6c2fecfeb9b7814b7f2ee4515bd6cb8d989f68', '["Consulta de Pasarela en Tiempo Real", "Sanitización de PII con Shield", "Consulta de Constancias de Solvencia"]', 1, '2026-11-14T07:11:31Z', '2026-11-14T07:11:31Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, short_name, avatar_text, role, role_label, clearance_level, entity, department, ed25519_key, ed25519_status, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-analista-04', 'vmarquez', 'vmarquez@aduana.gob.ve', 'Valeria Márquez', 'Valeria M.', 'VM', 'analista', 'Analista de Exoneraciones y Becas', 'Nivel 2 — Operativo Aduanero', 'Intendencia Nacional de Aduanas / Operaciones', 'Coordinación de Beneficios Institucionales', '0x6E3d...4A19', 'Validada y Activa', '84bcb4dfd9300888580164b3a286e5793b8ee54e1030391d5a2b8a7ca9fb28a2', 'pbkdf2_sha256$310000$e0704e376a3377bd3ec9818c38e34c4c$e37a5c9f26851e77b3a9f1c1766388e464fe74ebd87e4c9c07803a6bcdd96555', '["Consulta de Pasarela en Tiempo Real", "Sanitización Homomórfica de PII", "Revisión de Declaraciones Aduaneras"]', 1, '2026-11-14T07:11:31Z', '2026-11-14T07:11:31Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, short_name, avatar_text, role, role_label, clearance_level, entity, department, ed25519_key, ed25519_status, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-admin-01', 'mvivas', 'admin@aduana.gob.ve', 'Marcos Vivas', 'Marcos V.', 'MV', 'administrador', 'Administrador de Infraestructura & Ciberseguridad', 'Nivel 5 — Soberanía Crítica GovTech', 'Centro Nacional de Ciberseguridad / Red Nacional de Integridad', 'Coordinación Nacional de Infraestructura Soberana', '0xE4A1...77C0', 'Custodio Maestro Gov-Ed25519', '16629ffe5cc344e6255944fba676d5d9f8c5a1f8752883f195f03739a6ccf58e', 'pbkdf2_sha256$310000$eeccb467bd0a8a7a06474f64f8b16d26$d6bbd2b08f01d21e2228c63c7123164442582ad04f2051c40bd4394b6618f427', '["Control Total de Nodos y Consenso", "Simulación de Manipulación y Cuarentena", "Gestión de Claves Criptográficas y Enclaves", "Supervisión Perimetral ISO/IEC 27001"]', 1, '2026-11-14T07:11:31Z', '2026-11-14T07:11:31Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO usuarios_aduana (id, username, email, full_name, short_name, avatar_text, role, role_label, clearance_level, entity, department, ed25519_key, ed25519_status, blind_citizen_id, password_hash, permissions_json, is_active, created_at_utc, updated_at_utc)
VALUES ('usr-admin-02', 'rbriceno', 'rbriceno@aduana.gob.ve', 'Rafael Briceño', 'Rafael B.', 'RB', 'administrador', 'Administrador de Enclaves y KeyRing', 'Nivel 5 — Soberanía Crítica GovTech', 'Centro Nacional de Ciberseguridad / Red de Integridad', 'Seguridad Ofensiva y Enclaves Confinados', '0xF109...2B88', 'Custodio Maestro Gov-Ed25519', '839982a926b5e67b57ff3e923c99b7a318c2d11b8251807c1aa5336951e93f65', 'pbkdf2_sha256$310000$ca7aa40ec743133906eda052dbb61eea$635729d7b71310267ec5d22a72a4c13939397a880b3f190497e3bbc9304a3f29', '["Control de Nodos Perimetrales", "Simulación de Manipulación Criptográfica", "Aislamiento Preventivo de Memoria", "Gestión de Certificados Homomórficos"]', 1, '2026-11-14T07:11:31Z', '2026-11-14T07:11:31Z')
ON CONFLICT(id) DO NOTHING;

-- 3. Canales institucionales del Canal Seguro E2EE
INSERT INTO canal_seguro_channels (id, name, description, created_at_utc)
VALUES ('auditoria-general', 'auditoria-general', 'Canal general de trazabilidad, concordancia de expedientes y dictámenes soberanos.', '2026-11-14T07:11:31Z')
ON CONFLICT(id) DO NOTHING;

INSERT INTO canal_seguro_channels (id, name, description, created_at_utc)
VALUES ('alertas-ledger', 'alertas-ledger', 'Monitoreo de desajustes hash SHA-256, firmas no concordantes y aislamiento de nodos.', '2026-11-14T07:11:31Z')
ON CONFLICT(id) DO NOTHING;
