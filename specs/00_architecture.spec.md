# 00 — Arquitectura Backend (estructura base)

**Estado:** estructura creada; lógica por gatillos (PROMPT_MAESTRO Parte 4).

## Capas y dependencias (solo hacia abajo)
`app/` (Litestar, DTOs, DI) → `pipeline/` (etapas 0–5, LLM, orquestador) → `core/` (contexto, crypto, bóveda, protocolos, config, errores).

## Invariantes globales
- `raw_input` y mapa token→PII solo en `EphemeralVault` (RAM, TTL 180 s, `zeroize`).
- Ningún log, repr ni mensaje de error contiene texto ciudadano (DTOs de entrada redactan `__repr__`).
- Sin `random`; criptografía solo StdLib; sin FastAPI.
- Llaves (`server_master_key`, `institution_salt`) en RAM, fuera de `repr`.
- Persistencia detrás de `StorageRepositoryProtocol`.

## Decisiones tras revisión (Code Reviewer + Security Architect + Codex)
- **Llaves:** `KeyRing` único (`ADUANA_MASTER_KEY`) con subllaves por dominio; se elimina del entorno al leerse. Sin ella: llave y ledger efímeros (modo demo).
- **Ledger:** hash y HMAC sobre payload canónico JSON de TODOS los campos; `key_id` por bloque; índices contiguos, génesis y `ChainAnchor` contra truncado de cola; la justificación de override solo persiste como hash.
- **Pipeline:** stage0 calcula `blind_citizen_id` y rate-guard antes de SHIELD; SHIELD normaliza (NFKC, zero-width) primero; `BlockedPacket` y `LedgerEntry` resuelven trámites bloqueados y la circularidad paquete→recibo.
- **API:** token `X-Aduana-Token` + `Content-Type: application/json` estricto, `AllowedHosts` loopback, CSP y cabeceras, DTOs estrictos, cuerpo ≤ 64 KB, OpenAPI deshabilitado, `tamper-sim` solo con `ADUANA_DEMO_MODE=1` y sobre copia en RAM.
- **Operación:** `create_app` sin efectos de import; Granian `factory=True`, `workers=1`.
- **Pendiente de decisión:** autenticación institucional (OIDC/LDAP) y `actor_id` en el bloque; CA-06 debe redefinirse (cambio con circuito abierto vs. timeout en frío).

## Mapa gatillo → módulos
| Gatillo | Módulos | Spec | CA |
|---|---|---|---|
| 0 | core/crypto, core/ephemeral_vault | 00_kernel | CA-05 |
| 1 | stage0_consent, stage1_shield | 01_shield | CA-01 |
| 2 | stage2_guard_in, stage3_guard_out | 02_guardian | CA-02 |
| 3 | stage4_ledger | 03_ledger | CA-03 |
| 4 | stage5_explica | 04_explica | CA-04 |
| 5 | llm_adapter | 05_interconnect | CA-06 |
| 6 | orchestrator, app/controllers | — | todos |
| 7 | app/desktop | — | CA-06 |

## Endpoints (`/api/v1`)
`POST gateway/process`, `POST shield/inspect`, `GET ledger/verify`, `POST ledger/tamper-sim`, `GET metrics/benchmark`, `GET health/system`. Pendientes responden 501.
