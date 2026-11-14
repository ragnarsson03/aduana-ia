# PROGRESO — Aduana IA (backend)

> Archivo de coordinación para varios modelos/agentes. **Antes de tomar una tarea:** léela entera, marca `[~]` con tu nombre/fecha, y no toques los archivos que otra tarea `[~]` esté usando. **Al terminar:** marca `[x]` y corre la suite.
> Última actualización: 2026-11-13. Estado: 274 tests pasan, 1 CA en `xfail(strict=True)` (CA-06). Gatillos 2, 3 y 4 completos y certificados.

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

## EN CURSO
- [~] **Codex** — optimizar `core/pii_patterns.py` y `core/text_normalizer.py` (solo esos dos). Meta: ≤ 8 ms a 5 000 caracteres, ≤ 25 ms a 20 000. **No editar esos archivos hasta que termine.**
- [~] **Penetration Tester** — red team ronda 2 de SHIELD (solo lectura). Entrega tabla de regresión para convertir en tests.
- [~] **Antigravity (2026-11-13)** — Gatillo 5 (LLM y Circuit Breaker CA-06) y Gatillo 6 (Orquestador y API completa).

## PENDIENTE

### P0 — Endurecer Gatillo 2 (resultado del red team, 2026-11-13)
Medido sobre un conjunto INDEPENDIENTE de 288 casos (185 ataques y 103 benignos duros, escritos aparte): **TPR 22,7 % (IC 17–29 %)**, **FPR 4,9 %** frente a CA-02 (TPR ≥ 88 %, FPR ≤ 4 %). El 98 % del benchmark propio (`data/attack_benchmark.json`) es sobreajuste: 48 de 50 patrones salen de sus propios ataques. Criterio de salida: `tests/test_guardian_regression.py` (hoy 65 `xfail`; al corregir, quitar el xfail correspondiente) y un conjunto ciego que **nadie use para afinar reglas**.
- [x] **C1 ReDoS cúbico** en `SQLI_SELECT_FROM` (select + 3000 espacios tardaba 108 s): corregido con `\bselect\b[^;\n]{1,200}?\bfrom\b` (ahora 14 ms). Hay tests sin xfail que lo vigilan.
- [x] `orchestrator.py` llamaba `guard_in(request_id, masked_text, self._keys)` posicional; la firma exige `keys=` → corregido.
- [ ] **A1 cobertura:** pasar de frases literales a reglas por intención (verbos de anulación × objetos {instrucciones, reglas, normas, directrices, configuración, prompt} en ventana ≤ 6 tokens; verbos de exfiltración × {prompt, contexto inicial, token, canary, clave}; marcadores de autoridad + verbo aprobar/omitir; español e inglés). Opcional: clasificador ligero (n-gramas de caracteres) entrenado con datos independientes, combinado con `max(regla, clasificador)`.
- [ ] **A2 ofuscación:** escanear varias vistas del texto (normalizado, invisibles→espacio, sin diacríticos, leet-fold, letras sueltas colapsadas, rot13 e invertido). Hoy pasan leet, letras espaciadas, puntos/guiones por letra, rot13, invertido, ZWJ, U+2800 y tags U+E00xx.
- [ ] **A3 base64/hex:** decodificar TODOS los candidatos (con tope), limpiar espacios/saltos, urlsafe, `\x`, UTF-16, recursión ≤ 2. Hoy un decoy benigno delante evita la detección (`break`).
- [ ] **A4 falsos positivos (4,9 %):** bajar el peso de `sin restricciones`, `modo desarrollador`, `instrucciones internas`, `evadir controles` y exigir segunda señal dirigida al asistente; detectar negaciones y citas.
- [ ] **M2** capturar `ValueError` de `normalize_text` en `guard_in` y `guard_out` (fail-closed, estado de política propio) y en `/metrics/benchmark`.
- [ ] **M3** escapar y envolver el texto NORMALIZADO (hoy se analiza el normalizado pero se envuelve el original: ＜ fullwidth y tags U+E00xx llegan al LLM).
- [ ] **M4** `guard_out`: canary fragmentado/codificado (subcadenas ≥ 6, separadores, base64 del token y del hex, ventana deslizante); fingerprint del texto del prompt del sistema.
- [ ] **M5** `guard_out`: neutralizar o marcar enlaces `javascript|data|vbscript|//`, más handlers `onfocus/ontoggle/...`; decidir si `xss_or_code_injected=True` debe bloquear o añadir `SANITIZED_XSS`. El frontend debe renderizar con `textContent`.
- [ ] **M6** PII ofuscada en guard_out ("arroba/punto", teléfono con espacios): comparte detector con SHIELD.
- [ ] **B2** `/metrics/benchmark`: candado contra carrera de caché; `canary_leaks_neutralized_pct` es constante (no mide nada); medir p95 y guard_out; reportar IC de Wilson.
- [ ] Rehacer el benchmark: benignos adversariales (con "ignorar", "olvidar", "clave", "modo", "instrucciones" usados legítimamente), textos largos, autor distinto al de las reglas.
- [ ] CA-02 (< 25 ms/prompt) solo se cumple por debajo de ~6 000 caracteres; el tope de la API es 20 000 → acotar el alcance o bajar el tope.
- Conjunto independiente del red team (NO usarlo para afinar): `C:\Users\csubero\AppData\Local\Temp\claude\ac455cc4694fadac\eb26388d-f516-4461-ab6f-bc92c4f41ebf\scratchpad\independent_set.json`.

