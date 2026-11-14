# 06 — Identidad y RBAC aduanero Zero-Trust

**Estado:** FASE 1 (spec viva) del Gatillo RBAC. Contrato para `core/auth.py`, `core/rbac.py`, `core/rbac_db.py`, `core/identity.py`, `core/rbac_seed.py` y la capa `app/`.

## 1. Alcance

Autenticar a funcionarios y agentes y autorizar cada ruta por **rol operativo aduanero**, con segregación de funciones (SoD). Roles de negocio, no de sistemas/TI. Criptografía solo stdlib (`hashlib`, `hmac`, `secrets`, `base64`, `json`). Los identificadores de personas (cédula, RIF) nunca se guardan en claro: solo su índice ciego HMAC (Anillo 2).

## 2. Roles (`AduanaRoleType`)

| Rol | Quién es | Capacidad (resumen) |
|---|---|---|
| `INSPECTOR_TRIBUTARIO_SENIAT` | Funcionario SENIAT, nivel alto | Audita declaraciones de valor; sobreescribe bloqueos por falsos positivos (decisión humana vinculante); trazabilidad completa de un importador (por índice ciego); verifica el ledger completo. **No envía trámites.** |
| `AGENTE_ADUANAL_CERTIFICADO` | Usuario externo autenticado | Solo envía solicitudes de importación/exportación y recibe el paquete sanitizado. Sin bóveda, ledger, explicabilidad ni auditoría. |
| `FISCAL_ANTI_CONTRABANDO` | Fiscal | Solo lectura de la explicabilidad (`ExplicaResult`: probabilidad y SHAP) para detectar patrones de riesgo. No modifica el flujo ni sella nada. |
| `OPERADOR_LOGISTICO_ALMACEN` | Almacén / liberación de mercancía | Permisos mínimos: consultar el estado criptográfico (`LedgerReceipt`) de una orden de liberación. Sin PII ni payload. |
| `SUPERVISOR_PUERTO_ADUANERO` *(añadido)* | Jefe de puerto/aduana | Gestiona altas, suspensiones y roles de usuarios de su aduana; ve el ledger y las métricas. **No opera trámites** (SoD: quien administra identidades no decide ni envía trámites). |
| `ANALISTA_VALORACION_ADUANERA` *(añadido)* | Analista de valoración | Revisa el valor declarado: explicabilidad y saneamiento previo (`shield`) de documentos. Solo lectura; no sella ni sobreescribe. |

## 3. Permisos y matriz

Permisos (`Permission`): `tramite:submit`, `tramite:override`, `shield:inspect`, `explica:read`, `ledger:receipt`, `ledger:audit`, `audit:fiscal`, `metrics:read`, `users:manage`, `chat:ia`, `chat:canal`. La tabla siguiente cubre los nueve primeros; los de chat se describen en §3.1.

| Permiso | INSPECTOR | AGENTE | FISCAL | OPERADOR | SUPERVISOR | ANALISTA |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| `tramite:submit` |  | ✔ |  |  |  |  |
| `tramite:override` | ✔ |  |  |  |  |  |
| `shield:inspect` | ✔ |  |  |  |  | ✔ |
| `explica:read` | ✔ |  | ✔ |  |  | ✔ |
| `ledger:receipt` | ✔ |  |  | ✔ |  |  |
| `ledger:audit` | ✔ |  |  |  | ✔ |  |
| `audit:fiscal` | ✔ |  |  |  |  |  |
| `metrics:read` | ✔ |  |  |  | ✔ |  |
| `users:manage` |  |  |  |  | ✔ |  |

Mínimo privilegio: el fiscal solo tiene `explica:read`; el operador solo `ledger:receipt`; el agente solo `tramite:submit`.

### 3.1 Permisos de chat (`chat:ia` y `chat:canal`)

Los tiene únicamente `ANALISTA_VALORACION_ADUANERA` (además de `explica:read` y `shield:inspect`); no son permisos de escritura, así que el rol sigue siendo de solo lectura.

