# 🏛️ ADUANA IA: Ingeniería de Requisitos, Modelo de Negocio GovTech, Plan MVP en 48h y Estrategia de Venta al Jurado

> **Documento Maestro de Ejecución y Negocio (v2.1 — Cloudflare Edge & TypeScript)**  
> **Evento:** Hackathon UNETI IA 2026 $\rightarrow$ *Venezuela Innova*  
> **Documentos Base Sincronizados:** [SPEC.md](../SPEC.md) + [README.md](../README.md) + [PROMPT_MAESTRO.md](../PROMPT_MAESTRO.md)  
> **Propósito:** Servir como respaldo formal de ingeniería de software (SRS), viabilidad económica/institucional, plan táctico de construcción en 48 horas sobre **Cloudflare (Pages, Pages Functions/Workers, D1, Workers AI y KV)** con **TypeScript estricto**, y guion de defensa ante el jurado evaluador.

---

## 📐 PARTE 1: DOCUMENTO DE INGENIERÍA DE REQUISITOS (SRS ADAPTADO A SDD)

### 1.1 Propósito y Alcance del Sistema
**Aduana IA** es una pasarela soberana de seguridad, anonimización, explicabilidad matemática y auditoría criptográfica (*AI Security & Governance Gateway*) diseñada para interceptar, sanitizar, evaluar y sellar en tiempo real toda transacción entre usuarios de instituciones públicas/reguladas venezolanas y modelos de Inteligencia Artificial ejecutados en el *Edge* (**Cloudflare Workers AI** o adaptadores institucionales).

### 1.2 Actores y Perfiles de Usuario (*Stakeholders*)

| Actor | Rol en el Ecosistema | Necesidad Principal | Interfaz que Utiliza |
| :--- | :--- | :--- | :--- |
| **Ciudadano Venezolano** | Titular de los datos personales y solicitante del trámite público. | Que sus datos sensibles (Cédula, RIF, salud, ingresos) no se filtren al LLM ni al disco, y contar con un recibo verificable. | Recibo Criptográfico de Auditoría (`citizen_receipt_code`). |
| **Funcionario Analista** | Operador público encargado de evaluar y decidir sobre el trámite (*Human-in-the-Loop*). | Resúmenes ágiles de trámites asistidos por IA y un puntaje matemático transparente que respalde su decisión administrativa. | **🖥️ Panel del Funcionario** (Triaje, Explicabilidad SHAP y Decisión Humana). |
| **Auditor / Contralor** | Inspector de Contraloría Interna, SUSCERTE o Seguridad de la Información. | Comprobar matemáticamente que el historial de decisiones en Cloudflare D1 no fue alterado y auditar la resistencia a ataques. | **🔍 Panel de Auditoría y Contraloría** (Verificador Ledger D1 + Benchmark 100 ataques). |
| **Administrador / DevOps** | Responsable de despliegue e infraestructura serverless en el Edge. | Servicio ligero en **TypeScript**, dentro del presupuesto de **$< 10\text{ ms}$ CPU** del plan gratuito de Cloudflare Workers, sin llaves expuestas en código. | API `/api/v1/health/system`, `wrangler.jsonc` y Cloudflare Secrets. |

---

### 1.3 Catálogo de Requisitos Funcionales (RF) Trazables al Pipeline

#### Módulo 0: Consentimiento Informado y Protección de Tasa (Idea #8)
* **RF-01 (Validación de Consentimiento Explícito):** El sistema debe rechazar con estado `BLOCKED_NO_CONSENT` cualquier petición donde `citizen_consent.granted` sea `false` o carezca de propósito declarado (`purpose_code`).
* **RF-02 (Sello Criptográfico de Consentimiento):** El sistema debe generar un `consent_hash` (`SHA-256` mediante Web Crypto API `crypto.subtle`) vinculando `request_id`, `timestamp_utc` y `purpose_code`.
* **RF-03 (Control de Abuso sin Exposición de Identidad):** El sistema debe limitar la tasa de peticiones por ciudadano utilizando su índice ciego (`blind_citizen_id`) en memoria/KV sin almacenar su Cédula en texto plano.

