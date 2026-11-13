# 🏛️ ADUANA IA: Ingeniería de Requisitos, Modelo de Negocio GovTech, Plan MVP en 48h y Estrategia de Venta al Jurado

> **Documento Maestro de Ejecución y Negocio (v3.0 — Python 2026: Litestar + PyWebView Desktop + Criptografía Pura)**  
> **Evento:** Hackathon UNETI IA 2026 $\rightarrow$ *Venezuela Innova*  
> **Documentos Base Sincronizados:** [SPEC.md](../SPEC.md) + [README.md](../README.md) + [PROMPT_MAESTRO.md](../PROMPT_MAESTRO.md)  
> **Propósito:** Respaldo formal de ingeniería de software (SRS), viabilidad económica/institucional en Windows y Linux, plan táctico de construcción en 48 horas sobre **Litestar 2.10+ (ASGI)** y **PyWebView 5.1+ (Escritorio nativo)** con **criptografía pura de la librería estándar de Python**, y guion de defensa ante el jurado evaluador.

---

## 📐 PARTE 1: DOCUMENTO DE INGENIERÍA DE REQUISITOS (SRS ADAPTADO A SDD)

### 1.1 Propósito y Alcance del Sistema
**Aduana IA** es una pasarela soberana de seguridad, anonimización, explicabilidad matemática y auditoría criptográfica (*AI Governance & Security Gateway*) diseñada para interceptar, sanitizar, evaluar y sellar en tiempo real toda transacción entre usuarios de instituciones públicas/reguladas venezolanas y modelos de Inteligencia Artificial (locales o remotos), operando indistintamente como **Servidor Web Litestar** institucional o como **Aplicación de Escritorio PyWebView** en estaciones de trabajo de funcionarios.

### 1.2 Actores y Perfiles de Usuario (*Stakeholders*)

| Actor | Rol en el Ecosistema | Necesidad Principal | Interfaz que Utiliza |
| :--- | :--- | :--- | :--- |
| **Ciudadano Venezolano** | Titular de los datos personales y solicitante del trámite público. | Que sus datos sensibles (Cédula, RIF, salud, ingresos) no se filtren ni queden grabados en texto plano en disco, y contar con un comprobante verificable. | Recibo Criptográfico de Auditoría (`citizen_receipt_code`). |
| **Funcionario Analista** | Operador público encargado de evaluar y decidir sobre el trámite (*Human-in-the-Loop*). | Resúmenes de IA sobre datos ya anonimizados y un puntaje matemático transparente que respalde su decisión administrativa. | **🖥️ Panel del Funcionario** (App de Escritorio PyWebView o Navegador Web). |
| **Auditor / Contralor** | Inspector de Contraloría Interna, SUSCERTE o Seguridad de la Información. | Comprobar matemáticamente que el historial de decisiones en SQLite/Postgres no fue alterado y auditar la resistencia a ataques. | **🔍 Panel de Auditoría y Contraloría** (Verificador Ledger SHA-256/HMAC + Benchmark 100 ataques). |
| **Administrador TI** | Responsable de desplegar el servicio en centros de datos o estaciones de trabajo. | Binario ligero en **Python 3.11+** (< 60 MB RAM) sobre Litestar/Granian, sin dependencias pesadas, ejecutable tanto en Windows 10/11 como en Linux/Canaima. | API `/api/v1/health/system` y lanzador `iniciar_escritorio.bat` / `.sh`. |

---

### 1.3 Catálogo de Requisitos Funcionales (RF) Trazables al Pipeline

