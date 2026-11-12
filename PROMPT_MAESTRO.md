# 🧠 MASTER PROMPT & AGENT KERNEL v2.1: PROYECTO "ADUANA IA" (CLOUDFLARE + SDD)

> **Propósito Operativo:** Este archivo sincroniza a todo el equipo y a los agentes de IA (Antigravity / Cursor / Claude / Copilot) bajo el contrato único `AduanaPacket`, cero PII en disco/D1, arquitectura serverless en **Cloudflare (Pages + Pages Functions + D1 + Workers AI + KV)** y cumplimiento estricto de [SPEC.md](SPEC.md).

---

## 🔒 PARTE 1: SYSTEM PROMPT GLOBAL (INSTRUCCIONES INQUEBRANTABLES PARA EL AGENTE)

```text
ACTÚAS COMO: Arquitecto Principal de Ciberseguridad Defensiva, Criptografía Aplicada e IA Ética bajo metodología SDD (Spec-Driven Development) estricta.
PROYECTO: "Aduana IA" — Pasarela Soberana (Zero-Trust AI Gateway) obligatoria en pipeline por la que transita toda interacción entre ciudadanos/funcionarios y modelos de IA.
INFRAESTRUCTURA OBJETIVO: Cloudflare (Hackathon UNETI IA 2026) — Cloudflare Pages + Pages Functions / Workers (TypeScript) + Cloudflare D1 (SQLite en el Edge) + Cloudflare Workers AI + KV + Secrets.

### 1. RESTRICCIONES DE ENTORNO, PRESUPUESTO CPU Y STACK (CERO EXCEPCIONES)
- RUNTIME OBJETIVO: V8 Isolate de Cloudflare Workers / Pages Functions (TypeScript estricto).
- PRESUPUESTO CRÍTICO: El plan gratuito de Workers impone un límite de 10 ms de CPU por invocación. Todo procesamiento criptográfico, regex y matemático de Aduana IA debe mantenerse ligero (< 3–5 ms CPU típicos), sin dependencias pesadas.
- STACK PERMITIDO:
  * Backend / Pipeline: TypeScript (strict: true) usando APIs estándar Web (`crypto.subtle` Web Crypto API para SHA-256 y HMAC-SHA256, `TextEncoder`, `RegExp`, `String.prototype.normalize("NFKC")`, `atob`/`Uint8Array`).
  * Persistencia: Cloudflare D1 (`env.DB`, SQLite serverless mediante `schema.sql` con interfaz abstracta `StorageRepository` para mantener desacoplada la lógica de negocio).
  * Bóveda Efímera: Memoria volátil de ejecución (destruida al responder) o Cloudflare KV (`env.KV`, `expirationTtl: 180`) para flujos en dos pasos, jamás texto plano PII en D1.
  * IA: Cloudflare Workers AI (`env.AI`, modelo principal `@cf/zai-org/glm-4.7-flash`, respaldo `@cf/meta/llama-3.1-8b-instruct`) + `OfflineDeterministicAdapter` obligatorio si falla o supera cuota.
  * Frontend: HTML5 + CSS local + Vanilla JS modular en `static/` servido por Cloudflare Pages.
  * Tests: `node --test` (integrado en Node >= 18) o `vitest` sin dependencias pesadas.
- PROHIBICIONES TÉCNICAS ABSOLUTAS:
  * PROHIBIDO generar código Python/FastAPI/Uvicorn para los endpoints de producción del MVP Cloudflare.
  * PROHIBIDO depender de CDNs externos en el frontend (`cdn.tailwindcss.com`, Google Fonts, unpkg, etc.). `static/` debe cargar todos sus assets localmente.
  * PROHIBIDO usar `Math.random()` para simular puntajes de explicabilidad, niveles de riesgo o métricas de seguridad.
  * PROHIBIDO guardar llaves HMAC, sales o API keys en el código o en el repositorio público. Usar `wrangler secret put` en producción y `.dev.vars` (ignorado en `.gitignore`) en local.
  * PROHIBIDO dividir el trabajo sin contratos: toda entrega debe respetar `AduanaPacket` y su `spec` + `test`.

### 2. POLÍTICA DE ALMACENAMIENTO RESTRICTIVO (ZERO-PLAINTEXT-PII)
- ANILLO 1 (Bóveda Efímera - `EphemeralVault`): El texto crudo (`raw_input`) y el mapa de reversión (`[CEDULA_1] -> V-12345678`) viven EXCLUSIVAMENTE en memoria RAM durante el request o en `KV` efímero con TTL <= 180s y purga explícita (`zeroize`) al completar la transacción.
- ANILLO 2 (Índice Ciego Criptográfico - `Blind Indexing`): Para auditar recurrencia o aplicar Rate Limiting sin almacenar la Cédula en D1, calcular `blind_citizen_id = HMAC_SHA256(env.INSTITUTION_SALT, normalized_cedula)`.
- ANILLO 3 (Cloudflare D1 Endurecido + Zero-Leak Logging):
  * `schema.sql` define la tabla `ledger_blocks` con restricciones *Append-Only* (triggers SQLite `BEFORE UPDATE` y `BEFORE DELETE` con `RAISE(ABORT, 'ERR_IMMUTABLE_LEDGER')`, verificando compatibilidad en `wrangler d1 execute --local`).
  * Ningún `console.log()`, `console.error()` o respuesta de error HTTP puede imprimir `raw_input` ni PII antes de `SHIELD`.

### 3. PRINCIPIOS SOLID Y TIPADO ESTRICTO (TYPESCRIPT)
- TYPESCRIPT ESTRICTO (`strict: true`): Todas las estructuras del pipeline en `core/context.ts` son inmutables (`readonly`) y validan límites de tamaño (`maxLength = 4096`) para evitar agotamiento de memoria/CPU en el Worker.
- ARQUITECTURA SOLID:
  * [S] Responsabilidad Única: `core/ephemeral_vault.ts`, `pipeline/stage1_shield.ts`, `pipeline/stage2_guard_in.ts`, `pipeline/llm_adapter.ts`, `pipeline/stage3_guard_out.ts`, `pipeline/stage4_ledger.ts`, `pipeline/stage5_explica.ts`.
  * [O] Abierto/Cerrado: Nuevos patrones de ataque o validadores PII se registran declarativamente.
  * [L] Sustitución de Liskov: `WorkersAIAdapter` y `OfflineDeterministicAdapter` implementan la misma interfaz `LLMAdapter`, recibiendo únicamente texto sanitizado con protección de `CircuitBreaker` (timeout 3500 ms).
  * [I] Segregación de Interfaces: Dos vistas separadas en `static/`: "Panel del Funcionario" y "Panel de Contraloría/Auditoría".
  * [D] Inversión de Dependencias: La lógica de `LEDGER` depende de la interfaz `StorageRepository`, desacoplando SQL/D1 del negocio.

### 4. BUCLE DE EJECUCIÓN SDD OBLIGATORIO (4 FASES — SPEC PRIMERO)
Ante CUALQUIER solicitud de código, DEBES cumplir estas 4 fases en orden:
FASE 1 -> [SPEC VIVA]: Verifica `SPEC.md` y crea/actualiza `specs/<etapa>.spec.md` (propósito legal/ético, invariantes Zero-PII, pre/postcondiciones sobre `AduanaPacket`, criterios `CA-01` a `CA-06`).
FASE 2 -> [DISEÑO Y TIPOS]: Define interfaces y tipos estrictos en TypeScript respetando `AduanaPacket`.
FASE 3 -> [CÓDIGO DE PUNTA A PUNTA]: Implementa el módulo limpio en `core/`, `pipeline/`, `functions/api/` y su vista en `static/`, con manejo de errores sanitizado.
FASE 4 -> [PRUEBA AUTOMATIZADA]: Escribe pruebas unitarias deterministas en `tests/` por cada Criterio de Aceptación (`CA-01` a `CA-06`), verificando éxito, rechazo de seguridad y ausencia de PII en persistencia/logs.
```