| Permiso | Qué habilita | Estado en el backend |
|---|---|---|
| `chat:ia` | Chat con la IA institucional. El front lo atiende con `POST /shield/inspect`, cuya guarda acepta `shield:inspect` **o** `chat:ia`. | Implementado. |
| `chat:canal` | Canal seguro de chat entre funcionarios. | **Solo permiso**: el Canal Seguro del front es una interfaz simulada y no existe endpoint de mensajería. Hasta crearlo, el permiso no protege ninguna ruta. |

### 3.2 Anti-escalada de privilegios

Quien tiene `users:manage` solo puede **crear y gestionar roles operativos** (`AGENTE_ADUANAL_CERTIFICADO`, `FISCAL_ANTI_CONTRABANDO`, `OPERADOR_LOGISTICO_ALMACEN`, `ANALISTA_VALORACION_ADUANERA`; `core.rbac.MANAGEABLE_ROLES`). Las cuentas de inspector y de supervisor no se crean ni se modifican por la API: se siembran o se dan de alta fuera de banda. Nadie puede suspenderse ni cambiarse el rol a sí mismo, ni actuar sobre un rol superior. `IdentityService.create_user_as`, `suspend_user_as` y `change_role_as` reconsultan al actor en la BD en cada llamada.

### Invariantes SoD (verificadas por test sobre la matriz)
1. Ningún rol tiene `users:manage` junto a `tramite:submit` o `tramite:override`.
2. Ningún rol tiene `tramite:submit` junto a `tramite:override` (quien envía no decide) ni junto a `audit:fiscal`.
3. Ningún rol de solo lectura (`FISCAL`, `ANALISTA`) tiene permisos de escritura (`tramite:*`, `users:manage`).
4. El rol `OPERADOR_LOGISTICO_ALMACEN` no tiene `explica:read`, `shield:inspect` ni `audit:fiscal` (sin PII ni payload).

## 4. Endpoints y control de acceso (`/api/v1`)

Toda ruta (salvo `GET /health/system`) exige además la cabecera `X-Aduana-Token` (sesión de la aplicación). El control por rol se activa con `ADUANA_RBAC=1` (`Settings.rbac_enabled`); con RBAC apagado rige solo el token de sesión (compatibilidad). Con RBAC encendido se exige `Authorization: Bearer <token>` y el permiso indicado.

| Método y ruta | Permiso | Notas |
|---|---|---|
| `POST /auth/login` | pública (solo `X-Aduana-Token`) | `{identificador, password}` → `AuthToken`. Error uniforme. |
| `GET /auth/me` | cualquier usuario activo | Rol y permisos efectivos, sin material de contraseña. |
| `POST /gateway/process` | `tramite:submit`; con `human_decision` o `override_justification` exige `tramite:override` | El agente envía; el inspector decide. |
| `POST /shield/inspect` | `shield:inspect` | |
| `POST /explica/evaluate` *(nuevo)* | `explica:read` | Calcula `ExplicaResult` sin sellar ni persistir (solo lectura). |
| `GET /ledger/verify` | `ledger:audit` | |
| `GET /ledger/receipt/{codigo}` *(nuevo)* | `ledger:receipt` | `{codigo, block_index, block_hash, cadena_valida, liberacion_autorizada}`. Sin PII ni payload. |
| `POST /audit/fiscal` *(nuevo)* | `audit:fiscal` | `{identificador}` (cédula/RIF) → trazabilidad de bloques del importador por índice ciego. POST para no poner datos personales en la URL. |
| `GET /metrics/benchmark` | `metrics:read` | |
| `POST /ledger/tamper-sim` (demo) | `ledger:audit` | |
| `GET /usuarios`, `POST /usuarios`, `POST /usuarios/{codigo}/suspender` | `users:manage` | Nunca devuelve sal ni hash. |

Errores (cuerpo `{"error": "<CODIGO>"}`, sin contenido ciudadano): `401 ERR_AUTH_INVALID` (credencial o token inválido/expirado, mensaje uniforme), `403 ERR_FORBIDDEN` (rol sin permiso), `423 ERR_ACCOUNT_LOCKED`, `409 ERR_USER_EXISTS`, `422 ERR_WEAK_PASSWORD`.

