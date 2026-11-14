# 05 — Interconexión LLM, Circuit Breaker y orquestación

**Estado:** Gatillo 5 (`pipeline/llm_adapter.py`, CA-06) implementado y verificado en `tests/test_ca06_resilience.py`. `GatewayPipeline.process` (Gatillo 6) y lanzador de escritorio (Gatillo 7) siguen pendientes.

## Alcance y trazabilidad

`pipeline/llm_adapter.py`, `LLMAdapterProtocol` y `pipeline/orchestrator.py`: SPEC §8, CA-06 y todos los CA como integración; ingeniería RF-11/12 y RNF-03/04. Las rutas REST y el lanzador de escritorio son consumidores; no se modifican en esta entrega.

## Invariantes

- Adaptadores solo reciben prompt derivado de texto SHIELD, inspeccionado y encapsulado por GUARD-IN. Nunca reciben texto crudo, cédula explícita, mapa de reversión ni claves.
- Tres modos exactos: `LOCAL_OLLAMA`, `HYBRID_OPENAI` y `OFFLINE_DETERMINISTIC_FALLBACK`. La abstracción no impone proveedor de nube particular.
- Timeout primario **3.5 s**; error de red o timeout activa fallback institucional determinista. El fallback no descarga pesos ni necesita red para arrancar.
- La respuesta de cualquier adaptador, incluido fallback, pasa por GUARD-OUT. `raw_response` no se registra ni persiste antes de inspección.
- `ai_generated_notice=True` en el intercambio; el resumen no decide prioridad. EXPLICA y decisión humana preceden al sellado final.
- Orden documentado: consentimiento, SHIELD, GUARD-IN, LLM con Circuit Breaker, GUARD-OUT, EXPLICA, LEDGER. `vault.zeroize` siempre en `finally`, también ante bloqueo o error.
- Modo servidor Litestar y escritorio PyWebView comparten protecciones y almacenamiento restrictivo. Frontend local, sin CDNs ni dependencia obligatoria de internet.

## Firmas existentes (sin modificación)

~~~python
# core/protocols.py
class LLMAdapterProtocol(Protocol):
    mode: AdapterMode
    async def complete(self, prompt: str, *, timeout_s: float) -> str: ...

# pipeline/llm_adapter.py
class OllamaAdapter:
    mode: AdapterMode = "LOCAL_OLLAMA"
    async def complete(self, prompt: str, *, timeout_s: float) -> str: ...

class OpenAICompatAdapter:
    mode: AdapterMode = "HYBRID_OPENAI"
    async def complete(self, prompt: str, *, timeout_s: float) -> str: ...

class OfflineDeterministicAdapter:
    mode: AdapterMode = "OFFLINE_DETERMINISTIC_FALLBACK"
    async def complete(self, prompt: str, *, timeout_s: float) -> str: ...

class CircuitBreaker:
    def __init__(
        self,
        primary: LLMAdapterProtocol,
        fallback: LLMAdapterProtocol,
        timeout_s: float = LLM_TIMEOUT_SECONDS,
    ) -> None: ...
    async def exchange(self, prompt: str) -> LLMExchangeResult: ...

# pipeline/orchestrator.py
class GatewayInput:
    raw_text: str
    citizen_cedula: str
    consent_granted: bool
    purpose_code: str
    features: dict[str, float]
    human_decision: RecommendationType | None = None
    override_justification: str | None = None
    def __repr__(self) -> str: ...

class GatewayPipeline:
    def __init__(
        self,
        settings: Settings,
        vault: EphemeralVault,
        repo: StorageRepositoryProtocol,
        llm: CircuitBreaker,
        rate_guard: RateGuard,
    ) -> None: ...
    async def process(self, data: GatewayInput) -> AduanaPacket: ...
~~~

Constructores actuales solo almacenan dependencias; `GatewayInput` es dataclass `frozen=True, slots=True` y su `repr` implementado devuelve exactamente `GatewayInput(<redacted>)`. Ese tipo de entrada contiene PII transitoria y no se serializa a disco.

`LLMExchangeResult` incluye `adapter_mode`, `ai_generated_notice`, `circuit_breaker_tripped`, `prompt_sent_hash`, `raw_response` y `latency_ms`. `LLMUnavailableError` es el error del protocolo para timeout o fallo de red.

## Precondiciones y postcondiciones

| Operación | Precondiciones | Postcondiciones |
|---|---|---|
| `complete` | Prompt autorizado, `timeout_s` proporcionado; proveedor configurado si requiere red | Devuelve texto o `LLMUnavailableError`; sin incluir PII ni credenciales en logs/errores |
| `exchange` con primario disponible | Adaptadores cumplen protocolo; prompt seguro | Resultado en modo primario, `circuit_breaker_tripped=False`, aviso de IA y hash del prompt enviado |
| `exchange` tras fallo/timeout | Primario falla o agota presupuesto | Conmutación a fallback, `adapter_mode='OFFLINE_DETERMINISTIC_FALLBACK'` y `circuit_breaker_tripped=True`; respuesta determinista y aviso preservado |
| Fallback directo | Sin red, misma entrada institucional segura | Misma salida de plantilla para misma entrada; sin `random()` ni llamadas externas |
| `process` | Datos en RAM y dependencias inyectadas | Compone resultados por el orden indicado; solo texto permitido llega al LLM; decide humano y sella ledger; purga bóveda en éxito y error |
| Bloqueo de seguridad | GUARD-IN o GUARD-OUT no permite continuar | No entregar contenido inseguro; GUARD-IN bloqueado no llama al LLM. Retorno de paquete/errores y política de registro de bloqueos están pendientes |

