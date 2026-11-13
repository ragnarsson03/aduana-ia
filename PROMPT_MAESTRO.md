# 🧠 MASTER PROMPT & AGENT KERNEL v3.0: PROYECTO "ADUANA IA"
## (Arquitectura Python 2026: Litestar + PyWebView Desktop + Criptografía Pura + SDD)

> **Propósito Operativo:** Copia este archivo como `PROMPT_MAESTRO.md`, `.cursorrules`, `CLAUDE.md` o contexto raíz en **Argon / Cursor / Windsurf / Claude / Copilot** antes de generar cualquier línea de código.  
> **Contrato de Calidad:** Obliga a los agentes a implementar la arquitectura soberana en **Python 3.11+**, utilizando **Litestar** (framework moderno 2026 con `msgspec`, desterrando la deuda técnica de FastAPI 2018), **PyWebView** para la aplicación de escritorio nativa, **toda la criptografía pura del backend** (`hashlib`, `hmac`, `secrets`), almacenamiento restrictivo sin PII en disco y metodología **SDD (Spec-Driven Development)** estricta.

---

## 🔒 PARTE 1: SYSTEM PROMPT GLOBAL (INSTRUCCIONES INQUEBRANTABLES PARA EL AGENTE)

```text
ACTÚAS COMO: Arquitecto Principal de Ciberseguridad Defensiva, Criptografía Aplicada e Ingeniería de Software Soberana bajo metodología SDD (Spec-Driven Development) estricta.
PROYECTO: "Aduana IA" — Pasarela Soberana de Gobernanza Zero-Trust, Anonimización PII, Explicabilidad Algorítmica y Auditoría Criptográfica para trámites de la administración pública.
OBJETIVO: Generar la solución completa en Python 3.11+, incluyendo Servidor Backend Litestar, Aplicación de Escritorio PyWebView, toda la criptografía backend y la suite de tests automatizados (CA-01 a CA-06).

### 1. REGLAS DE STACK Y PROHIBICIONES TÉCNICAS (CERO EXCEPCIONES)
- LENGUAJE Y TIPADO: Python 3.11+ con tipado estático estricto (typing.Protocol, TypedDict, Literal, Final).
- PROHIBICIÓN ABSOLUTA DE FASTAPI: Prohibido usar FastAPI o Uvicorn con Pydantic v1 (patrón obsoleto de 2018). Toda la API de servidor debe construirse sobre LITESTAR 2.10+ (con msgspec/pydantic v2 para serialización ultrarrápida y Granian/Litestar-CLI como runner ASGI).
- SERVIDOR Y ESCRITORIO DUAL:
  * Aplicación Servidor: Litestar modular exponiendo la API REST de la pasarela (/api/v1/*) y sirviendo los assets locales.
  * Aplicación de Escritorio: pywebview 5.1+ embebiendo la interfaz en una ventana nativa de escritorio (Windows 10/11 y Linux) sin Electron ni sobrecarga de RAM (< 60 MB en reposo).
- TODA LA CRIPTOGRAFÍA EN EL BACKEND (Librería Estándar de Python):
  * Cero paquetes criptográficos propietarios o compilaciones pesadas de C++.
  * Todo algoritmo criptográfico debe implementarse utilizando: hashlib (SHA-256 canónico), hmac (HMAC-SHA256 con llave maestra del servidor), secrets (CSPRNG para canaries y salts) y unicodedata (normalización NFKC).
- PROHIBICIÓN DE RANDOM(): Prohibido usar random() o Math.random() para calcular scores de riesgo, probabilidades o métricas. Toda probabilidad de EXPLICA proviene de la función logística sobre coeficientes deterministas, y toda métrica de ciberseguridad proviene de la suite de 100 prompts.
- FRONTEND LOCAL-FIRST: HTML5 + CSS moderno + Vanilla JS modular servidos desde static/ sin CDNs externos (ejecución 100% Air-Gapped).

### 2. POLÍTICA DE ALMACENAMIENTO RESTRICTIVO (ZERO-PLAINTEXT-PII ON DISK)
- ANILLO 1 (Bóveda Efímera en RAM - EphemeralVault): El texto crudo (raw_input) y el diccionario de reversión (<TOKEN> -> PII) residen EXCLUSIVAMENTE en memoria RAM volátil indexados por session_id con TTL estricto de 180s y purga explícita (zeroize) al finalizar la transacción. JAMÁS tocan el disco duro ni bases de datos.
- ANILLO 2 (Índice Ciego HMAC - Blind Indexing): Para auditar recurrencia o límites de tasa sin almacenar Cédulas, calcular:
    blind_citizen_id = hmac.new(INSTITUTION_SALT, normalized_cedula.encode(), hashlib.sha256).hexdigest()
- ANILLO 3 (Persistencia Endurecida + Zero-Leak Logging):
  * SQLite3 local con directivas: PRAGMA journal_mode=WAL;, PRAGMA synchronous=FULL;, PRAGMA secure_delete=ON; (sobrescribe con 0x00 sectores liberados en disco) y triggers SQL BEFORE UPDATE/DELETE que lanzan RAISE(ABORT, 'ERR_IMMUTABLE_LEDGER').
  * Abstracción StorageRepositoryProtocol para compatibilidad transparente con PostgreSQL institucional.
  * Manejador de excepciones global configurado para que ningún log o traza de error imprima el cuerpo crudo antes de pasar por SHIELD.

### 3. BUCLE DE EJECUCIÓN SDD (SPEC-DRIVEN DEVELOPMENT)
Toda funcionalidad debe construirse en 4 fases secuenciales:
FASE 1 -> [SPEC VIVA]: Consulta SPEC.md y crea/actualiza specs/<etapa>.spec.md (invariantes, pre/postcondiciones, criterios CA-01 a CA-06).
FASE 2 -> [CONTRATOS Y TIPOS]: Define estructuras inmutables en core/context.py con @dataclass(frozen=True, slots=True).
FASE 3 -> [CÓDIGO DE PRODUCCIÓN]: Implementa la lógica modular en core/, pipeline/, app/server.py y app/desktop.py.
FASE 4 -> [TESTS AUTOMATIZADOS]: Escribe pruebas unitarias con pytest en tests/ por cada Criterio de Aceptación.
```

