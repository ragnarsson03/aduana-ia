# SPEC — Aduana IA: Pasarela Soberana de Gobernanza Zero-Trust

> **Estado:** Especificación Formal SDD v3.1 (Arquitectura Dual: Nodo Soberano Local Python 2026 + Demo Edge Cloudflare Pages/D1/Workers AI).  
> **Hackathon:** UNETI IA 2026 — Regla de Oro SDD.  
> **Normativa de Referencia:** CRBV Arts. 28 y 60 (*Habeas Data*), Ley de Infogobierno, Ley Especial contra Delitos Informáticos, Lineamientos CNTI / SUSCERTE.

---

## 0.2 Declaración Obligatoria de Uso de IA

| Pregunta Obligatoria del Jurado | Declaración Técnica Oficial |
|---|---|
| **¿Usas IA en tu solución?** | Sí, bajo una **arquitectura híbrida soberana** con *Circuit Breaker* y respaldo determinista offline. |
| **¿Qué modelo usas y por qué?** | Conector triple desacoplado: **1) Nodo Local Soberano:** Ollama / llama.cpp (`Qwen2.5-1.5B`, `Llama-3.2-1B`) en intranet institucional; **2) Demo Edge Cloudflare:** Workers AI (`@cf/meta/llama-3.1-8b-instruct` y `@cf/zai-org/glm-4.7-flash`); **3) Respaldo Offline:** `OfflineDeterministicAdapter` 100% libre de red ante caídas o timeouts. |
| **¿Qué problema resuelve la IA?** | Asiste al funcionario aduanero resumiendo expedientes extensos y redactando respuestas orientativas, operando exclusivamente sobre texto previamente anonimizado. |
| **¿Qué datos procesa la IA?** | Únicamente texto sanitizado por `SHIELD` (`[CEDULA_1]`, `[RIF_1]`, `[PHONE_1]`, `[BANK_1]`, `[CLINICAL_1]`). **Cero PII en texto plano** llega a ningún LLM local o cloud. |
| **¿Cómo evitas sesgos algorítmicos?** | El LLM **no decide prioridades ni solvencias**. La evaluación cuantitativa la ejecuta el módulo matemático White-Box `EXPLICA` mediante Regresión Logística determinista con pesos fijos auditables y cero uso de `random()`. |
| **¿Cómo explicas las decisiones?** | Cada dictamen desglosa el *logit* $z$, probabilidad sigmoide, contribuciones directas ($\beta_j x_j$) y valores SHAP lineales ($\phi_j = \beta_j(x_j - \mu_j)$) con error de reconstrucción $< 10^{-9}$ y aviso explícito de contenido asistido por IA. |
| **¿Qué hace la IA y qué hace el humano?** | La IA resume y propone una recomendación fundada; el funcionario humano (según su rol RBAC) toma la decisión administrativa vinculante (*Human-in-the-Loop*), con justificación obligatoria ($\ge 20$ caracteres) para cualquier *override*. |
| **¿Usaste IA para programar?** | Sí, bajo metodología **Spec-Driven Development (SDD)** estricta: especificación previa en `specs/`, contratos tipados inmutables, verificación criptográfica en stdlib y suite automatizada `pytest` + `vitest`. |

---

## 1. Problema
La adopción acelerada de Modelos de Lenguaje (LLMs) en ministerios, aduanas, gobernaciones y entes públicos en Venezuela expone datos ciudadanos protegidos (Cédula de Identidad, RIF, teléfonos, cuentas bancarias de 20 dígitos y diagnósticos clínicos) cuando expedientes completos se envían sin control a APIs externas o herramientas personales (*Shadow AI*). Esta práctica compromete la confidencialidad y el principio constitucional de *Habeas Data* (CRBV Arts. 28 y 60).

Adicionalmente, el uso directo de IA generativa en trámites administrativos y aduaneros introduce tres fallas críticas:
1. **Manipulación adversaria (*Prompt Injection / Jailbreak*):** inyección de instrucciones (directas, indirectas o codificadas en Base64/Hex/Unicode) para alterar dictámenes o exfiltrar directrices internas.
2. **Opacidad algorítmica ("caja negra"):** asignación de prioridades o aforos sin justificación matemática auditable por Contraloría.
3. **Vulnerabilidad de registros de auditoría:** bases de datos mutables donde un administrador o atacante puede alterar historiales sin detección criptográfica inmediata.