#### Módulo 0: Consentimiento Informado y Protección de Tasa (Idea #8)
* **RF-01 (Validación de Consentimiento Explícito):** El sistema debe rechazar con estado `BLOCKED_NO_CONSENT` cualquier petición donde `citizen_consent.granted` sea `False` o carezca de propósito declarado (`purpose_code`).
* **RF-02 (Sello Criptográfico de Consentimiento):** El sistema debe generar un `consent_hash` (`SHA-256` mediante `hashlib.sha256`) vinculando `request_id`, `timestamp_utc` y `purpose_code`.
* **RF-03 (Control de Abuso sin Exposición de Identidad):** El sistema debe limitar la tasa de peticiones por ciudadano utilizando su índice ciego (`blind_citizen_id`) en memoria sin almacenar su Cédula en texto plano.

#### Módulo 1: `SHIELD` — Anonimización Soberana y Almacenamiento Restrictivo (Ideas #6 y #8)
* **RF-04 (Detección y Enmascaramiento Estructurado Nacional):** El sistema debe detectar y sustituir por tokens indexados consistentes (`[CEDULA_1]`, `[RIF_1]`, `[PHONE_1]`, `[BANK_1]`, `[EMAIL_1]`) toda Cédula venezolana (`V/E`), RIF (`V/E/J/G/P/C`), teléfono nacional (`0412/0414/0424/0416/0426/0212...`), correo y cuenta bancaria de 20 dígitos.
* **RF-05 (Validación Matemática Módulo 11 SENIAT):** Cuando se detecte un patrón de RIF, el sistema debe ejecutar el algoritmo oficial Módulo 11 del SENIAT (mapeo `{"V":1,"E":2,"J":3,"P":4,"G":5,"C":3}` y vector de 9 pesos `[4,3,2,7,6,5,4,3,2]`) y registrar en `shield_meta.rif_mod11_verified` la autenticidad matemática del documento.
* **RF-06 (Reconocimiento Léxico Contextual de Salud e Identidad):** El sistema debe enmascarar nombres propios precedidos por marcadores contextuales de trámite y términos clínicos sensibles incluidos en el diccionario local de protección de salud (`[CLINICAL_1]`).
* **RF-07 (Bóveda Efímera y Zeroization):** El mapeo entre tokens (`[CEDULA_1]`) y el valor original (`V-12.345.678`) debe mantenerse únicamente en `EphemeralVault` en memoria RAM volátil con TTL $\le 180\text{ s}$ y purga explícita (`zeroize()`), **jamás en el disco duro ni bases de datos**.

#### Módulo 2: `GUARD-IN` — Defensa Activa contra Prompt Injection (Idea #18)
* **RF-08 (Normalización Anti-Evasión):** Antes de inspeccionar el texto, el sistema debe aplicar `unicodedata.normalize("NFKC", text)`, eliminar caracteres invisibles (*zero-width* `\u200b`, etc.) y decodificar cadenas sospechosas en `Base64` o `Hex` embebidas.
* **RF-09 (Cálculo Determinista de Riesgo Adversario):** El sistema debe evaluar el texto frente a reglas heurísticas y similitud léxica ponderada (intentos de *override* de instrucciones, *jailbreak*, *roleplay* malicioso, inyección SQL/comandos y exfiltración de prompt), generando un `risk_score` continuo en $[0.0, 1.0]$ sin usar `random()`, bloqueando entradas por encima del umbral ($\ge 0.65$).
* **RF-10 (Encapsulamiento XML Sandbox y Canary Token Dinámico):** Toda solicitud permitida hacia el LLM debe envolverse en etiquetas estructurales `<instruccion_institucional_inmutable>` y `<entrada_ciudadano>`, inyectando un token único por transacción firmado con HMAC vía `hmac.new()` (`[[CANARY-HMAC-XXXXXXXX]]`).