#### Módulo 1: `SHIELD` — Anonimización Determinista y Almacenamiento Restrictivo (Ideas #6 y #8)
* **RF-04 (Detección y Enmascaramiento Estructurado Nacional):** El sistema debe detectar y sustituir por tokens indexados consistentes (`[CEDULA_1]`, `[RIF_1]`, `[PHONE_1]`, `[BANK_1]`, `[EMAIL_1]`) toda Cédula venezolana (`V/E`), RIF (`V/E/J/G/P/C`), teléfono nacional (`0412/0414/0424/0416/0426/0212...`), correo y cuenta bancaria de 20 dígitos.
* **RF-05 (Validación Matemática Módulo 11 SENIAT):** Cuando se detecte un patrón de RIF, el sistema debe ejecutar el algoritmo oficial Módulo 11 del SENIAT (mapeo `{"V":1,"E":2,"J":3,"P":4,"G":5,"C":3}` y vector de 9 pesos `[4,3,2,7,6,5,4,3,2]`) y registrar en `shield_meta.rif_mod11_verified` la autenticidad matemática del documento.
* **RF-06 (Reconocimiento Léxico Contextual de Salud e Identidad):** El sistema debe enmascarar nombres propios precedidos por marcadores contextuales de trámite y términos clínicos sensibles incluidos en el diccionario local de protección de salud (`[CLINICAL_1]`).
* **RF-07 (Bóveda Efímera y Zeroization):** El mapeo entre tokens (`[CEDULA_1]`) y el valor original (`V-12.345.678`) debe mantenerse únicamente en memoria volátil de ejecución (destruida al responder) o en **Cloudflare KV** con `expirationTtl: 180` y purga explícita (`zeroize()`), **jamás en Cloudflare D1**.

#### Módulo 2: `GUARD-IN` — Defensa Activa contra Prompt Injection (Idea #18)
* **RF-08 (Normalización Anti-Evasión):** Antes de inspeccionar el texto, el sistema debe aplicar `text.normalize("NFKC")`, eliminar caracteres invisibles (*zero-width*) y decodificar cadenas sospechosas en `Base64` o `Hex` embebidas.
* **RF-09 (Cálculo Determinista de Riesgo Adversario):** El sistema debe evaluar el texto frente a reglas heurísticas y similitud léxica (intentos de *override* de instrucciones, *jailbreak*, *roleplay* malicioso, inyección SQL/comandos y exfiltración de prompt), generando un `risk_score` continuo en $[0.0, 1.0]$ sin usar `Math.random()`, bloqueando entradas por encima del umbral ($\ge 0.65$).
* **RF-10 (Encapsulamiento XML Sandbox y Canary Token Dinámico):** Toda solicitud permitida hacia el LLM debe envolverse en etiquetas estructurales `<instruccion_institucional_inmutable>` y `<entrada_ciudadano>`, inyectando un token único por transacción firmado con HMAC vía `crypto.subtle` (`[[CANARY-HMAC-XXXXXXXX]]`).

#### Módulo de Interconectividad: `LLMAdapter` (Workers AI) y `CircuitBreaker`
* **RF-11 (Conmutación Agnóstica de Proveedor IA):** El sistema debe procesar únicamente `masked_text` mediante una interfaz común `LLMAdapter` con soporte para **Cloudflare Workers AI (`env.AI`)** (`@cf/zai-org/glm-4.7-flash` y respaldo `@cf/meta/llama-3.1-8b-instruct`) y el **Motor Institucional Determinista (`OfflineDeterministicAdapter`)**.
* **RF-12 (Degradación Elegante por Circuit Breaker):** Si Workers AI supera el timeout de `3500 ms`, devuelve error o agota cuota (`10k neurons/día`), el `CircuitBreaker` debe conmutar automáticamente a `OfflineDeterministicAdapter` para garantizar que el funcionario reciba siempre el dictamen matemático de `EXPLICA` y el sellado en `LEDGER`.

#### Módulo 3: `GUARD-OUT` — Inspección de Salida y Prevención de Fugas (Idea #18)
* **RF-13 (Detección de Fuga de Canary y PII Residual):** El sistema debe inspeccionar la respuesta del LLM y abortar su entrega si contiene total o parcialmente el `canary_token` de la sesión o si detecta cualquier patrón de PII residual/alucinado.
* **RF-14 (Sanitización de Salida Segura y Aviso de IA):** El sistema debe neutralizar etiquetas ejecutables (`<script>`, `onload=`, `javascript:`), marcar afirmaciones sin respaldo institucional e indicar explícitamente en la respuesta (`ai_generated_notice: true`) cuándo el resumen fue generado por IA.

