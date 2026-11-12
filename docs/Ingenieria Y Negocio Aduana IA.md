# 🏛️ ADUANA IA: Ingeniería de Requisitos, Modelo de Negocio GovTech, Plan MVP en 48h (Tridente IA) y Estrategia de Venta al Jurado

> **Documento Maestro de Ejecución y Negocio (v2.0)**  
> **Evento:** Hackathon UNETI (13-14 de Noviembre) $\rightarrow$ *Venezuela Innova* (26-28 de Noviembre)  
> **Documentos Base Sincronizados:** `README.md` (Arquitectura v2.0) + `PROMPT_MAESTRO.md` (Agent Kernel v2.0)  
> **Propósito:** Servir como respaldo formal de ingeniería de software, viabilidad económica/institucional, manual táctico de construcción en 48 horas usando **Claude + ChatGPT + Gemini**, y guion comercial ganador ante el jurado evaluador.

---

## 📐 PARTE 1: DOCUMENTO DE INGENIERÍA DE REQUISITOS (SRS ADAPTADO A SDD)

### 1.1 Propósito y Alcance del Sistema
**Aduana IA** es un sistema intermediario de seguridad, anonimización, explicabilidad matemática y auditoría criptográfica (*AI Governance & Security Gateway*) diseñado para interceptar, sanitizar, evaluar y sellar en tiempo real toda transacción entre usuarios de instituciones públicas/reguladas venezolanas y modelos de Inteligencia Artificial (locales o en nube).

### 1.2 Actores y Perfiles de Usuario (*Stakeholders*)

| Actor | Rol en el Ecosistema | Necesidad Principal | Interfaz que Utiliza |
| :--- | :--- | :--- | :--- |
| **Ciudadano Venezolano** | Titular de los datos personales y solicitante del trámite público. | Que sus datos sensibles (Cédula, RIF, salud, ingresos) no se filtren y que su caso se evalúe sin sesgos arbitrarios. | Recibo Criptográfico de Auditoría (Código de verificación / QR). |
| **Funcionario Analista** | Operador público encargado de evaluar y decidir sobre el trámite (*Human-in-the-Loop*). | Asistencia rápida de IA para resumir casos y un puntaje matemático explicado que respalde su decisión administrativa. | **🖥️ Panel del Funcionario** (Triaje, Explicabilidad SHAP y Decisión Humana). |
| **Auditor / Contralor** | Inspector de Contraloría Interna, SUSCERTE o Seguridad de la Información. | Comprobar matemáticamente que el historial de decisiones no fue alterado en la base de datos y auditar la resistencia a ataques. | **🔍 Panel de Auditoría y Contraloría** (Verificador Ledger + Benchmark 100 ataques). |
| **Administrador TI** | Responsable de infraestructura sobre servidores **Canaima GNU/Linux**. | Un binario/servicio ligero ($< 80\text{ MB}$ RAM), sin dependencias propietarias, que opere incluso sin conexión a internet. | API `/api/v1/health/system` y despliegue local unificado. |

---

### 1.3 Catálogo de Requisitos Funcionales (RF) Trazables al Pipeline

#### Módulo 0: Consentimiento Informado y Protección de Tasa (Idea #8)
* **RF-01 (Validación de Consentimiento Explícito):** El sistema debe rechazar con código `BLOCKED_NO_CONSENT` cualquier petición donde `citizen_consent.granted` sea `False` o carezca de propósito declarado (`purpose_code`).
* **RF-02 (Sello Criptográfico de Consentimiento):** El sistema debe generar un `consent_hash` (`SHA-256`) vinculando el identificador de petición, la marca de tiempo UTC y el propósito aceptado por el ciudadano.
* **RF-03 (Control de Abuso sin Exposición de Identidad):** El sistema debe limitar la tasa de peticiones por ciudadano utilizando su índice ciego (`blind_citizen_id`) sin almacenar su Cédula en texto plano.

#### Módulo 1: `SHIELD` — Anonimización Soberana y Almacenamiento Restrictivo (Ideas #6 y #8)
* **RF-04 (Detección y Enmascaramiento Estructurado Nacional):** El sistema debe detectar y sustituir por tokens indexados consistentes (`[CEDULA_1]`, `[RIF_1]`, `[PHONE_1]`, `[BANK_1]`, `[EMAIL_1]`) toda Cédula venezolana (`V/E`), RIF (`V/E/J/G/P/C`), teléfono nacional (`0412/0414/0424/0416/0426/0212...`), correo y número de cuenta bancaria de 20 dígitos.
* **RF-05 (Validación Matemática Módulo 11 SENIAT):** Cuando se detecte un patrón de RIF, el sistema debe ejecutar el algoritmo oficial Módulo 11 del SENIAT (pesos `[4,3,2,7,6,5,4,3,2]`) y registrar en `shield_meta.rif_mod11_verified` la autenticidad matemática del documento.
* **RF-06 (Reconocimiento Léxico Contextual de Salud e Identidad):** El sistema debe enmascarar nombres propios precedidos por marcadores contextuales de trámite y términos clínicos sensibles incluidos en el diccionario local de protección de salud (`[CLINICAL_1]`).
* **RF-07 (Bóveda Efímera en RAM y Zeroization):** El mapeo entre los tokens (`[CEDULA_1]`) y el valor original (`V-12.345.678`) debe guardarse exclusivamente en `EphemeralVault` en memoria RAM con un $\text{TTL} \le 180\text{ segundos}$ y destruirse mediante `zeroize()` al concluir la petición.