#### Módulo de Interconectividad: `LLMAdapter` y `CircuitBreaker`
* **RF-11 (Conmutación Agnóstica de Proveedor IA):** El sistema debe procesar únicamente `masked_text` mediante la interfaz abstracta `LLMAdapter` con soporte para: 1) Modelos locales en intranet vía Ollama/llama.cpp (`Qwen2.5`, `Llama-3.2`), 2) Nubes híbridas compatibles con OpenAI API, y 3) Motor Institucional Determinista Offline (`OfflineDeterministicAdapter`).
* **RF-12 (Degradación Elegante por Circuit Breaker):** Si el LLM externo supera el timeout de `3.5 segundos` o devuelve error de red, el `CircuitBreaker` conmuta automáticamente a `OfflineDeterministicAdapter` para garantizar que el funcionario reciba siempre el dictamen de `EXPLICA` y el sellado en `LEDGER`.

#### Módulo 3: `GUARD-OUT` — Inspección de Salida y Prevención de Fugas (Idea #18)
* **RF-13 (Detección de Fuga de Canary y PII Residual):** El sistema debe inspeccionar la respuesta del LLM y abortar su entrega si contiene total o parcialmente el `canary_token` de la sesión o si detecta cualquier patrón de PII residual/alucinado.
* **RF-14 (Sanitización de Salida Segura y Aviso de IA):** El sistema debe neutralizar etiquetas ejecutables (`<script>`, `onload=`, `javascript:`), marcar afirmaciones sin respaldo institucional e indicar explícitamente en la respuesta (`ai_generated_notice: True`) que el resumen fue generado por IA.

#### Módulo 4: `LEDGER` — Registro Criptográfico Inmutable (Idea #17)
* **RF-15 (Encadenamiento SHA-256 y Doble Sello HMAC):** Cada transacción finalizada debe registrarse en la tabla `ledger_blocks` de SQLite3 / PostgreSQL como un bloque secuencial $i$ cuyo `block_hash` dependa de `prev_hash` ($H_{i-1}$), `payload_hash`, `timestamp_utc` y `blind_citizen_id`, acompañado de `hmac_signature` generada con la clave maestra del servidor en RAM.
* **RF-16 (Auditoría Completa y Detección Quirúrgica de Sabotaje):** El sistema debe proveer `verify_chain()` en `/api/v1/ledger/verify` que recalcule hashes y firmas HMAC con la StdLib desde el bloque génesis hasta el último bloque, identificando el `corrupted_block_index` exacto y el motivo (`HASH_MISMATCH`, `PREV_HASH_LINK_BROKEN` o `HMAC_SIGNATURE_FORGED`).
* **RF-17 (Simulador de Sabotaje en Vivo y Recibo Ciudadano):** El sistema debe incluir un endpoint controlado (`/api/v1/ledger/tamper-sim`) para alterar un registro histórico de prueba y evidenciar en vivo la detección criptográfica en el panel de auditoría, además de emitir `citizen_receipt_code` por trámite.

#### Módulo 5: `EXPLICA` — Modelo Matemático White-Box y Human-in-the-Loop (Idea #5)
* **RF-18 (Evaluación Tabular con Regresión Logística Determinista):** El sistema debe calcular la probabilidad de prioridad del trámite mediante la función sigmoide $P(y=1\mid\mathbf{x}) = \frac{1}{1+e^{-(\beta_0 + \sum \beta_j x_j)}}$ utilizando coeficientes $\beta$ y medias $\mu$ entrenados de forma determinista sobre `data/synthetic_tramites.csv` (cero `random()`).
* **RF-19 (Desglose de Pesos y Valores SHAP Lineales):** El sistema debe exponer para cada variable del trámite su aporte directo ($\beta_j x_j$) y su valor SHAP lineal centrado respecto a la media poblacional ($\phi_j = \beta_j(x_j - \mu_j)$), verificando que la suma algebraica reconstruya el *logit* $z$ con error $< 10^{-9}$.
* **RF-20 (Soberanía de Decisión Humana con Justificación de Override):** El sistema exige confirmación del funcionario antes de sellar el dictamen (`PRIORIDAD_ALTA`, `REVISION_ESTANDAR`, `RECAUDOS_INCOMPLETOS`); si el funcionario sobrescribe la recomendación matemática (`human_override = True`), se exige una justificación escrita ($\ge 20$ caracteres) grabada de forma inmutable en el Ledger.