---

## 2. Usuarios y Roles (RBAC Aduanero)
- **Ciudadanos:** Titulares de datos personales que exigen consentimiento explícito, anonimización irreversible y comprobante criptográfico de trámite (`citizen_receipt_code`).
- **Funcionarios con Control de Acceso Basado en Roles (`usuarios_aduana` — 6 roles):**
  1. `admin`: Administrador de Infraestructura & Ciberseguridad (gestión de nodos, claves y simulaciones de auditoría).
  2. `auditor`: Auditor Principal / Forense SHA-256 (inspección de Ledger inmutable, verificación de cadena y explicabilidad).
  3. `analista`: Analista de Operaciones & Solvencias (operación de Pasarela, sanitización `SHIELD`, Chat IA y Canal Seguro).
  4. `inspector_aforo`: Inspector de Aforo Físico y Documental (validación de expedientes aduaneros y *override* justificado).
  5. `oficial_cumplimiento`: Oficial de Cumplimiento y *Habeas Data* (auditoría de `GUARDIÁN`, consentimiento RF-02 y Zero-PII).
  6. `supervisor_aduana`: Supervisor Nacional de Operaciones Aduaneras (supervisión regional, *override* y verificación de trazabilidad).

---

## 3. Alcance del MVP
- **SÍ hará:**
  - **Arquitectura Dual (Soberana Local + Demo Edge Cloudflare):** Ejecución 100% offline/intranet en Python (**Litestar + Granian + PyWebView**) y despliegue Edge serverless compatible con **Cloudflare Pages + D1 SQLite + Workers AI + KV**.
  - **Criptografía Pura y Bóveda Efímera:** `EphemeralVault` en RAM con TTL de 180s y destrucción criptográfica (`zeroize`), `blind_citizen_id` HMAC-SHA256, doble sello `SHA-256` encadenado + `HMAC-SHA256`, y validación SENIAT Módulo 11 para RIF.
  - **Defensa Multicapa (`GUARDIÁN`):** Normalización canónica Unicode `NFKC`, detección multivista contra ofuscación, sandbox XML y *Canary Tokens* dinámicos HMAC por transacción.
  - **Explicabilidad White-Box (`EXPLICA`):** Regresión Logística determinista con valores SHAP lineales ($\phi_j = \beta_j(x_j - \mu_j)$) y *Human-in-the-Loop*.
  - **RBAC y Ledger Inmutable:** Esquema SQL unificado (`schema.sql`) y seed PBKDF2 (`seed_d1.sql`) compatibles tanto con SQLite3 endurecido (`WAL`, `secure_delete=ON`, triggers `BEFORE UPDATE/DELETE`) como con Cloudflare D1.
- **NO hará:**
  - Conexión directa en producción con bases de datos en vivo de SAIME o SENIAT (validado con datasets sintéticos auditables).
  - Envío de PII en texto plano a nubes externas ni almacenamiento persistente de cédulas sin hash HMAC.

---