#### Módulo 4: `LEDGER` — Registro Criptográfico Inmutable en Cloudflare D1 (Idea #17)
* **RF-15 (Encadenamiento SHA-256 y Doble Sello HMAC):** Cada transacción finalizada debe registrarse en la tabla `ledger_blocks` de **Cloudflare D1 (`env.DB`)** como un bloque secuencial $i$ cuyo `block_hash` dependa criptográficamente de `prev_hash` ($H_{i-1}$), `payload_hash`, `timestamp_utc` y `blind_citizen_id`, acompañado de `hmac_signature` calculada con `env.LEDGER_HMAC_KEY` (almacenada en Cloudflare Secrets).
* **RF-16 (Auditoría Completa y Detección Quirúrgica de Sabotaje):** El sistema debe proveer `verifyChain()` en `/api/v1/ledger/verify` que recalcule hashes y firmas HMAC con `crypto.subtle` desde el bloque génesis hasta el último bloque, identificando el `corrupted_block_index` exacto y el motivo (`HASH_MISMATCH`, `PREV_HASH_LINK_BROKEN` o `HMAC_SIGNATURE_FORGED`).
* **RF-17 (Simulador de Sabotaje en Vivo y Recibo Ciudadano):** El sistema debe incluir en el Panel de Contraloría un endpoint controlado de demostración (`/api/v1/ledger/tamper-sim`) para alterar un registro histórico de prueba en D1 y evidenciar en vivo la detección criptográfica, además de emitir `citizen_receipt_code` por trámite.

#### Módulo 5: `EXPLICA` — Modelo Matemático White-Box y Human-in-the-Loop (Idea #5)
* **RF-18 (Evaluación Tabular con Regresión Logística Determinista):** El sistema debe calcular la probabilidad de prioridad/elegibilidad del trámite mediante la función sigmoide $P(y=1\mid\mathbf{x}) = \frac{1}{1+e^{-(\beta_0 + \sum \beta_j x_j)}}$ utilizando coeficientes $\beta$ y medias $\mu$ calibrados de forma determinista sobre `data/synthetic_tramites.csv` e embebidos como constantes auditables en TypeScript (cero `Math.random()`).
* **RF-19 (Desglose de Pesos y Valores SHAP Lineales):** El sistema debe exponer para cada variable del trámite su aporte directo ($\beta_j x_j$) y su valor SHAP lineal centrado respecto a la media poblacional ($\phi_j = \beta_j(x_j - \mu_j)$), verificando que la suma algebraica reconstruya el *logit* $z$ con error $< 10^{-9}$.
* **RF-20 (Soberanía de Decisión Humana con Justificación de Override):** El sistema debe exigir confirmación del funcionario antes de sellar el dictamen (`PRIORIDAD_ALTA`, `REVISION_ESTANDAR`, `RECAUDOS_INCOMPLETOS`); si el funcionario sobrescribe la recomendación matemática (`human_override = true`), se exige una justificación escrita ($\ge 20$ caracteres) que queda grabada en D1.

---

### 1.4 Requisitos No Funcionales (RNF) y Restricciones de Calidad

| Código | Categoría | Especificación Medible y Verificable |
| :---: | :--- | :--- |
| **RNF-01** | **Presupuesto CPU Edge** | El procesamiento de seguridad, matemática `EXPLICA` y verificación criptográfica (`SHIELD` + `GUARD-IN` + `GUARD-OUT` + `EXPLICA` + `LEDGER` hashing, excluyendo I/O de red/D1/Workers AI) debe ejecutarse dentro del límite de **$< 10\text{ ms}$ de CPU** por invocación del plan gratuito de Cloudflare Workers. |
| **RNF-02** | **Cero PII en D1 y Logs** | **0 bytes** de Cédulas, RIFs, teléfonos o nombres originales pueden persistirse en tablas de Cloudflare D1 ni imprimirse en logs (`console.log`/`console.error`). |
| **RNF-03** | **Arquitectura Serverless Edge** | Implementación 100% en **TypeScript estricto (`strict: true`)** sobre **Cloudflare Pages + Pages Functions / Workers**, usando Web Crypto API (`crypto.subtle`) sin dependencias nativas pesadas ni servidores GPU dedicados. |
| **RNF-04** | **Frontend Autónomo Sin CDNs** | La interfaz web en `static/` debe servir CSS y JS locales sin llamadas a CDNs externos de estilos, fuentes o librerías. |
| **RNF-05** | **Efectividad Adversaria** | Tasa de Mitigación (**TPR**) $\ge 88\%$ y Tasa de Falsos Positivos (**FPR**) $\le 4\%$ medida automáticamente sobre `data/attack_benchmark.json` ($N=100$ prompts). |
| **RNF-06** | **Endurecimiento D1 y Secretos** | Tabla `ledger_blocks` definida en `schema.sql` con restricciones *Append-Only* (`BEFORE UPDATE/DELETE` triggers SQLite validados en `wrangler d1 execute`) y llaves maestras (`LEDGER_HMAC_KEY`, `INSTITUTION_SALT`) gestionadas exclusivamente vía `wrangler secret put` / `.dev.vars`. |

---

## 💼 PARTE 2: ESTRUCTURA Y MODELO DE NEGOCIO (GOVTECH & B2B REGULADO)

Un jurado de hackathon (y especialmente el jurado de *Venezuela Innova*) no solo evalúa que el código funcione: evalúa **si el proyecto es sostenible, escalable y resuelve un dolor económico e institucional real**.