#### Módulo 2: `GUARD-IN` — Defensa Activa contra Prompt Injection (Idea #18)
* **RF-08 (Normalización Anti-Evasión):** Antes de inspeccionar el texto, el sistema debe aplicar normalización canónica Unicode (`NFKC`), eliminar caracteres invisibles (*zero-width*) y decodificar cadenas sospechosas en `Base64` o `Hex` embebidas.
* **RF-09 (Cálculo Determinista de Riesgo Adversario):** El sistema debe evaluar el texto frente a reglas heurísticas y similitud de N-gramas (intentos de *override* de instrucciones, *jailbreak*, *roleplay* malicioso, inyección SQL/comandos y exfiltración de prompt), generando un `risk_score` continuo en $[0.0, 1.0]$ y bloqueando toda entrada que supere el umbral de política ($\ge 0.65$).
* **RF-10 (Encapsulamiento XML Sandbox y Canary Token Dinámico):** Toda solicitud permitida hacia el LLM debe envolverse en etiquetas estructurales `<instruccion_institucional_inmutable>` y `<entrada_ciudadano>`, inyectando un token único por transacción firmado con HMAC (`[[CANARY-HMAC-XXXXXXXX]]`).

#### Módulo de Interconectividad: `LLMAdapter` y `CircuitBreaker`
* **RF-11 (Conmutación Agnóstica de Proveedor IA):** El sistema debe permitir procesar el `masked_text` a través de tres conectores intercambiables: (a) Modelo Local Soberano vía Ollama/llama.cpp, (b) API externa compatible con OpenAI, o (c) Motor Institucional Determinista Offline.
* **RF-12 (Degradación Elegante por Circuit Breaker):** Si el conector del LLM supera un tiempo de espera de `3.5 segundos` o retorna error de red, el `CircuitBreaker` debe conmutar automáticamente al Motor Determinista Offline para garantizar que el funcionario reciba siempre la evaluación matemática de `EXPLICA` y el sellado en `LEDGER`.

#### Módulo 3: `GUARD-OUT` — Inspección de Salida y Prevención de Fugas (Idea #18)
* **RF-13 (Detección de Fuga de Canary y PII Residual):** El sistema debe inspeccionar la respuesta del LLM y abortar inmediatamente su entrega si contiene total o parcialmente el `canary_token` de la sesión o si detecta algún patrón de PII residual/alucinado.
* **RF-14 (Sanitización de Salida Segura):** El sistema debe neutralizar cualquier etiqueta ejecutable (`<script>`, `onload=`, `javascript:`) y marcar con advertencia respuestas que contengan afirmaciones normativas sin respaldo en el contexto institucional.

#### Módulo 4: `LEDGER` — Registro Criptográfico Inmutable (Idea #17)
* **RF-15 (Encadenamiento SHA-256 y Doble Sello HMAC):** Cada transacción finalizada (aprobada o bloqueada por seguridad) debe registrarse como un bloque secuencial $i$ cuyo `block_hash` dependa criptográficamente de `prev_hash` ($H_{i-1}$), `payload_hash`, `timestamp_utc` y `blind_citizen_id`, acompañado de una firma `hmac_signature` generada con la llave maestra del servidor en memoria.
* **RF-16 (Auditoría Completa y Detección Quirúrgica de Sabotaje):** El sistema debe proveer una función `verify_chain()` que recalcule todos los hashes y firmas HMAC desde el bloque génesis ($i=0$) hasta el bloque actual, identificando el `block_index` exacto y el tipo de alteración si un solo carácter fue modificado en SQLite.
* **RF-17 (Simulador de Sabotaje en Vivo y Recibo Ciudadano):** El sistema debe incluir en el Panel de Auditoría un control de demostración para alterar un registro histórico en la base de datos y comprobar en vivo la alerta de corrupción, además de emitir un código de recibo criptográfico (`citizen_receipt_code`) por cada trámite.