---

### 1.4 Requisitos No Funcionales (RNF) y Restricciones de Calidad

| Código | Categoría | Especificación Medible y Verificable |
| :---: | :--- | :--- |
| **RNF-01** | **Rendimiento y Latencia** | El procesamiento acumulado de seguridad y auditoría (`SHIELD` + `GUARD-IN` + `GUARD-OUT` + `EXPLICA` + `LEDGER` hashing) debe ejecutarse en **$< 40\text{ ms}$** en CPU estándar. |
| **RNF-02** | **Cero PII en Disco** | **0 bytes** de Cédulas, RIFs, teléfonos o nombres originales pueden persistirse en archivos SQLite (`.db`, `-wal`, `-shm`) ni imprimirse en logs (`stdout`/`stderr`). |
| **RNF-03** | **Arquitectura Python 2026** | Backend 100% sobre **Litestar 2.10+** (ASGI) con `msgspec`/`pydantic v2` y **PyWebView 5.1+** para escritorio, desterrando FastAPI (2018). |
| **RNF-04** | **Autonomía Offline-First** | La interfaz web y de escritorio debe operar al **100% sin conexión a internet**, sin enlaces a CDNs externos de CSS, fuentes o JavaScript. |
| **RNF-05** | **Efectividad Adversaria** | Tasa de Mitigación (**TPR**) $\ge 88\%$ y Tasa de Falsos Positivos (**FPR**) $\le 4\%$ medida automáticamente sobre `data/attack_benchmark.json` ($N=100$ prompts). |
| **RNF-06** | **Endurecimiento SQLite3** | Activación obligatoria de `PRAGMA journal_mode=WAL;`, `PRAGMA synchronous=FULL;`, `PRAGMA secure_delete=ON;` y triggers SQL `BEFORE UPDATE/DELETE` con `RAISE(ABORT)`. |

---

## 💼 PARTE 2: ESTRUCTURA Y MODELO DE NEGOCIO (GOVTECH & B2B REGULADO)

### 2.1 El Caso de Negocio: ¿Por qué el Estado y la Banca necesitan adoptar Aduana IA?

Actualmente, las instituciones públicas y empresas reguladas en Venezuela enfrentan una **paradoja paralizante** frente a la Inteligencia Artificial:
1. **Si prohíben la IA:** Pierden productividad, mantienen colas lentas en atención ciudadana y sus propios empleados terminan usando cuentas personales gratuitas desde sus teléfonos móviles, **filtrando datos críticos del Estado sin ningún control (*Shadow AI*)**.
2. **Si conectan formularios directo a LLMs externos:** Violan el principio de *Habeas Data* (CRBV Art. 60), exponen PII ciudadano, quedan vulnerables a *Prompt Injection* y pagan cómputo procesando spam o ataques.
3. **Si intentan comprar granjas de GPUs propias desde cero:** Requieren inversiones de decenas de miles de dólares fuera del alcance de alcaldías, hospitales o universidades.

> **La Solución Económica de Aduana IA:** Al construirse como una pasarela ultraligera en **Python 3.11+ (Litestar + PyWebView)** y estándares libres (**GNU GPL v3**), cualquier organismo puede desplegar pilotos inmediatos a **costo cero** sobre el hardware existente (servidores Linux o estaciones Windows 10/11) con **cero fugas de datos y auditoría de nivel contraloría desde el primer día**.

---

### 2.2 Segmentación de Mercado (Doble Motor: B2G Público + B2B Regulado)