### 2.1 El Caso de Negocio: ¿Por qué el Estado y la Banca Venezolana necesitan adoptar Aduana IA hoy?

Actualmente, las instituciones públicas y empresas reguladas en Venezuela enfrentan una **paradoja paralizante** frente a la Inteligencia Artificial:
1. **Si prohíben la IA:** Pierden productividad, mantienen colas lentas en atención ciudadana y sus propios empleados terminan usando cuentas personales gratuitas desde sus teléfonos móviles, **filtrando datos críticos del Estado sin ningún control (*Shadow AI*)**.
2. **Si conectan formularios directo a LLMs externos sin pasarela:** Violan el principio de *Habeas Data* (CRBV Art. 60), exponen PII ciudadano, quedan vulnerables a *Prompt Injection* y pagan cómputo procesando spam o ataques.
3. **Si intentan comprar granjas de GPUs propias desde cero:** Requieren inversiones de decenas de miles de dólares fuera del alcance de alcaldías, hospitales o universidades.

> **La Solución Económica de Aduana IA:** Al construirse como una pasarela ultraligera en **TypeScript sobre arquitectura Edge (Cloudflare Workers + D1 + Workers AI)** y estándares web abiertos (**GNU GPL v3**), cualquier organismo puede desplegar pilotos inmediatos a **costo inicial cero** sobre infraestructura serverless o adaptar el mismo repositorio mediante la interfaz `StorageRepository` y `LLMAdapter` hacia centros de datos institucionales propios con **cero fugas de datos y auditoría de nivel contraloría desde el día 1**.

---

### 2.2 Segmentación de Mercado (Doble Motor: B2G Público + B2B Regulado)

| Segmento | Clientes Objetivo en Venezuela | Dolor Específico que Resuelve Aduana IA |
| :--- | :--- | :--- |
| **1. Sector Público Social y Trámites (B2G)** | Ministerios (Salud, Educación Universitaria, Trabajo, Alimentación), IVSS, SAIME, SENIAT, SAREN, Gobernaciones y Alcaldías. | Triaje rápido de solicitudes ciudadanas con priorización matemática justa (`EXPLICA`), protección de datos (`SHIELD`) y auditoría anticorrupción (`LEDGER` D1). |
| **2. Sector Financiero y Asegurador (B2B Regulado)** | Banca Pública y Banca Privada Nacional, Aseguradoras. | Cumplimiento de controles de privacidad **SUDEBAN** al usar IA en atención de reclamos, análisis explicable (`EXPLICA`) y enmascaramiento de cuentas de 20 dígitos y RIFs. |
| **3. Sector Salud y Universitario (B2G / B2B)** | Red Hospitalaria, Clínicas privadas, UNETI y Universidades Nacionales. | Protección de historias clínicas sensibles antes de generar resúmenes asistidos por IA y asignación transparente de becas o cupos. |

---

### 2.3 Modelo de Sostenibilidad e Ingresos (Compatible con la Ley de Infogobierno)

Dado que la **Ley de Infogobierno de Venezuela** establece el uso de Software Libre y estándares abiertos en la Administración Pública, el repositorio base se publica bajo **GNU GPL v3** y se sostiene mediante un **Modelo Dual Open-Core**:

1. **Línea 1 — Núcleo Abierto Soberano (*GovTech Open Standard*):**
   - Motor base auditable y libre (`GNU GPL v3`) para universidades y pilotos estatales, alineado con lineamientos de interoperabilidad **CNTI / SUSCERTE**.
2. **Línea 2 — Contratos de Implantación, Integración y Calibración Institucional (B2G):**
   - Servicios especializados de ingeniería: integración de `StorageRepository` con bases de datos institucionales existentes, despliegue en nube privada o Edge dedicado, y **calibración a medida de modelos `EXPLICA`** según las reglas de negocio de cada ministerio.
3. **Línea 3 — Suscripción de Inteligencia de Amenazas (*Aduana Threat-Feed*):**
   - Actualización periódica de reglas heurísticas `GUARD-IN` contra nuevos vectores de *Jailbreak* y actualización de diccionarios regulatorios de `SHIELD`.
4. **Línea 4 — Licenciamiento Enterprise SLA para Banca, Seguros y Clínicas Privadas (B2B):**
   - Soporte 24/7, alta disponibilidad, paneles de cumplimiento normativo y auditoría extendida para el sector financiero y de salud privado, financiando la evolución continua de la plataforma pública.

---

### 2.4 Impacto Cuantificable (Objetivos de Valor para el Pitch)