#### Módulo 5: `EXPLICA` — Modelo Matemático White-Box y Human-in-the-Loop (Idea #5)
* **RF-18 (Evaluación Tabular con Regresión Logística Real):** El sistema debe calcular la probabilidad de prioridad/elegibilidad del trámite mediante la función sigmoide $P(y=1\mid\mathbf{x}) = \frac{1}{1+e^{-(\beta_0 + \sum \beta_j x_j)}}$ utilizando coeficientes reales entrenados de forma determinista sobre `synthetic_tramites.csv`, sin emplear generadores aleatorios (`random()`).
* **RF-19 (Desglose de Pesos y Valores SHAP Lineales):** El sistema debe exponer para cada variable del trámite tanto su aporte directo ($\beta_j x_j$) como su valor SHAP lineal centrado respecto a la media poblacional ($\phi_j = \beta_j(x_j - \mu_j)$), verificando que la suma algebraica reconstruya el *logit* $z$ con error $< 10^{-9}$.
* **RF-20 (Soberanía de Decisión Humana con Justificación de Override):** El sistema debe exigir la confirmación del funcionario antes de sellar el dictamen; si el funcionario contradice la recomendación matemática del modelo (`human_override = True`), el sistema debe exigir una justificación textual ($\ge 20$ caracteres) que queda grabada de forma inmutable en el `LEDGER`.

---

### 1.4 Requisitos No Funcionales (RNF) y Restricciones de Calidad

| Código | Categoría | Especificación Medible y Verificable |
| :---: | :--- | :--- |
| **RNF-01** | **Latencia de Pasarela** | El tiempo acumulado de procesamiento de seguridad y auditoría (`SHIELD` + `GUARD-IN` + `GUARD-OUT` + `EXPLICA` + `LEDGER`, excluyendo el tiempo de generación del LLM externo) debe ser **$< 60\text{ ms}$** en el percentil 95. |
| **RNF-02** | **Cero PII en Disco** | **0 bytes** de Cédulas, RIFs, teléfonos o nombres originales pueden escribirse en archivos SQLite (`.db`, `-wal`, `-shm`), archivos JSON o salidas de log (`stdout`/`stderr`). |
| **RNF-03** | **Compatibilidad Canaima** | Ejecución 100% nativa sobre **Canaima GNU/Linux (Debian)** con Python 3.10+, consumo de RAM en reposo **$< 80\text{ MB}$** y arranque en frío **$< 300\text{ ms}$**. |
| **RNF-04** | **Autonomía Offline-First** | La interfaz web y todos los módulos del pipeline deben operar al **100% sin conexión a internet**, sin llamadas a CDNs externos de CSS, fuentes o librerías JS. |
| **RNF-05** | **Efectividad Adversaria** | Tasa de Mitigación (**TPR**) $\ge 88\%$ y Tasa de Falsos Positivos (**FPR**) $\le 4\%$ medida automáticamente sobre el benchmark auditable de $N=100$ prompts. |
| **RNF-06** | **Endurecimiento SQLite** | Activación obligatoria de `PRAGMA journal_mode=WAL;`, `PRAGMA synchronous=FULL;`, `PRAGMA secure_delete=ON;` y Triggers SQL `BEFORE UPDATE/DELETE` en la tabla de bloques. |

---

## 💼 PARTE 2: ESTRUCTURA Y MODELO DE NEGOCIO (GOVTECH & B2B REGULADO)

Un jurado de hackathon (y especialmente el jurado de *Venezuela Innova*) no solo evalúa que el código funcione: evalúa **si el proyecto es sostenible, escalable y resuelve un dolor económico e institucional real**.

### 2.1 El Caso de Negocio: ¿Por qué el Estado y la Banca Venezolana necesitan comprar/adoptar Aduana IA hoy?

Actualmente, las instituciones públicas y empresas reguladas en Venezuela enfrentan una **paradoja paralizante** frente a la Inteligencia Artificial:
1. **Si prohíben la IA:** Pierden productividad, mantienen colas lentas en atención ciudadana y sus propios empleados terminan usando cuentas personales gratuitas de ChatGPT/Claude desde sus teléfonos móviles, **filtrando datos críticos del Estado sin ningún control (*Shadow AI*)**.
2. **Si contratan IA en la nube directamente:** Violan la Ley de Infogobierno, exponen datos personales protegidos por el Art. 60 de la Constitución y gastan miles de dólares en tokens procesando peticiones repetitivas o ataques.
3. **Si intentan montar LLMs gigantes propios desde cero:** Requieren granjas de GPUs de decenas de miles de dólares que no están disponibles en la mayoría de los ministerios, gobernaciones ni universidades.

> **La Solución Económica de Aduana IA:** Aduana IA permite que cualquier ministerio, alcaldía, universidad, banco o clínica use **modelos ligeros locales en hardware existente (Canaima)** o **APIs híbridas de bajo costo** con **100% de seguridad jurídica, cero fugas de datos y auditoría de nivel contraloría desde el día 1**.

