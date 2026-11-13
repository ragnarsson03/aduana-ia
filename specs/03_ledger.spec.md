# 03 — Ledger criptográfico y persistencia restrictiva

**Estado:** especificación viva de Gatillo 3. Repositorio, sellado y verificador son stubs. Las garantías descritas requieren implementación y las pruebas futuras indicadas aquí.

## Alcance y trazabilidad

`pipeline/stage4_ledger.py` y `StorageRepositoryProtocol`: SPEC RF4, CA-03, CA-05 y esquema §7; ingeniería RF-15 a RF-17 y RNF-02/06. EXPLICA se ejecuta antes del sellado, aunque su archivo tenga número de etapa mayor.

## Invariantes

- Ledger append-only, sin texto crudo, mapa de reversión ni respuesta LLM insegura. La justificación humana también debe respetar Zero-Plaintext-PII.
- SQLite: `PRAGMA journal_mode=WAL;`, `PRAGMA synchronous=FULL;` y `PRAGMA secure_delete=ON;`. Triggers `BEFORE UPDATE/DELETE` abortan con `RAISE(ABORT, 'ERR_IMMUTABLE_LEDGER')`.
- Clave maestra solo RAM. Hash encadenado y HMAC se calculan en backend; comparar firmas con `hmac.compare_digest`.
- El bloque referencia al anterior y el recibo corresponde al bloque realmente persistido. No emitir éxito de sellado cuando falla la inserción.
- La decisión administrativa requiere confirmación humana; override exige **≥ 20 caracteres**, según [04_explica.spec.md](04_explica.spec.md).

## Firmas existentes (sin modificación)

~~~python
# pipeline/stage4_ledger.py
class SQLiteLedgerRepository:
    def __init__(self, db_path: str) -> None: ...
    def append_block(self, block: LedgerBlock) -> None: ...
    def get_block(self, block_index: int) -> LedgerBlock | None: ...
    def last_block(self) -> LedgerBlock | None: ...
    def list_blocks(self) -> Sequence[LedgerBlock]: ...
    def count(self) -> int: ...
    def close(self) -> None: ...

def seal_packet(
    packet: AduanaPacket, repo: StorageRepositoryProtocol, *, master_key: bytes
) -> LedgerReceipt: ...

def verify_chain(blocks: Sequence[LedgerBlock], *, master_key: bytes) -> ChainVerification: ...

# core/protocols.py
class StorageRepositoryProtocol(Protocol):
    def append_block(self, block: LedgerBlock) -> None: ...
    def get_block(self, block_index: int) -> LedgerBlock | None: ...
    def last_block(self) -> LedgerBlock | None: ...
    def list_blocks(self) -> Sequence[LedgerBlock]: ...
    def count(self) -> int: ...
    def close(self) -> None: ...

class ChainVerifierProtocol(Protocol):
    def verify_chain(self, blocks: Sequence[LedgerBlock]) -> ChainVerification: ...

# core/crypto.py
def block_hash(
    index: int, timestamp_utc: str, blind_id: str, payload_hash: str, prev_hash: str
) -> str: ...
def block_signature(master_key: bytes, block_hash_hex: str, human_decision: str) -> str: ...
~~~

El constructor actual solo conserva `_db_path`; no crea aún tablas, PRAGMAs ni triggers. `Settings.db_path` es `Path` y el constructor recibe `str`: el llamador deberá convertirlo sin cambiar la firma.

## Datos y fórmulas canónicas existentes

`LedgerBlock` refleja los 14 campos de SPEC §7: `block_index`, `request_id`, `timestamp_utc`, `blind_citizen_id`, `payload_hash`, `prev_hash`, `block_hash`, `hmac_signature`, `security_verdict`, `model_recommendation`, `human_decision`, `human_override`, `override_justification` y `citizen_receipt_code`. SQL exige índice PRIMARY KEY, `request_id` y recibo UNIQUE, campos NOT NULL salvo justificación, y override INTEGER NOT NULL DEFAULT 0.

PROMPT Parte 3.4 fija exactamente:

~~~python
H_i = hashlib.sha256(
    f"{i}|{timestamp_utc}|{blind_citizen_id}|{payload_hash}|{prev_hash}".encode()
).hexdigest()
Sig_i = hmac.new(
    SERVER_MASTER_KEY, f"{H_i}|{human_decision}".encode(), hashlib.sha256
).hexdigest()
~~~

