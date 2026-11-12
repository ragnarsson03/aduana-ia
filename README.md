# 🛡️ Aduana IA: Pasarela Soberana de Gobernanza y Seguridad Zero-Trust

> **Estado actual del proyecto:** Fase de Especificación ([SPEC.md](SPEC.md)) y esqueleto SDD inicial para el **Hackathon UNETI IA 2026** (implementación en curso; los umbrales técnicos descritos corresponden a objetivos de aceptación verificables).

---

## Qué hace

**Aduana IA** es una pasarela obligatoria de seguridad, anonimización y auditoría (*AI Security & Governance Gateway*) por la que transita toda interacción entre ciudadanos/funcionarios y modelos de inteligencia artificial en trámites públicos.

Atiende cuatro riesgos críticos:
1. **Exfiltración de datos personales (PII):** intercepta y tokeniza Cédulas, RIFs, teléfonos, cuentas bancarias y datos clínicos antes de enviar cualquier texto a un modelo de IA.
2. **Manipulación adversaria (*Prompt Injection / Jailbreak*):** normaliza y evalúa entradas sospechosas e inyecta *Canary Tokens* dinámicos para bloquear fugas de sistema.
3. **Opacidad algorítmica ("caja negra"):** desacopla al LLM de la decisión de prioridad mediante un modelo matemático transparente (*White-Box*) con intervención humana obligatoria (*Human-in-the-Loop*).
4. **Alteración de auditoría:** sella cada transacción en una cadena criptográfica SHA-256 + HMAC en modo *Append-Only*.

```text
Ciudadano /       ┌──────────────────────────────────────────────────────────────────┐
Funcionario ────► │ [0. CONSENT] ──► [1. SHIELD] ──► [2. GUARD-IN]                   │
                  │                       │               │                          │
                  │              (Vault Efímero)          ▼                          │
                  │              (Cero PII en D1)  [Workers AI / Fallback]           │
                  │                       │               │                          │
                  │                       ▼               ▼                          │
                  │  [4. LEDGER D1] ◄── [5. EXPLICA] ◄── [3. GUARD-OUT]              │
                  └───────┬──────────────────┬───────────────────────────────────────┘
                          ▼                  ▼
               🔍 Panel Contraloría   🖥️ Panel Funcionario + Recibo Ciudadano
```

---

## Cómo se instala

El MVP sigue la arquitectura oficial serverless del evento sobre **Cloudflare** (`Node.js >= 18`, `npm >= 9` y `Wrangler CLI`).

1. Clona el repositorio:
   ```bash
   git clone https://github.com/ragnarsson03/aduana-ia.git
   cd aduana-ia
   ```
2. Instala Wrangler globalmente (si aún no está instalado) y las dependencias del proyecto:
   ```bash
   npm install -g wrangler
   npm install
   ```
3. Inicia sesión en Cloudflare:
   ```bash
   wrangler login
   ```
4. Crea la base de datos **Cloudflare D1** y registra su `database_id` en `wrangler.jsonc` *(una vez generados `wrangler.jsonc` y `schema.sql` en la fase de implementación)*:
   ```bash
   wrangler d1 create aduana-db
   wrangler d1 execute aduana-db --local --file=schema.sql
   ```
5. Configura el secreto HMAC local (`.dev.vars`, ignorado por Git) y remoto:
   ```bash
   wrangler secret put LEDGER_HMAC_KEY
   ```
6. Levanta el entorno de desarrollo local:
   ```bash
   npm run dev
   ```

---

## Cómo se usa

1. **Ingreso y Consentimiento (`Panel del Funcionario`):** el funcionario o ciudadano introduce la solicitud del trámite y registra el consentimiento explícito (`granted`, `purpose_code`).
2. **Anonimización Determinista (`SHIELD`):** antes de llamar a cualquier modelo de IA, el sistema detecta y sustituye PII nacional (`[CEDULA_1]`, `[RIF_1]` validado con algoritmo Módulo 11 SENIAT, `[PHONE_1]`, `[CLINICAL_1]`) y genera un índice ciego irreversible (`blind_citizen_id` via HMAC-SHA256).
3. **Defensa y Resumen Asistido (`GUARD-IN` → `Workers AI` → `GUARD-OUT`):** se normaliza el texto (`NFKC`), se evalúa el riesgo de inyección, se encapsula en delimitadores XML con *Canary Token* dinámico y se genera un resumen únicamente sobre el texto sanitizado.
4. **Explicabilidad y Decisión Humana (`EXPLICA`):** un modelo de Regresión Logística *White-Box* muestra la probabilidad, contribuciones ($\beta_j x_j$) y valores SHAP lineales ($\phi_j = \beta_j(x_j - \mu_j)$). El funcionario confirma la recomendación o realiza un *override* con justificación escrita ($\ge 20$ caracteres).
5. **Auditoría Inmutable (`Panel de Contraloría` / `LEDGER`):** la transacción se sella en **Cloudflare D1** con hash encadenado SHA-256 y firma HMAC. El verificador (`/api/v1/ledger/verify`) audita toda la cadena y detecta bloque y causa exacta ante alteraciones (`HASH_MISMATCH`, `PREV_HASH_LINK_BROKEN`, `HMAC_SIGNATURE_FORGED`).

---

## Arquitectura Cloudflare usada