---

### 2.2 Segmentación de Mercado (Doble Motor: B2G Público + B2B Regulado)

| Segmento | Clientes Objetivo en Venezuela | Dolor Específico que Resuelve Aduana IA |
| :--- | :--- | :--- |
| **1. Sector Público Social y Trámites (B2G)** | Ministerios (Salud, Educación Universitaria, Trabajo, Alimentación), IVSS, SAIME, SENIAT, SAREN, Gobernaciones y Alcaldías. | Triaje rápido de solicitudes ciudadanas con priorización matemática justa (`EXPLICA`), protección de datos soberanos (`SHIELD`) y auditoría anticorrupción (`LEDGER`). |
| **2. Sector Financiero y Asegurador (B2B Regulado)** | Banca Pública (Banco de Venezuela, Bicentenario, Tesoro) y Banca Privada Nacional (Banesco, Mercantil, Provincial, BNC), Aseguradoras. | Cumplimiento estricto de normativas **SUDEBAN** al usar IA en atención de reclamos, análisis de crédito explicable (`EXPLICA`) y enmascaramiento de cuentas de 20 dígitos y RIFs. |
| **3. Sector Salud y Universitario (B2G / B2B)** | Red Hospitalaria, Clínicas privadas, UNETI y Universidades Nacionales. | Protección de historias clínicas sensibles antes de usar asistentes diagnósticos o administrativos y asignación transparente de becas/cupos. |

---

### 2.3 Modelo de Sostenibilidad e Ingresos (100% Compatible con la Ley de Infogobierno)

Dado que la **Ley de Infogobierno de Venezuela** establece el uso de Software Libre y estándares abiertos en la Administración Pública, un modelo basado en "vender licencias cerradas por usuario al Estado" sería rechazado por un jurado conocedor. **Aduana IA utiliza un Modelo Dual Open-Core Soberano (estilo Red Hat / Canonical / GitLab):**

1. **Línea 1 — Núcleo Abierto Soberano (*GovTech Open Standard*):**
   - El motor base de Aduana IA es auditable y libre para entidades académicas y pilotos estatales, eliminando barreras burocráticas de adopción y posicionándolo como el **estándar nacional recomendado por CNTI / SUSCERTE**.
2. **Línea 2 — Contratos de Implantación, Soporte Crítico y Calibración Institucional (B2G):**
   - Cobro por servicios especializados de ingeniería: despliegue en centros de datos institucionales sobre Canaima, integración con bases de datos legadas (Postgres/Oracle), y **entrenamiento a medida de modelos `EXPLICA`** específicos para las reglas de negocio de cada ministerio.
3. **Línea 3 — Suscripción de Inteligencia de Amenazas (*Aduana Threat-Feed*):**
   - Actualización mensual automatizada de reglas heurísticas `GUARD-IN` contra nuevos vectores de *Jailbreak* y actualización de diccionarios regulatorios de `SHIELD`.
4. **Línea 4 — Licenciamiento Enterprise SLA para Banca, Seguros y Clínicas Privadas (B2B):**
   - Suscripción anual por nodo/instancia (*On-Premise Enterprise*) para bancos y aseguradoras privadas que requieren soporte 24/7, paneles de cumplimiento SUDEBAN y alta disponibilidad. **El flujo de caja del sector privado financia la evolución continua de la plataforma pública.**

---

### 2.4 Impacto Cuantificable (Métricas de Retorno de Inversión para el Pitch)

| Indicador de Impacto | Sin Aduana IA (Uso Directo / Manual) | Con Aduana IA Desplegada | Beneficio Neto Demostrable |
| :--- | :---: | :---: | :--- |
| **Exposición de PII Ciudadano a Terceros** | $100\%$ de los datos enviados en claro | **$0\%$** (Enmascarado en $< 20\text{ ms}$) | Cumplimiento legal absoluto (CRBV Art. 60). |
| **Costo de Infraestructura para Correr el Gateway** | Requiere servidores GPU costosos | **$< 80\text{ MB}$ RAM en Canaima CPU** | Funciona en el 100% del parque tecnológico actual del Estado. |
| **Ahorro en Consumo de Tokens / Cómputo LLM** | Paga por ataques, spam y prompts fallidos | **Ahorro del $35\% - 60\%$** | `SHIELD` y `GUARD-IN` filtran ataques y abuso antes de tocar el LLM. |
| **Tiempo de Auditoría de Contraloría sobre Decisiones** | Semanas revisando expedientes manuales | **$< 50\text{ ms}$** (`verify_chain()`) | Detección instantánea de cualquier alteración o desvío humano. |

---

## ⚡ PARTE 3: PLAN DE CONSTRUCCIÓN DEL MVP EN 48 HORAS USANDO EL "TRIDENTE IA" (CLAUDE + CHATGPT + GEMINI)