## 4. Requisitos Funcionales (RF)
- **RF0 (Consentimiento y Rate-Guard):** Rechazar con `BLOCKED_NO_CONSENT` peticiones sin consentimiento explícito (`granted=True`, `purpose_code`), calculando `consent_hash` SHA-256 y limitando tasa por `blind_citizen_id`.
- **RF1 (`SHIELD` — Anonimización Soberana):** Enmascarar Cédulas, RIFs (Módulo 11 SENIAT con pesos `[4,3,2,7,6,5,4,3,2]`), teléfonos nacionales, cuentas bancarias de 20 dígitos y patologías sensibles sin persistir PII en disco.
- **RF2 (`GUARD-IN` y `GUARD-OUT` — Defensa Activa):** Normalizar texto (`NFKC`), neutralizar evasiones Base64/Hex/Unicode, calcular `risk_score` determinista, encapsular en XML con Canary HMAC dinámico y bloquear fugas de Canary, PII residual o XSS en salida.
- **RF3 (`EXPLICA` — Explicabilidad White-Box):** Calcular probabilidad sigmoide $P(y=1\mid\mathbf{x}) = \frac{1}{1+e^{-z}}$ y valores SHAP lineales sin `random()`, exigiendo confirmación o justificación escrita ($\ge 20$ caracteres) ante *override*.
- **RF4 (`LEDGER` — Trazabilidad Inmutable):** Registrar bloques encadenados SHA-256 + HMAC-SHA256 con verificación completa en `/api/v1/ledger/verify`, detección exacta de manipulación (`HASH_MISMATCH`, `PREV_HASH_LINK_BROKEN`, `HMAC_SIGNATURE_FORGED`) y recibo ciudadano.
- **RF5 (`RBAC` — Control de Acceso Aduanero):** Gestionar 6 roles aduaneros en `usuarios_aduana` con contraseñas protegidas por `PBKDF2-HMAC-SHA256` (310,000 iteraciones) e identidad ciudadana pseudonimizada vía `blind_citizen_id`.

---

## 5. Criterios de Aceptación (CA-01 a CA-07)
- **CA-01 (`SHIELD`):** Enmascara el 100% de identificadores estructurados venezolanos en $< 20\text{ ms}$, valida Módulo 11 SENIAT, genera `blind_citizen_id` HMAC y mantiene el mapa de reversión exclusivamente en RAM.
- **CA-02 (`GUARDIÁN`):** Alcanza $\text{TPR} \ge 88\%$, $\text{FPR} \le 4\%$ en $< 25\text{ ms}$ por prompt y neutraliza el 100% de intentos de fuga de Canary.
- **CA-03 (`LEDGER`):** Ante alteración de un solo bit en SQLite, `/api/v1/ledger/verify` retorna `is_valid=False`, `corrupted_block_index` exacto y causa raíz en $< 50\text{ ms}$.
- **CA-04 (`EXPLICA`):** Reconstruye el *logit* $z$ a partir de valores SHAP lineales con error $< 10^{-9}$ y cero llamadas a `random()`.
- **CA-05 (`Zero-Plaintext-PII`):** Auditoría binaria del `.db`, `seed_d1.sql` y logs comprueba **0 bytes** de cédulas, RIFs o teléfonos en texto plano.
- **CA-06 (`Resiliencia`):** Ante caída o timeout del LLM externo ($3.5\text{ s}$), el *Circuit Breaker* conmuta en $< 100\text{ ms}$ al `OfflineDeterministicAdapter`.
- **CA-07 (`Desktop & Air-Gapped`):** Ventana nativa PyWebView + Granian en modo privado sin CDNs externos ni autocompletado de PII, y empaquetado Edge compatible con Cloudflare Pages.

---

## 6. Arquitectura Técnica Dual (Python Soberano + Cloudflare Edge)

Aduana IA implementa una **arquitectura dual** que comparte contratos, esquemas SQL y frontend React/TypeScript, permitiendo operar tanto en entornos gubernamentales aislados (Air-Gapped) como en la nube Edge del Hackathon:

| Capa / Componente | Nodo Soberano Local (Python On-Premise / Desktop) | Demo Edge Cloudflare (Hackathon UNETI IA 2026) |
|---|---|---|
| **Frontend / Interfaz** | React + Vite compilado en `static/` (Air-Gapped, cero CDNs externos), embebido en **PyWebView 5.1+** | React + Vite compilado en `dist/` servido globalmente por **Cloudflare Pages** (`wrangler.jsonc`) |
| **Runtime / Backend** | **Litestar 2.10+** (ASGI) + **Granian** / Uvicorn, serialización estricta `msgspec` / `dataclasses(slots=True, frozen=True)` | Workers / Pages Functions configuradas con bindings declarativos en `wrangler.jsonc` |
| **Base de Datos (SQL)** | **SQLite3 Endurecido** (`WAL`, `synchronous=FULL`, `secure_delete=ON`, `trusted_schema=OFF`, triggers `BEFORE UPDATE/DELETE`) | **Cloudflare D1** (SQLite serverless, binding `"DB"`, `database_name: "aduana-db"`), inicializado con `schema.sql` y `seed_d1.sql` |
| **Inferencia IA (LLM)** | **Ollama / llama.cpp** en intranet + `OfflineDeterministicAdapter` vía `CircuitBreaker` | **Cloudflare Workers AI** (binding `"AI"`, modelos `@cf/meta/llama-3.1-8b-instruct` y `@cf/zai-org/glm-4.7-flash`) |
| **Estado Efímero / Rate-Limit** | `EphemeralVault` en RAM (TTL 180s, `zeroize`) + `RateGuard` en memoria | **Cloudflare Workers KV** (binding `"KV"`) para sesiones efímeras y control de tasa distribuido |
| **Criptografía** | Python Stdlib (`hashlib`, `hmac`, `secrets`, `unicodedata`, PBKDF2-HMAC-SHA256) | Subconjunto compatible WebCrypto / hashes PBKDF2 y `blind_citizen_id` precomputados en D1 |

---

## 7. Modelo de Datos (`schema.sql` — `ledger_blocks` y `usuarios_aduana`)

Definido de forma unificada en [`schema.sql`](schema.sql) para SQLite3 local y Cloudflare D1:

### 7.1 Tabla `ledger_blocks` (Trazabilidad Inmutable)
- `block_index` (`INTEGER PRIMARY KEY`)
- `request_id` (`TEXT NOT NULL UNIQUE`)
- `timestamp_utc` (`TEXT NOT NULL`)
- `blind_citizen_id` (`TEXT NOT NULL` — HMAC-SHA256 irreversible de la Cédula)
- `payload_hash` (`TEXT NOT NULL` — SHA-256 del contenido sanitizado)
- `prev_hash` (`TEXT NOT NULL` — Enlace al `block_hash` anterior)
- `block_hash` (`TEXT NOT NULL` — Hash SHA-256 canónico del bloque)
- `hmac_signature` (`TEXT NOT NULL` — Sello HMAC-SHA256 con clave maestra en RAM)
- `security_verdict` (`TEXT NOT NULL` — `CLEAN`, `BLOCKED_NO_CONSENT`, `BLOCKED_INJECTION`, `BLOCKED_CANARY_LEAK`)
- `model_recommendation` (`TEXT NOT NULL` — `PRIORIDAD_ALTA`, `REVISION_ESTANDAR`, `RECAUDOS_INCOMPLETOS`)
- `human_decision` (`TEXT NOT NULL`)
- `human_override` (`INTEGER NOT NULL DEFAULT 0`)
- `citizen_receipt_code` (`TEXT NOT NULL UNIQUE`)
- `key_id` (`TEXT NOT NULL`)
- `override_justification_hash` (`TEXT` — Hash HMAC de la justificación, nunca texto plano con posible PII)
- **Índices y Triggers:** `idx_ledger_blocks_blind_citizen_id`, `idx_ledger_blocks_timestamp_utc`, `idx_ledger_blocks_security_verdict`, más triggers `prevent_ledger_update` y `prevent_ledger_delete` (`RAISE(ABORT, 'ERR_IMMUTABLE_LEDGER')`).

### 7.2 Tabla `usuarios_aduana` (RBAC Aduanero Zero-PII)
- `id` (`TEXT PRIMARY KEY` — Identificador institucional, ej. `usr-auditor-01`)
- `username` (`TEXT NOT NULL UNIQUE`)
- `email` (`TEXT NOT NULL UNIQUE`)
- `full_name` (`TEXT NOT NULL`)
- `role` (`TEXT NOT NULL CHECK (role IN ('admin', 'auditor', 'analista', 'inspector_aforo', 'oficial_cumplimiento', 'supervisor_aduana'))`)
- `role_label` (`TEXT NOT NULL`)
- `clearance_level` (`TEXT NOT NULL`)
- `department` (`TEXT NOT NULL`)
- `blind_citizen_id` (`TEXT NOT NULL UNIQUE` — HMAC-SHA256 de la cédula normalizada; **cero cédulas en texto plano**)
- `password_hash` (`TEXT NOT NULL` — `pbkdf2_sha256$310000$<salt_hex>$<dk_hex>`)
- `permissions_json` (`TEXT NOT NULL` — Arreglo JSON de permisos granulares)
- `is_active` (`INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))`)
- `created_at_utc` (`TEXT NOT NULL`)
- `updated_at_utc` (`TEXT NOT NULL`)
- **Índices:** `idx_usuarios_aduana_role`, `idx_usuarios_aduana_is_active`.