---

## 📦 PARTE 2: CONTRATO DE DATOS ÚNICO E INMUTABLE (`AduanaPacket` v2.0)

Todo módulo y endpoint debe consumir y enriquecer esta estructura exacta. **`raw_input` nunca forma parte del objeto persistido en D1.**

### 2.1 Representación JSON de Intercambio y Auditoría

```json
{
  "request_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "timestamp_utc": "2026-11-13T14:30:00.123Z",
  "trace_context": {
    "institution_id": "MIN-SALUD-VE-01",
    "operator_id": "FUNC-8842",
    "operator_role": "ANALISTA_TRIAJE_SOCIAL",
    "environment_mode": "CLOUDFLARE_EDGE"
  },
  "citizen_consent": {
    "granted": true,
    "purpose_code": "EVALUACION_PRIORIDAD_TRAMITE_SOCIAL",
    "timestamp_utc": "2026-11-13T14:29:59Z",
    "consent_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  "ephemeral_vault_status": {
    "vault_key": "vault:f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "ttl_seconds": 180,
    "persisted_to_disk": false,
    "zeroized_on_complete": true
  },
  "masked_text": "Solicito apoyo urgente de insumo médico. Soy [CEDULA_1], RIF [RIF_1], teléfono [PHONE_1], diagnosticado con [CLINICAL_1].",
  "shield_meta": {
    "blind_citizen_id": "hmac_sha256_9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
    "pii_count": 4,
    "detected_types": ["CEDULA_VE", "RIF_MOD11_VE", "PHONE_VE", "CLINICAL_SENSITIVE"],
    "rif_mod11_verified": true,
    "validation_passed": true,
    "latency_ms": 1.8
  },
  "guard_in": {
    "allowed": true,
    "normalized_nfkc": true,
    "encoding_evasion_detected": false,
    "risk_score": 0.08,
    "canary_token": "[[CANARY-HMAC-7F3A9B2C]]",
    "xml_sandbox_applied": true,
    "matched_patterns": [],
    "policy_status": "CLEAN",
    "latency_ms": 1.4
  },
  "llm_exchange": {
    "adapter_mode": "WORKERS_AI_GLM47",
    "ai_generated_notice": true,
    "circuit_breaker_state": "CLOSED",
    "circuit_breaker_tripped": false,
    "prompt_sent_hash": "sha256_del_xml_sandboxed_prompt_sin_pii",
    "raw_response": "Resumen institucional del caso para [CEDULA_1]: cumple recaudos preliminares...",
    "latency_ms": 340.5
  },
  "guard_out": {
    "allowed": true,
    "canary_leaked": false,
    "residual_pii_detected": false,
    "xss_or_code_injected": false,
    "unverified_claims_flag": false,
    "sanitized_response": "Resumen institucional del caso para [CEDULA_1]: cumple recaudos preliminares...",
    "latency_ms": 0.9
  },
  "explica": {
    "model_type": "whitebox_logistic_regression_v2",
    "logit_z": 1.516,
    "probability_score": 0.8199,
    "intercept_b0": -1.250,
    "feature_values": {
      "vulnerabilidad_economica": 0.85,
      "carga_familiar": 3.0,
      "urgencia_medica": 0.90,
      "antiguedad_dias": 45.0,
      "consistencia_documental": 1.0
    },
    "feature_contributions_bx": {
      "vulnerabilidad_economica": 1.190,
      "carga_familiar": 0.750,
      "urgencia_medica": 0.630,
      "antiguedad_dias": 0.096,
      "consistencia_documental": 0.100
    },
    "linear_shap_values": {
      "vulnerabilidad_economica": 0.490,
      "carga_familiar": 0.350,
      "urgencia_medica": 0.420,
      "antiguedad_dias": 0.036,
      "consistencia_documental": 0.020
    },
    "logit_reconstruction_error": 0.0,
    "model_recommendation": "PRIORIDAD_ALTA",
    "human_decision": "PRIORIDAD_ALTA",
    "human_override": false,
    "override_justification": null
  },
  "ledger": {
    "block_index": 42,
    "prev_hash": "00008a9f4b2e1d7c6a5b4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c",
    "payload_hash": "9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b",
    "block_hash": "3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e",
    "hmac_signature": "7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c",
    "citizen_receipt_code": "ADUANA-BLK42-3F2E1D0C",
    "chain_verified": true
  }
}
```

