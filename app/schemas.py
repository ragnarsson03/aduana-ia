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
