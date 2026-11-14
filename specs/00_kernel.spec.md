# 00 — Kernel, contratos y bóveda efímera

**Estado:** Gatillo 0 implementado: criptografía, KeyRing, normalización y bóveda efímera, con pruebas en `tests/`. CA-05 integral sobre SQLite sigue pendiente de Gatillo 3.

## Alcance y trazabilidad

Núcleo compartido por todas las etapas: `core/context.py`, `core/config.py`, `core/crypto.py`, `core/keyring.py`, `core/text_normalizer.py`, `core/ephemeral_vault.py`, `core/errors.py` y `core/protocols.py`. Consentimiento y tasa están en [01_shield.spec.md](01_shield.spec.md); los contratos de almacenamiento y LLM se detallan en [03_ledger.spec.md](03_ledger.spec.md) y [05_interconnect.spec.md](05_interconnect.spec.md).

RF0/RF1/RF2/RF4 de SPEC no son la misma numeración que RF-01 a RF-20 del documento de ingeniería y los docstrings. Se conserva cada nomenclatura con su fuente.

## Invariantes

- Texto crudo y mapa token→valor permanecen exclusivamente en RAM; nunca se serializan a SQLite, archivos temporales, logs o trazas. La entrada existe transitoriamente en el llamador; `EphemeralVault` almacena solo el mapa, nunca `raw_input`.
- TTL predeterminado de **180 s** (expira con edad **> 180 s**, vigente a los **180 s** exactos) y purga explícita al terminar cada transacción, incluso con excepción. La llave maestra permanece en RAM dentro de `KeyRing`, con `repr` redactado y subllaves por dominio.
- Criptografía de backend con StdLib: `hashlib`, `hmac`, `secrets` y normalización mediante `unicodedata`. Ningún score o probabilidad procede de `random()`.
- Resultados del pipeline usan dataclasses `frozen=True, slots=True`. `AduanaPacket` no contiene `raw_input` ni mapa de reversión. Esto no autoriza persistir el paquete completo: `llm.raw_response` también puede contener PII.
- Errores de dominio describen categorías sin incluir contenido ciudadano ni claves. Persistencia, LLM y verificación se desacoplan mediante protocolos.

## Firmas existentes (sin modificación)

En `core/crypto.py`, implementadas:

~~~python
def sha256_hex(data: bytes) -> str: ...
def normalize_cedula(cedula: str) -> str: ...
def blind_citizen_id(keys: KeyRing, cedula: str) -> str: ...
def consent_hash(request_id: str, timestamp_utc: str, purpose_code: str, blind_id: str) -> str: ...
def canary_token(keys: KeyRing, request_id: str) -> str: ...
def rif_mod11_valid(rif: str) -> bool: ...
def canonical_block_payload(
    source: LedgerBlock | LedgerEntry, *, index: int, prev_hash: str, key_id: str
) -> bytes: ...
def block_hash(payload: bytes) -> str: ...
def block_signature(keys: KeyRing, block_hash_hex: str) -> str: ...
~~~

En `core/keyring.py` y `core/text_normalizer.py`, implementadas:

~~~python
class KeyRing:
    def __init__(self, master: bytes) -> None: ...
    def hmac_hex(self, domain: str, data: bytes) -> str: ...
    def verify(self, domain: str, data: bytes, expected_hex: str) -> bool: ...
    @property
    def key_id(self) -> str: ...
    def wipe(self) -> None: ...

def normalize_text(text: str) -> str: ...
~~~

`KeyRing` deriva cada subllave como HMAC-SHA256 de `b"aduana/v1/" + domain.encode()` con la llave maestra. Dominios permitidos: `ledger-sign`, `canary`, `blind-index`, `rate-guard`, `consent`, `key-id` y `justification`. `hmac_hex` usa la subllave del dominio y `verify` compara en tiempo constante. La llave maestra exige al menos **32 bytes** y **4 valores de byte distintos** (guardarraíl, no medida de entropía); vive en un `bytearray`, sin permitir copia ni serialización. `wipe` la sobrescribe e inutiliza el KeyRing. `key_id` son los primeros **16 hex** del HMAC del dominio `key-id` sobre `b''`.

`normalize_text` aplica NFKC y elimina invisibles de formato, rellenos, selectores y controles salvo `\n`, `\r`, `\t`, hasta punto fijo con un máximo de **4 pasadas**; conserva espacios y acentos. `normalize_cedula` además convierte a mayúsculas, quita guiones, puntos y espacios, asume `V` si falta letra y elimina ceros iniciales. Forma canónica: **V|E + 5–9 dígitos ASCII, sin ceros a la izquierda**. Exige 5–9 dígitos antes y después de quitar ceros; formato inválido lanza `ValueError` sin eco del valor.

