"""Contrato de datos único de Aduana IA (``AduanaPacket`` v2.1).

Fase 2 del bucle SDD: tipos inmutables. ``raw_input`` NUNCA forma parte de
estos objetos: el texto crudo vive solo en ``EphemeralVault`` (RAM).

Desviaciones documentadas respecto a PROMPT_MAESTRO.md §2.1:
- Colecciones ``tuple`` / ``MappingProxyType`` (inmutabilidad real en profundidad).
- ``LedgerEntry`` (datos a sellar) separa el "antes del sello" de ``LedgerReceipt``
  (rompe la circularidad paquete -> recibo) y ``BlockedPacket`` representa trámites
  rechazados antes de completar el pipeline.
- ``LedgerBlock`` guarda ``override_justification_hash`` (nunca el texto) y ``key_id``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal

PolicyStatus = Literal[
    "CLEAN",
    "BLOCKED_INJECTION",
    "BLOCKED_CANARY_LEAK",
    "BLOCKED_NO_CONSENT",
    "BLOCKED_PII_LEAK",
]

RecommendationType = Literal[
    "PRIORIDAD_ALTA",
    "REVISION_ESTANDAR",
    "RECAUDOS_INCOMPLETOS",
    "BLOQUEADO_SEGURIDAD",
]

AdapterMode = Literal[
    "LOCAL_OLLAMA",
    "HYBRID_OPENAI",
    "OFFLINE_DETERMINISTIC_FALLBACK",
]

ChainFailureReason = Literal[
    "HASH_MISMATCH",
    "PREV_HASH_LINK_BROKEN",
    "HMAC_SIGNATURE_FORGED",
    "GENESIS_LINK_BROKEN",
    "INDEX_GAP",
    "TAIL_TRUNCATED",
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
    detected_types: tuple[str, ...]
    rif_mod11_verified: bool | None  # None = sin RIF; False si alguno falla
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
    matched_patterns: tuple[str, ...]
    policy_status: PolicyStatus
    latency_ms: float


@dataclass(frozen=True, slots=True)
class LLMExchangeResult:
    adapter_mode: AdapterMode
    ai_generated_notice: bool
    circuit_breaker_tripped: bool
    prompt_sent_hash: str
    raw_response: str  # interno: NUNCA se serializa a la API (usar sanitized_response)
    latency_ms: float


@dataclass(frozen=True, slots=True)
class GuardOutResult:
    allowed: bool
    canary_leaked: bool
    residual_pii_detected: bool
    xss_or_code_injected: bool
    unverified_claims_flag: bool
    sanitized_response: str
    policy_status: PolicyStatus
    latency_ms: float


def _freeze(mapping: Mapping[str, float]) -> Mapping[str, float]:
    return MappingProxyType(dict(mapping))


@dataclass(frozen=True, slots=True)
class ExplicaResult:
    model_type: str
    logit_z: float
    probability_score: float
    intercept_b0: float
    feature_values: Mapping[str, float]
    feature_contributions_bx: Mapping[str, float]
    linear_shap_values: Mapping[str, float]
    logit_reconstruction_error: float
    model_recommendation: RecommendationType
    human_decision: RecommendationType
    human_override: bool
    override_justification: str | None = None  # solo RAM; el ledger guarda su hash

    def __post_init__(self) -> None:
        for name in ("feature_values", "feature_contributions_bx", "linear_shap_values"):
            object.__setattr__(self, name, _freeze(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    """Datos a sellar (previos al hash). Sin PII; ``payload_hash`` cubre el contenido saneado."""

    request_id: str
    timestamp_utc: str
    blind_citizen_id: str
    payload_hash: str
    security_verdict: PolicyStatus
    model_recommendation: RecommendationType
    human_decision: RecommendationType
    human_override: bool
    citizen_receipt_code: str
    override_justification_hash: str | None = None


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


@dataclass(frozen=True, slots=True)
class BlockedPacket:
    """Trámite rechazado antes de completar el pipeline (consentimiento, inyección, etc.)."""

    request_id: str
    timestamp_utc: str
    policy_status: PolicyStatus
    consent: CitizenConsent | None
    ledger: LedgerReceipt


@dataclass(frozen=True, slots=True)
class LedgerBlock:
    """Fila de ``ledger_blocks`` (SPEC §7 + ``key_id``). Sin PII.

    ``block_hash`` y ``hmac_signature`` cubren el payload canónico de TODOS los
    campos restantes (ver ``core.crypto.canonical_block_payload``).
    """

    block_index: int
    request_id: str
    timestamp_utc: str
    blind_citizen_id: str
    payload_hash: str
    prev_hash: str
    block_hash: str
    hmac_signature: str
    security_verdict: PolicyStatus
    model_recommendation: RecommendationType
    human_decision: RecommendationType
    human_override: bool
    citizen_receipt_code: str
    key_id: str
    override_justification_hash: str | None = None


@dataclass(frozen=True, slots=True)
class ChainAnchor:
    """Ancla externa a la tabla: detecta truncado de cola (count y último hash)."""

    count: int
    head_hash: str


@dataclass(frozen=True, slots=True)
class ChainVerification:
    """Resultado de ``verify_chain`` (RF-16)."""

    is_valid: bool
    blocks_checked: int
    corrupted_block_index: int | None = None
    failure_reason: ChainFailureReason | None = None


# --- Identidad y RBAC aduanero (specs/06_rbac_aduanero.spec.md) -------------------------------

AduanaRoleType = Literal[
    "INSPECTOR_TRIBUTARIO_SENIAT",
    "AGENTE_ADUANAL_CERTIFICADO",
    "FISCAL_ANTI_CONTRABANDO",
    "OPERADOR_LOGISTICO_ALMACEN",
    "SUPERVISOR_PUERTO_ADUANERO",
    "ANALISTA_VALORACION_ADUANERA",
]

UserStatus = Literal["ACTIVO", "SUSPENDIDO"]


@dataclass(frozen=True, slots=True)
class UsuarioAduana:
    """Usuario del sistema. NO contiene sal ni hash de contraseña ni identificador en claro:
    ``blind_identifier`` es el HMAC (Anillo 2) de la cédula o el RIF."""

    user_id: str
    codigo_usuario: str  # alias no personal (p. ej. "insp.senat.01")
    blind_identifier: str
    rol: AduanaRoleType
    estado: UserStatus
    created_utc: str
    last_login_utc: str | None = None
    failed_attempts: int = 0
    locked_until_utc: str | None = None


@dataclass(frozen=True, slots=True)
class AuthToken:
    """Token de sesión firmado (``v1.<payload>.<hmac>``). El valor no aparece en ``repr``."""

    token: str = field(repr=False)
    user_id: str
    codigo_usuario: str
    rol: AduanaRoleType
    issued_at: int
    expires_at: int
    token_id: str
