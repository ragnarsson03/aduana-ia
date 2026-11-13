# SPEC — Aduana IA: Pasarela Soberana de Gobernanza Zero-Trust

> **Estado:** Especificación Formal SDD v3.0 (Python 2026 — Litestar + PyWebView Desktop + Criptografía Pura).  
> **Normativa de Referencia:** CRBV Arts. 28 y 60, Ley de Infogobierno, Ley Especial contra Delitos Informáticos, Lineamientos CNTI / SUSCERTE.

---

## 1. Problema
La adopción acelerada de Modelos de Lenguaje (LLMs) en ministerios, gobernaciones y entes públicos en Venezuela expone datos ciudadanos protegidos (Cédula de Identidad, RIF, teléfonos, cuentas bancarias de 20 dígitos y diagnósticos clínicos) cuando expedientes completos se envían sin control a APIs externas o herramientas personales (*Shadow AI*). Esta práctica compromete la confidencialidad y el principio de *Habeas Data* (CRBV Arts. 28 y 60).

Adicionalmente, el uso directo de IA generativa en trámites introduce tres fallas críticas:
1. **Manipulación adversaria (*Prompt Injection / Jailbreak*):** inyección de instrucciones para alterar dictámenes o exfiltrar directrices internas.
2. **Opacidad algorítmica ("caja negra"):** asignación de prioridades en becas o salud sin justificación matemática auditable por Contraloría.
3. **Vulnerabilidad de registros de auditoría:** bases de datos mutables donde un administrador o intruso puede alterar historiales sin detección criptográfica inmediata.

---

## 2. Usuarios
- **Ciudadanos:** Titulares de datos personales que exigen consentimiento explícito, anonimización irreversible y comprobante criptográfico de trámite (`citizen_receipt_code`).
- **Funcionarios Públicos (Analistas):** Operadores que utilizan la pasarela en su estación de trabajo (**Aplicación de Escritorio** o **Portal Web**) para recibir resúmenes de IA sobre datos ya anonimizados y un dictamen explicable transparente, manteniendo la decisión final (*Human-in-the-Loop*).
- **Contraloría / Auditores (SUSCERTE / CNTI):** Inspectores que auditan la cadena criptográfica inmutable en tiempo real y verifican la resistencia adversaria contra inyección de prompts.
- **Administradores TI:** Responsables de desplegar el **Servidor Litestar** (on-premise en Linux/Windows Server) o distribuir el ejecutable de **Escritorio PyWebView** en estaciones Windows 10/11.

---

## 3. Alcance del MVP
- **SÍ hará:**
  - **Servidor Backend Moderno en Python 2026:** Motor asíncrono sobre **Litestar** con serialización ultra-rápida `msgspec`/`pydantic v2` y servidor **Granian** (o Uvicorn), reemplazando arquitecturas legacy de FastAPI.
  - **Aplicación de Escritorio Nativa:** Lanzador y ventana nativa de escritorio mediante **PyWebView** sin sobrecarga de Electron, con interfaz local offline-first (< 60 MB RAM).
  - **Criptografía Pura y Almacenamiento Restrictivo:** Bóveda efímera en memoria RAM (`EphemeralVault`) con TTL de 180s y destrucción criptográfica (`zeroize`), índice ciego HMAC (`blind_citizen_id`), doble sello `SHA-256` encadenado + `HMAC-SHA256` de servidor, y algoritmo oficial SENIAT Módulo 11 para RIF.
  - **Defensa Multicapa (Guardián):** Normalización canónica Unicode `NFKC`, eliminación de caracteres *zero-width*, sandbox XML, y *Canary Tokens* dinámicos HMAC por transacción.
  - **Explicabilidad White-Box:** Regresión Logística determinista con cálculo exacto de valores SHAP lineales ($\phi_j = \beta_j(x_j - \mu_j)$) y supervisión humana vinculante (*Human-in-the-Loop* con override justificado $\ge 20$ caracteres).
  - **Persistencia Endurecida:** Motor SQLite3 con directivas `WAL`, `synchronous=FULL`, `secure_delete=ON` y triggers SQL `BEFORE UPDATE/DELETE` de inmutabilidad (con interfaz abstracta compatible con PostgreSQL institucional).
- **NO hará:**
  - Integración directa en producción con bases de datos en vivo de SAIME o SENIAT (se validará con datasets sintéticos auditables).
  - Descarga obligatoria de pesos LLM de 500 MB en tiempo de arranque (incluye modo fallback institucional determinista 100% offline).