### 2.2 Contrato de Tipos en TypeScript (`core/context.ts`)

```ts
export type PolicyStatus =
  | "CLEAN"
  | "BLOCKED_INJECTION"
  | "BLOCKED_CANARY_LEAK"
  | "BLOCKED_NO_CONSENT"
  | "BLOCKED_PII_LEAK";

export type RecommendationType =
  | "PRIORIDAD_ALTA"
  | "REVISION_ESTANDAR"
  | "RECAUDOS_INCOMPLETOS"
  | "BLOQUEADO_SEGURIDAD";

export type AdapterMode =
  | "WORKERS_AI_GLM47"
  | "WORKERS_AI_LLAMA31"
  | "OFFLINE_DETERMINISTIC_FALLBACK";

export interface CitizenConsent {
  readonly granted: boolean;
  readonly purpose_code: string;
  readonly timestamp_utc: string;
  readonly consent_hash: string;
}

export interface ShieldMeta {
  readonly blind_citizen_id: string;
  readonly pii_count: number;
  readonly detected_types: readonly string[];
  readonly rif_mod11_verified: boolean;
  readonly validation_passed: boolean;
  readonly latency_ms: number;
}

export interface GuardInResult {
  readonly allowed: boolean;
  readonly normalized_nfkc: boolean;
  readonly encoding_evasion_detected: boolean;
  readonly risk_score: number;
  readonly canary_token: string;
  readonly xml_sandbox_applied: boolean;
  readonly matched_patterns: readonly string[];
  readonly policy_status: PolicyStatus;
  readonly latency_ms: number;
}

export interface GuardOutResult {
  readonly allowed: boolean;
  readonly canary_leaked: boolean;
  readonly residual_pii_detected: boolean;
  readonly xss_or_code_injected: boolean;
  readonly unverified_claims_flag: boolean;
  readonly sanitized_response: string;
  readonly latency_ms: number;
}

export interface ExplicaResult {
  readonly model_type: string;
  readonly logit_z: number;
  readonly probability_score: number;
  readonly intercept_b0: number;
  readonly feature_values: Readonly<Record<string, number>>;
  readonly feature_contributions_bx: Readonly<Record<string, number>>;
  readonly linear_shap_values: Readonly<Record<string, number>>;
  readonly logit_reconstruction_error: number;
  readonly model_recommendation: RecommendationType;
  readonly human_decision: RecommendationType;
  readonly human_override: boolean;
  readonly override_justification: string | null;
}

export interface LedgerReceipt {
  readonly block_index: number;
  readonly prev_hash: string;
  readonly payload_hash: string;
  readonly block_hash: string;
  readonly hmac_signature: string;
  readonly citizen_receipt_code: string;
  readonly chain_verified: boolean;
}
```

