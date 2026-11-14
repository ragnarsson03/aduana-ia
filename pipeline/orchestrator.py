"""Orquestador del pipeline completo (POST /api/v1/gateway/process).

Orden: stage0 (blind id, rate-guard, consentimiento) -> shield -> guard_in -> LLM
-> guard_out -> explica -> ledger. ``vault.zeroize`` siempre en ``finally``.
Un trámite rechazado produce ``BlockedPacket`` y se sella igualmente en el ledger.
``request_id`` lo genera el servidor (``secrets.token_urlsafe(16)``), nunca el cliente.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.context import AduanaPacket, BlockedPacket, RecommendationType
from core.ephemeral_vault import EphemeralVault
from core.keyring import KeyRing
from core.protocols import LLMGatewayProtocol, RateGuardProtocol, StorageRepositoryProtocol


@dataclass(frozen=True, slots=True)
class GatewayInput:
    raw_text: str
    citizen_cedula: str
    consent_granted: bool
    purpose_code: str
    features: dict[str, float]
    human_decision: RecommendationType | None = None
    override_justification: str | None = None

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
        raise NotImplementedError("Gatillo 6: GatewayPipeline.process pendiente")