| Segmento | Clientes Objetivo en Venezuela | Dolor Específico que Resuelve Aduana IA |
| :--- | :--- | :--- |
| **1. Sector Público Social y Trámites (B2G)** | Ministerios (Salud, Educación Universitaria, Trabajo, Alimentación), IVSS, SAIME, SENIAT, SAREN, Gobernaciones y Alcaldías. | Triaje rápido de solicitudes ciudadanas con priorización matemática justa (`EXPLICA`), protección de datos (`SHIELD`) y auditoría anticorrupción (`LEDGER`). |
| **2. Sector Financiero y Asegurador (B2B Regulado)** | Banca Pública y Banca Privada Nacional (Banesco, Mercantil, Provincial, BNC), Aseguradoras. | Cumplimiento de normativas **SUDEBAN** al usar IA en atención de reclamos, análisis de crédito explicable (`EXPLICA`) y enmascaramiento de cuentas de 20 dígitos y RIFs. |
| **3. Sector Salud y Universitario (B2G / B2B)** | Red Hospitalaria, Clínicas privadas, UNETI y Universidades Nacionales. | Protección de historias clínicas sensibles antes de generar resúmenes asistidos por IA y asignación transparente de becas o cupos. |

---

### 2.3 Modelo de Sostenibilidad e Ingresos (Compatible con la Ley de Infogobierno)

El repositorio base se publica bajo **GNU GPL v3** y se sostiene mediante un **Modelo Dual Open-Core Soberano**:
1. **Línea 1 — Núcleo Abierto Soberano (*GovTech Open Standard*):** Motor base auditable y libre para universidades y pilotos estatales, alineado con estándares **CNTI / SUSCERTE**.
2. **Línea 2 — Contratos de Implantación, Integración y Calibración Institucional (B2G):** Servicios especializados de ingeniería: integración de `StorageRepositoryProtocol` con bases de datos institucionales (Postgres/Oracle), despliegue en Windows Server / Linux y **calibración a medida de modelos `EXPLICA`** según las reglas de negocio de cada ministerio.
3. **Línea 3 — Suscripción de Inteligencia de Amenazas (*Aduana Threat-Feed*):** Actualización periódica de reglas heurísticas `GUARD-IN` contra nuevos vectores de *Jailbreak* y actualización de diccionarios regulatorios de `SHIELD`.
4. **Línea 4 — Licenciamiento Enterprise SLA para Banca, Seguros y Clínicas Privadas (B2B):** Soporte 24/7, alta disponibilidad y paneles de cumplimiento normativo para el sector financiero y de salud privado.

---

### 2.4 Impacto Cuantificable (Objetivos de Valor para el Pitch)

| Indicador de Impacto | Sin Aduana IA (Uso Directo / Manual) | Con Aduana IA Desplegada | Beneficio Neto Demostrable |
| :--- | :---: | :---: | :--- |
| **Exposición de PII Ciudadano al LLM** | $100\%$ de los datos enviados en claro | **$0\%$** (Tokenizado en $< 20\text{ ms}$) | Resguardo efectivo de privacidad (CRBV Art. 60). |
| **Costo de Arranque del MVP / Piloto** | Requiere servidores dedicados o GPUs | **Costo \$0 inicial** (< 60 MB RAM en hardware actual) | Adopción inmediata sin fricción de infraestructura. |
| **Ahorro en Consumo de Cómputo IA** | Paga por ataques, spam y prompts fallidos | **Reducción estimada $35\% - 60\%$** | `SHIELD` y `GUARD-IN` bloquean abuso antes de invocar al LLM. |
| **Tiempo de Auditoría de Contraloría** | Semanas revisando expedientes manuales | **$< 50\text{ ms}$** (`/api/v1/ledger/verify`) | Detección instantánea de cualquier alteración o *override*. |

---

## ⚡ PARTE 3: PLAN DE CONSTRUCCIÓN DEL MVP EN 48 HORAS (PYTHON 2026)

Para construir el sistema en **48 horas** de forma limpia entre compañeros y asistentes de IA (**Antigravity + Claude + ChatGPT + Gemini**), todo código se genera estrictamente bajo el flujo SDD definido en [SPEC.md](../SPEC.md) y [PROMPT_MAESTRO.md](../PROMPT_MAESTRO.md).