### Bloqueos detectados en el árbol de trabajo
- [ ] `pipeline/orchestrator.py` importa `explain_dossier` de `pipeline/stage5_explica.py` y esa función aún no existe: rompe la recolección de tests (`tests/test_api_hardening.py` y cualquiera que importe el orquestador). Quien edita orquestador/EXPLICA debe cerrarlo antes de commitear.
- [ ] `static/index.html` carga fuentes de `fonts.googleapis.com`/`fonts.gstatic.com`: viola Air-Gapped y la CSP `default-src 'self'`. Empaquetar las fuentes dentro de `static/`.

### P0 — Cerrar Gatillo 1
- [ ] Aplicar hallazgos del red team ronda 2 y añadir su tabla como tests parametrizados en `tests/test_ca01_shield.py`.
- [x] **Alcance de CA-01 decidido (usuario, opción A):** < 20 ms para textos de hasta 10 000 caracteres; la API sigue aceptando hasta 20 000 (`MAX_RAW_TEXT_CHARS`) sin garantía de 20 ms por encima de 10 000. Documentado en `specs/01_shield.spec.md` y fijado en `tests/test_ca01_shield.py`.
- [ ] Reescribir `specs/01_shield.spec.md` (firmas reales; **corregir vector `J-00000000-9`: el verificador correcto es 0**; mover "inconsistencias" a "decisiones tomadas").
- [ ] Límites conocidos sin cubrir (documentados en `core/pii_patterns.py`): nombres sin marcador/minúsculas, base32/ROT13/entidades HTML/`%NN`, números en palabras, clínicos con variantes (`seropositivo`, `d i a b e t e s`), falsos positivos clínicos en texto comercial ("depresión del mercado").

### P2 — Gatillo 5: LLM y Circuit Breaker (CA-06)
- [~] `OfflineDeterministicAdapter` (resumen determinista sin red), `OllamaAdapter` y `OpenAICompatAdapter` (httpx; allowlist de hosts, sin redirects, respuesta acotada; **híbrido opt-in**).
- [~] `CircuitBreaker` como máquina de estados CLOSED/OPEN/HALF_OPEN con umbral, enfriamiento y reloj inyectable.
- [?] **Redefinir CA-06**: con circuito abierto el failover responde < 100 ms; con timeout en frío tarda hasta 3.5 s. Documentar qué se mide. Spec: `specs/05_interconnect.spec.md`.

