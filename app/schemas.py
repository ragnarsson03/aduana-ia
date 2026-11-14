"""DTOs de la API (msgspec). Estrictos: sin campos extra, con límites; entradas con PII
redactan su ``repr``. Ningún DTO de salida incluye ``raw_response`` ni el canary."""

from __future__ import annotations

from typing import Annotated, Literal

import msgspec

from core.config import MAX_RAW_TEXT_CHARS, OVERRIDE_MAX_JUSTIFICATION_CHARS
from core.context import ChainFailureReason, PolicyStatus, RecommendationType

RawText = Annotated[str, msgspec.Meta(min_length=1, max_length=MAX_RAW_TEXT_CHARS)]
Cedula = Annotated[str, msgspec.Meta(pattern=r"^[A-Za-z]?-?[0-9.]{5,12}$", max_length=20)]
PurposeCode = Annotated[str, msgspec.Meta(pattern=r"^[A-Z0-9_]{3,32}$")]
Features = Annotated[dict[str, float], msgspec.Meta(max_length=32)]
Justification = Annotated[str, msgspec.Meta(max_length=OVERRIDE_MAX_JUSTIFICATION_CHARS)]
TamperScenario = Literal[
    "flip_payload_bit", "recompute_sha_without_key", "break_prev_link", "flip_override"
]


class ConsentIn(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    granted: bool
    purpose_code: PurposeCode


class GatewayProcessRequest(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    raw_text: RawText
    citizen_cedula: Cedula
    consent: ConsentIn
    features: Features
    human_decision: RecommendationType | None = None
    override_justification: Justification | None = None

    def __repr__(self) -> str:  # Zero-Leak
        return "GatewayProcessRequest(<redacted>)"


class GatewayProcessResponse(msgspec.Struct, frozen=True):
    request_id: str
    timestamp_utc: str
    policy_status: PolicyStatus
    masked_text: str | None
    sanitized_response: str
    ai_generated_notice: bool
    model_recommendation: RecommendationType
    human_decision: RecommendationType
    human_override: bool
    citizen_receipt_code: str
    block_index: int
    chain_verified: bool
    latency_ms: float
    probability_score: float | None = None
    linear_shap_values: dict[str, float] | None = None


class ShieldInspectRequest(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    raw_text: RawText

    def __repr__(self) -> str:  # Zero-Leak
        return "ShieldInspectRequest(<redacted>)"


class ShieldInspectResponse(msgspec.Struct, frozen=True):
    masked_text: str
    pii_count: int
    detected_types: tuple[str, ...]
    rif_mod11_verified: bool | None
    latency_ms: float


class LedgerVerifyResponse(msgspec.Struct, frozen=True):
    is_valid: bool
    blocks_checked: int
    corrupted_block_index: int | None
    failure_reason: ChainFailureReason | None
    head_hash: str | None
    latency_ms: float


class TamperSimRequest(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    scenario: TamperScenario
    block_index: Annotated[int, msgspec.Meta(ge=0)]  # 0 = bloque génesis, también simulable


class TamperSimResponse(msgspec.Struct, frozen=True):
    simulated: bool  # siempre True: opera sobre una copia en RAM, nunca sobre el ledger real
    scenario: TamperScenario
    tampered_block_index: int
    detection: LedgerVerifyResponse


class BenchmarkResponse(msgspec.Struct, frozen=True):
    total: int
    tpr: float
    fpr: float
    mean_latency_ms: float
    canary_leaks_neutralized_pct: float


class HealthResponse(msgspec.Struct, frozen=True):
    status: str
    ledger_mode: Literal["ephemeral", "persistent"]
    implemented_stages: tuple[str, ...]


class LoginRequest(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    cedula: Annotated[str, msgspec.Meta(min_length=5, max_length=128)]
    password: Annotated[str, msgspec.Meta(min_length=1, max_length=128)]

    def __repr__(self) -> str:  # Zero-Leak
        return "LoginRequest([REDACTED])"


class LoginUserOut(msgspec.Struct, frozen=True):
    id: str
    username: str
    full_name: str
    short_name: str
    avatar_text: str
    role: Literal["analista", "administrador", "auditor"]
    role_label: str
    clearance_level: str
    entity: str
    department: str
    permissions: tuple[str, ...]
    default_tab: Literal["pasarela", "ledger"]
    allowed_tabs: tuple[str, ...]


class LoginResponse(msgspec.Struct, frozen=True):
    authenticated: bool
    session_token: str
    token_type: Literal["Bearer"]
    expires_in_seconds: int
    user: LoginUserOut
    block_index: int
    citizen_receipt_code: str

    def __repr__(self) -> str:  # Zero-Leak
        return "LoginResponse([REDACTED])"


class SessionStatusResponse(msgspec.Struct, frozen=True):
    authenticated: bool
    user_id: str
    role: Literal["analista", "administrador", "auditor"]
    jti: str
    expires_at_epoch: int
    user: LoginUserOut

    def __repr__(self) -> str:  # Zero-Leak
        return "SessionStatusResponse([REDACTED])"


class LogoutResponse(msgspec.Struct, frozen=True):
    revoked: bool
    jti: str

    def __repr__(self) -> str:  # Zero-Leak
        return "[REDACTED_CHAT_PAYLOAD]"


class ChatIAUploadRequest(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    prompt: RawText
    citizen_cedula: Cedula = "V-12345678"
    purpose_code: PurposeCode = "CHAT_IA_CONSULTA"
    consent_granted: bool = True
    file_name: Annotated[str, msgspec.Meta(min_length=1, max_length=120)] | None = None
    file_mime_type: Annotated[str, msgspec.Meta(min_length=3, max_length=64)] | None = None
    file_content_b64: Annotated[str, msgspec.Meta(min_length=1, max_length=48_000)] | None = None
    features: Features | None = None
    human_decision: RecommendationType | None = None
    override_justification: Justification | None = None

    def __repr__(self) -> str:  # Zero-Leak
        return "[REDACTED_CHAT_PAYLOAD]"


class ChatIAResponse(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    request_id: str
    timestamp_utc: str
    policy_status: PolicyStatus
    masked_prompt: str | None
    sanitized_response: str
    restored_response: str
    ai_generated_notice: bool
    pii_count: int
    detected_types: tuple[str, ...]
    rif_mod11_verified: bool | None
    file_name_sanitized: str | None
    file_sha256: str | None
    file_size_bytes: int
    model_recommendation: RecommendationType
    human_decision: RecommendationType
    human_override: bool
    probability_score: float | None
    linear_shap_values: dict[str, float] | None
    citizen_receipt_code: str
    block_index: int
    chain_verified: bool
    latency_ms: float

    def __repr__(self) -> str:  # Zero-Leak
        return "[REDACTED_CHAT_PAYLOAD]"