### 4.1 Formas de petición y respuesta (fijadas por `tests/test_ca07_rbac_aduana.py`)

- `POST /auth/login` → `200` con `{"token": "v1....", "codigo_usuario", "rol", "expires_at"}`; sin hash ni sal. Usuario inexistente, contraseña errónea y usuario suspendido dan el mismo `401 ERR_AUTH_INVALID`. Los 4 primeros fallos dan 401; con el bloqueo activo, `423 ERR_ACCOUNT_LOCKED` también con la contraseña correcta.
- `GET /auth/me` → `200` con `{"codigo_usuario", "rol", "permisos": [...]}`; sin secretos.
- `POST /explica/evaluate` → cuerpo `{"features": {...5 variables...}}`; respuesta `200` con `probability_score`, `linear_shap_values`, `model_recommendation` en el nivel superior. No crea bloques.
- `POST /audit/fiscal` → cuerpo `{"identificador": "V-12345678"}`; respuesta `{"blocks": [{"block_index", "citizen_receipt_code", "security_verdict", "timestamp_utc", "block_hash"}]}`; solo los bloques cuyo `blind_citizen_id` coincide con el índice ciego del identificador; nunca devuelve el identificador ni `blind_citizen_id`.
- `GET /ledger/receipt/{codigo}` → `{"codigo", "block_index", "block_hash", "cadena_valida", "liberacion_autorizada"}`; `404 ERR_NOT_FOUND` sin eco si no existe.
- `POST /usuarios` → cuerpo `{"codigo_usuario", "identificador", "rol", "password"}`; respuesta `201` con el `UsuarioAduana` público (sin sal, hash ni `blind_identifier`). `POST /usuarios/{codigo}/suspender` sin cuerpo → `200`.
- Con RBAC apagado las rutas nuevas no existen (`404`; `405` aceptable en POST por el router estático).

## 5. Invariantes criptográficas

1. **Contraseñas:** nunca en claro. `hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations, dklen=32)` con `salt = secrets.token_bytes(32)` único por usuario. Iteraciones por defecto `600_000` (OWASP 2023), guardadas por usuario para poder migrar. Comparación con `hmac.compare_digest`.
2. **Política mínima:** ≥ 12 caracteres, al menos una letra y un dígito, no todos los caracteres iguales. `WeakPasswordError` sin eco de la contraseña.
3. **Índice ciego (Anillo 2):** todo identificador de funcionario o agente (cédula `V|E`+5–9 dígitos, o RIF `V|E|J|P|G|C`+8 dígitos+verificador) se normaliza y se guarda solo como `hmac_hex("blind-index", canónico)` (`core.keyring.KeyRing`). Un RIF y una cédula nunca colisionan (el RIF lleva dígito verificador de 9 dígitos y se canoniza con su letra). El mismo índice liga al usuario con los bloques del ledger de su propio trámite.
4. **No se guarda nombre ni identificador en claro.** El usuario se identifica por `codigo_usuario` (alias no personal, p. ej. `insp.senat.01`).
5. **Token** (sin librerías externas): `v1.<base64url(JSON)>.<hmac>`; JSON `{sub, rol, iat, exp, jti}`; HMAC-SHA256 con la subllave `auth-token` del `KeyRing`; verificación en tiempo constante y comprobación de `exp`. Cada petición **vuelve a consultar** al usuario (Zero-Trust): una suspensión o un cambio de rol surte efecto de inmediato. TTL por defecto 30 min.
6. **Resistencia a enumeración y fuerza bruta:** login con tiempo comparable exista o no el usuario (hash ficticio), error uniforme, bloqueo tras 5 intentos fallidos durante 15 min (reloj inyectable), contador reiniciado tras éxito.
7. Con llave efímera (sin `ADUANA_MASTER_KEY`) el índice ciego cambiaría en cada arranque: **RBAC exige llave persistente** (`Settings` rechaza `rbac_enabled` con `ledger_ephemeral`).

## 6. Persistencia (`usuarios_aduana`, SQLite)