La referencia a hash del prompt sugiere SHA-256 según el núcleo criptográfico; su codificación/canon y relación con prompt externo tras envolturas propias del proveedor no están publicados. No inventar serialización HTTP, URL, credenciales o nombres de parámetros de proveedores.

## Criterios de aceptación y umbrales exactos

- **CA-06:** ante caída o timeout externo, conmutar al generador institucional determinista en **< 100 ms**, con trámite sellado en **Servidor Litestar y App de Escritorio PyWebView**.
- **Timeout 3.5 s:** PROMPT Parte 4 Gatillo 5, docs RF-12 y `LLM_TIMEOUT_SECONDS=3.5`. No confundirlo con el tiempo de conmutación: medir por separado espera hasta fallo y transición al fallback. Interpretación operativa respaldada por docstring del breaker; SPEC no define los instantes exactos de medición de los 100 ms.
- **CA-05 transversal:** tras **20 trámites**, **0 bytes** de Cédulas/RIF/teléfonos en `.db`/logs; RNF-02 añade nombres y archivos WAL/SHM.
- **CA-01..04 integrados:** **100%** de identificadores estructurados enmascarados en **< 20 ms**; benchmark **100** prompts, **TPR ≥ 88%**, **FPR ≤ 4%**, **< 25 ms/prompt**, **100%** de fugas Canary neutralizadas; sabotaje detectado en **< 50 ms** con índice/motivo; reconstrucción logit **< 10^-9** sin `random()`.
- SPEC §3 y PROMPT fijan escritorio **< 60 MB RAM** (PROMPT precisa en reposo). Ingeniería RNF-01 exige procesamiento de seguridad/auditoría acumulado **< 40 ms**. Son requisitos adicionales, no nuevos presupuestos de red ni sustitutos de CA-06.

## Casos de prueba concretos a escribir en tests/

Archivo principal: `tests/test_ca06_resilience.py`; integración: `tests/test_gateway_pipeline.py`. Adaptadores fake implementan protocolo y registran llamadas en memoria. Prompts y datos fabricados; no usar servicios externos ni credenciales reales.

| Caso | Fixture / acción | Comprobación |
|---|---|---|
| `test_primary_success` | Fake primario devuelve `Resumen orientativo [CEDULA_1]` | Sin llamada fallback; modo primario correcto, breaker falso, aviso verdadero y hash reproducible del prompt |
| `test_immediate_failure` | Primario lanza `LLMUnavailableError`, fallback devuelve plantilla segura | Fallback invocado, breaker verdadero, modo offline; transición medida **<100 ms** |
| `test_timeout` | Primario suspendido hasta cancelación, breaker con predeterminado **3.5 s** | Agotamiento del presupuesto primario y transición posterior **<100 ms** por separado; no exigir respuesta total <100 ms tras iniciar la llamada |
| `test_timeout_propagation` | Fake captura `timeout_s` recibido | Recibe **3.5** por defecto; prueba adicional con valor explícito verifica DI sin redefinir el valor normativo |
| `test_offline_repeatability` | Dos llamadas offline con idéntico prompt tokenizado; sockets deshabilitados | Misma salida, cero red/descarga de pesos y aviso de contenido asistido |
| `test_guard_after_fallback` | Fake fallback devuelve Canary completo o `V-00000001` o `<script>alert(1)</script>` | GUARD-OUT inspecciona y evita entrega insegura también al degradar |
| `test_pipeline_order_and_zeroize` | Entrada sintética `V-00000001`, `0412-0000001`, propósito `BECA` y features del modelo ya definido; espías de etapas | Orden de llamadas; LLM solo ve tokens/sandbox; decisión explícita; recibo verificable; bóveda purgada |
| `test_no_consent_no_llm` | `consent_granted=False` | `ConsentError`/`BLOCKED_NO_CONSENT`, cero llamadas LLM y cero fugas en logs |
| `test_failures_zeroize` | Fallos parametrizados de SHIELD, guardián, ambos adaptadores, EXPLICA y repo | Purga en `finally`, error sin datos; sin recibo exitoso ante fallo de persistencia |
| `test_server_and_desktop_offline` | Mismo trámite sintético confirmado con red desconectada en servidor y lanzador PyWebView | En ambos: fallback, EXPLICA y sellado verificable; medir transición **<100 ms**. Requiere prueba de escritorio real además de cliente HTTP |
| `tests/test_ca05_restrictive_db.py` | 20 trámites sintéticos combinando éxito externo simulado y fallback | Cero PII original en DB/logs, sin mapa ni respuesta insegura persistidos |