### 3.1 Orquestación Especializada de Herramientas IA

| Herramienta / Rol | Especialidad en el Hackathon | Entregables Exactos que Debe Generar |
| :--- | :--- | :--- |
| **🟣 Antigravity / Claude** | **Arquitecto Backend Python, Criptografía, Litestar y Tests SDD** | `core/context.py`, `core/crypto.py`, `core/ephemeral_vault.py`, `pipeline/stage1_shield.py` (Módulo 11 SENIAT), `pipeline/stage2_guard_in.py`, `pipeline/stage3_guard_out.py`, `pipeline/stage4_ledger.py` (SQLite endurecido), `pipeline/stage5_explica.py`, `pipeline/llm_adapter.py`, `app/server.py` (Litestar) y toda la suite `tests/` con `pytest`. |
| **🟢 ChatGPT** | **Red Teamer, Datos Sintéticos y UI de Escritorio / Web** | `data/attack_benchmark.json` (100 prompts: 50 trámites benignos + 50 ataques en español venezolano), `data/synthetic_tramites.csv` (casos sociales para calibrar `EXPLICA`), `static/index.html`, `static/styles.css` (local sin CDNs), `static/app.js` y el lanzador `app/desktop.py` con PyWebView. |
| **🔵 Gemini** | **Auditor de Contexto Global, Integrador y Director de Pitch** | Revisión cruzada de extremo a extremo, validación de cero `random()` y cero PII en disco, redacción formal de `specs/01..05.spec.md` y pulido del guion de defensa de 3 minutos. |

---

### 3.2 Cronograma Táctico de 48 Horas

#### 🗓️ DÍA 1: Criptografía, Almacenamiento Restrictivo y Pipeline en Python Puro

* **Bloque 1 (Horas 0 a 3) — Kernel Base y Bóveda Efímera (Gatillo 0):**
  * Generar `core/context.py` (`AduanaPacket` inmutable en Python), `core/crypto.py` (StdLib pura) y `core/ephemeral_vault.py` (RAM con TTL 180s y `zeroize`).
  * Generar `data/synthetic_tramites.csv` y `data/attack_benchmark.json`.
  * **Hito de Control:** `pytest tests/test_ca05_restrictive_db.py` pasa en verde.

* **Bloque 2 (Horas 3 a 8) — Etapas 1, 2 y 3: `SHIELD` + `GUARDIÁN` (Gatillos 1 y 2):**
  * Implementar `pipeline/stage1_shield.py` (Regex venezolano, algoritmo Módulo 11 SENIAT con 9 pesos `[4,3,2,7,6,5,4,3,2]`, clínica y `blind_citizen_id` HMAC).
  * Implementar `pipeline/stage2_guard_in.py` (NFKC, Base64 check, risk scoring, XML sandbox, Canary dinámico) y `pipeline/stage3_guard_out.py`.
  * **Hito de Control:** `pytest tests/test_ca01_shield.py` y `pytest tests/test_ca02_guardian.py` pasan en verde ($\text{TPR} \ge 88\%$, $\text{FPR} \le 4\%$).

* **Bloque 3 (Horas 8 a 14) — Etapas 4 y 5: `LEDGER` + `EXPLICA` (Gatillos 3 y 4):**
  * Implementar `pipeline/stage4_ledger.py` sobre SQLite3 endurecido (WAL, secure_delete, triggers SQL, encadenamiento SHA-256 + HMAC y simulación de sabotaje).
  * Implementar `pipeline/stage5_explica.py` (pesos deterministas, sigmoide, SHAP lineal y validación de human override $\ge 20$ chars).
  * **Hito de Control (Cierre Día 1):** `pytest tests/test_ca03_ledger.py` y `pytest tests/test_ca04_explica.py` pasan en verde. Todo el pipeline opera en Python puro.

---