| Indicador de Impacto | Sin Aduana IA (Uso Directo / Manual) | Con Aduana IA Desplegada | Beneficio Neto Demostrable |
| :--- | :---: | :---: | :--- |
| **Exposición de PII Ciudadano al LLM** | $100\%$ de los datos enviados en claro | **$0\%$** (Tokenizado en $< 20\text{ ms}$) | Resguardo efectivo de privacidad (CRBV Art. 60). |
| **Costo de Arranque del MVP / Piloto** | Requiere servidores dedicados o GPUs | **\$0 inicial** (Cloudflare Free Tier, `< 10 ms` CPU) | Adopción inmediata sin fricción de infraestructura. |
| **Ahorro en Consumo de Cómputo IA** | Paga por ataques, spam y prompts fallidos | **Reducción estimada $35\% - 60\%$** | `SHIELD` y `GUARD-IN` bloquean abuso antes de invocar `env.AI`. |
| **Tiempo de Auditoría de Contraloría** | Semanas revisando expedientes manuales | **Milisegundos** (`/api/v1/ledger/verify`) | Detección instantánea de cualquier alteración o *override*. |

---

## ⚡ PARTE 3: PLAN DE CONSTRUCCIÓN DEL MVP EN 48 HORAS SOBRE CLOUDFLARE (SPEC PRIMERO)

Para construir un sistema sólido en **48 horas** sin errores de integración entre compañeros y asistentes IA (**Antigravity + Claude + ChatGPT + Gemini**), todo código se genera estrictamente bajo el flujo SDD definido en [SPEC.md](../SPEC.md) y [PROMPT_MAESTRO.md](../PROMPT_MAESTRO.md).

### 3.1 División Estratégica del Trabajo (Orquestación de Herramientas IA)

| Herramienta / Rol | Especialidad en el Hackathon | Entregables Exactos que Debe Generar |
| :--- | :--- | :--- |
| **🟣 Antigravity / Claude** | **Arquitecto TypeScript, Criptografía Edge, D1 y Tests SDD** | `wrangler.jsonc`, `schema.sql`, `core/config.ts`, `core/context.ts`, `core/ephemeral_vault.ts`, `pipeline/stage1_shield.ts` (Módulo 11 SENIAT), `pipeline/stage2_guard_in.ts`, `pipeline/stage3_guard_out.ts`, `pipeline/stage4_ledger.ts` (D1 + `crypto.subtle`), `pipeline/stage5_explica.ts`, `pipeline/llm_adapter.ts` (`Workers AI` + `CircuitBreaker`), `functions/api/v1/*.ts` y suite `tests/*.test.js` (`node --test`). |
| **🟢 ChatGPT** | **Red Teamer, Datos Sintéticos y UI Cloudflare Pages** | `data/attack_benchmark.json` (100 prompts: 50 trámites benignos + 50 ataques en español venezolano), `data/synthetic_tramites.csv` (casos sociales coherentes para calibrar pesos de `EXPLICA`), `static/index.html`, `static/styles.css` (local sin CDNs) y `static/app.js`. |
| **🔵 Gemini** | **Auditor de Contexto Global, Integración y Pitch** | Revisión cruzada de que `static/app.js` consuma exactamente las llaves JSON de `AduanaPacket` v2.0 devueltas por `functions/api/v1/*`, redacción de `specs/01..05.spec.md`, verificación de cero `Math.random()` / cero PII en D1 y pulido del guion de 3 minutos. |

---

### 3.2 Regla de Oro para Cero Colisiones en el Equipo

Antes de pedir cualquier archivo a un asistente de código:
1. Cargar [SPEC.md](../SPEC.md) y [PROMPT_MAESTRO.md](../PROMPT_MAESTRO.md) (y mantener `.cursorrules` en raíz).
2. Exigir explícitamente: *"Respeta exactamente los tipos `readonly` de `core/context.ts`, las llaves JSON de `AduanaPacket` v2.0 y las APIs estándar de Cloudflare Workers (`env.DB`, `env.AI`, `env.KV`, `crypto.subtle`) dentro de 10 ms CPU"*.

---

### 3.3 Cronograma Táctico de 48 Horas

#### 🗓️ DÍA 1: Especificación, Base D1 y Motor del Pipeline en TypeScript

* **Bloque 1 (Horas 0 a 3) — Contrato, Wrangler y Esquema D1 (Gatillo 0):**
  * **Acción:** Crear `wrangler.jsonc`, `schema.sql` (`ledger_blocks`), `core/config.ts`, `core/context.ts` (`AduanaPacket` v2.0 en TypeScript) y `core/ephemeral_vault.ts`.
  * **Acción paralela de datos:** Generar `data/synthetic_tramites.csv` y `data/attack_benchmark.json` (50 consultas benignas + 50 ataques de Prompt Injection, DAN, Base64/Hex y fuga de Canary).
  * **Hito de Control (Hora 3):** `wrangler d1 execute aduana-db --local --file=schema.sql` aplicado y `node --test tests/test_ca05_restrictive_db.test.js` en verde.