Relojes y fakes deben permitir observar instante del fallo y comienzo/fin de transición. Hasta definir el alcance de `latency_ms`, registrar también tiempo externo total y de fallback; no presentar solo ese campo como prueba. La prueba PyWebView requiere entorno de GUI: si no se ejecuta, registrar aceptación desktop pendiente, no inferirla de mocks.

## Decisiones tomadas (Gatillo 5)

1. **Medición de CA-06 (`< 100 ms` vs `3.5 s`):** El timeout primario (`timeout_s = 3.5` por defecto) y el tiempo de transición + generación offline (`< 100 ms` tras el fallo) se miden por separado; cuando el circuito está `OPEN` o el fallo es inmediato, la respuesta completa del intercambio toma `< 100 ms`.
2. **Máquina de estados de `CircuitBreaker`:** `CLOSED` -> `OPEN` tras `failure_threshold = 3` fallos consecutivos; permanece `OPEN` durante `cooldown_s = 30.0` (medido con `clock` inyectable, `time.monotonic` por defecto) respondiendo directo vía `fallback`; luego pasa a `HALF_OPEN` para una petición de prueba (éxito cierra a `CLOSED`, fallo reabre a `OPEN`).
3. **Endurecimiento de adaptadores HTTP:** `OllamaAdapter` (loopback por defecto) y `OpenAICompatAdapter` (opt-in estricto `enabled=False` por defecto, TLS obligatorio en hosts no loopback, `repr` redactado) validan host contra `allowed_hosts`, deshabilitan redirects (`follow_redirects=False`) y acotan respuestas a `32 KiB`.

## Inconsistencias y decisiones pendientes (Gatillos 6/7)

1. **3.5 s** de espera y **<100 ms** de conmutación son presupuestos diferentes; interpretar CA-06 como tiempo total desde solicitud entraría en conflicto con timeout configurado. Falta definición formal del intervalo de transición (incluye o no generación fallback).
2. No están definidos endpoints/credenciales de proveedores, plantillas offline, reintentos, contador de fallos, estados abierto/semicerrado, enfriamiento ni recuperación. El nombre `CircuitBreaker` no autoriza inventar esos umbrales.
3. `AduanaPacket` exige todos los resultados y recibo aun si hay rechazo temprano. `process` solo retorna ese tipo y no publica contrato de bloqueos parciales; tampoco resuelve paquete previo a ledger ni confirmación humana opcional.
4. El `repr` predeterminado de `LLMExchangeResult` incluye `raw_response`: podría revelar PII al registrar el objeto antes de GUARD-OUT. `GatewayInput` sí tiene `repr` redactado, pero su `dict` de features no es inmutable en profundidad.
5. SPEC §6 permite Granian o Uvicorn. PROMPT exige Granian/Litestar-CLI y prohíbe específicamente FastAPI o Uvicorn con Pydantic v1. No es una prohibición inequívoca de todo Uvicorn; registrar la divergencia de runners sin inventarla.
6. La Guía Ministerial §§3–6 propone AES-256, WebCrypto cliente, archivos `.aduana`, PIN/roles y doble hosting; excede el MVP/stubs y contradice la regla de toda criptografía en backend si se adopta WebCrypto. No convertir `05_interconnect` en especificación de esas funciones sin contrato.
7. Guía Ministerial §1.1 menciona **<80 MB RAM** frente a **<60 MB** de SPEC/PROMPT. Ingeniería §4.1 habla de SHIELD **<10 ms** y de **100 ataques/casos reales** en el pitch frente a CA-01 **<20 ms** y benchmark sintético **50 ataques + 50 benignos**. Las pruebas conservan los CA formales y la distribución explícita, sin usar PII real.
8. No existen `data/attack_benchmark.json` ni `data/synthetic_tramites.csv`; las pruebas actuales de aceptación se omiten con `pytest.skip`. La existencia del esqueleto no demuestra CA-01..06.

## Fuentes

- [SPEC.md](../SPEC.md), §§3–6 y §8: modos, resiliencia, stack, CA y función asistiva del LLM.
- [PROMPT_MAESTRO.md](../PROMPT_MAESTRO.md), Parte 1, Parte 2 y Parte 4 Gatillos 5–7: timeout, servidor, escritorio y contratos.
- [Ingeniería y Negocio](<../docs/Ingenieria Y Negocio Aduana IA.md>), §1.3 RF-11/12/14, §1.4 RNF-01/03/04, §3.1 y §3.2 Bloques 4–6; §4.1 para diferencias de pitch.
- [Guía Ministerial](<../docs/Guia Implementacion Ministerial Y Defensa.md>), §§1.1, 2.2 y 3–6: contexto operativo y ampliaciones no soportadas por los stubs.
- [Arquitectura existente](00_architecture.spec.md); firmas contrastadas con `pipeline/llm_adapter.py`, `pipeline/orchestrator.py` y `core/protocols.py`.