---

## 4. Requisitos Funcionales (RF)
- **RF0 (Consentimiento y Rate-Guard):** Rechazar con código `BLOCKED_NO_CONSENT` peticiones sin consentimiento explícito (`granted=True`, `purpose_code`), calculando `consent_hash` SHA-256 y limitando tasa por `blind_citizen_id`.
- **RF1 (`SHIELD` — Anonimización Soberana):** Enmascarar Cédulas, RIFs (validando dígito verificador Módulo 11 SENIAT con pesos `[4,3,2,7,6,5,4,3,2]`), teléfonos nacionales, cuentas bancarias de 20 dígitos y patologías sensibles con tokens coherentes (`[CEDULA_1]`, `[RIF_1]`, etc.) sin persistir PII en disco.
- **RF2 (`GUARD-IN` y `GUARD-OUT` — Defensa Activa):** Normalizar texto con `NFKC`, bloquear evasiones Base64/Hex, calcular `risk_score` determinista, encapsular en XML inmutable con Canary HMAC dinámico, y verificar en salida que no exista fuga de Canary, PII residual ni etiquetas ejecutables XSS.
- **RF3 (`EXPLICA` — Explicabilidad White-Box):** Calcular probabilidad sigmoide $P(y=1\mid\mathbf{x}) = \frac{1}{1+e^{-z}}$ y valores SHAP lineales sin invocar `random()`, exigiendo confirmación del funcionario o justificación escrita ($\ge 20$ caracteres) si hay override.
- **RF4 (`LEDGER` — Trazabilidad Inmutable):** Registrar bloques encadenados con SHA-256 y firma HMAC-SHA256 del servidor, proveyendo auditoría completa en `/api/v1/ledger/verify` con detección exacta de manipulación (`HASH_MISMATCH`, `PREV_HASH_LINK_BROKEN`, `HMAC_SIGNATURE_FORGED`) y emisión de recibo ciudadano.

---

## 5. Criterios de Aceptación (CA-01 a CA-06)
- **CA-01 (`SHIELD`):** Enmascara el 100% de identificadores estructurados venezolanos en $< 20\text{ ms}$, valida Módulo 11 SENIAT, genera `blind_citizen_id` HMAC y almacena el mapa de reversión exclusivamente en RAM.
- **CA-02 (`GUARDIÁN`):** Sobre el benchmark local de 100 prompts (`data/attack_benchmark.json`), alcanza $\text{TPR} \ge 88\%$, $\text{FPR} \le 4\%$ en $< 25\text{ ms}$ por prompt y neutraliza el 100% de intentos de fuga de Canary.
- **CA-03 (`LEDGER`):** Ante la alteración de un solo bit en la base de datos (incluso recalculando hashes SHA-256 sin la clave HMAC en RAM), `/api/v1/ledger/verify` retorna `is_valid=False`, el `corrupted_block_index` exacto y el motivo de fallo en $< 50\text{ ms}$.
- **CA-04 (`EXPLICA`):** Para cualquier vector $\mathbf{x}$, retorna $P(y=1\mid\mathbf{x})$, contribuciones $\beta_j x_j$ y valores SHAP lineales $\phi_j$ reconstruyendo el *logit* $z$ con error $< 10^{-9}$ y cero uso de `random()`.
- **CA-05 (`Zero-Plaintext-PII`):** Tras procesar 20 trámites simulados, una auditoría binaria del archivo `.db` y logs comprueba **0 bytes** de Cédulas, RIFs o teléfonos en texto plano.
- **CA-06 (`Resiliencia y Desktop`):** Ante caída o timeout del LLM externo, el *Circuit Breaker* conmuta en $< 100\text{ ms}$ al generador institucional determinista, sellando el trámite tanto en modo Servidor Litestar como en la App de Escritorio PyWebView.

---

## 6. Arquitectura Técnica (Python 2026)

