# SPEC — Aduana IA: Pasarela Soberana de Gobernanza Zero-Trust

> **Estado:** Especificación inicial aprobada antes de implementar código (Regla de Oro SDD — Hackathon UNETI IA 2026).

## 1. Problema
La adopción acelerada de Modelos de Lenguaje (LLMs) en organismos públicos y procesos administrativos en Venezuela expone datos ciudadanos protegidos (Cédula de Identidad, RIF, números telefónicos, cuentas bancarias de 20 dígitos y diagnósticos médicos) cuando expedientes completos se envían sin control a APIs externas o herramientas personales (*Shadow AI*). Esta práctica compromete la confidencialidad y el principio de *Habeas Data* (CRBV Arts. 28 y 60).

Adicionalmente, el uso directo de IA generativa en trámites sociales o administrativos introduce tres fallas operativas críticas: 1) vulnerabilidad ante ataques de *Prompt Injection* o *Jailbreak* capaces de manipular respuestas o exfiltrar instrucciones internas, 2) opacidad algorítmica ("caja negra") que impide justificar ante una contraloría por qué se priorizó un expediente sobre otro, y 3) registros de auditoría mutables que pueden ser alterados internamente sin dejar rastro criptográfico.

## 2. Usuarios
- **Ciudadanos:** Solicitantes de trámites sociales o administrativos que requieren consentimiento explícito, protección de su PII y un comprobante verificable de procesamiento.
- **Funcionarios Públicos:** Analistas que utilizan la pasarela como apoyo de resumen y priorización matemática transparente, manteniendo siempre la decisión vinculante (*Human-in-the-Loop*).
- **Contraloría / Auditores:** Supervisores internos o de seguridad (CNTI / SUSCERTE) encargados de verificar la integridad matemática del Ledger en D1 y auditar métricas de mitigación adversaria.

## 3. Alcance del MVP
- **SÍ hará (48h):**
  - Pipeline secuencial en TypeScript sobre Cloudflare Pages Functions / Workers: `Consent` → `SHIELD` → `GUARD-IN` → `Workers AI (con Fallback Determinista)` → `GUARD-OUT` → `EXPLICA` → `LEDGER`.
  - Interfaz dual local-first en Cloudflare Pages (`Panel del Funcionario` y `Panel de Contraloría / Auditoría`) sin dependencias de CDNs externos.
  - Persistencia inmutable (*Append-Only*) en Cloudflare D1 con detección de sabotaje SHA-256 + HMAC y benchmark reproducible de 100 prompts (`data/attack_benchmark.json`).
- **NO hará (fuera de alcance del MVP):**
  - Integración directa en producción con bases de datos legadas del SAIME, SENIAT o IVSS (se emplearán casos y datasets sintéticos auditables).
  - Despliegue de modelos LLM auto-hospedados con GPU dedicada en el Hackathon (se usará Cloudflare Workers AI con respaldo determinista offline).

## 4. Requisitos funcionales
- **RF0 (Consentimiento y Tasa):** Rechazar con estado `BLOCKED_NO_CONSENT` toda solicitud sin consentimiento explícito (`granted === true` y `purpose_code`), generando `consent_hash` SHA-256 y aplicando límite de tasa usando `blind_citizen_id`.
- **RF1 (`SHIELD`):** Detectar y enmascarar de forma determinista Cédulas venezolanas, RIFs (validando dígito verificador Módulo 11 SENIAT con pesos `[4,3,2,7,6,5,4,3,2]`), teléfonos nacionales, cuentas de 20 dígitos, correos y términos clínicos sensibles mediante tokens consistentes (`[CEDULA_1]`, `[RIF_1]`, `[PHONE_1]`, `[CLINICAL_1]`) sin escribir PII en texto plano en D1.
- **RF2 (`GUARD-IN` y `GUARD-OUT`):** Normalizar texto con Unicode `NFKC`, remover caracteres *zero-width*, inspeccionar cargas codificadas (`Base64`/`Hex`), calcular un `risk_score` determinista, aislar el texto en delimitadores XML e inyectar un `canary_token` HMAC dinámico por transacción; verificar en `GUARD-OUT` que no existan fugas del Canary, PII residual ni etiquetas XSS.
- **RF3 (`EXPLICA` White-Box + Human-in-the-Loop):** Evaluar la prioridad del trámite mediante Regresión Logística determinista (coeficientes estáticos $\beta$ y medias $\mu$ sin `Math.random()`), devolviendo probabilidad sigmoide, contribuciones $\beta_j x_j$ y valores SHAP lineales $\phi_j = \beta_j(x_j - \mu_j)$, exigiendo justificación escrita ($\ge 20$ caracteres) si el funcionario sobrescribe la recomendación.
- **RF4 (`LEDGER` D1 Inmutable):** Registrar cada transacción en Cloudflare D1 encadenada con SHA-256 (`prev_hash` → `block_hash`) y firmada con `HMAC-SHA256` (secreto en Cloudflare Secrets), proveyendo verificación completa de cadena y un modo controlado de simulación de sabotaje para demostración de auditoría.