#### 🗓️ DÍA 2: Servidor Litestar, Escritorio PyWebView, UI y Ensayo de Pitch

* **Bloque 4 (Horas 14 a 18) — Servidor Litestar y Adaptadores LLM (Gatillos 5 y 6):**
  * Implementar `pipeline/llm_adapter.py` (Local Ollama, OpenAI-compat, Fallback Offline determinista + Circuit Breaker a 3.5s).
  * Implementar `app/server.py` utilizando **Litestar 2.10+** con endpoints `/api/v1/*` y servido de `static/`.
  * **Hito de Control:** El servidor levanta con `granian --interface asgi app.server:app` y responde en Swagger `/schema` y cURL.

* **Bloque 5 (Horas 18 a 26) — Aplicación de Escritorio PyWebView y Dashboard Dual (Gatillo 7):**
  * Implementar `app/desktop.py` (PyWebView 5.1+ embebiendo la UI local con ventana nativa en Windows/Linux) y crear `iniciar_escritorio.bat` / `.sh`.
  * Construir en `static/` (100% libre de CDNs externos) la interfaz con Panel del Funcionario (Sliders SHAP, recibo ciudadano) y Panel de Contraloría (sabotaje y verificación).

* **Bloque 6 (Horas 26 a 34) — Auditoría Global y Pruebas de Estrés Offline (Air-Gap Test):**
  * Desconectar el cable de red / Wi-Fi, reiniciar la aplicación de escritorio y el servidor Litestar, correr `pytest -v` (100% passed) y ejecutar las 3 demos en vivo sin internet.

* **Bloque 7 (Horas 34 a 48) — *Code Freeze* y Ensayo Cronometrado:**
  * Congelar código tras la Hora 38. Ensayar el pitch de 3 minutos con cronómetro y dejar en pantalla la app de escritorio y una terminal con `pytest` en verde.

---

## 🏆 PARTE 4: ESTRUCTURA DE VENTA Y PITCH GANADOR PARA EL JURADO

### 4.1 Guion de Demostración en Vivo (3 Minutos Exactos)

#### 🔥 Acto 1: El Gancho de Impacto Nacional (0:00 a 0:30) — *El Problema Real*
> **Qué decir:**  
> *"Buenas tardes, jurado. Hoy mismo, funcionarios en ministerios y alcaldías están copiando expedientes con Cédulas, RIFs y diagnósticos médicos directamente en IAs externas para redactar informes. Quieren agilizar trámites, pero sin querer están comprometiendo la privacidad de los ciudadanos, quedando expuestos a inyecciones de prompts y operando sobre cajas negras que ninguna Contraloría puede auditar.*  
> *No podemos prohibir la IA, pero tampoco usarla a ciegas. Por eso creamos **Aduana IA**: la primera pasarela soberana de gobernanza Zero-Trust y auditoría criptográfica, construida en **Python 2026 sobre Litestar**, con aplicación nativa de **Escritorio para Windows y Linux**, y operativa al 100% sin internet."*

#### 🛡️ Acto 2: Demo 1 — Privacidad Soberana y Justicia Matemática (0:30 a 1:25) — *SHIELD + EXPLICA*
> **Qué hacer en pantalla:** En la aplicación de escritorio, haz clic en **"Caso 1: Trámite Médico con Datos Reales"** y presiona **Procesar por Aduana IA**.  
> **Qué decir:**  
> *"Observen esto en vivo: una ciudadana solicita prioridad médica e incluye Cédula, RIF, teléfono y diagnóstico. En menos de 10 milisegundos, **SHIELD** valida matemáticamente el RIF con el **algoritmo Módulo 11 del SENIAT**, enmascara los datos sensibles con tokens reversibles únicamente en memoria RAM —**cero datos personales tocan jamás el disco duro**— y envía al modelo solo texto sanitizado.*  
> *Al mismo tiempo, **EXPLICA** no usa cajas negras ni números al azar: calcula la prioridad con una **Regresión Logística White-Box y valores SHAP lineales** que muestran exactamente cuántos puntos aporta cada variable. La máquina recomienda, pero **el funcionario humano tiene siempre la última palabra**, y si decide contradecir al modelo, el sistema le exige justificar por qué."*