| Componente | Tecnología Seleccionada | Justificación Técnica |
|---|---|---|
| **Servidor API Web** | **Litestar 2.10+** (ASGI) + **Granian** / Uvicorn | Framework Python de última generación (2026): tipado estricto nativo, OpenAPI 3.1, inyección de dependencias desacoplada y rendimiento superior sin la deuda técnica de FastAPI 2018. |
| **Serialización / Contratos** | **msgspec / Pydantic v2** (`@dataclass(slots=True, frozen=True)`) | Serialización estructurada en C/Rust hasta 10x más rápida que Pydantic v1, consumo de RAM reducido en 40%. |
| **Aplicación de Escritorio** | **PyWebView 5.1+** (Native Webview) | Empaqueta la interfaz del funcionario en una ventana nativa de escritorio (Windows 10/11 y Linux) sin Electron ni compilación pesada (< 60 MB RAM). |
| **Criptografía Backend** | Python Standard Library (`hashlib`, `hmac`, `secrets`, `unicodedata`) | Cero dependencias binarias externas complejas: SHA-256 canónico, HMAC-SHA256 con llave rotativa en RAM y normalización NFKC. |
| **Base de Datos** | **SQLite3 Endurecido** (`WAL`, `secure_delete`, Triggers SQL) / **PostgreSQL** | Modo local portable con triggers `BEFORE UPDATE/DELETE` de inmutabilidad y abstracción `StorageRepositoryProtocol` para escalar a PostgreSQL institucional. |
| **Interfaz de Usuario** | **HTML5 + CSS Moderno + Vanilla JS Modular** | Servida por Litestar en web y embebida por PyWebView en escritorio, 100% autónoma sin CDNs externos (Air-Gapped). |

---

## 7. Modelo de Datos (`ledger_blocks`)
Esquema de la tabla inmutable en SQLite3 / PostgreSQL:
- `block_index` (`INTEGER PRIMARY KEY`)
- `request_id` (`TEXT NOT NULL UNIQUE`)
- `timestamp_utc` (`TEXT NOT NULL`)
- `blind_citizen_id` (`TEXT NOT NULL` — HMAC-SHA256 irreversible de la Cédula)
- `payload_hash` (`TEXT NOT NULL` — SHA-256 del contenido sanitizado)
- `prev_hash` (`TEXT NOT NULL` — Enlace al `block_hash` anterior)
- `block_hash` (`TEXT NOT NULL` — Hash canónico del bloque)
- `hmac_signature` (`TEXT NOT NULL` — Sello HMAC-SHA256 generado con la clave maestra en RAM)
- `security_verdict` (`TEXT NOT NULL` — `CLEAN` / `BLOCKED_INJECTION` / etc.)
- `model_recommendation` (`TEXT NOT NULL` — `PRIORIDAD_ALTA` / `REVISION_ESTANDAR` / etc.)
- `human_decision` (`TEXT NOT NULL`)
- `human_override` (`INTEGER NOT NULL DEFAULT 0`)
- `override_justification` (`TEXT`)
- `citizen_receipt_code` (`TEXT NOT NULL UNIQUE`)

---

## 8. Uso de IA y Ética Algorítmica (Declaración Oficial)

| Pregunta Obligatoria | Declaración Técnica Oficial |
|---|---|
| **¿Usas IA en tu solución?** | Sí (con arquitectura híbrida soberana). |
| **¿Qué modelo usas y por qué?** | Conector triple desacoplado: 1) Modelos locales en intranet institucional vía Ollama/llama.cpp (`Qwen2.5-1.5B`, `Llama-3.2-1B`), 2) Nubes híbridas compatibles con OpenAI API, y 3) Adaptador determinista offline institucional ante fallos de conectividad. |
| **¿Qué problema resuelve la IA?** | Asiste al funcionario resumiendo expedientes extensos y redactando respuestas orientativas, operando exclusivamente sobre texto previamente anonimizado. |
| **¿Qué datos procesa?** | Únicamente texto sanitizado por `SHIELD` (`[CEDULA_1]`, `[RIF_1]`, `[PHONE_1]`, `[CLINICAL_1]`). Cero PII en texto plano llega al LLM. |
| **¿Cómo evitas sesgos?** | El LLM no decide prioridades. La evaluación cuantitativa la realiza el módulo matemático `EXPLICA` con Regresión Logística White-Box sobre variables objetivas y coeficientes fijos, sin `random()`. |
| **¿Cómo explicas las decisiones?** | Cada cálculo desglosa contribuciones directas ($\beta_j x_j$) y valores SHAP lineales ($\phi_j$) en la interfaz, con aviso visible de contenido asistido por IA. |
| **¿Qué hace la IA y qué hace el humano?** | La máquina propone una recomendación fundada; el funcionario humano toma la decisión administrativa vinculante, registrando justificación obligatoria en caso de override. |
| **¿Usaste IA para programar?** | Sí, bajo metodología SDD estricta (especificación viva en `specs/`, contratos tipados, implementación modular y pruebas unitarias `pytest` por cada criterio de aceptación). |