* **Bloque 2 (Horas 3 a 8) — Etapas 1, 2 y 3: `SHIELD` + `GUARDIÁN` (Gatillos 1 y 2):**
  * **Integrante A:** Implementa `pipeline/stage1_shield.ts` (Regex venezolano, Módulo 11 SENIAT con 9 pesos `[4,3,2,7,6,5,4,3,2]`, diccionario clínico, tokens `[CEDULA_1]`/`[RIF_1]` y `blind_citizen_id` HMAC vía `crypto.subtle`). Ejecuta `node --test tests/test_ca01_shield.test.js`.
  * **Integrante B:** Implementa `pipeline/stage2_guard_in.ts` (normalización `NFKC`, decodificación Base64/Hex, heurísticas, XML Sandbox, Canary HMAC dinámico) + `pipeline/stage3_guard_out.ts` + `runSecurityBenchmark()`. Ejecuta `node --test tests/test_ca02_guardian.test.js` verificando $\text{TPR} \ge 88\%$ y $\text{FPR} \le 4\%$.
  * **Hito de Control (Hora 8):** `SHIELD` y `GUARDIÁN` pasan sus pruebas en `< 5 ms` CPU.

* **Bloque 3 (Horas 8 a 14) — Etapas 4 y 5: `LEDGER` D1 + `EXPLICA` (Gatillos 3 y 4):**
  * **Integrante A:** Implementa `pipeline/stage4_ledger.ts` sobre `StorageRepository` / **Cloudflare D1 (`env.DB`)** con encadenamiento SHA-256 + HMAC (`env.LEDGER_HMAC_KEY`), `verifyChain()` (`HASH_MISMATCH`, `PREV_HASH_LINK_BROKEN`, `HMAC_SIGNATURE_FORGED`) y `simulateTampering(blockIndex)`. Ejecuta `node --test tests/test_ca03_ledger.test.js`.
  * **Integrante B:** Calibra los pesos deterministas $\beta$ y medias $\mu$ sobre `data/synthetic_tramites.csv`, los fija en `pipeline/stage5_explica.ts`, implementa sigmoide + **Valores SHAP Lineales** $\phi_j = \beta_j(x_j - \mu_j)$ y validación de *Human Override* ($\ge 20$ caracteres). Ejecuta `node --test tests/test_ca04_explica.test.js`.
  * **Hito de Control (Hora 14 - Cierre Día 1):** Las 5 etapas en TypeScript pasan sus pruebas unitarias en consola con `node --test`.

---

#### 🗓️ DÍA 2: Workers AI, Pages Functions, Interfaz Dual y Despliegue en Vivo

* **Bloque 4 (Horas 14 a 18) — Workers AI, Circuit Breaker y Pages Functions (Gatillos 5 y 6 backend):**
  * **Acción:** Implementar `pipeline/llm_adapter.ts` (`WorkersAIAdapter` usando `env.AI.run('@cf/zai-org/glm-4.7-flash', ...)` + `OfflineDeterministicAdapter` + `CircuitBreaker` de 3.5s) y los endpoints en `functions/api/v1/` (`/api/v1/gateway/process`, `/api/v1/shield/inspect`, `/api/v1/ledger/verify`, `/api/v1/ledger/tamper-sim`, `/api/v1/metrics/benchmark`, `/api/v1/health/system`).
  * **Hito de Control (Hora 18):** `npm run dev` (`wrangler pages dev static`) levanta localmente y responde en `http://127.0.0.1:8787/api/v1/health/system` usando D1 y Workers AI emulados/remotos.

* **Bloque 5 (Horas 18 a 26) — Construcción del Panel Dual en `static/` (Pages):**
  * **Acción:** Construir `static/index.html`, `static/styles.css` (100% local, cero CDNs externos) y `static/app.js` consumiendo `functions/api/v1/*`:
    1. **Selector Rápido de Casos de Demo (1 Clic):** botones para *"Trámite Médico Legítimo con PII"*, *"Ataque Prompt Injection DAN"* y *"Ataque Ofuscado Base64"*.
    2. **Rayos-X del Pipeline en Vivo:** tarjetas secuenciales (`SHIELD` $\rightarrow$ `GUARD-IN` $\rightarrow$ `Workers AI` $\rightarrow$ `GUARD-OUT` $\rightarrow$ `EXPLICA` $\rightarrow$ `LEDGER D1`) comparando entrada cruda vs. texto enmascarado (`[CEDULA_1]`, `[RIF_1]`) y mostrando aviso de contenido generado por IA.
    3. **Gráfico Horizontal de Barras SHAP en `EXPLICA`:** contribuciones positivas y negativas, más botones de **Confirmar Recomendación** o **Sobrescribir con Justificación** ($\ge 20$ caracteres).
    4. **Consola de Contraloría Interactiva:** bloques encadenados de D1, botón **"⚡ Simular Sabotaje en D1"**, botón **"🔍 Verificar Integridad Criptográfica"** y ejecutor en vivo del **Benchmark de 100 Ataques**.