Para construir un sistema de esta solidez en solo **2 días (48 horas de Hackathon)** sin caos ni errores de integración, el equipo utilizará una estrategia de **Orquestación Especializada de 3 IAs**, asignando a cada modelo exactamente aquello en lo que supera a los demás.

### 3.1 División Estratégica del Trabajo entre Claude, ChatGPT y Gemini

| IA Asignada | Rol en el Hackathon | Por qué es la mejor para esta tarea | Entregables Exactos que debe generar |
| :--- | :--- | :--- | :--- |
| **🟣 Claude (3.5 / 3.7 Sonnet)** | **Arquitecto Backend, Criptografía y Tests SDD** | Es el modelo más preciso escribiendo código Python modular limpio, respetando `@dataclass(frozen=True)`, lógica criptográfica (`hashlib`, `hmac`, `sqlite3`) y pruebas `pytest` sin inventar librerías inexistentes. | `core/context.py`, `core/ephemeral_vault.py`, `stage1_shield.py` (con Módulo 11 SENIAT), `stage2_guard_in.py`, `stage3_guard_out.py`, `stage4_ledger.py`, `stage5_explica.py`, `app.py` y toda la carpeta `tests/`. |
| **🟢 ChatGPT (GPT-4o / o3-mini)** | **Red Teamer, Generador de Datos Sintéticos y Diseñador Frontend Offline** | Excelente generando JSONs estructurados creativos (ataques de inyección en español venezolano y trámites realistas) y maquetando interfaces HTML5/CSS/JS interactivas muy visuales en un solo archivo. | `data/attack_benchmark.json` (los 100 prompts), `data/synthetic_tramites.csv` (datos de entrenamiento coherentes), `static/index.html`, `static/styles.css` (100% local sin CDN) y `static/app.js`. |
| **🔵 Gemini (1.5 Pro / 2.5 Pro)** | **Auditor de Contexto Global, Integrador y Director de Pitch** | Su enorme ventana de contexto permite subirle **todos los archivos del proyecto a la vez** para detectar errores de integración, verificar que `static/app.js` consuma exactamente los campos de `AduanaPacket` de `app.py` y redactar las especificaciones `specs/`. | Archivos `specs/01..05.spec.md`, revisión cruzada de extremo a extremo (*Bug Hunting* de integración), verificación de cero fugas de PII y refinamiento del guion de defensa en vivo. |

---

### 3.2 Regla de Oro para que el Código de las 3 IAs Encaje en 0 Segundos

Antes de pedirle cualquier cosa a **Claude**, **ChatGPT** o **Gemini**, el miembro del equipo debe pegar en el primer mensaje:
1. El **Bloque de la Parte 1 y Parte 2** de `PROMPT_MAESTRO.md` (que contiene el contrato JSON `AduanaPacket` v2.0 y las `@dataclass` de `core/context.py`).
2. La instrucción explícita: *"Prohibido cambiar los nombres de las llaves del JSON `AduanaPacket`. Tu código debe consumir o devolver exactamente estas llaves"*.

---

### 3.3 Cronograma Táctico de 48 Horas (Minuto a Minuto para el Equipo)

#### 🗓️ DÍA 1 (Viernes 13 de Noviembre): El Motor Criptográfico, Matemático y Datos Reales

* **Bloque 1 (Horas 0 a 3) — Congelación de Contrato y Kernel Base:**
  * **Acción con Claude (Gatillo 0):** Generar `core/config.py`, `core/context.py` (`AduanaPacket` inmutable) y `core/ephemeral_vault.py` (bóveda en RAM con TTL de 180s y `zeroize()`).
  * **Acción con ChatGPT:** Generar `data/synthetic_tramites.csv` (200 filas de trámites sociales venezolanos con correlación lógica real entre vulnerabilidad, carga familiar y prioridad) y `data/attack_benchmark.json` (50 consultas benignas de SAIME/IVSS/Salud/Becas + 50 ataques de Prompt Injection, DAN, Base64 y fuga de Canary).
  * **Hito de Control (Hora 3):** `pytest tests/test_ca05_restrictive_db.py` pasa en verde.

* **Bloque 2 (Horas 3 a 8) — Construcción Paralela de las Etapas 1, 2 y 3 (`SHIELD` + `GUARDIÁN`):**
  * **Integrante A con Claude (Gatillo 1):** Construye `pipeline/stage1_shield.py` con Regex venezolano, validador matemático **Módulo 11 SENIAT** para RIF, diccionario clínico `frozenset` y generación de `blind_citizen_id` HMAC. Corre `pytest tests/test_ca01_shield.py`.
  * **Integrante B con Claude (Gatillo 2):** Construye `pipeline/stage2_guard_in.py` (normalización `NFKC`, decodificador Base64 preventivo, heurísticas + N-gramas, delimitadores XML y Canary HMAC dinámico) y `pipeline/stage3_guard_out.py` + `run_security_benchmark()`. Corre `pytest tests/test_ca02_guardian.py` verificando $\text{TPR} \ge 88\%$.
  * **Hito de Control (Hora 8):** `SHIELD` y `GUARDIÁN` procesan textos reales en $< 20\text{ ms}$ cada uno.