## 5. Criterios de aceptación
- **CA-01 (`SHIELD`):** Dado un texto mixto con Cédula, RIF válido Módulo 11, teléfono venezolano, cuenta bancaria de 20 dígitos y diagnóstico clínico, cuando pase por `SHIELD`, entonces el 100% de los identificadores estructurados quedan tokenizados (`[CEDULA_1]`, `[RIF_1]`, etc.), se genera `blind_citizen_id` HMAC y el mapa de reversión no se persiste en D1 (`< 20 ms`).
- **CA-02 (`GUARD-IN` / `GUARD-OUT`):** Dado el benchmark `data/attack_benchmark.json` (50 consultas benignas + 50 ataques de inyección/jailbreak/ofuscación), cuando se ejecute `run_security_benchmark()`, entonces alcanza $\text{TPR} \ge 88\%$, $\text{FPR} \le 4\%$ y bloquea el 100% de fugas del Canary dinámico (`< 25 ms` por prompt).
- **CA-03 (`LEDGER`):** Dada una alteración manual en cualquier fila histórica de `ledger_blocks` en D1 (incluso recalculando `block_hash` sin la llave secreta HMAC), cuando se invoque `/api/v1/ledger/verify`, entonces retorna `is_valid: false`, el `corrupted_block_index` exacto y el motivo (`HASH_MISMATCH`, `PREV_HASH_LINK_BROKEN` o `HMAC_SIGNATURE_FORGED`).
- **CA-04 (`EXPLICA`):** Dado cualquier vector de entrada $\mathbf{x}$, cuando `EXPLICA` calcule $P(y=1 \mid \mathbf{x})$, entonces $\left|(\beta_0 + \sum \beta_j x_j) - z\right| < 10^{-9}$ y cero uso de `Math.random()`.
- **CA-05 (`Zero-Plaintext-PII`):** Dado el procesamiento de 20 trámites con PII simulado, cuando se inspeccionen los registros persistidos en D1 y los logs de ejecución, entonces existen 0 ocurrencias de Cédulas, RIFs, teléfonos o nombres originales en texto plano.
- **CA-06 (`Resiliencia`):** Dado un fallo o timeout de Workers AI, cuando el *Circuit Breaker* conmute al adaptador determinista offline, entonces el sistema entrega la evaluación matemática de `EXPLICA` y sella el bloque en D1 sin interrumpir la atención.

## 6. Arquitectura
- **Frontend:** Cloudflare Pages (`static/` con HTML5, CSS local y Vanilla JS modular, sin CDNs externos).
- **Backend:** Cloudflare Pages Functions (`functions/api/` en TypeScript, Web Crypto API `crypto.subtle`, consumo estricto dentro del presupuesto de `10 ms` CPU por invocación en Workers Free).
- **Base de datos:** Cloudflare D1 (`schema.sql`, SQLite serverless en el edge para `ledger_blocks`).
- **IA:** Cloudflare Workers AI (`env.AI`) con respaldo determinista institucional ante fallos o cuota agotada.
- **Servicios Cloudflare usados:** Pages, Pages Functions / Workers, D1, Workers AI, KV (opcional para tokens efímeros con `expirationTtl: 180`) y Secrets (`wrangler secret put`).

## 7. Modelo de datos
Tabla principal en Cloudflare D1 (`ledger_blocks` en `schema.sql`):
- `block_index` (`INTEGER PRIMARY KEY`)
- `request_id` (`TEXT NOT NULL UNIQUE`)
- `timestamp_utc` (`TEXT NOT NULL`)
- `blind_citizen_id` (`TEXT NOT NULL` — Hash HMAC-SHA256 irreversible)
- `payload_hash` (`TEXT NOT NULL` — SHA-256 del paquete sanitizado)
- `prev_hash` (`TEXT NOT NULL` — Enlace al `block_hash` del bloque anterior)
- `block_hash` (`TEXT NOT NULL` — SHA-256 canónico del bloque)
- `hmac_signature` (`TEXT NOT NULL` — Sello HMAC-SHA256 con secreto de servidor)
- `security_verdict` (`TEXT NOT NULL` — `CLEAN` / `BLOCKED_*`)
- `model_recommendation` (`TEXT NOT NULL`)
- `human_decision` (`TEXT NOT NULL`)
- `human_override` (`INTEGER NOT NULL DEFAULT 0`)
- `override_justification` (`TEXT`)
- `citizen_receipt_code` (`TEXT NOT NULL`)

