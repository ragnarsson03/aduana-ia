# 06 — Verificación de Archivos Institucionales y Chat con IA en Frontend

**Estado:** Especificación Formal de Extensión v1.0 (Python 2026 — Litestar + PyWebView).  
**Trazabilidad:** SPEC §3, §4 (RF1, RF2, RF4); Guía Ministerial (Preguntas 3, 4, 5 y 6); RNF-01 a RNF-04.

---

## 1. Verificación y Despacho Seguro de Archivos (`/api/v1/files/verify-and-seal`)

### 1.1 Propósito
Garantizar que todo archivo comercial (PDF, Word, Excel, imagen, audio) enviado entre funcionarios vía correo institucional (o subido por ciudadanos) sea auditado, sanitizado criptográficamente y sellado en el Ledger antes de su entrega.

### 1.2 Flujo de Procesamiento en el Servidor

```text
[Remitente / Correo] ──► Subida de Archivo ──► [1. SHA-256 Checksum]
                                                     │
                                                     ▼
                                        [2. Inspección SHIELD + GUARD-IN]
                                        (Detección PII / Macros / Inyecciones)
                                                     │
                                                     ▼
                                        [3. Verificación de Políticas]
                                        (CLEAN / BLOCKED_INJECTION / PII_LEAK)
                                                     │
                                                     ▼
                                        [4. Doble Sello en LEDGER]
                                        (SHA-256 encadenado + HMAC Servidor)
                                                     │
                                                     ▼
                                        [5. Emisión de Recibo Criptográfico]
                                        (citizen_receipt_code para el correo)
```

### 1.3 Contratos y DTOs (Msgspec)

~~~python
class FileVerifyRequest(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    filename: str
    file_bytes_base64: str
    sender_email: str
    recipient_email: str
    purpose_code: str
    extracted_text: str | None = None

class FileVerifyResponse(msgspec.Struct, frozen=True):
    file_sha256: str
    is_safe: bool
    policy_status: PolicyStatus
    shield_pii_detected: bool
    detected_pii_types: tuple[str, ...]
    citizen_receipt_code: str
    block_index: int
    chain_verified: bool
    latency_ms: float
~~~

### 1.4 Reglas de Inmutabilidad y Auditoría
1. **Zero-Plaintext-PII:** Si el archivo contiene datos personales sensibles que deben transferirse al destinatario legítimo, viaja dentro de un sobre blindado `.aduana` cifrado con `AES-256-GCM`. El servidor solo almacena en SQLite el `payload_hash` (SHA-256 del contenido binario) y el hash de la justificación, **jamás los bytes del documento en claro ni el texto sensible**.
2. **Certificación de Despacho:** Al completarse la verificación, el Ledger genera un bloque con:
   * `payload_hash`: SHA-256 del archivo verificado.
   * `security_verdict`: `CLEAN` o código de bloqueo correspondiente.
   * `citizen_receipt_code`: Identificador único que se adjunta al correo institucional.
3. **Validación en Destino:** El destinatario puede consultar `GET /api/v1/ledger/verify` o ingresar el recibo en la interfaz para confirmar que el archivo recibido por correo es idéntico byte a byte al que fue auditado por el servidor.

---

## 2. Definición del Chat de la IA en el Frontend

### 2.1 Modelo de Interacción en Pantalla
El Chat institucional opera como la interfaz unificada del **Panel del Funcionario** y la **Taquilla Ciudadana** (servida por Litestar en web y embebida por PyWebView en escritorio):

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 🛡️ ADUANA IA — Perímetro Soberano de Gobernanza Zero-Trust             │
│ Sesión: FUNC-SALUD-084 | Modo: Local Air-Gapped | Ledger: Válido (265) │
├────────────────────────────────────────────────────────────────────────┤
│ [09:14] 👤 Funcionario / Solicitante:                                  │
│ "Solicito revisión de expediente de salud para V-12345678 con informe."│
│ 🛡️ [Perímetro]: Enmascarado a [CEDULA_1] en RAM (TTL: 180s)            │
│                                                                        │
│ [09:14] 🤖 Asistente Institucional (Aviso Oficial Art. 60 CRBV):       │
│ "Expediente de solicitud de apoyo médico registrado para [CEDULA_1].   │
│  Recaudos evaluados: Cédula y récipe consignados.                      │
│  Borrador de resolución orientativa generado."                         │
│                                                                        │
│ 📊 [EXPLICA]: 85% Prioridad Alta (SHAP: Gravedad +42%, Antigüedad +23%)│
│ ⚖️ Decisión Funcionario: [ APROBAR (Firme) ] [ REVISAR ] [ OVERRIDE ]  │
│ 🔗 Recibo Ledger: REC-20261113-0914-A8F2 (Sello SHA-256 + HMAC Válido)│
├────────────────────────────────────────────────────────────────────────┤
│ [ Escriba su consulta o arrastre un documento...              ] [Enviar]│
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Componentes Obligatorios del Chat en el Frontend
1. **Transparencia de Perímetro Visible:**
   * Cada mensaje enviado muestra la indicación de enmascaramiento soberano: qué variables fueron protegidas antes de enviarse a la IA (`[CEDULA_1]`, `[RIF_1]`).
2. **Aviso Mandatorio de Inteligencia Artificial:**
   * Cumpliendo con el requisito **RF-14** y normativas SUSCERTE, todo mensaje de la IA lleva la etiqueta visible: `🤖 Asistente Institucional Asistido por IA — La decisión final corresponde al funcionario público`.
3. **Tarjeta de Explicabilidad Vinculante (`EXPLICA`):**
   * El chat no es un texto libre infinito: cada dictamen de trámite genera una tarjeta matemática interactiva que desglosa las variables de decisión objetivas y sus valores SHAP lineales ($\phi_j$).
   * Incluye los botones de acción del funcionario: `APROBAR`, `REVISAR`, `RECAUDOS INCOMPLETOS` o `MODIFICAR (Override)`. Si hay override, la interfaz abre un modal obligatorio que exige justificación escrita $\ge 20$ caracteres.
4. **Badge de Trazabilidad Criptográfica:**
   * Muestra el `citizen_receipt_code` con un enlace o botón de "Verificar Integridad", que consulta en vivo `/api/v1/ledger/verify` y muestra check verde con la latencia en milisegundos (< 50 ms).

### 2.3 Protocolo de Conexión Frontend $\rightarrow$ Backend
* **Web (Litestar):** Conexión vía `fetch()` asíncrono con `POST /api/v1/gateway/process` y cabecera de seguridad obligatoria `X-Aduana-Token`.
* **Escritorio (PyWebView):** Comunicación directa a través de la API puente nativa `window.pywebview.api`, ejecutándose en hilo local desacoplado, sin exponer puertos a la red local y consumiendo menos de 60 MB de memoria RAM.
* **Cero CDNs:** Todo el CSS, fuentes del sistema e iconos son 100% locales en `static/` (Air-Gapped compliant).
