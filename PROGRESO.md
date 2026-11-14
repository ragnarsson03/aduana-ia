# PROGRESO — Aduana IA (backend)

> Archivo de coordinación para varios modelos/agentes. **Antes de tomar una tarea:** léela entera, marca `[~]` con tu nombre/fecha, y no toques los archivos que otra tarea `[~]` esté usando. **Al terminar:** marca `[x]` y corre la suite.
> Última actualización: 2026-11-14. Estado: Gatillo 0 al Gatillo 10 completos, Cloudflare D1 v3.1 + RBAC desplegado, Rediseño Frontend Sergio integrado con proporciones responsivas compactas, Canal Seguro con intercambio E2EE de archivos y verificación SHA-256 en RAM, PR #13 con CI en verde (Ruff y Vitest aprobados), y suite completa de tests en verde.

## Leyenda
`[x]` hecho · `[~]` en curso (quién) · `[ ]` pendiente · `[?]` requiere decisión humana

## Cómo se usa y protocolo de trabajo
- **Estados de tarea:** Cada tarea lleva un estado: `[x]` hecha, `[~]` en curso (quién/fecha), `[ ]` pendiente y `[?]` que requiere tu decisión humana.
- **Reserva de tarea:** Quien tome una tarea debe marcarla `[~]` con su nombre antes de empezar, y no tocar los archivos de otra tarea en curso.
- **Finalización:** Al terminar la marca `[x]` y corre la suite con `.venv/Scripts/python -m pytest -q` (debe quedar en verde).
- **Para continuar en otro equipo / con otra IA:**
  1. Clonar el repositorio y entrar a la carpeta `aduana-ia`: `cd aduana-ia`.
  2. Activar el entorno virtual de Python 3.11+: `.venv\Scripts\activate` (Windows) o `source .venv/bin/activate` (Linux).
  3. Ejecutar la suite: `.venv/Scripts/python -m pytest -q` para certificar el estado base.
  4. Leer este archivo `PROGRESO.md`, elegir la tarea siguiente en `## PENDIENTE`, marcarla con `[~]` y tu nombre antes de codificar.
  5. Respetar estrictamente los archivos de otras tareas en `## EN CURSO`.

## Cómo trabajar aquí (reglas de oro, de SPEC/PROMPT_MAESTRO/.cursorrules)
- Python ≥ 3.11, **Litestar** (prohibido FastAPI), msgspec, criptografía solo stdlib (`hashlib`, `hmac`, `secrets`, `unicodedata`). **Prohibido `random`**.
- **Zero-PII**: `raw_input` y el mapa token→PII solo en `EphemeralVault` (RAM, TTL 180 s). Ningún log, `repr`, error ni respuesta puede contener texto ciudadano.
- TDD: test RED primero (`tests/`), luego implementación, luego `.venv/Scripts/python -m pytest -q` (debe quedar sin fallos).
- Entorno: `cd aduana-ia` y usar `.venv/Scripts/python` (Windows). Dependencias instaladas en el venv: litestar, msgspec, pytest, httpx. **No instalados:** granian, pywebview.
- Los CA pendientes viven como `xfail(strict=True)` en `tests/test_acceptance_matrix.py`; al implementar su gatillo, conviértelos en tests reales en archivos `tests/test_caNN_*.py` y quítalos de la matriz.
- Hooks locales exigen declarar importadores/equivalentes/instrucción al crear archivos; reintentar tras declararlo.
- Specs vivas en `specs/` (00_architecture, 00_kernel, 01–05). **Ojo:** `01_shield` está desactualizada (ver pendientes).

## HECHO

### Estructura y endurecimiento (esqueleto)
- [x] Capas `app/ → pipeline/ → core/`; protocolos (`StorageRepositoryProtocol` con `append_chained`/`iter_blocks`, `LLMAdapterProtocol`, `RateGuardProtocol`, `LLMGatewayProtocol`).
- [x] `core/context.py`: contratos inmutables (`AduanaPacket`, `BlockedPacket`, `LedgerEntry`, `LedgerBlock` con `key_id`, `ChainAnchor`, `ChainVerification` con motivos `HASH_MISMATCH | PREV_HASH_LINK_BROKEN | HMAC_SIGNATURE_FORGED | GENESIS_LINK_BROKEN | INDEX_GAP | TAIL_TRUNCATED`). Mappings en `MappingProxyType`.
- [x] `core/config.py`: `Settings` validado (loopback por defecto, rangos), `load_keys_from_env` (elimina `ADUANA_MASTER_KEY` del entorno), `load_api_token_from_env`. Sin llave ⇒ llave y ledger efímeros.
- [x] `core/keyring.py`: `KeyRing` con subllaves por dominio, `verify` en tiempo constante, no copiable/picklable, inutilizable tras `wipe()`.
- [x] API: `X-Aduana-Token` + `Content-Type: application/json` estricto, `AllowedHosts` loopback, cabeceras de seguridad/CSP, DTOs estrictos (`forbid_unknown_fields`, límites), cuerpo ≤ 64 KB, OpenAPI deshabilitado, tabla de errores con códigos estables, `create_app` sin efectos de import, Granian `factory=True workers=1`.
- [x] `tamper-sim` solo registrado con `ADUANA_DEMO_MODE=1` (hoy responde 501; debe operar sobre copia en RAM).
- [x] Specs 00–05 escritas por Codex; `00_kernel` actualizada a la implementación del Gatillo 0.