#### 🚨 Acto 3: Demo 2 — Defensa Activa y Métricas Honestas (1:25 a 2:10) — *EL GUARDIÁN*
> **Qué hacer en pantalla:** Haz clic en **"Caso 2: Prompt Injection + Intento de Fuga"** y luego en **"Ejecutar Benchmark de 100 Ataques"**.  
> **Qué decir:**  
> *"¿Qué ocurre si un atacante intenta inyectar órdenes ocultas o código ofuscado en Base64 para saltar requisitos? Nuestro **Guardián (`Guard-In` y `Guard-Out`)** normaliza el texto, detecta el patrón adversario e inyecta un **Canary Token dinámico con HMAC** por transacción, neutralizando el ataque de inmediato.*  
> *Y como en ciberseguridad seria no pedimos fe ciega, incluimos un **Benchmark Abierto de 100 casos reales**: aquí mismo el jurado puede auditar nuestra tasa real de mitigación superior al 88% con menos del 4% de falsos positivos."*

#### 🔗 Acto 4: Demo 3 y Cierre — Sabotaje en Base de Datos y Verificación (2:10 a 3:00) — *LEDGER INMUTABLE*
> **Qué hacer en pantalla:** Cambia al **Panel de Contraloría**, muestra la cadena en **VERDE**, haz clic en **"⚡ Simular Sabotaje en Base de Datos"** y luego en **"🔍 Auditar Cadena Criptográfica"** (la pantalla se ilumina en **ROJO** señalando el bloque exacto).  
> **Qué decir para cerrar:**  
> *"Finalmente, cada decisión se sella en nuestro **Ledger con doble sello: encadenamiento SHA-256 más firma HMAC del servidor**, entregando un recibo criptográfico al ciudadano. Si mañana un atacante con acceso root altera un registro en SQLite... Al auditar la cadena, **Aduana IA detecta el sabotaje en milisegundos con precisión quirúrgica en el bloque exacto**.*  
> *Desarrollado bajo metodología **SDD estricta**, con arquitectura moderna en **Litestar**, disponible para **Servidor y Escritorio en Windows y Linux**, con menos de 60 MB de RAM y código libre bajo GPL v3. Muchas gracias."*

---

### 4.2 Argumentos Clave según el Perfil del Jurado

| Perfil del Jurado | Qué Valora | Frase Clave de Defensa |
| :--- | :--- | :--- |
| **👨‍💻 Ingeniero / Ciberseguridad** | Rigor técnico, que no sea un wrapper con `if/else` falsos ni `random()`. | *"Validación real Módulo 11 SENIAT, normalización Unicode NFKC, valores SHAP lineales exactos ($\phi_j = \beta_j(x_j - \mu_j)$) y doble sello SHA-256 + HMAC con `PRAGMA secure_delete=ON` en SQLite. Aquí tienen nuestra suite de `pytest` corriendo en vivo."* |
| **🏛️ Institucional / Ética IA** | Cumplimiento legal, soberanía de datos y control humano. | *"Cumplimos los Arts. 28 y 60 de la Constitución y la Ley de Infogobierno: cero PII en disco, el LLM solo ve texto tokenizado, corre localmente sin depender de internet y el funcionario humano tiene la decisión final vinculante."* |
| **📈 Estratega / *Venezuela Innova*** | Viabilidad real, bajo costo y facilidad de implantación en el Estado. | *"No pide cambiar los sistemas actuales ni comprar servidores costosos: corre como servidor Litestar o como aplicación de escritorio nativa PyWebView en cualquier PC con Windows o Linux con 60 MB de RAM, listo para desplegar en ministerios, alcaldías y banca."* |