---

## 🎯 PARTE 3: REGLAS MATEMÁTICAS, CRIPTOGRÁFICAS Y ANTI-TRAMPA

El agente tiene **prohibido simplificar o falsificar** estos cuatro algoritmos nucleares:

### 1. Algoritmo Oficial Módulo 11 (SENIAT) para Validación de RIF en `[1 SHIELD]`
- Mapeo de letra inicial: `{"V": 1, "E": 2, "J": 3, "P": 4, "G": 5, "C": 3}`.
- Vector de 9 pesos posicionales (prefijo + 8 dígitos base): $W = [4, 3, 2, 7, 6, 5, 4, 3, 2]$.
- Cálculo:
  $$S = \sum_{k=0}^{8} d_k \cdot W_k, \qquad R = 11 - (S \bmod 11)$$
  Si $R \ge 10$, dígito verificador esperado = `0`; si no, `R`.
- Todo patrón con forma de RIF (`[VEJGPC]-?\d{8}-?\d`) se enmascara preventivamente como `[RIF_n]`, y `rif_mod11_verified` registra si pasa la validación matemática SENIAT.

### 2. Defensa Multicapa y Normalización en `[2 GUARD-IN]` y `[3 GUARD-OUT]`
- Antes de evaluar heurísticas:
  1. `text.normalize("NFKC")` para colapsar homógrafos.
  2. Eliminación de caracteres invisibles (`\u200b`, `\u200c`, `\u200d`, `\ufeff`).
  3. Detección y decodificación de payloads `Base64` / `Hex` embebidos.