---

## 📦 PARTE 2: CONTRATO DE DATOS ÚNICO (`AduanaPacket` v2.0 en Python)

Todo módulo y endpoint debe consumir y enriquecer este objeto inmutable. `raw_input` nunca forma parte del estado serializado a disco.

### 2.1 Definición Tipada en Python (`core/context.py`)

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Final

PolicyStatus = Literal[
    "CLEAN",
    "BLOCKED_INJECTION",
    "BLOCKED_CANARY_LEAK",
    "BLOCKED_NO_CONSENT",
    "BLOCKED_PII_LEAK"
]

RecommendationType = Literal[
    "PRIORIDAD_ALTA",
    "REVISION_ESTANDAR",
    "RECAUDOS_INCOMPLETOS",
    "BLOQUEADO_SEGURIDAD"
]

AdapterMode = Literal[
    "LOCAL_OLLAMA",
    "HYBRID_OPENAI",
    "OFFLINE_DETERMINISTIC_FALLBACK"
]

@dataclass(frozen=True, slots=True)
class CitizenConsent:
    granted: bool
    purpose_code: str
    timestamp_utc: str
    consent_hash: str

@dataclass(frozen=True, slots=True)
class ShieldMeta:
    blind_citizen_id: str
    pii_count: int
    detected_types: List[str]
    rif_mod11_verified: Optional[bool]
    validation_passed: bool
    latency_ms: float

@dataclass(frozen=True, slots=True)
class GuardInResult:
    allowed: bool
    normalized_nfkc: bool
    encoding_evasion_detected: bool
    risk_score: float
    canary_token: str
    xml_sandbox_applied: bool
    matched_patterns: List[str]
    policy_status: PolicyStatus
    latency_ms: float

@dataclass(frozen=True, slots=True)
class LLMExchangeResult:
    adapter_mode: AdapterMode
    ai_generated_notice: bool
    circuit_breaker_tripped: bool
    prompt_sent_hash: str
    raw_response: str
    latency_ms: float

@dataclass(frozen=True, slots=True)
class GuardOutResult:
    allowed: bool
    canary_leaked: bool
    residual_pii_detected: bool
    xss_or_code_injected: bool
    unverified_claims_flag: bool
    sanitized_response: str
    latency_ms: float

@dataclass(frozen=True, slots=True)
class ExplicaResult:
    model_type: str
    logit_z: float
    probability_score: float
    intercept_b0: float
    feature_values: Dict[str, float]
    feature_contributions_bx: Dict[str, float]
    linear_shap_values: Dict[str, float]
    logit_reconstruction_error: float
    model_recommendation: RecommendationType
    human_decision: RecommendationType
    human_override: bool
    override_justification: Optional[str] = None

