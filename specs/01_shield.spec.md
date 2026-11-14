# 01 — Consentimiento, Rate-Guard y SHIELD

**Estado:** IMPLEMENTADO (Gatillo 1). Revisado por Code Reviewer y dos rondas de red team; los hallazgos viven como tests en `tests/test_shield_regression.py`.

## Alcance y trazabilidad

`pipeline/stage0_consent.py`, `pipeline/stage1_shield.py`, `core/pii_patterns.py`, `core/text_normalizer.py`. RF0/RF1 de SPEC; RF-01 a RF-07 de ingeniería; CA-01 y CA-05. Criptografía y bóveda: [00_kernel.spec.md](00_kernel.spec.md).

## Invariantes

- Ninguna solicitud sin consentimiento explícito (`granted is True`) y propósito no vacío continúa. La tasa se controla en RAM por índice ciego, nunca por cédula.
- Se tokenizan **antes de cualquier llamada a IA**: cédulas V/E, RIF V/E/J/P/G/C, teléfonos 04xx/02xx, cuentas de 20 dígitos (y runs mayores), correos, nombres contextuales, términos clínicos y bloques Base64/hex que decodifican a PII.
- Tokens coherentes dentro del trámite: la misma identidad en formatos distintos (`V-00000001`, `v00000001`, `V-00.000.001`) comparte token. No hay estabilidad entre trámites.
- El mapa token→original y el texto crudo viven solo en `EphemeralVault`. El mapa guarda el texto **normalizado** (NFKC) y una sola forma por identidad.
- **Fail-closed:** si tras `MAX_PASSES` pasadas queda PII detectable se lanza `ShieldResidualPiiError` (HTTP 422 `ERR_UNSAFE_INPUT`) y no se guarda nada en la bóveda. Ningún llamador recibe texto con PII residual.
- Ningún error, `repr`, log o metadato reproduce texto ciudadano.
- Los literales `[KIND_n]` ya presentes en la entrada se neutralizan (`［`) para no colisionar con los tokens generados.

## Firmas

```python
# pipeline/stage0_consent.py
class RateGuard:
    def __init__(self, limit_per_minute: int, *, window_s=60.0, max_keys=10_000, clock=time.monotonic): ...
    def check(self, blind_citizen_id: str) -> None: ...   # RateLimitError (HTTP 429)

def validate_consent(request_id, granted, purpose_code, timestamp_utc, blind_citizen_id) -> CitizenConsent: ...

# pipeline/stage1_shield.py
def shield(request_id: str, raw_text: str, *, vault: EphemeralVault,
           blind_citizen_id: str) -> tuple[str, ShieldMeta]: ...

# core/pii_patterns.py
def find_pii(normalized_text: str, *, regions: list[tuple[int, int]] | None = None) -> tuple[PiiMatch, ...]: ...
# core/text_normalizer.py
def normalize_text(text: str) -> str: ...   # ValueError si la expansión NFKC supera 2x+64
```

El `blind_citizen_id` lo calcula la etapa 0/orquestador con `core.crypto.blind_citizen_id(keys, cedula)` (diverge de PROMPT_MAESTRO, que lo situaba en `stage1`, para que el rate-guard actúe antes de cualquier procesamiento costoso).

## Decisiones tomadas