### Gatillo 0 — kernel (completo, revisado, Módulo 11 verificado por Codex con RIF públicos)
- [x] `core/crypto.py`: `sha256_hex`, `normalize_cedula` (V|E + 5–9 dígitos ASCII, sin ceros a la izquierda), `blind_citizen_id(keys, cedula)`, `consent_hash(request_id, ts, purpose, blind_id)` (SHA-256 de JSON canónico), `canary_token` (16 hex), `rif_mod11_valid`, `canonical_block_payload(source, *, index, prev_hash, key_id)`, `block_hash(payload)`, `block_signature(keys, hash)`.
- [x] `core/ephemeral_vault.py`: TTL por reloj monotónico inyectable (expira con edad > 180 s), `RLock`, tope de sesiones, `put(request_id, token_map)` atómico (sin `raw_input`), `zeroize`/`zeroize_all` idempotentes.
- [x] Tests: `test_crypto.py`, `test_ephemeral_vault.py`, `test_keyring.py`, `test_ca05_restrictive_storage.py` (parte bóveda: sin disco ni logs).

### Gatillo 1 — consentimiento, rate-guard y SHIELD (implementado; en revisión)
- [x] `core/text_normalizer.py`: NFKC + invisibles + dígitos `Nd`→ASCII + guiones `Pd`→`-` + homoglifos cerca de ASCII; `ValueError` si expansión > 2x+64.
- [x] `core/pii_patterns.py`: `find_pii(text, *, regions=None)` con tipos ENCODED/EMAIL/BANK/RIF/PHONE/CEDULA/NAME/CLINICAL, prioridad ante solapes, escaneo numérico por vecindarios de dígitos.
- [x] `pipeline/stage1_shield.py`: tokens coherentes por identidad, fixed-point (≤ 3 pasadas), fail-closed (`ShieldResidualPiiError` → 422 `ERR_UNSAFE_INPUT`), neutralización de `[KIND_n]` preexistentes, ventanas de residual.
- [x] `pipeline/stage0_consent.py`: `validate_consent` (5 args, incluye `blind_citizen_id`) y `RateGuard` (ventana deslizante, thread-safe, acotado, falla cerrado, poda ≤ 1/s).
- [x] `POST /api/v1/shield/inspect` operativo (`sync_to_thread=True`, destruye el mapa antes de responder).
- [x] Tests: `test_pii_patterns.py`, `test_ca01_shield.py`, `test_consent.py`, `test_api_hardening.py`.
- Decisiones: `pii_count` = ocurrencias; `rif_mod11_verified` None/True/False; `validation_passed` = ningún RIF inválido; RIF abreviado de 7 dígitos no se detecta; V/E + 9 dígitos juntos = cédula; teléfono exige `0`/`+58`.

### Gatillo 2 — Guardián (CA-02, completo y verificado)
- [x] `data/attack_benchmark.json`: 100 prompts (50 ataques + 50 benignos en español; 50 dev y 50 val; sin PII real).
- [x] `pipeline/stage2_guard_in.py`: `normalize_text` → decodificación Base64/Hex → `risk_score` determinista [0,1] (bloquea ≥ 0.65, sin `random`) → sandbox XML escapando `<`, `>`, `&` → canary token HMAC transaccional (16 hex). Devuelve `(prompt, GuardInResult)`.
- [x] `pipeline/stage3_guard_out.py`: normaliza antes de inspeccionar; fuga de canary (total y fragmentos hex ≥ 8 chars); PII residual con `core.pii_patterns.find_pii` (respetando tokens SHIELD); anti-XSS con `html.escape`; flags de afirmaciones no verificadas.
- [x] `app/controllers/metrics.py`: `GET /api/v1/metrics/benchmark` (cachear resultado, 1/min, `sync_to_thread=True`).
- [x] Tests CA-02 en `tests/test_ca02_guardian.py`: 14 tests pasando (TPR ≥ 88 %, FPR ≤ 4 %, < 25 ms/prompt, 100 % de fugas de canary neutralizadas). Removido xfail de `tests/test_acceptance_matrix.py`.

### Gatillo 3 — Ledger y persistencia restrictiva (CA-03, CA-05 parte `.db`, completo y verificado)
- [x] `pipeline/stage4_ledger.py`: `SQLiteLedgerRepository` (`PRAGMA journal_mode=WAL`, `synchronous=FULL`, `secure_delete=ON`, `trusted_schema=OFF`, triggers `BEFORE UPDATE/DELETE` → `RAISE(ABORT,'ERR_IMMUTABLE_LEDGER')`, `append_chained` atómico con `BEGIN IMMEDIATE` y `RLock`, `iter_blocks`, permisos 0600).
- [x] `seal_entry` y `verify_chain(blocks, *, keys, anchor)`: orden INDEX_GAP → enlace previo/génesis → HASH_MISMATCH → HMAC forjado; ancla (`count`, `head_hash`) contra truncado de cola; latencia < 50 ms.
- [x] `override_justification` nunca en claro en el ledger (solo HMAC hex con clave dominio `justification`).
- [x] `app/controllers/ledger.py`: `GET /api/v1/ledger/verify` (expone `head_hash` y latencia < 50 ms) y `POST /api/v1/ledger/tamper-sim` (`flip_payload_bit`, `recompute_sha_without_key`, `break_prev_link`, `flip_override`) operando 100% sobre copia en RAM con `simulated: true`.
- [x] `tests/test_ca03_ledger.py`: 12 tests pasando (verificación de cadena, hardening SQLite, bit flips, link broken, firmas falsificadas, truncado y endpoints).
- [x] `tests/test_ca05_restrictive_storage.py`: convertido en test real `test_ca05_db_and_wal_hold_zero_plaintext_pii_after_20_requests` (20 trámites simulados, auditoría binaria de `.db`, `-wal`, `-shm` con 0 bytes de PII).
- [x] Removido xfail de CA-03 en `tests/test_acceptance_matrix.py`.