* **Bloque 6 (Horas 26 a 34) — Auditoría Global y Despliegue en Producción Cloudflare:**
  * **Acción de auditoría:** Revisión cruzada de contratos JSON entre `functions/api/v1/*` y `static/app.js`, verificación de cero `Math.random()`, cero PII en D1 (`wrangler d1 execute aduana-db --remote --command "SELECT * FROM ledger_blocks LIMIT 5;"`) y `specs/01..05.spec.md` completos.
  * **Despliegue real según Manual:**
    1. `wrangler d1 execute aduana-db --remote --file=schema.sql`
    2. `wrangler secret put LEDGER_HMAC_KEY` y `wrangler secret put INSTITUTION_SALT`
    3. `wrangler pages deploy static --project-name aduana-ia`
    4. Verificación en navegador incógnito, consola F12 limpia, móvil y `wrangler tail`.
    5. Actualizar Demo y Video en `README.md` y en **`https://hackathon-uneti-ia.pages.dev/remoto`**.

* **Bloque 7 (Horas 34 a 48) — *Code Freeze* y Ensayo Cronometrado de 3 Minutos:**
  * **Congelar código tras la Hora 38.** Dedicar el cierre exclusivamente a ensayar la demo en vivo sobre la URL pública `*.pages.dev` y mantener lista la terminal con `node --test` en verde.

---

## 🏆 PARTE 4: ESTRUCTURA DE VENTA Y PITCH GANADOR PARA EL JURADO

Mientras otros equipos muestran diapositivas o un wrapper frágil de chat, **Aduana IA presenta una arquitectura verificable en vivo sobre Cloudflare Pages, Workers (TypeScript), D1 y Workers AI, construida bajo Spec-Driven Development desde `SPEC.md`.**

### 4.1 Guion de Demostración en Vivo (3 Minutos Exactos)

#### 🔥 Acto 1: El Gancho de Impacto Nacional (0:00 a 0:30) — *El Problema Real*
> **Qué decir:**  
> *"Buenas tardes, jurado. Hoy mismo, funcionarios y analistas están pegando expedientes con Cédulas, RIFs y diagnósticos médicos directamente en inteligencias artificiales externas. Quieren agilizar trámites, pero sin querer exponen la privacidad ciudadana, quedan vulnerables a ataques de Prompt Injection y dependen de cajas negras imposibles de auditar.*  
> *No podemos prohibir la IA, pero tampoco usarla a ciegas. Por eso construimos **Aduana IA**: una pasarela Zero-Trust corriendo en **Cloudflare Workers, D1 y Workers AI** que protege cada dato antes de tocar el modelo, explica matemáticamente la prioridad y sella cada decisión en un Ledger verificable."*

#### 🛡️ Acto 2: Demo 1 — Privacidad Soberana y Justicia Matemática (0:30 a 1:25) — *SHIELD + EXPLICA*
> **Qué hacer en pantalla:** Haz clic en **"Caso 1: Trámite de Salud con Datos Reales"** y presiona **Procesar por Aduana IA**.  
> **Qué decir mientras se ilumina el pipeline:**  
> *"Vean esto en vivo en nuestra URL pública: una ciudadana solicita prioridad médica e incluye su Cédula, RIF, teléfono y diagnóstico. En pocos milisegundos, **SHIELD** valida el RIF con el **algoritmo Módulo 11 del SENIAT**, sustituye los identificadores por tokens (`[CEDULA_1]`, `[RIF_1]`) y genera un índice ciego HMAC —**cero datos personales reales salen hacia Workers AI ni se guardan en D1**.*  
> *Luego, nuestra interfaz marca claramente el resumen generado por `@cf/zai-org/glm-4.7-flash`, mientras **EXPLICA** calcula la prioridad mediante una **Regresión Logística determinista con valores SHAP lineales**. La IA resume y recomienda, pero **el funcionario humano tiene siempre la decisión final**, y si decide contradecir al modelo, el sistema le exige justificarlo por escrito."*