| Tema | Decisión |
|---|---|
| `pii_count` | Ocurrencias enmascaradas (no valores únicos). |
| `rif_mod11_verified` | `None` sin RIF; `True` si todos validan; `False` si alguno falla. RIF sin letra (contexto "RIF: …") no se valida. |
| `validation_passed` | Ningún RIF falló el Módulo 11. El residual ya no es posible (lanza). |
| RIF inválido | Se enmascara igualmente (preventivo). |
| RIF abreviado (cuerpo de 7) | No se detecta como RIF. |
| V/E + 9 dígitos juntos | Es **cédula**, no RIF (los RIF V/E exigen separador antes del verificador). |
| Cédula sin letra | Solo tras palabra clave ("cédula", "C.I.", "documento de identidad", "identificación", "DNI"…). |
| Cuenta | 20 dígitos con separadores libres; runs mayores se enmascaran completos. |
| Teléfono | Exige `0` inicial o prefijo `+58`/`0058`; un monto de 10 dígitos que empiece por 2 no se enmascara. |
| Nombres | Solo contextuales (marcador + 1–4 palabras capitalizadas o en mayúsculas); con lista de exclusión de cargos ("Presidente", "Comercial"…). |
| Clínico | Diccionario local; se enmascara siempre (falso positivo conocido en texto comercial: "depresión del mercado"). |
| Consentimiento | Vacío o sin `granted is True` ⇒ `ConsentError` (`BLOCKED_NO_CONSENT`). El hash vincula `request_id`, `timestamp`, propósito y ciudadano. |
| Exceso de tasa | `RateLimitError` (429); `PolicyStatus` no tiene estado de tasa. La tabla llena falla cerrado; la poda es O(n) como máximo una vez por segundo. |

## Criterios de aceptación

- **CA-01:** enmascarar el 100 % de identificadores estructurados venezolanos con `latency_ms < 20`. **Alcance medido:** textos de prosa de hasta 10 000 caracteres (mediana ≈ 9 ms, p95 ≈ 15 ms); con 20 000 caracteres y PII el p95 supera 20 ms. **Decisión (usuario): CA-01 se acota a textos de hasta 10 000 caracteres**; la API sigue aceptando hasta `MAX_RAW_TEXT_CHARS` = 20 000, pero entre 10 000 y 20 000 el objetivo de 20 ms no está garantizado.
- **CA-05:** tras 20 trámites, 0 bytes de PII en `.db`, WAL/SHM y logs (parte de bóveda cubierta en `tests/test_ca05_restrictive_storage.py`; parte `.db` en el Gatillo 3).
- `Settings.rate_limit_per_minute = 30` es un valor por defecto, no un CA.

## Vectores de verificación (calculados, Módulo 11)

| RIF | Resultado | Cálculo |
|---|---|---|
| `J-12345678-4` | válido | S=150, R=4 |
| `J-12345678-5` | inválido | esperado 4 |
| `V-00000001-5` | válido | S=6, R=5 |
| `V-00000000-7` | válido | S=4, R=7 |
| `J-00000000-0` | válido | S=12, R=10 → 0 |
| `J-00000000-9` | **inválido** | el verificador correcto es 0 (el vector original de esta spec estaba mal) |

## Tests

`tests/test_pii_patterns.py` (detectores), `tests/test_ca01_shield.py` (CA-01, fail-closed, fixed-point, colisión de tokens, latencia por tamaño), `tests/test_consent.py` (consentimiento y rate-guard, hilos, memoria acotada), `tests/test_shield_regression.py` (red team: ~100 casos de evasión, ReDoS y límites conocidos), `tests/test_api_hardening.py` (endpoint, Zero-Leak).

## Límites conocidos (documentados, no cubiertos)

- Nombres sin marcador o en minúsculas; sin detector general de nombres.
- Base32, ASCII85, ROT13, números escritos con palabras.
- Términos clínicos con variantes ("d i a b e t e s", "seropositivo") y falsos positivos en contexto comercial.
- Correos con dominio IDN; pegados de teléfonos sin separador.
- El texto enmascarado puede contener `［` (corchete fullwidth) y no es idempotente al re-procesarse.
- Reversión con pérdida: una sola forma original por identidad y texto normalizado, no el crudo.

## Fuentes

[SPEC.md](../SPEC.md) §§3–5 y §8; [PROMPT_MAESTRO.md](../PROMPT_MAESTRO.md) Parte 1 §2, Parte 3 §1, Gatillos 0–1; [Ingeniería y Negocio](<../docs/Ingenieria Y Negocio Aduana IA.md>) §1.3 RF-01..RF-07 y §1.4 RNF-02; [00_architecture.spec.md](00_architecture.spec.md).