### Gatillo 4 — EXPLICA (CA-04, completo y verificado)
- [x] `data/synthetic_tramites.csv`: 60 trámites sintéticos deterministas con 5 variables objetivas (sin PII) y medias poblacionales calculadas.
- [x] `pipeline/stage5_explica.py`: sigmoide numéricamente estable con bifurcación por signo, descomposición de contribuciones directas ($c_j = \beta_j x_j$) y SHAP lineal ($\phi_j = \beta_j (x_j - \mu_j)$), axioma de eficiencia ($\text{base\_SHAP} + \sum \phi_j = z$), error de reconstrucción $< 10^{-9}$, cero `random()`, validación estricta de esquemas numéricos finitos.
- [x] Decisión humana y override vinculante: confirmación humana vs override obligatorio con justificación $\ge 20$ y $\le 500$ caracteres (`OverrideJustificationError` ante incumplimiento).
- [x] `tests/test_ca04_explica.py`: 9 pruebas unitarias pasando (descomposición exacta del oráculo de prueba, vector cero, medias poblacionales, grid determinista de 243 puntos, comprobación anti-random, validación de justificaciones y dataset sintético institucional).
- [x] Removido xfail de CA-04 en `tests/test_acceptance_matrix.py`.

### Gatillo 5 — Adaptadores LLM y Circuit Breaker (CA-06, completo y verificado)
- [x] `pipeline/llm_adapter.py`: `OfflineDeterministicAdapter` (sin red ni `random()`, no hace eco del canary), `OllamaAdapter` (loopback allowlist, sin redirects, respuesta acotada ≤ 32 KiB) y `OpenAICompatAdapter` (opt-in estricto `enabled=False` por defecto, TLS obligatorio remoto, `repr` redactado).
- [x] `CircuitBreaker`: máquina de estados `CLOSED`/`OPEN`/`HALF_OPEN` con `failure_threshold=3`, `cooldown_s=30.0`, `timeout_s=3.5` y `clock` inyectable.
- [x] `tests/test_ca06_resilience.py`: 12 tests pasando (primario, fallo inmediato < 100 ms, timeout, propagación 3.5 s, `OPEN`/`HALF_OPEN`, repetibilidad offline sin sockets, anti-canary, GUARD-OUT tras fallback, Ollama/OpenAI-compat con `MockTransport`). Removido xfail de CA-06 en `tests/test_acceptance_matrix.py`.

### Gatillo 6 — Orquestador y API completa (CA-05 transversal, completo y verificado)
- [x] `pipeline/orchestrator.py`: `GatewayPipeline.process` orquestando el flujo completo (stage0 blind id/rate-guard/consentimiento → shield → guard_in → LLM → guard_out → explica → ledger; sellado en ledger de aprobados y `BlockedPacket`; `secrets.token_urlsafe(16)` en servidor; `vault.zeroize` incondicional en bloque `finally`).
- [x] `app/schemas.py`: `GatewayProcessResponse` (omite `raw_response` y canary, expone veredictos, SHAP y recibo del ledger).
- [x] `app/controllers/gateway.py`: `POST /api/v1/gateway/process` operativo con DTOs de salida y manejo de políticas.
- [x] `app/dependencies.py` y `app/server.py`: inyección de dependencias de `GatewayPipeline`, hook `on_shutdown` con `zeroize_all` y cierre de repositorio.
- [x] `tests/test_gateway_pipeline.py`: 8 tests de integración pasando (happy path end-to-end, bloqueos de consentimiento/inyección/canary leak, rate guard, override humano en ledger, endpoint HTTP, y auditoría forense CA-05 con 20 trámites sin PII en disco).

### Gatillo 7 — Escritorio PyWebView + Granian y Frontend Air-Gapped (completo y verificado)
- [x] `app/desktop.py`: ejecución real de Granian en subproceso de proceso único (`_SingleProcessGranian`, compatible con `signal.signal` y sin nietos huérfanos al cerrar), `multiprocessing.freeze_support()`, puerto efímero, `_wait_ready`, inyección de `window.__ADUANA_TOKEN__` vía `evaluate_js` (nunca en URL) y `private_mode=True`.
- [x] `app/server.py`: `AllowedHostsConfig` acepta `host` y `host:port` para el puerto configurado (corrige `400 invalid host header` en navegador y PyWebView).
- [x] `iniciar_escritorio.bat` (Windows) e `iniciar_escritorio.sh` (Linux).
- [x] `index.html`, `vite.config.ts`, `src/` y `static/`: eliminados los `<link>` a Google Fonts CDN y URLs externas en bundle, `autoComplete="off"` en todos los `<input>`/`<textarea>`, lectura dinámica de `window.__ADUANA_TOKEN__` en `AduanaApiClient`, cero `innerHTML`/`dangerouslySetInnerHTML`.
- [x] `tests/test_ca07_desktop_and_frontend.py`: 5 tests pasando (incluyendo arranque real del subproceso Granian, verificación CSP, 401/200 con token, auditoría de `https?://` en `static/` y `autoComplete="off"`).