| Componente | Servicio Cloudflare | Función en Aduana IA |
|---|---|---|
| **Frontend Dual** | **Cloudflare Pages** (`static/`) | Panel del Funcionario y Panel de Contraloría (HTML5 + CSS local + Vanilla JS, sin CDNs externos). |
| **API y Pipeline** | **Cloudflare Pages Functions / Workers** (`functions/`, `core/`, `pipeline/`) | Ejecución en TypeScript de las 5 etapas y criptografía nativa con Web Crypto API (`crypto.subtle`) dentro del presupuesto de `10 ms` CPU. |
| **Base de Datos Ledger** | **Cloudflare D1** (`env.DB`, SQLite en el Edge) | Almacenamiento *Append-Only* en `ledger_blocks` sin PII en texto plano. |
| **Bóveda Efímera** | Memoria de ejecución / **Cloudflare KV** (`env.KV`, `expirationTtl: 180`) | Mapeo temporal de reversión de tokens cuando se requiera entre pasos de una sesión. |
| **Inferencia IA** | **Cloudflare Workers AI** (`env.AI`) | Resumen de texto previamente anonimizado con respaldo determinista ante fallos o límites de cuota. |
| **Llaves Criptográficas** | **Cloudflare Secrets** | Almacenamiento seguro de `LEDGER_HMAC_KEY` e `INSTITUTION_SALT` fuera del código fuente. |

### Estructura del Repositorio (SDD)

```text
aduana-ia/
├── SPEC.md                    # Especificación oficial y Declaración de Uso de IA (Paso 0)
├── PROMPT_MAESTRO.md          # Contrato único (AduanaPacket) y reglas para agentes SDD
├── .cursorrules               # Reglas raíz cargables por asistentes de código
├── README.md                  # Documentación técnica y guía de despliegue
├── package.json               # Configuración Node / Wrangler scripts
├── LICENSE                    # Licencia GNU GPL v3
├── .gitignore                 # Exclusión de node_modules, .wrangler, .dev.vars, *.db
├── specs/                     # Especificaciones detalladas por etapa del pipeline
├── core/                      # Tipos (AduanaPacket), configuración y bóveda efímera
├── pipeline/                  # Módulos TypeScript: Shield, Guard-In/Out, Explica, Ledger, LLM
├── functions/                 # Cloudflare Pages Functions (endpoints /api/v1/*)
├── static/                    # Interfaz web offline-first (HTML/CSS/JS local)
├── data/                      # Datasets sintéticos y benchmark auditable de 100 prompts
├── tests/                     # Pruebas automatizadas por criterio de aceptación (CA-01 a CA-06)
└── docs/                      # Documentación extendida de ingeniería y negocio
```

### Contratos Técnicos y Objetivos de Aceptación (SDD)

| ID | Etapa | Criterio Verificable (Objetivo) |
|---|---|---|
| **CA-01** | `SHIELD` | Enmascara el 100% de PII estructurado (Cédula, RIF Módulo 11 con pesos `[4,3,2,7,6,5,4,3,2]`, teléfono, cuenta 20 dígitos, clínica) en `< 20 ms` sin persistir texto plano en D1. |
| **CA-02** | `GUARD-IN` / `GUARD-OUT` | Evalúa `data/attack_benchmark.json` (50 benignos + 50 ataques) buscando $\text{TPR} \ge 88\%$, $\text{FPR} \le 4\%$ y 0% fugas de *Canary Token* ni XSS. |
| **CA-03** | `LEDGER` | `/api/v1/ledger/verify` detecta manipulaciones en D1 identificando `corrupted_block_index` y causa (`HASH_MISMATCH`, `PREV_HASH_LINK_BROKEN`, `HMAC_SIGNATURE_FORGED`). |
| **CA-04** | `EXPLICA` | Calcula $P(y=1 \mid \mathbf{x})$ con Regresión Logística determinista (cero `Math.random()`) y error de reconstrucción del *logit* $< 10^{-9}$. |
| **CA-05** | `STORAGE` | Cero ocurrencias de PII en texto plano en tablas D1 o logs de ejecución. |
| **CA-06** | `RESILIENCE` | Degradación elegante hacia modo determinista si Workers AI falla o excede tiempo límite. |

### Marco Normativo de Referencia
Proyecto diseñado conforme a principios de protección de datos, software libre y seguridad de la información: **CRBV (Arts. 28 y 60)**, **Ley de Infogobierno** (licencia libre [GNU GPL v3](LICENSE)), **Ley Especial contra Delitos Informáticos** y lineamientos de interoperabilidad **CNTI / SUSCERTE**.

---

## Uso de IA

- **Modelo utilizado:** `@cf/zai-org/glm-4.7-flash` vía **Cloudflare Workers AI** (con respaldo `@cf/meta/llama-3.1-8b-instruct` y adaptador determinista).
- **Propósito:** resumir y estructurar el contexto de solicitudes ciudadanas exclusivamente sobre texto previamente anonimizado por `SHIELD`.
- **Protección contra sesgos y decisiones autónomas:** el LLM nunca decide prioridades ni aprueba trámites. El cálculo cuantitativo corre exclusivamente en el módulo matemático transparente `EXPLICA` y la decisión final vinculante corresponde siempre al funcionario humano.
- **Declaración completa:** ver [SPEC.md](SPEC.md) (Secciones 8, 9 y Tabla de Declaración Obligatoria de Uso de IA).

---

## Enlaces

- **Especificación oficial:** [SPEC.md](SPEC.md)
- **Reglas de arquitectura SDD:** [PROMPT_MAESTRO.md](PROMPT_MAESTRO.md)
- **Licencia:** [GNU GPL v3](LICENSE)
- **Demo (Cloudflare Pages):** *Pendiente de despliegue tras fase de implementación*
- **Video demostrativo:** *Pendiente de grabación*
