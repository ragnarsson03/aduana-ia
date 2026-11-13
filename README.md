# 🛡️ Aduana IA: Pasarela Soberana de Gobernanza y Seguridad Zero-Trust
## Arquitectura Python 2026 — Servidor Litestar + Escritorio PyWebView + Criptografía Pura

> **Ruta Oficial:** Hackathon UNETI IA 2026 $\rightarrow$ *Venezuela Innova*  
> **Documentación del Proyecto:** [SPEC.md](SPEC.md) (Especificación Formal SDD) · [PROMPT_MAESTRO.md](PROMPT_MAESTRO.md) (Kernel para Agentes IA) · [Licencia GNU GPL v3](LICENSE)

---

## 🎯 Qué hace

**Aduana IA** es una pasarela obligatoria de ciberseguridad defensiva, anonimización soberana y auditoría matemática (*AI Governance & Security Gateway*) por la que transita toda interacción entre ciudadanos o funcionarios públicos y modelos de Inteligencia Artificial.

Resuelve cuatro riesgos críticos de la administración pública venezolana:
1. **Exfiltración de PII Ciudadano:** intercepta y anonimiza Cédulas, RIFs (validando Módulo 11 SENIAT), teléfonos, cuentas de 20 dígitos y datos médicos antes de que cualquier texto salga hacia el LLM.
2. **Manipulación Adversaria (*Prompt Injection / Jailbreak*):** neutraliza ataques mediante normalización Unicode `NFKC`, barrera léxica, delimitadores XML y *Canary Tokens* dinámicos HMAC por transacción.
3. **Opacidad Algorítmica ("Caja Negra"):** separa la redacción del LLM del cálculo de elegibilidad; un modelo de Regresión Logística *White-Box* calcula la prioridad y genera valores SHAP lineales transparentes con supervisión humana vinculante (*Human-in-the-Loop*).
4. **Vulnerabilidad de Registros de Auditoría:** sella cada trámite en un Ledger inmutable con doble sello (`SHA-256` encadenado + `HMAC-SHA256` de servidor), detectando en milisegundos cualquier intento de sabotaje en base de datos.

```text
                        ┌─────────────────────────────────────────────────────────────┐
                        │                PERÍMETRO SOBERANO (ADUANA IA)               │
Ciudadano /             │                                                             │
Funcionario ──[HTTP]────► [0. CONSENT] ──► [1. SHIELD] ──► [2. GUARD-IN]              │
                        │                       │                │                    │
                        │              (Bóveda RAM Efímera)      ▼                    │
                        │              (Cero PII en Disco) [Conector Agnóstico]       │
                        │                       │                │                    │
                        │                       ▼                ▼                    │
                        │  [4. LEDGER] ◄── [5. EXPLICA] ◄── [3. GUARD-OUT] ◄── [LLM]  │
                        └───────┬───────────────┬─────────────────────────────────────┘
                                │               │
                                ▼               ▼
                     🔍 Panel Contraloría   🖥️ Panel Funcionario + Recibo Ciudadano
```

---

## 💻 Cómo se instala

Aduana IA está construida en **Python 3.11+** y funciona de forma idéntica en servidores institucionales (Linux / Windows Server) y en estaciones de trabajo de funcionarios (Windows 10/11 y Canaima GNU/Linux), consumiendo menos de 60 MB de RAM.

### 1. Clonar el repositorio
```bash
git clone https://github.com/ragnarsson03/aduana-ia.git
cd aduana-ia
```