En `core/ephemeral_vault.py`, implementadas; operaciones protegidas por `threading.RLock`:

~~~python
class EphemeralVault:
    def __init__(
        self,
        ttl_seconds: int = VAULT_TTL_SECONDS,
        max_sessions: int = VAULT_MAX_SESSIONS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None: ...
    @property
    def active_sessions(self) -> int: ...
    def put(self, request_id: str, token_map: Mapping[str, str]) -> None: ...
    def get_map(self, request_id: str) -> Mapping[str, str]: ...
    def purge_expired(self) -> int: ...
    def zeroize(self, request_id: str) -> None: ...
    def zeroize_all(self) -> None: ...
~~~

Configuración existente, ya implementada:

~~~python
class Settings:
    @classmethod
    def from_env(cls, env: MutableMapping[str, str] | None = None) -> Settings: ...

def load_keys_from_env(env: MutableMapping[str, str] | None = None) -> KeyRing: ...
def load_api_token_from_env(env: MutableMapping[str, str] | None = None) -> str: ...
~~~

`Settings` tiene host `127.0.0.1`, puerto `8000`, rutas locales y `rate_limit_per_minute=30`; no contiene secretos. `from_env` lee `ADUANA_HOST`, `ADUANA_PORT`, `ADUANA_DB_PATH`, `ADUANA_STATIC_DIR`, `ADUANA_RATE_LIMIT_PER_MINUTE`, `ADUANA_DEMO_MODE`, `ADUANA_ALLOW_REMOTE` y la presencia de `ADUANA_MASTER_KEY`; no lee rutas de benchmark o de trámites desde entorno. Se llama antes de `load_keys_from_env`, que extrae y elimina `ADUANA_MASTER_KEY` del entorno y carga la llave hex mediante `KeyRing`; sin ella genera **32 bytes** con `secrets.token_bytes` y `ledger_ephemeral=True` limita la verificación a la vida del proceso. Con llave configurada, `ledger_ephemeral=False` permite verificar entre reinicios conservando esa llave. `load_api_token_from_env` extrae y elimina `ADUANA_API_TOKEN`; acepta al menos **32 caracteres** o genera uno con `secrets.token_urlsafe(32)`. La bóveda usa `VAULT_TTL_SECONDS=180`, `VAULT_MAX_SESSIONS=1000` y exige `ttl_seconds > 0`, `max_sessions >= 1`. Estos valores proceden del código, no son umbrales CA.

Contratos de `core/context.py`: `CitizenConsent`, `ShieldMeta`, `GuardInResult`, `LLMExchangeResult`, `GuardOutResult`, `ExplicaResult`, `LedgerEntry`, `LedgerReceipt`, `AduanaPacket`, `BlockedPacket`, `LedgerBlock`, `ChainAnchor` y `ChainVerification`. Las colecciones de detección son `tuple[str, ...]` y los mapas de EXPLICA son `Mapping[str, float]`, copiados y protegidos con `MappingProxyType`. Protocolos existentes: `StorageRepositoryProtocol`, `LLMAdapterProtocol`, `RateGuardProtocol` y `LLMGatewayProtocol`.

## Precondiciones y postcondiciones

| Operación | Precondición | Postcondición exigida por las fuentes |
|---|---|---|
| SHA/HMAC | Datos bytes; HMAC mediante `KeyRing` y dominio permitido | Hexadecimal SHA-256/HMAC-SHA256 de 64 caracteres, determinista para idéntica entrada; sin I/O |
| Índice ciego | Cédula sintácticamente normalizable y `KeyRing` | HMAC-SHA256 del dominio `blind-index` de `normalize_cedula(cedula).encode()`; no guardar la cédula |
| Consentimiento | Identificador, instante UTC, propósito e índice ciego | SHA-256 simple (no HMAC) del JSON canónico de `[request_id, timestamp_utc, purpose_code, blind_id]` |
| Canary | `KeyRing` y `request_id` de la transacción | `[[CANARY-HMAC-` + primeros 16 hex de HMAC-SHA256 del dominio `canary` sobre `request_id.encode()`, en mayúsculas + `]]` |
| RIF | Letra, cuerpo de 8 dígitos ASCII y verificador ASCII tras NFKC, mayúsculas y eliminación de guiones y espacios | Módulo 11 con mapa `V=1,E=2,J=3,P=4,G=5,C=3` y pesos `(4,3,2,7,6,5,4,3,2)`; `R=11-(S%11)`; `0` si `R>=10`, de otro modo `R`; formato inválido devuelve `False`, sin rellenar abreviados |
| Hash/firma de bloque | Campos canónicos y clave en RAM | JSON canónico con claves ordenadas, separadores compactos y `ensure_ascii=True`, codificado a bytes; cubre todos los campos de `LedgerBlock` excepto `block_hash` y `hmac_signature`. Hash = SHA-256 del payload; firma = HMAC-SHA256 del dominio `ledger-sign` sobre `block_hash_hex.encode()` |
| `put` | ID de transacción y mapa en memoria; cupo tras purga | Sesión RAM con reloj monotónico y valores en `bytearray`; reemplaza y sobrescribe sesión previa del mismo ID; sin `raw_input` ni escritura en disco |
| `get_map` | Sesión existente, vigente | Devuelve copia de solo lectura (`MappingProxyType`) solo vigente; sesión expirada se purga, sin exponer contenido en error |
| `purge_expired` | Reloj controlable en pruebas | Elimina sesiones expiradas y devuelve cantidad purgada |
| `zeroize` | ID de sesión a finalizar | Sobrescribe buffers con `0x00` y elimina sesión; idempotente. `zeroize_all` actúa sobre todas; no garantiza borrado de copias externas |

`get_map` lanza `VaultExpiredError` al purgar una sesión expirada; accesos posteriores o IDs inexistentes lanzan `VaultSessionNotFoundError`. `put` lanza `VaultError` por capacidad agotada o valor inválido; un valor inválido conserva la sesión previa vigente. `active_sessions` y `put` purgan expiradas oportunistamente. `RLock` permite llamadas anidadas de purga y sobrescritura entre operaciones protegidas.

## Criterios de aceptación y umbrales exactos

- **CA-05, principal:** después de **20 trámites simulados**, auditoría binaria de `.db` y logs encuentra **0 bytes** de Cédulas, RIF o teléfonos en texto plano (SPEC §5).
- **CA-01, apoyo:** mapa de reversión exclusivamente RAM y `blind_citizen_id` HMAC. El rendimiento SHIELD completo es **< 20 ms**, no un presupuesto independiente para cada función de crypto.
- TTL: SPEC §3 y PROMPT Parte 1 fijan **180 s**; ingeniería RF-07 dice **≤ 180 s** y PROMPT Parte 3.2 dice expiración con edad **> 180 s**. Implementación y prueba de frontera fijan edad **> 180 s**, vigente a los **180 s** exactos; la redacción de RF-07 requiere conciliación documental.
- Ingeniería RNF-02 amplía el barrido a `.db`, `-wal`, `-shm`, `stdout` y `stderr`, e incluye nombres originales. Se conserva como requisito documental adicional, sin reducir CA-05.

## Casos de prueba concretos en tests/

Claves de prueba fijas, nunca claves de entorno. Se usan fixtures sintéticas y vectores RIF públicos identificados en `tests/test_crypto.py`, sin consultar servicios reales. Se distingue cobertura implementada de pruebas integrales pendientes; no se crean pruebas en esta entrega.

| Archivo / caso | Datos y acción | Comprobación |
|---|---|---|
| `tests/test_crypto.py::test_sha256_hex_matches_stdlib` | `b'abc'` | Igualdad exacta con `hashlib.sha256` |
| `tests/test_crypto.py` (cédula, índice y consentimiento) | Cédula `V-12.345.678`, variantes Unicode y ceros iniciales; KeyRing con `bytes(range(32))` y `bytes(range(1, 33))`; cuatro campos de consentimiento | Canon ASCII estable; cambiar llave cambia índice; cambiar cada campo cambia consentimiento; sin ambigüedad por separadores |
| `tests/test_crypto.py::test_canary_token_format_and_uniqueness` | Dos llaves y dos IDs | Prefijo y sufijo exactos, 16 hex mayúsculas, determinismo y variación por llave/ID |
| `tests/test_crypto.py` (RIF y ledger) | Vectores públicos y sintéticos; modificación de cada campo del payload | Módulo 11, rechazo de abreviados, JSON compacto ordenado, cobertura de todos los campos y firma verificable |
| `tests/test_ephemeral_vault.py::test_ttl_boundary_is_strictly_greater_than_180s` | Reloj falso; `put('r1', PII)` | Vigente a 180 s; a 180.001 s lanza `VaultExpiredError` y purga |
| `tests/test_ephemeral_vault.py` (ciclo y concurrencia) | Sesiones sintéticas, referencias a buffers, mapa inválido y uso desde 8 hilos | Copia de solo lectura, sobrescritura, reemplazo, idempotencia, capacidad, purga y ausencia de `raw_input` en la firma |
| `tests/test_keyring.py` | Llaves fijas, dominios, copia/serialización, entorno y Unicode | Separación de dominios, verificación, rechazo de llaves inválidas, wipe, carga de secretos y normalización idempotente |
| `tests/test_ca05_restrictive_storage.py` | 20 ciclos de bóveda en directorio temporal; captura de logs y análisis AST | Ningún archivo creado, sin logs de PII ni primitivas de I/O; errores sin PII |
| `tests/test_ca05_restrictive_storage.py::test_ca05_db_and_wal_hold_zero_plaintext_pii_after_20_requests` | Llamada al ledger SQLite | Pendiente: `xfail(strict=True, raises=NotImplementedError)` hasta Gatillo 3; no acredita auditoría binaria integral |
| `test_zero_leak_failures` (pendiente integral) | Provocar error de consentimiento, LLM y almacenamiento con fixtures | Capturar logs, errores y `repr`; no contienen identificadores crudos; la bóveda se purga en todos los caminos |

Para CA-05 integral se buscarán secuencias completas de las fixtures y sus variantes de formato declaradas, no los dígitos individuales que pueden aparecer legítimamente en hashes. Los ciclos de bóveda ya se prueban en directorios temporales de pytest; el barrido binario SQLite/WAL sigue pendiente.

## Inconsistencias y decisiones pendientes

1. PROMPT Parte 1 indexa la bóveda por `session_id`; Parte 3 y la implementación usan `request_id`. Se documenta la firma actual sin introducir un segundo identificador.
2. `str` y `Mapping[str, str]` no ofrecen un contrato de sobrescritura física de todas las copias en Python. `zeroize` sobrescribe los `bytearray` internos, pero CPython no garantiza borrar copias previas; la copia con `str` de `get_map` sobrevive a la purga. El llamador debe soltarla cuanto antes, sin persistirla ni loguearla. Sigue pendiente conciliar el shredding garantizado por PROMPT con esta mitigación de mejor esfuerzo.
3. `frozen=True` con `Mapping` no impide que el llamador entregue o modifique un `dict`. `ExplicaResult` ya copia los mapas a `MappingProxyType` en `__post_init__`; ese hueco está resuelto en la implementación actual.
4. Canon de cédula, JSON de consentimiento y política de claves tras reinicio ya están definidos arriba. Sin `ADUANA_MASTER_KEY`, claves nuevas por arranque cambian índices ciegos e impiden verificar HMAC históricos con la llave actual; se usa ledger efímero. La rotación y conservación de llaves históricas quedan pendientes.
5. Los números RF en los docstrings remiten a ingeniería; SPEC solo enumera RF0–RF4. No tratarlos como referencias ausentes en ingeniería ni renumerar código.

6. SPEC §2 promete «anonimización irreversible», pero PROMPT Parte 1 §2/Parte 3 §2 y `EphemeralVault.get_map` mantienen un mapa de reversión en RAM. Es tokenización reversible durante la vigencia de la bóveda; el índice HMAC es un mecanismo distinto. Falta conciliar esa promesa con el contrato efectivo.

7. El mapa RIF implementa `C=3` por contrato del proyecto, sin fuente oficial que lo respalde. Su validación documental sigue abierta; los vectores sintéticos no constituyen fuente oficial.
8. El RIF abreviado no se rellena con ceros: `J-7013380-5` se rechaza; se exige cuerpo de 8 dígitos. La posible aceptación de abreviados queda abierta, sin cambiar el contrato vigente.
9. `consent_hash` usa SHA-256 simple del JSON canónico de cuatro campos, no HMAC, aunque `KeyRing` permite el dominio `consent`. La decisión de autenticar además el consentimiento queda abierta; el hash actual vincula campos sin aportar autenticación por clave.

## Fuentes

- [SPEC.md](../SPEC.md), §§3–5, §7 y §8: RAM, crypto, CA-01, CA-05 y tipos persistibles.
- [PROMPT_MAESTRO.md](../PROMPT_MAESTRO.md), Parte 1 §§1–3, Parte 2 §2.1, Parte 3 §§1–4 y Parte 4 Gatillo 0: fórmulas, bóveda y ciclo SDD.
- [Ingeniería y Negocio](<../docs/Ingenieria Y Negocio Aduana IA.md>), §1.3 RF-02/03/05/07, §1.4 RNF-02/06 y §3.2 Bloque 1.
- [Arquitectura existente](00_architecture.spec.md), invariantes globales y mapa de gatillos; firmas contrastadas con `core/`.

- Implementación Gatillo 0: `core/crypto.py`, `core/keyring.py`, `core/ephemeral_vault.py`, `core/text_normalizer.py` y `core/config.py`; cobertura contrastada con `tests/test_crypto.py`, `tests/test_ephemeral_vault.py`, `tests/test_keyring.py` y `tests/test_ca05_restrictive_storage.py`.