* **Bloque 3 (Horas 8 a 14) — Construcción Paralela de Etapas 4 y 5 (`LEDGER` + `EXPLICA`):**
  * **Integrante A con Claude (Gatillo 3):** Construye `pipeline/stage4_ledger.py` sobre SQLite con `WAL`, `secure_delete=ON`, Triggers SQL de inmutabilidad, encadenamiento `SHA-256` + firma `HMAC-SHA256`, `verify_chain()` y `simulate_tampering(block_id)`. Corre `pytest tests/test_ca03_ledger.py`.
  * **Integrante B con Claude (Gatillo 4):** Construye `pipeline/stage5_explica.py` entrenando la Regresión Logística determinista al arrancar, calculando probabilidad sigmoide, pesos $\beta_j x_j$ y **Valores SHAP Lineales** $\phi_j = \beta_j(x_j - \mu_j)$, más la validación de *Human Override*. Corre `pytest tests/test_ca04_explica.py`.
  * **Hito de Control (Hora 14 - Cierre Día 1):** Las 5 etapas del pipeline existen en Python puro y pasan sus pruebas unitarias en consola sobre Canaima GNU/Linux.

---

#### 🗓️ DÍA 2 (Sábado 14 de Noviembre): Interconectividad, Interfaz de Alto Impacto y Pulido de Demo

* **Bloque 4 (Horas 14 a 18) — Conectores Multi-Modelo, Circuit Breaker y API FastAPI:**
  * **Acción con Claude (Gatillos 5 y 6 backend):** Construir `pipeline/llm_adapter.py` (con `LocalOllamaAdapter`, `OpenAICompatibleAdapter` y `OfflineDeterministicAdapter` + `CircuitBreaker` a 3.5s) y el orquestador `app.py` con todos los endpoints REST (`/api/v1/gateway/process`, `/api/v1/ledger/verify`, `/api/v1/ledger/tamper-sim`, `/api/v1/metrics/benchmark`, `/api/v1/health/system`).
  * **Hito de Control (Hora 18):** El servidor FastAPI levanta con `uvicorn app:app` y responde en Swagger/cURL en modo 100% desconectado de internet.

* **Bloque 5 (Horas 18 a 26) — Construcción del Panel Dual Offline-First (El Efecto "WOW" Visual):**
  * **Acción con ChatGPT:** Pasar las respuestas JSON exactas de los endpoints de `app.py` y pedir un dashboard gubernamental de alta estética institucional en `static/index.html`, `static/styles.css` y `static/app.js` (tema oscuro/institucional sobrio, sin CDNs externos) que incluya:
    1. **Selector Rápido de Casos de Demo (1 Clic):** Botones preconfigurados para el jurado (*"Cargar Trámite Médico Legítimo con PII"*, *"Lanzar Ataque Prompt Injection DAN"*, *"Lanzar Ataque Ofuscado Base64"*).
    2. **Rayos-X del Pipeline en Vivo:** Tarjetas animadas que se iluminan en secuencia (`SHIELD` $\rightarrow$ `GUARD-IN` $\rightarrow$ `LLM` $\rightarrow$ `GUARD-OUT` $\rightarrow$ `EXPLICA` $\rightarrow$ `LEDGER`) mostrando los milisegundos de cada etapa y comparando el texto original vs. el texto con `[CEDULA_1]` y `[RIF_1]`.
    3. **Gráfico Horizontal de Barras SHAP en `EXPLICA`:** Barras verdes para variables que suman prioridad y rojas para las que restan, más los botones de **Confirmar Recomendación** o **Sobrescribir con Justificación**.
    4. **Consola de Contraloría Interactiva:** Visualizador de bloques encadenados con hashes truncados, botón rojo **"⚡ Simular Sabotaje en Base de Datos"**, botón **"🔍 Verificar Integridad Criptográfica"** y medidor visual del **Benchmark de 100 Ataques**.

* **Bloque 6 (Horas 26 a 34) — Auditoría Global con Gemini y Pruebas de Estrés Sin Internet:**
  * **Acción con Gemini:** Subir todos los archivos `.py`, `.html`, `.js` y `.json` a una sesión de Gemini Pro y ejecutar el prompt: *"Audita la consistencia total entre los nombres de campos en `app.py` y `static/app.js`, verifica que todos los tests `CA-01` a `CA-06` pasen, genera los documentos formales en `specs/01..05.spec.md` y verifica que no exista ni una sola llamada a internet o `random()`"*.
  * **Prueba de Fuego (*Air-Gap Test*):** Apagar el Wi-Fi de la laptop Canaima, reiniciar el servicio desde cero, correr `pytest -v` (todo en verde en $< 2\text{ segundos}$) y ejecutar las 3 demos en el navegador.