## 8. Uso de IA (obligatorio)
- **¿Qué modelo usas?** `@cf/zai-org/glm-4.7-flash` vía Cloudflare Workers AI (con respaldo configurable `@cf/meta/llama-3.1-8b-instruct` y adaptador determinista offline).
- **¿Para qué lo usas?** Redacción de resúmenes institucionales y estructuración preliminar de contexto a partir de solicitudes ciudadanas ya anonimizadas.
- **¿Qué datos le envías?** ÚNICAMENTE texto sanitizado por `SHIELD` (ej. `"La ciudadana [CEDULA_1] solicita apoyo médico por [CLINICAL_1]..."`). CERO PII real.
- **¿Cómo mitigas sesgos?** Desacoplando el LLM generativo del puntaje de prioridad: la evaluación cuantitativa la ejecuta exclusivamente `EXPLICA` mediante Regresión Logística White-Box determinista sobre variables estandarizadas.
- **¿Cómo explicas sus decisiones al usuario?** Mediante el desglose gráfico y numérico de contribuciones directas ($\beta_j x_j$) y valores SHAP lineales ($\phi_j = \beta_j(x_j - \mu_j)$) en el Panel del Funcionario, junto con etiqueta explícita de contenido asistido por IA.
- **¿Qué hace la IA y qué hace el humano?** La IA resume el expediente sanitizado y `EXPLICA` emite una recomendación matemática fundada; el funcionario humano toma la decisión vinculante (confirmar o sobrescribir con justificación obligatoria $\ge 20$ caracteres registrada en el Ledger).

## 9. Ética y privacidad
- **Datos personales tratados:** Cédula, RIF, teléfono, cuenta bancaria de 20 dígitos, correo y condiciones clínicas sensibles (tratados únicamente de forma transitoria en memoria de ejecución / KV efímero con TTL máximo de 180s).
- **Consentimiento:** Validación obligatoria del consentimiento ciudadano (`granted: true`, `purpose_code`) antes de ejecutar el pipeline, generando `consent_hash` auditable.
- **Retención:** Política *Zero-Plaintext-PII* en disco y en D1. El mapa de reversión se destruye al finalizar la transacción; D1 conserva únicamente índices ciegos HMAC y hashes SHA-256.
- **Riesgos identificados y mitigación:**
  - *Exfiltración hacia LLM:* mitigado con `SHIELD` antes de invocar `env.AI`.
  - *Prompt Injection / Fuga de sistema:* mitigado con normalización `NFKC`, scoring heurístico, sandbox XML y Canary HMAC verificado en `GUARD-OUT`.
  - *Sabotaje interno de base de datos:* mitigado con cadena SHA-256 + doble firma HMAC y verificación íntegra en `/api/v1/ledger/verify`.

## 10. Métricas de éxito
- Detección de PII estructurado venezolano: **100% Recall** en `CA-01`, `< 20 ms`.
- Defensa contra Prompt Injection en benchmark de 100 casos: **TPR $\ge 88\%$**, **FPR $\le 4\%$**, `< 25 ms`.
- Error de reconstrucción del *logit* en `EXPLICA`: **$< 10^{-9}$** sin llamadas aleatorias.
- Detección de alteración en cadena D1 (`LEDGER`): **100% detección** con identificación exacta de bloque y causa.
- Presupuesto de ejecución en Edge: procesamiento de seguridad y auditoría dentro del límite de **10 ms CPU** del plan gratuito de Cloudflare Workers.

---

## Declaración Obligatoria de Uso de IA (Paso 0.2)

| Pregunta | Respuesta |
|---|---|
| ¿Usas IA en tu solución? | Sí |
| ¿Qué modelo y por qué? | `@cf/zai-org/glm-4.7-flash` vía Cloudflare Workers AI por su baja latencia en el edge, seguimiento de instrucciones en español y disponibilidad en el plan gratuito del hackathon (con respaldo `@cf/meta/llama-3.1-8b-instruct` y modo determinista). |
| ¿Qué problema resuelve la IA? | Asiste al funcionario resumiendo y estructurando solicitudes ciudadanas largas de forma rápida sin reemplazar el criterio humano ni el cálculo matemático. |
| ¿Qué datos procesa? | Exclusivamente texto previamente anonimizado por `SHIELD` (tokens `[CEDULA_1]`, `[RIF_1]`, `[PHONE_1]`, `[CLINICAL_1]`). Nunca recibe Cédulas, RIFs ni datos personales reales. |
| ¿Cómo evitas sesgos? | El LLM tiene prohibido decidir prioridades o aprobar trámites; el puntaje proviene de un modelo lineal auditado (`EXPLICA`) con pesos fijos y transparentes, sin variables protegidas discriminatorias ni `Math.random()`. |
| ¿Cómo explicas las decisiones? | Cada puntaje muestra sus pesos directos ($\beta_j x_j$) y valores SHAP lineales ($\phi_j$) en el Panel del Funcionario, y la interfaz identifica explícitamente la salida generada por IA. |
| ¿Qué decides tú y qué decide la IA? | La IA resume texto sanitizado y `EXPLICA` propone una recomendación; el funcionario humano decide aprobar, revisar o hacer *override* justificado (decisión final vinculante). |
| ¿Usaste IA para programar? | Sí (bajo metodología SDD: especificación primero, contratos tipados, código y verificación por criterios de aceptación). |
| ¿Qué herramientas? | Antigravity, Claude, ChatGPT y Gemini. |