Base distinta del ledger (`ADUANA_USERS_DB_PATH`, por defecto `data/usuarios.db`): el ledger es inmutable y esta tabla debe poder actualizar contadores y estado.

PRAGMAs: `journal_mode=WAL`, `synchronous=FULL`, `secure_delete=ON`, `trusted_schema=OFF`, `foreign_keys=ON`. Permisos del archivo `0600` cuando el SO lo permita. Un trigger impide `DELETE` (`ERR_NO_DELETE_USUARIOS`): la baja es lógica (`estado='SUSPENDIDO'`).

```sql
CREATE TABLE usuarios_aduana (
  user_id            TEXT PRIMARY KEY,            -- uuid4 hex generado en servidor
  codigo_usuario     TEXT NOT NULL UNIQUE,        -- alias no personal
  blind_identifier   TEXT NOT NULL UNIQUE,        -- HMAC-SHA256 del identificador
  rol                TEXT NOT NULL CHECK (rol IN (...6 roles...)),
  estado             TEXT NOT NULL CHECK (estado IN ('ACTIVO','SUSPENDIDO')),
  password_salt      BLOB NOT NULL CHECK (length(password_salt) = 32),
  password_hash      BLOB NOT NULL CHECK (length(password_hash) = 32),
  kdf_iterations     INTEGER NOT NULL CHECK (kdf_iterations >= 1),
  failed_attempts    INTEGER NOT NULL DEFAULT 0,
  locked_until_utc   TEXT,
  created_utc        TEXT NOT NULL,
  last_login_utc     TEXT
);
```

## 7. Contratos (firmas exactas)

```python
# core/context.py
AduanaRoleType = Literal["INSPECTOR_TRIBUTARIO_SENIAT", "AGENTE_ADUANAL_CERTIFICADO",
    "FISCAL_ANTI_CONTRABANDO", "OPERADOR_LOGISTICO_ALMACEN",
    "SUPERVISOR_PUERTO_ADUANERO", "ANALISTA_VALORACION_ADUANERA"]
UserStatus = Literal["ACTIVO", "SUSPENDIDO"]

@dataclass(frozen=True, slots=True)
class UsuarioAduana:           # sin material de contraseña
    user_id: str; codigo_usuario: str; blind_identifier: str
    rol: AduanaRoleType; estado: UserStatus; created_utc: str
    last_login_utc: str | None = None; failed_attempts: int = 0
    locked_until_utc: str | None = None

@dataclass(frozen=True, slots=True)
class AuthToken:
    token: str = field(repr=False); user_id: str; codigo_usuario: str
    rol: AduanaRoleType; issued_at: int; expires_at: int; token_id: str

# core/rbac.py (política pura)
ROLE_PERMISSIONS: Mapping[AduanaRoleType, frozenset[Permission]]
def permissions_of(role) -> frozenset[Permission]
def has_permission(role, permission) -> bool

# core/auth.py (funciones puras)
PBKDF2_ITERATIONS: Final = 600_000
@dataclass(frozen=True, slots=True)
class PasswordRecord: salt: bytes; hash: bytes = field(repr=False); iterations: int
def validate_password_policy(password: str) -> None            # WeakPasswordError
def derive_key(password: str, salt: bytes, iterations: int) -> bytes
def hash_password(password: str, *, iterations: int = PBKDF2_ITERATIONS) -> PasswordRecord
def verify_password(password: str, record: PasswordRecord) -> bool
def normalize_identifier(identifier: str) -> str                # cédula o RIF canónicos; ValueError sin eco
def blind_identifier(keys: KeyRing, identifier: str) -> str
@dataclass(frozen=True, slots=True)
class TokenClaims: user_id: str; rol: AduanaRoleType; issued_at: int; expires_at: int; token_id: str
def issue_token(keys: KeyRing, user: UsuarioAduana, *, now: int, ttl_seconds: int) -> AuthToken
def verify_token(keys: KeyRing, token: str, *, now: int) -> TokenClaims   # InvalidTokenError

# core/rbac_db.py
class UsuariosRepository:
    def __init__(self, db_path: str) -> None
    def create_user(self, *, codigo_usuario: str, blind_identifier: str, rol: AduanaRoleType,
                    password: PasswordRecord, now_utc: str) -> UsuarioAduana     # DuplicateUserError
    def get_by_id(self, user_id: str) -> UsuarioAduana | None
    def get_credentials(self, blind_identifier: str) -> tuple[UsuarioAduana, PasswordRecord] | None
    def list_users(self) -> list[UsuarioAduana]
    def register_failed_attempt(self, user_id: str, *, max_attempts: int, lockout_seconds: int, now: datetime) -> UsuarioAduana
    def register_successful_login(self, user_id: str, *, now_utc: str) -> UsuarioAduana
    def set_estado(self, user_id: str, estado: UserStatus) -> UsuarioAduana
    def set_rol(self, user_id: str, rol: AduanaRoleType) -> UsuarioAduana
    def count(self) -> int
    def close(self) -> None

# core/identity.py (lógica de dominio, sin Litestar)
class IdentityService:
    def __init__(self, repo: UsuariosRepository, keys: KeyRing, *, iterations: int, token_ttl_seconds: int,
                 max_failed_attempts: int, lockout_seconds: int, clock: Callable[[], datetime] = utcnow) -> None
    def login(self, identificador: str, password: str) -> AuthToken   # AuthenticationError / AccountLockedError
    def resolve_token(self, token: str) -> UsuarioAduana             # AuthenticationError; consulta BD y exige ACTIVO
    def create_user(self, *, codigo_usuario: str, identificador: str, rol: AduanaRoleType, password: str) -> UsuarioAduana
    def authorize(self, user: UsuarioAduana, permission: Permission) -> None   # AuthorizationError
```