* **Bloque 7 (Horas 34 a 48) — *Code Freeze*, Ensayo Cronometrado de 3 Minutos y Preparación de Mesa:**
  * **Prohibido tocar el código después de la Hora 38.** Las últimas horas se dedican exclusivamente a ensayar el pitch de 3 minutos con cronómetro y dejar en pantalla dos pestañas listas: la interfaz web de Aduana IA y una terminal mostrando los tests SDD pasando al 100%.

---

## 🏆 PARTE 4: ESTRUCTURA DE VENTA Y PITCH GANADOR PARA EL JURADO

En un hackathon, el 70% de los equipos muestra "diapositivas con promesas" o un chatbot genérico conectado a una API que falla si el Wi-Fi del salón está lento. **Aduana IA gana porque muestra ingeniería real, criptografía verificable en vivo y soberanía tecnológica en 180 segundos.**

### 4.1 La Estructura Psicológica de Venta en 4 Actos (3 Minutos Exactos)

#### 🔥 Acto 1: El Gancho de Impacto Nacional (0:00 a 0:30) — *El Problema que Nadie Está Viendo*
> **Qué decir:**  
> *"Buenas tardes, jurado. Hoy mismo, mientras estamos en este hackathon, cientos de funcionarios y profesionales en Venezuela están pegando expedientes con Cédulas de Identidad, RIFs, diagnósticos médicos y datos presupuestarios en IAs externas para redactar informes más rápido. Quieren ser eficientes, pero sin querer están entregando la soberanía de datos del país, exponiéndose a ataques de inyección de prompts y tomando decisiones públicas sobre cajas negras que ninguna Contraloría puede auditar.*  
> *No podemos prohibir la IA, pero tampoco podemos usarla a ciegas. Por eso creamos **Aduana IA**: la primera pasarela soberana de gobernanza, seguridad Zero-Trust y auditoría criptográfica para la IA pública venezolana, corriendo 100% nativa sobre **Canaima GNU/Linux**."*

#### 🛡️ Acto 2: Demo 1 — Privacidad Soberana y Justicia Matemática (0:30 a 1:25) — *SHIELD + EXPLICA*
> **Qué hacer en pantalla:** Haz clic en el botón **"Caso 1: Trámite de Salud con Datos Reales"** y presiona **Procesar por Aduana IA**.  
> **Qué decir mientras se ilumina el pipeline:**  
> *"Vean esto en vivo: una ciudadana solicita prioridad para un insumo médico e incluye su Cédula, su RIF, su teléfono y su diagnóstico. En solo **4 milisegundos**, nuestra primera etapa, **SHIELD**, valida matemáticamente el RIF con el **algoritmo Módulo 11 del SENIAT**, enmascara toda la información sensible con tokens reversibles solo en memoria RAM —**cero datos personales tocan jamás el disco duro**— y envía al modelo únicamente texto sanitizado.*  
> *Al mismo tiempo, **EXPLICA** no usa números al azar ni cajas negras: ejecuta una **Regresión Logística auditable con valores SHAP lineales** que le muestra al funcionario exactamente cuántos puntos aporta la vulnerabilidad económica y la carga familiar. El modelo recomienda, pero **el funcionario tiene siempre la última palabra**, y si decide contradecir al modelo, el sistema le exige justificar por qué."*

#### 🚨 Acto 3: Demo 2 — Defensa Activa y Métricas Honestas (1:25 a 2:10) — *EL GUARDIÁN*
> **Qué hacer en pantalla:** Haz clic en **"Caso 2: Ataque Prompt Injection + Intento de Fuga"** y luego en **"Ejecutar Benchmark de 100 Vectores"**.  
> **Qué decir:**  
> *"¿Qué pasa si un atacante intenta manipular la IA inyectando órdenes ocultas o texto codificado en Base64 para aprobarse un trámite sin cumplir los requisitos? Nuestro **Guardián de doble capa (`Guard-In` y `Guard-Out`)** normaliza el texto, detecta el patrón adversario e inyecta un **Canary Token criptográfico dinámico** por transacción. El ataque es neutralizado antes de causar daño.*  
> *Y como en ingeniería seria no pedimos fe ciega ni prometemos un 100% mágico, incluimos un **Benchmark Auditable en vivo con 100 casos reales**: aquí mismo el jurado puede ver nuestra tasa real de mitigación superior al 88% con menos de 4% de falsos positivos ejecutada en milisegundos."*