`GENESIS_PREV_HASH='0'*64` está fijado por `core/config.py`, no por SPEC. El índice inicial no está publicado. `payload_hash` es SHA-256 del contenido sanitizado según SPEC; su representación exacta (texto SHIELD, respuesta o conjunto de campos serializados) no está definida.

## Precondiciones y postcondiciones

| Operación | Precondición | Postcondición |
|---|---|---|
| Repositorio | Ruta local; conexión disponible | Esquema y endurecimiento activos; `append_block` inserta sin modificar bloques previos |
| Lecturas | Repositorio abierto | `get_block` devuelve bloque o `None`; `last_block` devuelve último o `None`; conteo y lista reflejan persistencia; orden requerido por verificación es secuencial |
| `seal_packet` | Datos sanitizados, resultado matemático y decisión humana válidos, repositorio y clave disponibles | Añade bloque enlazado, calcula hashes/firma y devuelve `LedgerReceipt` con índice, hashes, firma, código y `chain_verified` coherentes |
| `verify_chain` | Secuencia de bloques en orden y clave correspondiente | Recalcula desde génesis; detecta fallo de hash, enlace o HMAC; `ChainVerification.is_valid=False` y `corrupted_block_index` exacto con motivo |
| Cadena íntegra | Todos los controles satisfechos | `is_valid=True` y sin índice/motivo de corrupción; contador `blocks_checked` refleja bloques revisados |
| Intento UPDATE/DELETE | DML ordinario contra tabla inmutable | Abortado por trigger; no altera historial. Tipos de error disponibles: `ImmutableLedgerError` y `StorageError` |

Motivos existentes: `HASH_MISMATCH`, `PREV_HASH_LINK_BROKEN` y `HMAC_SIGNATURE_FORGED`. Precedencia si concurren varios, cadena vacía, índices discontinuos y semántica de `blocks_checked` al fallar requieren definición. Los tests deben aislar fallos para obtener motivos inequívocos.

## Criterios de aceptación y umbrales exactos

- **CA-03:** ante alteración de **un solo bit**, incluso con SHA-256 recalculado sin clave HMAC, `GET /api/v1/ledger/verify` responde `is_valid=False`, índice exacto y motivo, en **< 50 ms**.
- **CA-05:** después de **20 trámites**, **0 bytes** de Cédulas, RIF o teléfonos en `.db`/logs; ingeniería RNF-02 añade WAL/SHM y nombres.
- Endurecimiento SQLite es obligatorio por SPEC §3 y PROMPT Parte 1 §2, sin un porcentaje parcial admisible.

Medir CA-03 en el endpoint además de la función pura. No se especifican tamaño máximo de cadena, hardware ni si tiempo incluye transporte HTTP; registrar ambos tiempos y número de bloques, sin inventar un límite de longitud ni sustituir el umbral por un promedio.

## Casos de prueba concretos a escribir en tests/

Archivo principal: `tests/test_ca03_ledger.py`. Usar SQLite temporal, IDs `fixture-ledger-001..003`, UTC fijos, índices ciegos HMAC de fixtures y clave `b'k'*32`. Para aislar pruebas criptográficas, tres bloques con índices de fixture **1, 2, 3**, sin inferir que 1 sea génesis obligatorio.