## 8. Seeders (`core/rbac_seed.py` y `scripts/seed_usuarios.py`)

12 usuarios sintéticos (identificadores obviamente ficticios): **uno por cada uno de los 6 roles**, **4 usuarios "normales"** (cuentas de mínimo privilegio: 2 `AGENTE_ADUANAL_CERTIFICADO` y 2 `OPERADOR_LOGISTICO_ALMACEN`) y **2 usuarios con acceso a los dos chats** (`chat.analista.01` y `chat.analista.02`, rol `ANALISTA_VALORACION_ADUANERA`, con `chat:ia` y `chat:canal`), distintos entre sí para poder conversar. Idempotente (omite los ya existentes por `codigo_usuario`). Las contraseñas **no están en el repositorio**: el script las genera con `secrets` y las escribe una vez en `data/seed_credenciales.local.json` (permisos restrictivos, ignorado por git); la función `seed_users` las recibe por parámetro (los tests pasan contraseñas propias).

## 9. Criterios de aceptación (tests)

- **CA-07a (core):** PBKDF2 correcto y verificable, salt único de 32 bytes, nada en claro en el `.db`, índice ciego estable por formato (`V-12.345.678` = `12345678`), token inmanipulable y con expiración, política de contraseña, bloqueo tras 5 fallos.
- **CA-07b (matriz):** las invariantes SoD de la sección 3.
- **CA-07c (API):** un AGENTE no accede a `/audit/fiscal`, `/ledger/verify`, `/explica/evaluate` ni `/usuarios` (403); un INSPECTOR no puede enviar trámites (403) pero sí auditar; el OPERADOR solo consulta recibos y recibe 403 en auditoría; el FISCAL solo evalúa explicabilidad; sin token 401; un usuario suspendido pierde acceso al instante; con RBAC apagado el comportamiento previo no cambia.
- **Zero-PII:** ninguna respuesta ni el `.db` contienen cédulas, RIF, contraseñas, sal ni hash expuestos por la API.

## 10. Decisiones abiertas

- Rotación de contraseñas y MFA (fuera de este gatillo).
- Mapeo a un directorio institucional (OIDC/LDAP) en producción.
- Persistir `ExplicaResult` para consulta posterior (hoy `/explica/evaluate` recalcula sin sellar).
- El inspector sobreescribe mediante `human_decision`/`override_justification` en `/gateway/process`; un flujo dedicado de revisión de bloqueos queda para un gatillo posterior.