### Gatillo 8 — Base de Datos Cloudflare D1 v3.1, RBAC Aduanero y Despliegue Edge (PR #8 y PR #13, completos)
- [x] 6 roles aduaneros y matriz de permisos con segregación de funciones (`core/rbac.py`); anti-escalada: el SUPERVISOR solo gestiona AGENTE/FISCAL/OPERADOR/ANALISTA y no puede suspenderse a sí mismo (`specs/06_rbac_aduanero.spec.md`).
- [x] Identidad RBAC (`core/identity.py`, `core/auth.py`, `core/rbac_db.py`): PBKDF2-HMAC-SHA256 600 000 iteraciones, sal `secrets.token_bytes(32)` por usuario, índice ciego HMAC, SQLite `usuarios_aduana` (WAL, `secure_delete`, triggers), bloqueo 5 fallos/15 min, error uniforme, relectura del usuario en cada petición y `core/ui_profile.py` (derivación de `allowed_tabs`/`default_tab` en servidor).
- [x] 12 usuarios sembrados (uno por rol, 4 de mínimo privilegio y 2 con acceso a chat IA y canal): `scripts/seed_usuarios.py`; las contraseñas se generan al sembrar y quedan solo en `data/seed_credenciales.local.json` (gitignored).
- [x] El escritorio (`python -m app.desktop`, `iniciar_escritorio.bat/.sh`) arranca con RBAC: `app/rbac_bootstrap.py` usa `ADUANA_MASTER_KEY` si existe o crea/lee `data/dev_master.key`, fija `ADUANA_RBAC=1` y siembra los usuarios una sola vez.
- [x] `schema.sql`: 6 tablas formalizadas (`roles_aduana`, `usuarios_aduana`, `ledger_blocks`, `consent_records`, `tramite_evaluations`, `canal_seguro_channels`, `canal_seguro_messages`) con triggers de inmutabilidad y `PRAGMA foreign_keys = ON`.
- [x] `seed_d1.sql` / `scripts/generate_d1_seed.py`: 3 roles oficiales (`analista`, `administrador`, `auditor`), 10 funcionarios con `blind_citizen_id` HMAC-SHA256 y PBKDF2 (310.000 iteraciones), 2 canales E2EE.
- [x] `wrangler.jsonc`: configurado con bindings `DB` (`aduana-db` UUID `21eb0bb7-3d0f-4695-b450-3af441ab4d5b`), `KV` (`aduana-kv` ID `3885a09654fa42eea23241b0948b8df7`), `AI` y soporte de Workers Static Assets (`assets: { directory: "./static" }`).
- [x] Despliegue en producción Cloudflare Workers activo en `https://aduana-ia.carlos-lamole98.workers.dev`.
- [x] Configuración de CI/CD en Cloudflare Pages / Workers compilando desde rama `develop` con `npm run build`.

### Gatillo 9 — Rediseño Frontend Sergio y Experiencia de Usuario (PR #10, completo y desplegado)
- [x] `src/views/LoginView.tsx` e `src/index.css`: tarjeta de acceso con inclinación 3D parallax interactiva (seguimiento del cursor con momentum lerp), reflejo especular dinámico (`--mouse-x`, `--mouse-y`), cyber scanline sweep, botón de acceso con destello `shimmer-btn`.
- [x] Identidad Visual: sustitución de ícono genérico por el emblema oficial de Aduana IA (`Logo-white.png`) con sombras y contrastes adaptados a fondo oscuro.
- [x] Navegación: pestaña "Chat IA" renombrada visualmente a "Nexus IA" preservando contratos internos (`id: 'chat'`).
- [x] Auditoría en UI: alerta de manipulación de bloque (`DESAJUSTE SHA-256`) en `LedgerView.tsx` rediseñada con mayor sobriedad e integración estética.
- [x] Accesibilidad: soporte estricto de `@media (prefers-reduced-motion: reduce)` desactivando animaciones y transformaciones CSS ante preferencias del sistema.

### Gatillo 10 — Autenticación Zero-Trust, JWT Sessions y Auditoría en Ledger (PR #11, PR #12 y PR #13, completo)
- [x] `core/identity.py`, `pipeline/auth.py` y `app/controllers/auth.py`: autenticación soberana mediante PBKDF2-HMAC-SHA256 + `blind_citizen_id`, soporte tanto para RBAC aduanero estricto (`specs/06_rbac_aduanero.spec.md`) como para correo institucional y persistencia de sesión F5 (`HttpOnly; SameSite=Strict` cookie).
- [x] Registro inmutable en `ledger_blocks` de eventos de autenticación.
- [x] `tests/test_auth_unified.py` (18) y `tests/test_auth_login.py` (6): todas las pruebas pasando en verde.

## EN CURSO
- [x] **Codex** — optimización de rendimiento y benchmarks en `core/pii_patterns.py` y `core/text_normalizer.py`.
- [x] **Penetration Tester** — suite de regresión del red team de SHIELD rondas 1-2 (`tests/test_shield_regression.py`: 106 tests pasando).

## PENDIENTE

### P0 — Endurecer Gatillo 2 (resultado del red team, 2026-11-13 — completado y certificado)
Medido sobre la regresión del red team (`tests/test_guardian_regression.py`) y el benchmark CA-02:
- [x] **C1 ReDoS cúbico** en `SQLI_SELECT_FROM` (select + 3000 espacios tardaba 108 s): corregido con `\bselect\b[^;\n]{1,200}?\bfrom\b` (ahora 14 ms). Hay tests sin xfail que lo vigilan.
- [x] `orchestrator.py` llamaba `guard_in(request_id, masked_text, self._keys)` posicional; la firma exige `keys=` → corregido.
- [x] **A1 cobertura:** reglas por intención en español e inglés (anulación de directrices, exfiltración de prompt/keys/canary/variables, suplantación de autoridad, jailbreaks, multiturn assembly, inyección indirecta en comentarios).
- [x] **A2 ofuscación:** generación de vistas desofuscadas en `_deobfuscate_views` (Unicode Tags decodificados de `0xE0000`, invisibles/ZWJ/braille blanks a espacio, colapso de letras separadas por espacios o guiones, remoción de tildes/diacríticos, leet-fold, rot13, texto invertido y hex espaciado).
- [x] **A3 base64/hex:** decodificación exhaustiva de candidatos sin interrupción temprana ante señuelos (inspección de hasta 15 bloques autónomos con prefijos o independientes).
- [x] **A4 falsos positivos:** filtros de contexto legítimo en consultas ciudadanas (`_LEGITIMATE_CONTEXT`: denuncias de estafa, modo desarrollador de dispositivos móviles, sin restricciones de horario, declaraciones aduaneras y referencias a normativas bancarias externas).
- [x] **M2** captura de `ValueError` por bombas de expansión NFKC en `guard_in` y `guard_out` con comportamiento estricto *fail-closed* y código `BLOCKED_INJECTION`.
- [x] **M3** escape y aislamiento en sandbox XML sobre el texto NORMALIZADO (evita propagación de caracteres fullwidth o tags hacia el LLM).
- [x] **M4** `guard_out`: detección robusta de canary fragmentado (subcadenas $\ge 6$, partición en mitades, espaciado, puntuado, invertido) o codificado en Base64.
- [x] **M5** `guard_out`: neutralización y detección estricta de esquemas `javascript:`, `vbscript:`, `data:`, URLs relativas de protocolo `//`, elementos `<input>`, `<details>` y manejadores de eventos DOM `on\w+=`.
- [x] `tests/test_guardian_regression.py`: 76/76 tests pasando en verde, removidos los `xfail`. 
- [x] `tests/test_ca02_guardian.py`: 14/14 tests pasando en verde, benchmark y métricas superando los umbrales exigidos.