| Caso | Acción sintética | Comprobación |
|---|---|---|
| `test_hash_signature_vector` | Construir campos fijos y calcular con StdLib las dos fórmulas anteriores | Igualdad exacta con helpers; cambiar decisión cambia HMAC |
| `test_append_and_receipt` | Sellar tres transacciones ya confirmadas | Conteo aumenta, enlaces correctos, recibos únicos corresponden a filas; verificación íntegra |
| `test_sqlite_hardening` | Consultar PRAGMAs de conexión temporal y disparar UPDATE y DELETE | `journal_mode=wal`, `synchronous=2` (FULL), `secure_delete=1`; ambos abortan con `ERR_IMMUTABLE_LEDGER` y filas intactas |
| `test_schema_uniqueness` | Repetir `request_id` o recibo en una nueva fila | SQLite rechaza duplicado; no emitir recibo de éxito |
| `test_payload_bit_flip` | En copia de bloques, cambiar un hex de `payload_hash` del bloque 2 de `0` a `1` manteniendo hash/firma | `False`, índice 2, `HASH_MISMATCH` |
| `test_prev_link_only` | Alterar `prev_hash` del bloque 2 y recalcular su hash y HMAC con clave de fixture | Hash y HMAC internamente válidos; enlace incorrecto: índice 2, `PREV_HASH_LINK_BROKEN` |
| `test_rehashed_without_hmac` | Cambiar payload del bloque 2, recalcular SHA-256 y enlaces siguientes, conservar firmas antiguas | Índice 2, `HMAC_SIGNATURE_FORGED`; atacante sin clave no legitima cambio |
| `test_forged_signature` | Cambiar un bit de firma del bloque 2, mantener resto | Índice 2, `HMAC_SIGNATURE_FORGED` |
| `test_uncovered_fields` | Alterar separadamente `override_justification`, `security_verdict`, `model_recommendation`, `request_id` o recibo conservando resto | Prueba de brecha: CA-03 exige detectar; fórmulas actuales no lo garantizan. No declarar aprobación hasta resolver cobertura |
| `test_verify_endpoint_latency` | Repetir sabotajes aislados en copia temporal de base de prueba | JSON con índice/motivo exactos y **<50 ms**; no confundir rechazo del trigger con detección criptográfica |
| `tests/test_ca05_restrictive_db.py` | 20 trámites sintéticos; incluir justificación que contenga cédula ficticia | Auditoría binaria de DB/logs y WAL/SHM sin originales; la justificación debe sanearse o rechazarse sin fuga |

Para sabotaje usar copias de dataclasses en pruebas puras. Para prueba de base de datos, usar copia temporal controlada y acceso de prueba que eluda los triggers solo allí; nunca deshabilitar endurecimiento en la ruta normal. No alterar bytes arbitrarios de la estructura interna SQLite que solo provoquen corrupción de páginas sin índice recuperable.

## Inconsistencias y decisiones pendientes

1. PROMPT describe `verify_chain(blocks)` y retorno tupla `(False, corrupted_idx, reason)`; stub real recibe `master_key` keyword-only y devuelve `ChainVerification`. El protocolo declara un método sin ese parámetro: falta adaptador con clave inyectada o conciliación futura del contrato.
2. `seal_packet` recibe `AduanaPacket`, pero ese tipo ya exige `ledger: LedgerReceipt` no opcional. El flujo previo al sellado no tiene recibo genuino; falta estado intermedio. No inventar un recibo provisional como contrato ya aceptado.
3. El hash/HMAC explícitos no cubren todos los campos de SPEC §7. Sin canon adicional de payload que incluya esos campos y verificación correspondiente, cambios en justificación, recomendación o recibo pueden ser invisibles, contradiciendo la garantía general de CA-03.
4. No se define algoritmo del recibo, canon de payload, índice inicial, política de concurrencia para append ni recuperación/rotación de claves entre arranques. `chain_verified` tampoco especifica cuándo se ejecuta verificación completa.
5. Triggers impiden sabotaje DML ordinario; el endpoint demo necesita un mecanismo controlado aún no definido. Borrado del último bloque o sustitución completa de la cadena tampoco es detectable solo con enlaces sin ancla externa; no hay ancla en los stubs.
6. Justificación libre puede reintroducir PII después de SHIELD. No existe stub específico para sanear ese campo antes de persistirlo.

## Fuentes

- [SPEC.md](../SPEC.md), §§3–5 y §7: persistencia, RF4, CA-03/05 y esquema SQL.
- [PROMPT_MAESTRO.md](../PROMPT_MAESTRO.md), Parte 1 §2, Parte 2, Parte 3 §4 y Parte 4 Gatillos 3/6: fórmulas, verificación y endpoints.
- [Ingeniería y Negocio](<../docs/Ingenieria Y Negocio Aduana IA.md>), §1.3 RF-15/16/17/20 y §1.4 RNF-02/06.
- [Guía Ministerial](<../docs/Guia Implementacion Ministerial Y Defensa.md>), §1.2: menciona resumen diario a Contraloría; no define protocolo de anclaje en los stubs y no se supone implementado.
- [Arquitectura existente](00_architecture.spec.md); firmas contrastadas con `pipeline/stage4_ledger.py`, `core/protocols.py` y `core/crypto.py`.