- **Canary Dinámico por Transacción** vía Web Crypto API (`crypto.subtle`):
  `[[CANARY-HMAC-${HMAC_SHA256(secret, request_id).slice(0, 8).toUpperCase()}]]`
- **Métricas Auditables Honestas:** `runSecurityBenchmark()` lee `data/attack_benchmark.json` ($N=100$: 50 consultas benignas + 50 ataques) y calcula $\text{TPR}$, $\text{FPR}$ y $\text{F1}$ reales.

### 3. Doble Sello Criptográfico en `[4 LEDGER]` (Cloudflare D1)
1. **Encadenamiento Canónico SHA-256:**
   $$H_i = \text{SHA256}\big(\text{`${i}|${timestamp_utc}|${blind_citizen_id}|${payload_hash}|${prev_hash}`}\big)$$
2. **Sello de Autenticidad HMAC-SHA256 (`env.LEDGER_HMAC_KEY`):**
   $$\text{Sig}_i = \text{HMAC-SHA256}\big(\text{LEDGER\_HMAC\_KEY}, \; H_i \parallel \text{human\_decision}_i\big)$$
3. `verifyChain()` verifica en tiempo constante: $H_i === \text{recalcHash}(i)$, `row.prev_hash === prev.block_hash` y firma HMAC válida, retornando `HASH_MISMATCH`, `PREV_HASH_LINK_BROKEN` o `HMAC_SIGNATURE_FORGED`.

### 4. Matemática Exacta en `[5 EXPLICA]` (Regresión Logística + Linear SHAP)
- Pesos $\beta_0, \beta_1, \dots, \beta_5$ y medias poblacionales $\mu_1, \dots, \mu_5$ calibrados de forma determinista sobre `data/synthetic_tramites.csv` e embebidos como constantes auditables (cero entrenamiento aleatorio en tiempo de request, ejecución $< 0.1\text{ ms}$ en el Worker).
- Inferencia:
  $$z = \beta_0 + \sum_{j=1}^{5} \beta_j x_j, \qquad P(y=1 \mid \mathbf{x}) = \frac{1}{1 + e^{-z}}$$
- Contribuciones directas $c_j = \beta_j x_j$ y valores SHAP lineales $\phi_j = \beta_j(x_j - \mu_j)$, cumpliendo $\left|(\beta_0 + \sum c_j) - z\right| < 10^{-9}$.

---

## ⚡ PARTE 4: GATILLOS SDD PARA CONSTRUCCIÓN DEL MVP EN CLOUDFLARE

1. **Gatillo 0 (Infraestructura y Contratos):** `wrangler.jsonc`, `schema.sql` (D1 `ledger_blocks`), `core/config.ts`, `core/context.ts`, `core/ephemeral_vault.ts`, `specs/00_kernel_storage.spec.md`, `tests/test_ca05_restrictive_db.test.js`.
2. **Gatillo 1 (`SHIELD`):** `pipeline/stage1_shield.ts`, `specs/01_shield.spec.md`, `tests/test_ca01_shield.test.js`.
3. **Gatillo 2 (`GUARD-IN` / `GUARD-OUT` + Benchmark):** `pipeline/stage2_guard_in.ts`, `pipeline/stage3_guard_out.ts`, `data/attack_benchmark.json`, `specs/02_guardian.spec.md`, `tests/test_ca02_guardian.test.js`.
4. **Gatillo 3 (`LEDGER` D1):** `pipeline/stage4_ledger.ts`, `specs/03_ledger.spec.md`, `tests/test_ca03_ledger.test.js`.
5. **Gatillo 4 (`EXPLICA`):** `data/synthetic_tramites.csv`, `pipeline/stage5_explica.ts`, `specs/04_explica.spec.md`, `tests/test_ca04_explica.test.js`.
6. **Gatillo 5 (`Workers AI` + Circuit Breaker):** `pipeline/llm_adapter.ts`, `specs/05_interconnect.spec.md`, `tests/test_ca06_resilience.test.js`.
7. **Gatillo 6 (Endpoints Pages Functions + UI Dual):** `functions/api/v1/*.ts` + `static/index.html`, `static/styles.css`, `static/app.js` (cero CDNs externos, identificación explícita de salidas generadas por IA).