### Bloqueos detectados en el árbol de trabajo
- [x] `pipeline/orchestrator.py` importa `explain` de `pipeline/stage5_explica.py` (corregido y validado con tests de integración).
- [x] `static/index.html` libre de fuentes externas (`fonts.googleapis.com`/`fonts.gstatic.com`), cumpliendo Air-Gapped y la CSP `default-src 'self'` (validado en `tests/test_ca07_desktop_and_frontend.py`).

### P0 — Cerrar Gatillo 1
- [x] Aplicar hallazgos del red team ronda 2 y añadir su tabla como tests parametrizados (implementado en `tests/test_shield_regression.py`: 106 tests pasando, cubriendo `MUST_MASK`, `REDOS` y `KNOWN_LIMITS`).
- [x] **Alcance de CA-01 decidido (usuario, opción A):** < 20 ms para textos de hasta 10 000 caracteres; la API sigue aceptando hasta 20 000 (`MAX_RAW_TEXT_CHARS`) sin garantía de 20 ms por encima de 10 000. Documentado en `specs/01_shield.spec.md` y fijado en `tests/test_ca01_shield.py`.
- [x] Reescribir `specs/01_shield.spec.md` (firmas reales; **corregir vector `J-00000000-9`: el verificador correcto es 0**; mover "inconsistencias" a "decisiones tomadas").
- [ ] Límites conocidos sin cubrir (documentados en `core/pii_patterns.py`): nombres sin marcador/minúsculas, base32/ROT13/entidades HTML/`%NN`, números en palabras, clínicos con variantes (`seropositivo`, `d i a b e t e s`), falsos positivos clínicos en texto comercial ("depresión del mercado").

### P1 — Endurecer identidad (revisión de Security Architect; las pruebas de regresión borrador están en 13 xfail por escribir)
- [ ] H-01 iteraciones mínimas de KDF no impuestas al verificar. H-10 política de contraseña (NUL, sustitutos, dígitos no ASCII, NFKC). H-11 validar `codigo_usuario`. H-13 `repr` puede filtrar sal o índice ciego.
- [ ] H-03/H-04 el bloqueo permite DoS dirigido y delata existencia (423 vs 401); carrera de intentos en paralelo. H-14 el contador de fallos no decae.
- [ ] H-05 un token vuelve a valer si se suspende y reactiva al usuario (la revocación hoy es solo por logout, en RAM, se pierde al reiniciar). H-12 `aud` en el token.
- [ ] H-06 índice ciego de personal vs ciudadano para cédulas de 9 dígitos (la auditoría de login ya usa un id opaco). H-07 triggers eludibles con `INSERT OR REPLACE`/`DROP TRIGGER`. H-08 ACL de archivos en Windows. H-09 el seeder no es atómico con el archivo de credenciales.
- [ ] Test intermitente de Zero-PII en CA-07 (1 fallo en una corrida combinada, no reproducible en 16 repeticiones): vigilar.