#### 🚨 Acto 3: Demo 2 — Defensa Activa y Métricas Honestas (1:25 a 2:10) — *EL GUARDIÁN*
> **Qué hacer en pantalla:** Haz clic en **"Caso 2: Ataque Prompt Injection + Intento de Fuga"** y luego en **"Ejecutar Benchmark de 100 Vectores"**.  
> **Qué decir:**  
> *"¿Qué ocurre si un atacante intenta inyectar instrucciones ocultas o código Base64 para manipular la respuesta o extraer el prompt del sistema? Nuestro **Guardián (`Guard-In` y `Guard-Out`)** normaliza el texto con NFKC, evalúa el riesgo sin funciones aleatorias e inyecta un **Canary Token HMAC dinámico** por transacción, bloqueando la fuga al instante.*  
> *Para no pedir fe ciega, incluimos un **Benchmark Auditable de 100 casos reales** ejecutable aquí mismo, mostrando nuestra tasa real de mitigación ($\text{TPR} \ge 88\%$) y falsos positivos ($\text{FPR} \le 4\%$)."*

#### 🔗 Acto 4: Demo 3 y Cierre — Inmutabilidad en Cloudflare D1 (2:10 a 3:00) — *LEDGER D1*
> **Qué hacer en pantalla:** Cambia al **Panel de Contraloría**, muestra la cadena en **VERDE**, haz clic en **"⚡ Simular Sabotaje en D1"** y luego en **"🔍 Verificar Integridad Criptográfica"** (cambia a **ROJO** señalando el bloque exacto).  
> **Qué decir para cerrar:**  
> *"Finalmente, cada transacción queda sellada en **Cloudflare D1** con **doble sello: encadenamiento SHA-256 más firma HMAC-SHA256** cuya llave vive aislada en Cloudflare Secrets, emitiendo un recibo verificable al ciudadano. ¿Qué pasa si alguien con acceso directo a la base de datos intenta alterar un dictamen histórico? Simulémoslo ahora... Al auditar la cadena con Web Crypto API, **Aduana IA detecta el sabotaje con precisión quirúrgica en el bloque exacto y señala la causa**.*  
> *Especificado primero en `SPEC.md`, ejecutándose en TypeScript sobre el Edge con degradación elegante si el modelo falla y código abierto bajo GPL v3. Muchas gracias."*

---

### 4.2 Argumentos Clave según el Perfil del Jurado

| Perfil del Jurado | Qué Valora | Frase Clave de Defensa |
| :--- | :--- | :--- |
| **👨‍💻 Ingeniero / Ciberseguridad** | Rigor técnico, que no sea un wrapper con `if/else` falsos ni `Math.random()`. | *"Validación real Módulo 11 SENIAT, normalización Unicode NFKC, valores SHAP lineales exactos ($\phi_j = \beta_j(x_j - \mu_j)$) y doble sello SHA-256 + HMAC con `crypto.subtle` en Cloudflare Workers/D1 dentro del límite de 10 ms CPU."* |
| **🏛️ Institucional / Ética IA** | Cumplimiento de `SPEC.md`, privacidad ciudadana, explicabilidad y control humano. | *"Alineado con los Arts. 28 y 60 de la Constitución y la Ley de Infogobierno: ningún dato personal viaja a Workers AI ni se graba en D1, marcamos las salidas de IA y el humano siempre decide con trazabilidad de overrides."* |
| **📈 Estratega / *Venezuela Innova*** | Escalabilidad, costo de despliegue y modelo sostenible. | *"Arranca a costo cero en Cloudflare Free Tier y, gracias a `StorageRepository` y `LLMAdapter`, se enchufa delante de sistemas existentes con un modelo sostenible de implantación B2G y licenciamiento SLA para banca y salud."* |

---

### 4.3 Checklist Final de Demo (15 Minutos Antes de Evaluar)

1. **Despliegue Público Verificado:** Confirmar la URL en `*.pages.dev` en pestaña incógnito y revisar `wrangler tail` sin errores 5xx ni logs con PII.
2. **Cadena D1 Poblada:** Tener 4 o 5 trámites variados ya sellados en `ledger_blocks` remoto (aprobados, con override justificado y un ataque bloqueado) para que la auditoría luzca viva desde el primer segundo.
3. **Suite de Pruebas SDD Lista:** Tener una terminal con la ejecución reciente de `node --test` mostrando `CA-01` a `CA-06` en verde, y `SPEC.md` abierto si el jurado pregunta por la declaración de uso de IA.
4. **Roles del Equipo en el Pitch:**
   - **Vocero Principal:** Conduce los 3 minutos sin leer la pantalla.
   - **Piloto de Demo:** Ejecuta los clics exactos (Caso 1 $\rightarrow$ Ataque + Benchmark $\rightarrow$ Sabotaje D1 + Verificación).
   - **Defensor Técnico:** Responde preguntas sobre criptografía `crypto.subtle`, límites de Workers/D1 y fórmulas de `EXPLICA`.