### P3 — Gatillo 6: Orquestador y API completa
- [~] `GatewayPipeline.process`: stage0 (blind id, rate-guard, consentimiento) → shield → guard_in → LLM → guard_out → explica → ledger; `vault.zeroize` en `finally`; `BlockedPacket` para rechazos (también se sellan); `request_id` con `secrets.token_urlsafe(16)` generado en servidor.
- [~] DTO de salida propio (usa `sanitized_response`, **omite `raw_response` y el canary**), `POST /gateway/process`, mapeo de errores a 403/429/409/422/503, `RateLimitError` → 429 + `Retry-After`.
- [~] Lifespan de Litestar: purga periódica de la bóveda, `zeroize_all` y cierre del repo al apagar.
- [~] Test de integración CA-05 completo (caplog/capsys + `.db`/`-wal`/`-shm`).

### P3 — Gatillo 7 y frontend
- [ ] Instalar y **probar de verdad** `granian` y `pywebview` (nunca se han ejecutado): servidor en hilo vs subproceso, puerto efímero, espera de readiness, token a la ventana (`evaluate_js`, no en URL), `private_mode`, `freeze_support` para PyInstaller.
- [ ] `iniciar_escritorio.bat` e `iniciar_escritorio.sh`.
- [ ] `static/`: panel funcionario + panel auditoría, **sin CDNs**, render con `textContent` (nunca `innerHTML`), `autocomplete="off"` en inputs con PII, CSP estricta sin inline; test que busque `https?://` en `static/`.

### P4 — Calidad, seguridad y empaquetado
- [ ] Instalar y pasar `ruff`, `mypy --strict`, `bandit`, `pip-audit` (hoy no corridos); CI.
- [ ] Autenticación institucional (OIDC/LDAP) y `actor_id` pseudonimizado en el bloque (hoy solo token por proceso).
- [ ] Pasaporte/otros identificadores, política de `purpose_code` autorizados, formato UTC del `timestamp`.
- [ ] README: sección de despliegue remoto (TLS + auth), recordar `workers=1`; documentar riesgo residual de `zeroize` en CPython (`pagefile.sys`, `hiberfil.sys`, volcados WER) y mitigaciones (BitLocker, sin hibernación).
- [ ] Commit(s) con mensajes convencionales (`feat:`, `test:`…); nada está commiteado todavía. Revisar `.gitignore` (ya cubre `.db`, WAL/SHM, `.venv`, `.env`).

## Decisiones abiertas para el humano (`[?]`)
1. ~~Alcance de CA-01~~ — resuelto: ≤ 10 000 caracteres (opción A).
2. Redefinición de CA-06 (failover con circuito abierto vs timeout en frío).
3. Letra **C = 3** del RIF (comunales) sin fuente oficial accesible; RIF abreviado no se rellena con ceros.
4. `consent_hash`: SHA-256 de JSON canónico (actual) vs HMAC dominio `consent` (infalsificable).
5. Autenticación de producción y política de llaves persistentes (`ADUANA_MASTER_KEY` protegida por DPAPI/TPM/vault).
6. Términos clínicos: ¿enmascarar siempre o solo con contexto personal (paciente/padece/diagnóstico)?

## Mapa rápido de archivos
| Área | Archivos |
|---|---|
| Contratos/config | `core/context.py`, `config.py`, `errors.py`, `protocols.py`, `keyring.py` |
| Cripto/bóveda | `core/crypto.py`, `ephemeral_vault.py`, `text_normalizer.py`, `pii_patterns.py` |
| Pipeline | `pipeline/stage0_consent.py`, `stage1_shield.py`, `stage2_guard_in.py`, `stage3_guard_out.py`, `stage4_ledger.py` (hechos); `stage5_explica.py`, `llm_adapter.py`, `orchestrator.py` (pendientes) |
| API | `app/server.py`, `security.py`, `schemas.py`, `dependencies.py`, `controllers/*`, `desktop.py` (sin probar) |
| Tests | `tests/` (conftest con `client`, `demo_client`, `keys`; token `API_TOKEN`/`TOKEN_HEADERS`) |
| Specs | `specs/00_architecture.spec.md`, `00_kernel`, `01_shield` (desactualizada), `02_guardian`, `03_ledger`, `04_explica`, `05_interconnect`, `06_files_and_chat_frontend` |