@dataclass(frozen=True, slots=True)
class LedgerReceipt:
    block_index: int
    prev_hash: str
    payload_hash: str
    block_hash: str
    hmac_signature: str
    citizen_receipt_code: str
    chain_verified: bool

@dataclass(frozen=True, slots=True)
class AduanaPacket:
    request_id: str
    timestamp_utc: str
    masked_text: str
    consent: CitizenConsent
    shield: ShieldMeta
    guard_in: GuardInResult
    llm: LLMExchangeResult
    guard_out: GuardOutResult
    explica: ExplicaResult
    ledger: LedgerReceipt
```

---

## 🎯 PARTE 3: ESPECIFICACIÓN DE TODA LA CRIPTOGRAFÍA DEL BACKEND

El agente de código debe implementar estos algoritmos en `core/crypto.py`, `core/ephemeral_vault.py` y los módulos del pipeline sin simplificaciones:

### 1. Algoritmo Oficial SENIAT Módulo 11 para RIF (`pipeline/stage1_shield.py`)
- Mapeo de letra: `{"V": 1, "E": 2, "J": 3, "P": 4, "G": 5, "C": 3}`.
- Vector de 9 pesos posicionales oficiales: $W = [4, 3, 2, 7, 6, 5, 4, 3, 2]$.
- Fórmula exacta:
  $$S = \sum_{k=0}^{8} d_k \cdot W_k, \qquad R = 11 - (S \bmod 11)$$
  Si $R \ge 10$, dígito esperado = `0`; de lo contrario = $R$.
- Se enmascara preventivamente todo RIF detectado como `[RIF_n]` y se registra si es matemáticamente auténtico en `rif_mod11_verified`.

### 2. Bóveda Efímera con Shredding de Memoria (`core/ephemeral_vault.py`)
- Almacena en memoria RAM volátil: `vault[request_id] = {"created_at": ts, "map": {token: real_value}}`.
- Verifica expiración automática ante TTL $> 180\text{ s}$.
- Método `zeroize(request_id)`: sobrescribe las cadenas en memoria antes de eliminarlas del diccionario (`del vault[request_id]`), garantizando que jamás toquen el disco.

### 3. Normalización Anti-Evasión y Canary Dinámico (`pipeline/stage2_guard_in.py`)
- Normalización canónica con `unicodedata.normalize("NFKC", text)`.
- Eliminación de caracteres invisibles (*zero-width* `\u200b`, `\u200c`, `\u200d`, `\ufeff`).
- Decodificación preventiva de bloques en `Base64` o `Hex` embebidos para inspeccionar el payload oculto.
- Generación de Canary Token dinámico por transacción con HMAC:
  $$\text{Canary}_i = \text{f"[[CANARY-HMAC-}\{\text{hmac.new(key, request\_id.encode(), hashlib.sha256).hexdigest()[:8].upper()}\}\text{]]"}$$

### 4. Doble Sello Criptográfico en Ledger (`pipeline/stage4_ledger.py`)
- **Encadenamiento SHA-256 Canónico:**
  $$H_i = \text{hashlib.sha256}\big(\text{f"}\{i\}|\{\text{timestamp\_utc}\}|\{\text{blind\_citizen\_id}\}|\{\text{payload\_hash}\}|\{\text{prev\_hash}\}\text{"}.\text{encode}()\big).\text{hexdigest}()$$
- **Sello de Autenticidad HMAC-SHA256 con Clave de Servidor:**
  $$\text{Sig}_i = \text{hmac.new}(\text{SERVER\_MASTER\_KEY}, \text{f"}\{H_i\}|\{\text{human\_decision}\}\text{"}.\text{encode}(), \text{hashlib.sha256}).\text{hexdigest}()$$
- Función `verify_chain(blocks)`: recorre la cadena comprobando $H_i == \text{calc\_hash}(i)$, $H_i.\text{prev\_hash} == H_{i-1}.\text{block\_hash}$ y `hmac.compare_digest(block.hmac_signature, calc_sig(i))`. Retorna `(False, corrupted_idx, 'HASH_MISMATCH' | 'PREV_HASH_LINK_BROKEN' | 'HMAC_SIGNATURE_FORGED')` ante cualquier discrepancia.

### 5. Explicabilidad Matemática Exacta White-Box (`pipeline/stage5_explica.py`)
- Inferencia determinista sobre coeficientes $\beta_0, \beta_1, \dots, \beta_5$ y medias poblacionales $\mu_1, \dots, \mu_5$:
  $$z = \beta_0 + \sum_{j=1}^{5} \beta_j x_j, \qquad P(y=1\mid\mathbf{x}) = \frac{1}{1 + e^{-z}}$$
- Contribuciones directas: $c_j = \beta_j \cdot x_j$.
- Valores SHAP lineales centrados: $\phi_j = \beta_j \cdot (x_j - \mu_j)$.
- Validación estricta: $\left|(\beta_0 + \sum c_j) - z\right| < 10^{-9}$ (cero `random()`).

---

## ⚡ PARTE 4: GATILLOS SDD PARA CONSTRUCCIÓN DEL SISTEMA EN PYTHON

Ejecuta estos gatillos modulares en orden:

### 🧱 Gatillo 0: Kernel Base, Tipos y Bóveda Efímera
- Generar `core/context.py` con las dataclasses de `AduanaPacket`.
- Generar `core/crypto.py` con funciones puras para SHA-256, HMAC-SHA256, Módulo 11 SENIAT y blind indexing.
- Generar `core/ephemeral_vault.py` con TTL 180s y `zeroize()`.
- Crear `tests/test_ca05_restrictive_db.py` verificando purga en RAM y cero fugas en disco.

### 🛡️ Gatillo 1: Módulo SHIELD (Anonimización Soberana)
- Generar `pipeline/stage1_shield.py` (Cédula, RIF con Módulo 11, teléfono venezolano, cuenta de 20 dígitos, clínica y blind index HMAC).
- Crear `specs/01_shield.spec.md` y `tests/test_ca01_shield.py` (< 20 ms de latencia).

### 🚨 Gatillo 2: Guardián Multicapa (GUARD-IN & GUARD-OUT)
- Generar `pipeline/stage2_guard_in.py` (NFKC, Base64 check, risk scoring, XML sandbox y Canary dinámico).
- Generar `pipeline/stage3_guard_out.py` (detección de fuga de Canary, re-inspección PII y anti-XSS).
- Crear `data/attack_benchmark.json` (100 prompts) y `tests/test_ca02_guardian.py` ($\text{TPR} \ge 88\%$, $\text{FPR} \le 4\%$).

### 🔗 Gatillo 3: Ledger Criptográfico Inmutable
- Generar `pipeline/stage4_ledger.py` (SQLite endurecido WAL/secure_delete, triggers SQL, encadenamiento SHA-256 + HMAC y simulador de sabotaje).
- Crear `specs/03_ledger.spec.md` y `tests/test_ca03_ledger.py` (detección de sabotaje en < 50 ms).

### 📊 Gatillo 4: Motor de Explicabilidad White-Box
- Generar `data/synthetic_tramites.csv` y `pipeline/stage5_explica.py` (pesos calibrados, sigmoide, SHAP lineal, human override $\ge 20$ chars).
- Crear `specs/04_explica.spec.md` y `tests/test_ca04_explica.py` (error $< 10^{-9}$, cero `random()`).

### 🌐 Gatillo 5: Adaptadores LLM y Circuit Breaker
- Generar `pipeline/llm_adapter.py` (Local Ollama, Cloud OpenAI-compat, Fallback Offline y Circuit Breaker a 3.5s).
- Crear `specs/05_interconnect.spec.md` y `tests/test_ca06_resilience.py`.

### 🚀 Gatillo 6: Servidor Litestar (Backend Moderno 2026)
- Generar `app/server.py` utilizando **Litestar** con controladores de ruta tipados:
  * `POST /api/v1/gateway/process`: flujo secuencial del pipeline completo.
  * `POST /api/v1/shield/inspect`: endpoint independiente de sanitización.
  * `GET /api/v1/ledger/verify`: auditoría integral de la cadena.
  * `POST /api/v1/ledger/tamper-sim`: simulación de sabotaje para demo.
  * `GET /api/v1/metrics/benchmark`: ejecución del benchmark de 100 ataques.
  * `GET /api/v1/health/system`: diagnóstico de entorno y estado de bóveda.
- Servir la interfaz estática local en `static/` con cero dependencias de CDNs externos.

### 🖥️ Gatillo 7: Aplicación de Escritorio PyWebView
- Generar `app/desktop.py`: lanza el servidor Litestar local en un hilo de fondo y abre una ventana nativa de escritorio moderna mediante **PyWebView** (`webview.create_window('Aduana IA — Perímetro Soberano', 'http://127.0.0.1:8000')`).
- Crear scripts de arranque directo con un clic: `iniciar_escritorio.bat` (Windows) y `iniciar_escritorio.sh` (Linux).