---

## 8. Seguridad, Privacidad y Cumplimiento Normativo
1. **Zero-Plaintext-PII en Repositorio y Discos:** Ni `ledger.db`, ni `schema.sql`, ni `seed_d1.sql`, ni los logs de servidor contienen cédulas, RIFs o teléfonos sin anonimizar/pseudonimizar.
2. **Aislamiento de Secretos:** `ADUANA_MASTER_KEY` y `ADUANA_API_TOKEN` se leen y eliminan del entorno al arrancar (`core/config.py`); el token de escritorio se inyecta en memoria vía `window.evaluate_js` (`window.__ADUANA_TOKEN__`).
3. **Endurecimiento HTTP y Desktop:** Cabeceras `CSP`, `X-Content-Type-Options: nosniff`, `AllowedHostsConfig` estricto por host/puerto, `private_mode=True` en PyWebView y `autoComplete="off"` en todos los formularios.

---

## 9. Plan de Verificación y Pruebas Automatizadas
- **Linter y Tipado:** `ruff check core pipeline app tests` (longitud máxima 100, reglas `pyproject.toml`).
- **Suite Backend Python (`pytest`):**
  - `tests/test_ca01_shield.py` y `tests/test_pii_patterns.py`: Validación de cédulas, RIF Módulo 11 y `SHIELD`.
  - `tests/test_ca02_guardian.py` y `tests/test_guardian_*.py`: Benchmark adversario, deofuscación multivista y Canary leaks.
  - `tests/test_ca03_ledger.py` y `tests/test_tamper_sim_genesis.py`: Integridad SHA-256 + HMAC y detección de manipulación.
  - `tests/test_ca04_explica.py`: Exactitud SHAP lineal y *override* humano.
  - `tests/test_ca05_restrictive_storage.py` y `tests/test_gateway_pipeline.py`: Auditoría binaria Zero-PII en SQLite.
  - `tests/test_ca06_resilience.py`: *Circuit Breaker* y failover determinista.
  - `tests/test_ca07_desktop_and_frontend.py` y `tests/e2e_harness/`: Lanzador PyWebView/Granian, bundle Air-Gapped y pruebas E2E reales.
- **Suite Frontend (`vitest`):** `npm test`.

---

## 10. Despliegue y Operación (Local Soberano + Cloudflare Edge)

### 10.1 Despliegue Edge en Cloudflare (Pages + D1 + Workers AI + KV)
1. **Generar el seed criptográfico RBAC (10 usuarios / 6 roles):**
   ```bash
   python scripts/generate_d1_seed.py
   ```
2. **Crear e inicializar la base de datos D1 (`aduana-db`):**
   ```bash
   wrangler d1 execute aduana-db --remote --file=schema.sql
   wrangler d1 execute aduana-db --remote --file=seed_d1.sql
   ```
3. **Compilar frontend para Pages (`dist`) y desplegar usando `wrangler.jsonc`:**
   ```bash
   npx vite build --outDir dist
   wrangler pages deploy dist
   ```

### 10.2 Ejecución en Nodo Soberano Local (Escritorio / Servidor)
- **Aplicación de Escritorio Nativa:** `iniciar_escritorio.bat` (Windows) o `./iniciar_escritorio.sh` (Linux/macOS).
- **Servidor ASGI Litestar + Granian:** `python -m app.main` (sirviendo API + `static/` Air-Gapped en `127.0.0.1:8000`).