### 2. Crear entorno virtual e instalar dependencias
```bash
python3 -m venv .venv
source .venv/bin/activate       # En Linux
# En Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Ejecutar la suite de verificación SDD (`CA-01` a `CA-06`)
```bash
pytest -v
```

---

## 🚀 Cómo se usa

Aduana IA cuenta con **dos modos de ejecución nativos**:

### Modo A: Servidor Web Institucional (Litestar 2026)
Inicia la pasarela como servicio API de alta concurrencia impulsado por **Litestar** y el runner ASGI de alto rendimiento **Granian**:
```bash
# Iniciar servidor Litestar
python -m app.server
# O utilizando el runner Granian directamente:
granian --interface asgi --factory --workers 1 app.server:create_app --host 127.0.0.1 --port 8000
```
- **Seguridad:** escucha solo en loopback; un host remoto exige `ADUANA_ALLOW_REMOTE=1` (más TLS y autenticación). `workers=1` es obligatorio (bóveda, llaves y rate-guard viven en el proceso). Las rutas `/api/v1/*` exigen `X-Aduana-Token` (`ADUANA_API_TOKEN` o generado al arrancar).
- **Llaves:** con `ADUANA_MASTER_KEY` (hex, ≥ 32 bytes) el ledger es persistente y verificable entre reinicios; sin ella, llave y ledger efímeros (modo demo). `ADUANA_DEMO_MODE=1` habilita `/api/v1/ledger/tamper-sim` (siempre sobre copia en RAM).
- **Panel Web Unificado:** abre `http://127.0.0.1:8000` en tu navegador.
- **Documentación OpenAPI:** deshabilitada (su UI cargaba CDNs externos; incompatible con Air-Gapped).

### Modo B: Aplicación de Escritorio Nativa (PyWebView)
Para funcionarios en estaciones de trabajo de ministerios o alcaldías (Windows 10/11 o Linux) sin requerir navegador abierto ni configuraciones de red:
```bash
# Lanzar ventana nativa de escritorio
python -m app.desktop

# O en Windows con doble clic:
iniciar_escritorio.bat
```
*PyWebView abre una ventana de escritorio compacta, acelerada por hardware nativo y con cero sobrecarga de Electron.*

---

## 🏛️ Arquitectura Técnica (Python 2026)

| Módulo / Capa | Tecnología | Función en Aduana IA |
|---|---|---|
| **Servidor API Web** | **Litestar 2.10+ (ASGI) + Granian** | Framework moderno 2026 con tipado estricto nativo, inyección de dependencias desacoplada y serialización ultrarrápida (desterrando la deuda técnica de FastAPI 2018). |
| **Aplicación de Escritorio** | **PyWebView 5.1+** | Ventana nativa de escritorio para funcionarios en Windows/Linux con consumo menor a 60 MB de RAM. |
| **Criptografía Backend** | **hashlib + hmac + secrets (StdLib)** | Doble sello SHA-256 + HMAC-SHA256, índices ciegos de privacidad, Canaries dinámicos y Módulo 11 SENIAT sin dependencias compiladas externas. |
| **Almacenamiento Restrictivo** | **EphemeralVault (RAM) + SQLite3 / Postgres** | Memoria volátil con TTL de 180s y purga `zeroize`. Base de datos endurecida con directivas `WAL`, `secure_delete=ON` y triggers SQL `BEFORE UPDATE/DELETE`. |
| **Explicabilidad Algorítmica** | **EXPLICA (White-Box Determínico)** | Regresión Logística con valores SHAP lineales ($\phi_j = \beta_j(x_j - \mu_j)$), error de reconstrucción $< 10^{-9}$ y cero llamadas a `random()`. |
| **Interfaz Dual Offline-First** | **HTML5 + CSS Moderno + Vanilla JS** | Servida por Litestar y embebida por PyWebView. Funciona al 100% desconectada de internet (Air-Gapped, sin CDNs). |

### Estructura Limpia del Repositorio (SDD)
```text
aduana-ia/
├── SPEC.md                    # Especificación Formal SDD y Declaración de Uso de IA
├── PROMPT_MAESTRO.md          # Master Agent Kernel v3.0 (Reglas, Contratos y Gatillos SDD)
├── README.md                  # Presentación oficial, instalación y uso (Este archivo)
├── requirements.txt           # Dependencias Python 2026 (Litestar, Granian, PyWebView, msgspec)
├── LICENSE                    # Licencia Libre GNU General Public License v3.0
├── .cursorrules               # Reglas de desarrollo cargables por agentes
├── .gitignore                 # Exclusión de venvs, bases de datos locales, logs y temporales
├── specs/                     # Especificaciones formales por componente (01_shield a 05_interconnect)
├── core/                      # Núcleo de seguridad y almacenamiento restrictivo
│   ├── context.py             # Dataclass AduanaPacket inmutable (@dataclass(frozen=True, slots=True))
│   ├── crypto.py              # SHA-256 canónico, HMAC-SHA256, Módulo 11 SENIAT, Canary y Blind Index
│   └── ephemeral_vault.py     # Bóveda volátil en RAM con TTL 180s y destrucción segura zeroize()
├── pipeline/                  # Etapas verticales del pipeline de seguridad
│   ├── stage1_shield.py       # Detección PII venezolano + Módulo 11 RIF + Enmascaramiento consistente
│   ├── stage2_guard_in.py     # Normalización Unicode NFKC + Anti-evasión Base64 + Sandbox XML + Canary
│   ├── stage3_guard_out.py    # Detección de fuga de Canary + Re-inspección PII residual + Anti-XSS
│   ├── stage4_ledger.py       # Motor SQLite endurecido + Triggers de inmutabilidad + verify_chain()
│   ├── stage5_explica.py      # Inferencia logística + Contribuciones directas + Valores SHAP Lineales
│   └── llm_adapter.py         # Adaptador multi-modelo (Ollama local, OpenAI cloud y Fallback offline)
├── app/                       # Puntos de entrada de la aplicación
│   ├── server.py              # Aplicación Servidor Web moderna sobre Litestar 2.10+
│   └── desktop.py             # Aplicación de Escritorio nativa sobre PyWebView 5.1+
├── static/                    # Interfaz unificada offline-first (Panel Funcionario + Panel Auditoría)
├── data/                      # Dataset sintético de trámites y Benchmark de 100 ataques adversarios
├── tests/                     # Suite de pruebas SDD obligatorias por Criterio de Aceptación (CA-01 a CA-06)
└── docs/                      # Ingeniería de Requisitos (SRS), Modelo de Negocio GovTech y Guía Ministerial
```

---

## 🧪 Matriz de Verificación SDD (`pytest`)

| ID | Componente | Criterio Verificable | Umbral Exigido |
|:---:|---|---|:---:|
| **CA-01** | `SHIELD` | Enmascara Cédula, RIF (validado Módulo 11), teléfono, cuenta de 20 dígitos y condición médica sensible en RAM. | $100\%$ detección en $< 20\text{ ms}$. |
| **CA-02** | `GUARDIÁN` | Evalúa 100 prompts adversarios (`data/attack_benchmark.json`) y bloquea fuga de Canary y evasiones Base64. | $\text{TPR} \ge 88\%$, $\text{FPR} \le 4\%$ en $< 25\text{ ms}$. |
| **CA-03** | `LEDGER` | `/api/v1/ledger/verify` detecta cualquier alteración en SQLite identificando el bloque exacto y causa. | Detección $100\%$ en $< 50\text{ ms}$. |
| **CA-04** | `EXPLICA` | Calcula probabilidad sigmoide y SHAP lineal exacto sin generadores aleatorios. | Error de reconstrucción $< 10^{-9}$; cero `random()`. |
| **CA-05** | `STORAGE` | Auditoría forense en disco de archivos `.db` y logs tras procesar solicitudes simuladas. | **$0$ bytes** de PII en texto plano. |
| **CA-06** | `RESILIENCE` | Caída o timeout de modelo externo conmuta automáticamente al generador institucional determinista. | Conmutación en $< 100\text{ ms}$; trámite sellado. |

---

## 📜 Declaración Ética y Enlaces Oficiales

- **Alineación con el Banco de Ideas Oficial:** #18 (El Guardián), #17 (Ledger Inmutable), #5 (Explicabilidad Algorítmica), #6 y #8 (Anonimización y Consentimiento / Shield).
- **Marco Jurídico de Referencia:** Constitución de la República Bolivariana de Venezuela (Arts. 28 y 60), Ley de Infogobierno y Ley Especial contra Delitos Informáticos.
- **Especificación Formal Completa:** [SPEC.md](SPEC.md)
- **Kernel para Agentes IA:** [PROMPT_MAESTRO.md](PROMPT_MAESTRO.md)
- **Ingeniería y Negocio GovTech:** [docs/Ingenieria Y Negocio Aduana IA.md](docs/Ingenieria%20Y%20Negocio%20Aduana%20IA.md)
- **Licencia:** [GNU General Public License v3.0](LICENSE)
