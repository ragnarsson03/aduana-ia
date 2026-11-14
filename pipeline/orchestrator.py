"""Orquestador del pipeline completo (POST /api/v1/gateway/process).

Orden: stage0 (blind id, rate-guard, consentimiento) -> shield -> guard_in -> LLM
-> guard_out -> explica -> ledger. ``vault.zeroize`` siempre en ``finally``.
Un trámite rechazado produce ``BlockedPacket`` y se sella igualmente en el ledger.
``request_id`` lo genera el servidor (``secrets.token_urlsafe(16)``), nunca el cliente.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

from core import crypto
from core.context import (
    AduanaPacket,
    BlockedPacket,
    CitizenConsent,
    LedgerEntry,
    RecommendationType,
    ShieldMeta,
)
from core.ephemeral_vault import EphemeralVault
from core.errors import (
    ConsentError,
    ShieldResidualPiiError,
)
from core.keyring import KeyRing
from core.protocols import LLMGatewayProtocol, RateGuardProtocol, StorageRepositoryProtocol
from pipeline.stage0_consent import validate_consent
from pipeline.stage1_shield import shield
from pipeline.stage2_guard_in import guard_in
from pipeline.stage3_guard_out import guard_out
from pipeline.stage4_ledger import compute_attachment_audit_hash, seal_entry
from pipeline.stage5_explica import explain


@dataclass(frozen=True, slots=True)
class GatewayInput:
    raw_text: str
    citizen_cedula: str
    consent_granted: bool
    purpose_code: str
    features: dict[str, float]
    human_decision: RecommendationType | None = None
    override_justification: str | None = None
    attachment_sha256: str | None = None
    attachment_size_bytes: int = 0
    user_role: str = "analista"
    audit_action: str = "CHAT_IA_STREAM_UPLOAD"
    pre_shielded_text: str | None = None
    pre_shielded_meta: ShieldMeta | None = None
    request_id_override: str | None = None

    def __repr__(self) -> str:  # Zero-Leak: nunca imprimir PII
        return "GatewayInput(<redacted>)"


class GatewayPipeline:
    def __init__(
        self,
        keys: KeyRing,
        vault: EphemeralVault,
        repo: StorageRepositoryProtocol,
        llm: LLMGatewayProtocol,
        rate_guard: RateGuardProtocol,
    ) -> None:
        self._keys = keys
        self._vault = vault
        self._repo = repo
        self._llm = llm
        self._rate_guard = rate_guard

    async def process(self, data: GatewayInput) -> AduanaPacket | BlockedPacket:
        request_id = data.request_id_override or secrets.token_urlsafe(16)
        timestamp_utc = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            # 1. Blind Citizen ID
            blind_id = crypto.blind_citizen_id(self._keys, data.citizen_cedula)

            # 2. Rate guard: si excede tasa lanza RateLimitError (no se sella en ledger)
            self._rate_guard.check(blind_id)

            # 3. Stage 0: Consentimiento explícito
            consent: CitizenConsent | None = None
            try:
                consent = validate_consent(
                    request_id=request_id,
                    granted=data.consent_granted,
                    purpose_code=data.purpose_code,
                    timestamp_utc=timestamp_utc,
                    blind_citizen_id=blind_id,
                )
            except ConsentError:
                p_hash = (
                    compute_attachment_audit_hash(
                        file_sha256=data.attachment_sha256,
                        blind_citizen_id=blind_id,
                        user_role=data.user_role,
                        timestamp_utc=timestamp_utc,
                        action=data.audit_action,
                    )
                    if data.attachment_sha256 is not None
                    else crypto.sha256_hex(b"")
                )
                entry = LedgerEntry(
                    request_id=request_id,
                    timestamp_utc=timestamp_utc,
                    blind_citizen_id=blind_id,
                    payload_hash=p_hash,
                    security_verdict="BLOCKED_NO_CONSENT",
                    model_recommendation="BLOQUEADO_SEGURIDAD",
                    human_decision="BLOQUEADO_SEGURIDAD",
                    human_override=False,
                    citizen_receipt_code=f"REC-{request_id}",
                    override_justification_hash=None,
                )
                receipt = seal_entry(entry, self._repo, keys=self._keys)
                return BlockedPacket(
                    request_id=request_id,
                    timestamp_utc=timestamp_utc,
                    policy_status="BLOCKED_NO_CONSENT",
                    consent=None,
                    ledger=receipt,
                )

            # 4. Stage 1: SHIELD (Anonimización Soberana o flujo ya anonimizado por chunks)
            if data.pre_shielded_text is not None and data.pre_shielded_meta is not None:
                masked_text = data.pre_shielded_text
                shield_meta = data.pre_shielded_meta
            else:
                try:
                    masked_text, shield_meta = shield(
                        request_id,
                        data.raw_text,
                        vault=self._vault,
                        blind_citizen_id=blind_id,
                    )
                except ShieldResidualPiiError:
                    p_hash = (
                        compute_attachment_audit_hash(
                            file_sha256=data.attachment_sha256,
                            blind_citizen_id=blind_id,
                            user_role=data.user_role,
                            timestamp_utc=timestamp_utc,
                            action=data.audit_action,
                        )
                        if data.attachment_sha256 is not None
                        else crypto.sha256_hex(b"")
                    )
                    entry = LedgerEntry(
                        request_id=request_id,
                        timestamp_utc=timestamp_utc,
                        blind_citizen_id=blind_id,
                        payload_hash=p_hash,
                        security_verdict="BLOCKED_PII_LEAK",
                        model_recommendation="BLOQUEADO_SEGURIDAD",
                        human_decision="BLOQUEADO_SEGURIDAD",
                        human_override=False,
                        citizen_receipt_code=f"REC-{request_id}",
                        override_justification_hash=None,
                    )
                    receipt = seal_entry(entry, self._repo, keys=self._keys)
                    return BlockedPacket(
                        request_id=request_id,
                        timestamp_utc=timestamp_utc,
                        policy_status="BLOCKED_PII_LEAK",
                        consent=consent,
                        ledger=receipt,
                    )

            # 5. Stage 2: GUARD-IN (Sandbox XML y Canary dinámico HMAC)
            prompt, guard_in_res = guard_in(request_id, masked_text, keys=self._keys)
            if not guard_in_res.allowed:
                p_hash = (
                    compute_attachment_audit_hash(
                        file_sha256=data.attachment_sha256,
                        blind_citizen_id=blind_id,
                        user_role=data.user_role,
                        timestamp_utc=timestamp_utc,
                        action=data.audit_action,
                    )
                    if data.attachment_sha256 is not None
                    else crypto.sha256_hex(masked_text.encode())
                )
                entry = LedgerEntry(
                    request_id=request_id,
                    timestamp_utc=timestamp_utc,
                    blind_citizen_id=blind_id,
                    payload_hash=p_hash,
                    security_verdict=guard_in_res.policy_status,
                    model_recommendation="BLOQUEADO_SEGURIDAD",
                    human_decision="BLOQUEADO_SEGURIDAD",
                    human_override=False,
                    citizen_receipt_code=f"REC-{request_id}",
                    override_justification_hash=None,
                )
                receipt = seal_entry(entry, self._repo, keys=self._keys)
                return BlockedPacket(
                    request_id=request_id,
                    timestamp_utc=timestamp_utc,
                    policy_status=guard_in_res.policy_status,
                    consent=consent,
                    ledger=receipt,
                )

            # 6. Intercambio con LLM mediante Circuit Breaker
            llm_res = await self._llm.exchange(prompt)

            # 7. Stage 3: GUARD-OUT (Anti-fuga de canary, anti-XSS, PII residual y rehidratación)
            token_map = self._vault.get_map(request_id)
            guard_out_res = guard_out(
                llm_res.raw_response,
                canary_token=guard_in_res.canary_token,
                token_map=token_map,
            )
            if not guard_out_res.allowed:
                p_hash = (
                    compute_attachment_audit_hash(
                        file_sha256=data.attachment_sha256,
                        blind_citizen_id=blind_id,
                        user_role=data.user_role,
                        timestamp_utc=timestamp_utc,
                        action=data.audit_action,
                    )
                    if data.attachment_sha256 is not None
                    else crypto.sha256_hex(masked_text.encode())
                )
                entry = LedgerEntry(
                    request_id=request_id,
                    timestamp_utc=timestamp_utc,
                    blind_citizen_id=blind_id,
                    payload_hash=p_hash,
                    security_verdict=guard_out_res.policy_status,
                    model_recommendation="BLOQUEADO_SEGURIDAD",
                    human_decision="BLOQUEADO_SEGURIDAD",
                    human_override=False,
                    citizen_receipt_code=f"REC-{request_id}",
                    override_justification_hash=None,
                )
                receipt = seal_entry(entry, self._repo, keys=self._keys)
                return BlockedPacket(
                    request_id=request_id,
                    timestamp_utc=timestamp_utc,
                    policy_status=guard_out_res.policy_status,
                    consent=consent,
                    ledger=receipt,
                )

            # 8. Stage 5: EXPLICA (Regresión logística white-box y SHAP lineal)
            explica_res = explain(
                data.features,
                human_decision=data.human_decision,
                override_justification=data.override_justification,
            )

            # 9. Stage 4: LEDGER (Sellado inmutable con doble hash y firma HMAC)
            override_hash = None
            if explica_res.human_override and data.override_justification:
                override_hash = self._keys.hmac_hex(
                    "justification", data.override_justification.strip().encode()
                )

            if data.attachment_sha256 is not None:
                payload_h = compute_attachment_audit_hash(
                    file_sha256=data.attachment_sha256,
                    blind_citizen_id=blind_id,
                    user_role=data.user_role,
                    timestamp_utc=timestamp_utc,
                    action=data.audit_action,
                )
            else:
                payload_h = crypto.sha256_hex(guard_out_res.sanitized_response.encode())
            receipt_code = f"REC-{request_id}"

            entry = LedgerEntry(
                request_id=request_id,
                timestamp_utc=timestamp_utc,
                blind_citizen_id=blind_id,
                payload_hash=payload_h,
                security_verdict="CLEAN",
                model_recommendation=explica_res.model_recommendation,
                human_decision=explica_res.human_decision,
                human_override=explica_res.human_override,
                citizen_receipt_code=receipt_code,
                override_justification_hash=override_hash,
            )
            receipt = seal_entry(entry, self._repo, keys=self._keys)

            return AduanaPacket(
                request_id=request_id,
                timestamp_utc=timestamp_utc,
                masked_text=masked_text,
                consent=consent,
                shield=shield_meta,
                guard_in=guard_in_res,
                llm=llm_res,
                guard_out=guard_out_res,
                explica=explica_res,
                ledger=receipt,
            )
        finally:
            # Destrucción criptográfica incondicional en RAM (Zero-PII)
            self._vault.zeroize(request_id)