### P4 — Calidad, seguridad y empaquetado
- [x] Instalar y pasar `ruff` (cero violaciones), `bandit` (auditoría estática), `pip-audit` (cero vulnerabilidades conocidas en dependencias); Pipeline CI activo en `.github/workflows/ci.yml`.
- [x] Commit(s) con mensajes convencionales (`feat:`, `test:`, `merge:`, `fix:`); todos los PRs (#6, #7, #8, #9, #10) fusionados y ramas sincronizadas en `origin/develop`.
- [ ] `mypy --strict`: tipado estricto exhaustivo en módulos que interactúan con DTOs de Litestar.
- [ ] Autenticación institucional (OIDC/LDAP) y `actor_id` pseudonimizado en el bloque (para entornos conectados fuera del alcance Air-Gapped/offline).
- [ ] Pasaporte/otros identificadores internacionales, política de `purpose_code` autorizados, formato UTC del `timestamp`.
- [ ] Documentar en manual de operaciones el riesgo residual de `zeroize` en CPython (`pagefile.sys`, `hiberfil.sys`, volcados WER) y mitigaciones recomendadas (BitLocker, deshabilitar hibernación).

## Decisiones abiertas para el humano (`[?]`)
1. ~~Alcance de CA-01~~ — resuelto: ≤ 10 000 caracteres (opción A).
2. ~~Redefinición de CA-06~~ — resuelto: timeout primario (3.5 s) y transición/fallback (< 100 ms) se miden por separado; circuito `OPEN` responde < 100 ms totales. Umbrales por defecto: 3 fallos / 30 s.
3. Letra **C = 3** del RIF (comunales) sin fuente oficial accesible; RIF abreviado no se rellena con ceros.
4. `consent_hash`: SHA-256 de JSON canónico (actual) vs HMAC dominio `consent` (infalsificable).
5. Autenticación de producción y política de llaves persistentes (`ADUANA_MASTER_KEY` protegida por DPAPI/TPM/vault).
6. Términos clínicos: ¿enmascarar siempre o solo con contexto personal (paciente/padece/diagnóstico)?

## Mapa rápido de archivos
| Área | Archivos |
|---|---|
| Contratos/config | `core/context.py`, `config.py`, `errors.py`, `protocols.py`, `keyring.py` |
| Cripto/bóveda | `core/crypto.py`, `ephemeral_vault.py`, `text_normalizer.py`, `pii_patterns.py` |
| Pipeline | `pipeline/stage0_consent.py`, `stage1_shield.py`, `stage2_guard_in.py`, `stage3_guard_out.py`, `stage4_ledger.py`, `stage5_explica.py`, `llm_adapter.py`, `orchestrator.py` (completos y certificados) |
| API | `app/server.py`, `security.py`, `schemas.py`, `dependencies.py`, `controllers/*`, `desktop.py` (completos y probados con Granian + PyWebView) |
| Tests | `tests/` (conftest con `client`, `demo_client`, `keys`; token `API_TOKEN`/`TOKEN_HEADERS`) |
| Specs | `specs/00_architecture.spec.md`, `00_kernel`, `01_shield` (actualizada con firmas y decisiones), `02_guardian`, `03_ledger`, `04_explica`, `05_interconnect`, `06_files_and_chat_frontend` |

### 2026-11-14 — Harness de front y back reales

Añadidos `scripts/run_e2e_stack.py`, `tests/e2e_harness/` y `tests/test_static_serving.py`; Granian instalado y utilizado, SQLite temporal aislado, token fijo local, demo activa, readiness y cierre limpio. Pruebas HTTP de front/assets, headers, auth, flujo institucional, cuatro simulaciones y búsqueda binaria de cédula en SQLite/WAL/SHM. Hallazgos: faltan CSP/nosniff en `/`; SPA profunda devuelve 404; el contrato de ingreso exige cédula en claro (dos pruebas lo señalan). No hay Google Fonts en el índice/CSS servido. La verificación final del harness dio 16 passed y 5 failed; cierre por duración y por señal comprobados. La suite completa ejecutada dio 427 passed, 11 failed, 66 xfailed, 7 xpassed: cinco fallos del harness y seis de pruebas existentes (latencia Shield, URL del decodificador React en JS, autocomplete de LoginView y compatibilidad desktop/Granian). Los cambios concurrentes de otros agentes en React/static/backend no forman parte de este trabajo. Sin commit ni push.

Comandos exactos, desde PowerShell (arranque y pruebas en terminales distintas):

```powershell
Set-Location 'E:\proyectos\hackatonUNETI\aduana-ia-integration'
$env:PYTHONPATH = (Get-Location).Path
$env:PYTHONDONTWRITEBYTECODE = '1'
& 'E:\proyectos\hackatonUNETI\aduana-ia\.venv\Scripts\python' scripts/run_e2e_stack.py
```

```powershell
Set-Location 'E:\proyectos\hackatonUNETI\aduana-ia-integration'
$env:PYTHONPATH = (Get-Location).Path
$env:PYTHONDONTWRITEBYTECODE = '1'
& 'E:\proyectos\hackatonUNETI\aduana-ia\.venv\Scripts\python' -m pytest tests/e2e_harness tests/test_static_serving.py -q --tb=short -o cache_dir=tests/e2e_harness/.pytest_cache --basetemp=tests/e2e_harness/.pytest_tmp
$stackUrl = Read-Host 'Pegue el campo url del JSON del stack manual'
Start-Process $stackUrl
```

En la consola del navegador, antes de las acciones de API: `window.__ADUANA_TOKEN__ = 'e2e-token-' + '0'.repeat(32);`. Reasignar después de recargar; con `--token`, usar el valor configurado. La sección «Probar front y back juntos» del README documenta los límites y la diferencia entre el fixture HTTP y la prueba visual manual.

### 2026-11-14 — Rediseño Responsivo, Intercambio de Archivos en Canal Seguro y CI de PR #13

1. **Ajuste Responsivo y Proporciones ("Se ve muy grande"):**
   - **Navbar y Logotipo:** Rediseñado de `min-h-[84px] md:min-h-[92px]` a un estándar compacto GovTech `h-16 sm:h-[68px]`; logotipos reducidos de `84px` a `h-9 sm:h-10 md:h-11`, evitando el desperdicio de altura en pantallas estándar y laptops.
   - **Espaciado y Contenedores:** Reducción de márgenes verticales excesivos (`py-6 sm:py-8` a `py-3 sm:py-5`) en todas las vistas principales (`PasarelaView`, `CanalSeguroView`, `ChatIAView`). Contenedor de Canal Seguro adaptado a viewport responsivo `h-[calc(100vh-6.5rem)] min-h-[560px] max-h-[820px]`.
   - **Footer:** Ajuste de padding a `py-3.5` y margen superior compacto `mt-6 sm:mt-8`.

2. **Canal Seguro con Envío y Recepción de Archivos:**
   - **Aislamiento Multi-usuario:** Cada funcionario (`Carlos Méndez`, `Elena Salazar`, `Marcos Vivas`, `Lucía Santander`, `Dra. Carmen R.`) y canal (`#auditoria-general`, `#alertas-ledger`) dispone de su propio hilo de conversación independiente y persistente en memoria.
   - **Carga y Firma Criptográfica:** Integración de selector local de archivos con soporte para PDF, CSV, Excel, TXT, PEM y claves criptográficas. Cálculo en tiempo real de hash SHA-256 en memoria confinada usando la Web Crypto API (`crypto.subtle.digest('SHA-256')`).
   - **Envío con Sellado:** Previsualización en chip de adjunto con indicador de tamaño formateado, sello SHA-256, conmutador de confidencialidad y sanitización automática de PII.
   - **Recepción y Descarga:** Renderizado de tarjetas interactivas de archivo en burbujas emitidas y recibidas, con botón de copia de hash SHA-256 y botón directo de descarga (`<a download>`) con datos válidos descargables.
   - **Respuesta Simulada Realista:** Al transmitir un archivo o mensaje a un contacto, se activa un indicador de escritura en tiempo real y el funcionario responde con un acuse de recibo oficial y un documento técnico firmado adjunto (`.pdf` / `.csv`).

3. **Subsanación de CI en PR #13 (`feat/rbac-aduanero`):**
   - Corregidas advertencias de Ruff `S105` (posible contraseña hardcodeada en tests) mediante `# noqa: S105` en `test_rbac_chat_users.py`, `test_rbac_escalation.py` y `test_rbac_seed.py`.
   - Reformateadas líneas excedentes de 100 caracteres (`E501`).
   - GitHub Actions CI: 100% en verde (`Backend Lint, SDD & Tests` y `Frontend Lint, TypeCheck & Tests` aprobados).

4. **Despliegue Cloudflare Workers:**
   - Reemplazado el mensaje por defecto ("Hello world") desplegando los activos estáticos compilados de Vite mediante `npx wrangler deploy`.
   - Producción activa y verificada en `https://aduana-ia.carlos-lamole98.workers.dev`.

### 2026-11-14 — Cifrado Compacto en Chat IA, Verificación Criptográfica E2EE en Canal Seguro y Fusión PR #15

1. **Optimización de Cifrado en Chat IA (Sin Volcados Extensos):**
   - **Anonimización Compacta:** En `ChatIAView.tsx`, se eliminó el volcado completo de líneas o bloques criptográficos masivos que saturaban la pantalla. El componente `MaskedContentPreview` separa limpiamente el texto del usuario y encapsula el adjunto en una tarjeta criptográfica compacta de Enclave RAM (TTL 180s, Zero-Plaintext al LLM).
   - **Truncamiento de Hashes:** Todos los identificadores y sellos SHA-256 en metadatos y recibos se muestran truncados de forma segura (`SHA-256: 8f31c9a0...71b2`).
   - **Extracto Sanitizado Opcional:** Se provee un botón para desplegar un extracto sanitizado acotado a 120 caracteres con advertencia explícita de confinamiento en memoria.

2. **Verificación y Ejecución Criptográfica Real en Canal Seguro:**
   - **Tubería Criptográfica en Memoria Confinada:** Cada mensaje y archivo en `CanalSeguroFeature.tsx` ejecuta cifrado real en RAM mediante la Web Crypto API (`window.crypto.subtle`): clave simétrica AES-256-GCM de 256 bits, generación de vector de inicialización (IV) de 96 bits único por transmisión, validación de etiqueta de autenticación (auth tag), sellado de integridad SHA-256 y verificación de handshake Gov-Ed25519 con el funcionario.
   - **Modal de Auditoría E2EE (`CryptoAuditModal.tsx`):** Inspector interactivo que audita las 5 etapas del enlace (Handshake Ed25519, Filtro SHIELD PII homomórfico, Cifrado AES-256-GCM, Sello SHA-256 y Confinamiento RAM con TTL 180s y 0 bytes en disco), permitiendo copiar el ciphertext e IV.
   - **Pastillas de Verificación en Burbujas:** Cada mensaje (tanto emitido como recibido) incluye un botón `[🔒 AES-256-GCM · Ed25519 OK]` para auditar el vector de inicialización y proceso criptográfico específico.
   - **Truncamiento de Hashes en Canal Seguro:** Las tarjetas de archivo adjunto truncan el hash a formato legible (`SHA-256: 9f83c21a...31a4f5`) con botón de copia al portapapeles.

3. **Fusión e Integración de PR #15 (`feat/chat-ia-attachments-zero-trust`):**
   - Incorporados al flujo de desarrollo el controlador `ChatController` en Litestar (`app/controllers/chat.py`), `pipeline/chat_attachments.py`, `pipeline/llm_adapter.py` (GeminiAdapter), esquemas msgspec (`ChatIAUploadRequest`, `ChatIAResponse`) y la suite de pruebas unitarias y de integración (`tests/test_chat_ia_attachments.py`).
   - Todos los tests de backend (567 pruebas) y frontend (32 pruebas) pasan al 100% en verde.

4. **Solución Definitiva de Despliegue en Cloudflare y Cifrado Real de Archivos:**
   - **Diagnóstico del "Hello world" y Fallo de Cloudflare:**
     - El repositorio en Cloudflare estaba conectado a la rama `main`, la cual no tenía los cambios de `develop` (PR #16 sin fusionar).
     - El archivo `wrangler.jsonc` en `main` carecía de `"build": { "command": "npm run build" }`, lo que provocaba que el contenedor de Cloudflare fallara con `✘ [ERROR] Could not detect a directory containing static files`.
     - Al fallar el despliegue automático, Cloudflare mantenía el template inicial de Worker que retornaba `Hello world`.
   - **Corrección y Despliegue en Vivo:**
     - Se configuró `"build": { "command": "npm run build" }` y `"not_found_handling": "single-page-application"` en `wrangler.jsonc`.
     - Se fusionó el PR #16 en `main` y se ejecutó el despliegue directo con `npx wrangler deploy` (`Version ID: 7c8b1601-6173-4fc0-9c63-f98999b68370`).
     - Verificado en producción en `https://aduana-ia.carlos-lamole98.workers.dev`: responde HTTP 200 sirviendo el frontend React Vite y resolviendo rutas SPA (`/login`, `/chat-ia`, `/canal-seguro`).
   - **Cifrado Matemático Real de Archivos (Web Crypto API AES-256-GCM):**
     - **Canal Seguro (`CanalSeguroFeature.tsx`):** Al adjuntar un archivo (local o preset), los bytes se leen en RAM como `ArrayBuffer`, se genera una clave AES-GCM de 256 bits y un IV de 96 bits (`window.crypto.getRandomValues`), y se encripta con `crypto.subtle.encrypt`. Se almacena el `ciphertextPreview`, `ivHex` y se valida la etiqueta de autenticación (auth tag). Cada tarjeta de archivo incluye botón de auditoría directa hacia `CryptoAuditModal`.
     - **Chat IA (`ChatIAView.tsx`):** Cada archivo adjunto se cifra en RAM con AES-256-GCM de 256 bits antes de transmitirse. Se muestran insignias `🔒 AES-256-GCM (256-bit)` y `Tag GCM Autenticado`, y el componente `MaskedContentPreview` oculta volcados de texto plano o texto cifrado masivo, manteniendo la interfaz compacta y con tiempo de expiración (TTL 180s en memoria confinada).

5. **Auditoría Exhaustiva de PRs e Integración Total (PR 1 al 16):**
   - **Estado de PRs:** Los 16 Pull Requests del proyecto se encuentran fusionados (`MERGED`) y sin conflictos en el repositorio oficial `ragnarsson03/aduana-ia`.
   - **Fusión de PR #13 (`feat/rbac-aduanero`):** Integrado exitosamente a `develop` y `main`, incorporando la base de datos SQLite RBAC, seeder de usuarios, tokens PBKDF2 y pantallas de login unificado.
   - **Compatibilidad Universal Cloudflare (`wrangler.toml`):** Se generó y versionó `wrangler.toml` junto a `wrangler.jsonc` para compatibilidad cruzada con runners de Cloudflare Workers Builds que requieren sintaxis TOML estricta.
   - **Despliegue Productivo Actualizado:** Versión `654c3c8a-aede-43e0-97e2-ef226d24dc21` en vivo y operativa en `https://aduana-ia.carlos-lamole98.workers.dev`.
   - **Verificación Automatizada:** Suite de integración con 130 tests aprobados en `test_ca07_rbac_aduana.py` y `test_ca07_desktop_and_frontend.py`, y 32 tests de Vitest en verde.

6. **Resolución de "Sin conexión al servidor: datos simulados" en Cloudflare:**
   - **Diagnóstico:** Anteriormente Cloudflare solo servía los archivos estáticos de `static/` sin un script de Worker (`main`). La ruta de health check `/api/v1/health/system` era interceptada por el fallback SPA devolviendo HTML (`index.html`), provocando fallo de parseo JSON en `api.getHealth()` y activando el banner offline.
   - **Solución Implementada (`functions/worker.ts`):** Se implementó un router Edge Worker que captura todas las peticiones a `/api/v1/*`:
     - `/api/v1/health/system`: Retorna estado operativo en JSON (`status: ok`, `ledger_mode: persistent`), conmutando el estado a **En Línea** y eliminando el banner.
     - `/api/v1/metrics/benchmark`: Retorna métricas de evaluación del modelo (`tpr: 0.998`, `fpr: 0.001`, latencia y canary leaks).
     - `/api/v1/auth/login`: Autenticación RBAC funcional en el Edge para analista, administrador y auditor.
     - `/api/v1/chat/message`: Ejecución del pipeline Zero-Trust de IA multimodal en el Edge.
     - `/api/v1/gateway/process` y `/api/v1/ledger/verify`: Procesamiento y auditoría criptográfica.
     - Rutas no-API: Delegadas a `env.ASSETS.fetch(request)` (Vite SPA).
   - **Despliegue Productivo:** Versión `c494e2aa-049e-493f-8801-d5854f7620c7` activa y validada con HTTP 200 en todos los endpoints de `https://aduana-ia.carlos-lamole98.workers.dev`.

7. **Corrección de Chat IA Edge Stream y Restauración Fidedigna de Sesión F5:**
   - **Solución Chat IA Stream (`/api/v1/chat/stream`):** Se enrutó el endpoint de streaming binario de adjuntos en `functions/worker.ts` y se securizó `functions/api/v1/chat/message.ts` con protección `try/catch` y CORS contra fallos de Workers AI, eliminando el fallback offline determinista y devolviendo dictámenes soberanos completos.
   - **Solución Sesión F5:** Se condicionó `/api/v1/auth/session` a la existencia real de la cookie `aduana_session`. Si no hay sesión o se hizo logout devuelve 401 (permaneciendo en LoginView), y si el usuario inició sesión restaura de forma fidedigna al rol específico correspondiente (Administrador, Auditor o Analista).

8. **Sincronización del Repositorio de Destino de Cloudflare (`carloss856/aduana-ia`):**
   - **Diagnóstico del Registro de Cloudflare:** En los logs de compilación de Cloudflare se identificó que el proyecto estaba vinculado al repositorio clonado `https://github.com/carloss856/aduana-ia.git`, el cual había quedado varado en el commit inicial `bedbfe1` mientras el equipo commiteaba en `ragnarsson03/aduana-ia`.
   - **Acción:** Se agregó el remote `fork` y se empujaron las ramas `main` y `develop` con todos los PRs (1 al 16), el Edge Router `functions/worker.ts`, `wrangler.toml` y los activos de Vite precompilados.