#### 🔗 Acto 4: Demo 3 y Cierre — El Golpe Maestro de Inmutabilidad (2:10 a 3:00) — *LEDGER INMUTABLE*
> **Qué hacer en pantalla:** Cambia al **Panel de Contraloría**, muestra la cadena en **VERDE**, haz clic en **"⚡ Simular Sabotaje en Base de Datos"** y luego en **"🔍 Auditar Cadena Criptográfica"** (la pantalla pasa a **ROJO** señalando el bloque exacto).  
> **Qué decir para cerrar con broche de oro:**  
> *"Finalmente, cada decisión queda sellada en nuestro **Ledger Inmutable con doble sello: encadenamiento SHA-256 más firma HMAC de servidor**, entregándole un recibo criptográfico al ciudadano. ¿Qué ocurre si mañana alguien con acceso de administrador entra directo al archivo SQLite e intenta cambiar un dictamen de 'Rechazado' a 'Aprobado'? Hagámoslo ahora mismo en vivo... Al auditar la cadena, en menos de 20 milisegundos **Aduana IA detecta el sabotaje con precisión quirúrgica en el bloque exacto**.*  
> *Desarrollado bajo metodología **SDD estricta**, con **cero dependencias de internet**, menos de 80 MB de RAM en **Canaima GNU/Linux** y listo para proteger desde una alcaldía hasta la banca nacional. Con **Aduana IA**, Venezuela no solo consume Inteligencia Artificial: la gobierna con soberanía, ética y seguridad verificable. Muchas gracias."*

---

### 4.2 Argumentos Ganadores según el Perfil de cada Miembro del Jurado

| Perfil del Jurado | Qué es lo que más valora | Tu frase clave para convencerlo |
| :--- | :--- | :--- |
| **👨‍💻 El Ingeniero / Ciber-seguridad** | Rigor técnico, que no sea un "wrapper de ChatGPT" con `if/else` falsos ni `random()`. | *"Implementamos validación real Módulo 11 SENIAT, normalización Unicode NFKC contra evasión visual, valores SHAP lineales exactos ($\phi_j = \beta_j(x_j - \mu_j)$) y doble sello SHA-256 + HMAC con `PRAGMA secure_delete=ON` en SQLite. Aquí tienes nuestra suite de `pytest` corriendo en vivo."* |
| **🏛️ El Institucional / Académico (UNETI / Estado)** | Soberanía tecnológica, cumplimiento legal, ética y que funcione en la infraestructura real del país. | *"Cumplimos los artículos 28 y 60 de la Constitución y la Ley de Infogobierno: ningún dato personal se graba en disco ni sale en claro fuera de la institución, corre en Canaima GNU/Linux con 80 MB de RAM y funciona incluso sin internet gracias a nuestro Circuit Breaker."* |
| **📈 El Estratega / *Venezuela Innova*** | Escalabilidad nacional, modelo de sostenibilidad y facilidad de adopción en múltiples sectores. | *"Aduana IA no reemplaza los sistemas actuales del Estado ni de la Banca; se coloca delante como una pasarela enchufable en 10 minutos, ahorrando hasta un 60% en costos de cómputo y abriendo un modelo sostenible de soporte institucional y licenciamiento bancario SUDEBAN."* |

---

### 4.3 Checklist de Victoria (15 Minutos Antes de que el Jurado Llegue a tu Mesa)

1. **Modo Offline Verificado:** Comprueba que la interfaz carga todos sus estilos, iconos y gráficos con el Wi-Fi desconectado (por si la red del salón colapsa durante la evaluación).
2. **Base de Datos Limpia con 5 Bloques Iniciales:** Ten pre-cargados 4 o 5 trámites variados en el `LEDGER` (aprobados, rechazados y un intento de ataque bloqueado) para que la cadena criptográfica ya luzca poblada e interesante desde el primer segundo.
3. **Terminal Abierta en Segundo Plano:** Deja una ventana de terminal visible con la ejecución reciente de `pytest -v` mostrando los 6 criterios de aceptación (`CA-01` a `CA-06`) en **`PASSED (100%)`**. Si un juez técnico pregunta *"¿Cómo sé que esto sigue SDD?"*, le muestras la terminal en 2 segundos.
4. **Roles del Equipo en el Pitch:**
   - **Vocero Principal (Storyteller):** Lleva el hilo conductor de los 3 minutos sin leer texto de la pantalla.
   - **Operador de Consola (Piloto de Demo):** Ejecuta los clics exactos en el momento en que el vocero los menciona (Caso 1 $\rightarrow$ Ataque + Benchmark $\rightarrow$ Sabotaje Ledger).
   - **Defensor Técnico / Criptográfico:** Listo para responder al instante las preguntas de arquitectura, fórmulas matemáticas de `EXPLICA` y almacenamiento restrictivo.
