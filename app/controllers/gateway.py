"""POST /api/v1/gateway/process y POST /api/v1/shield/inspect."""

from __future__ import annotations

import secrets

from litestar import Controller, Request, post
from litestar.params import JSONBody

from app.dependencies import AppState
from app.rbac_guards import SCOPE_USER_KEY, require_any_permission, require_permission
from app.schemas import (
    GatewayProcessRequest,
    GatewayProcessResponse,
    ShieldInspectRequest,
    ShieldInspectResponse,
)
from app.security import api_guard
from core.config import API_PREFIX
from core.context import BlockedPacket
from core.rbac import Permission
from pipeline.orchestrator import GatewayInput
from pipeline.stage1_shield import shield


def _authorize_gateway_action(request: Request, data: GatewayProcessRequest) -> None:
    """Con RBAC: decidir (override) exige ``tramite:override``; enviar exige ``tramite:submit``."""
    user = request.scope.get(SCOPE_USER_KEY)
    if user is None:  # RBAC apagado
        return
    is_override = data.human_decision is not None or data.override_justification is not None
    needed: Permission = "tramite:override" if is_override else "tramite:submit"
    request.app.state.aduana.identity.authorize(user, needed)


class GatewayController(Controller):
    path = f"{API_PREFIX}/gateway"
    guards = [api_guard]

    @post("/process", guards=[require_any_permission("tramite:submit", "tramite:override")])
    async def process(
        self, request: Request, data: JSONBody[GatewayProcessRequest]
    ) -> GatewayProcessResponse:
        state: AppState = request.app.state.aduana
        _authorize_gateway_action(request, data)
        gateway_in = GatewayInput(
            raw_text=data.raw_text,
            citizen_cedula=data.citizen_cedula,
            consent_granted=data.consent.granted,
            purpose_code=data.consent.purpose_code,
            features=data.features,
            human_decision=data.human_decision,
            override_justification=data.override_justification,
        )
        packet = await state.pipeline.process(gateway_in)
        if isinstance(packet, BlockedPacket):
            return GatewayProcessResponse(
                request_id=packet.request_id,
                timestamp_utc=packet.timestamp_utc,
                policy_status=packet.policy_status,
                masked_text=None,
                sanitized_response="",
                ai_generated_notice=False,
                model_recommendation="BLOQUEADO_SEGURIDAD",
                human_decision="BLOQUEADO_SEGURIDAD",
                human_override=False,
                citizen_receipt_code=packet.ledger.citizen_receipt_code,
                block_index=packet.ledger.block_index,
                chain_verified=packet.ledger.chain_verified,
                latency_ms=0.0,
            )

        total_latency = (
            packet.shield.latency_ms
            + packet.guard_in.latency_ms
            + packet.llm.latency_ms
            + packet.guard_out.latency_ms
        )
        return GatewayProcessResponse(
            request_id=packet.request_id,
            timestamp_utc=packet.timestamp_utc,
            policy_status=packet.guard_out.policy_status,
            masked_text=packet.masked_text,
            sanitized_response=packet.guard_out.sanitized_response,
            ai_generated_notice=packet.llm.ai_generated_notice,
            model_recommendation=packet.explica.model_recommendation,
            human_decision=packet.explica.human_decision,
            human_override=packet.explica.human_override,
            citizen_receipt_code=packet.ledger.citizen_receipt_code,
            block_index=packet.ledger.block_index,
            chain_verified=packet.ledger.chain_verified,
            latency_ms=total_latency,
            probability_score=packet.explica.probability_score,
            linear_shap_values=dict(packet.explica.linear_shap_values),
        )


class ShieldController(Controller):
    path = f"{API_PREFIX}/shield"
    guards = [api_guard]

    # sync_to_thread: trabajo CPU, no bloquear el event loop
    @post("/inspect", guards=[require_permission("shield:inspect")], sync_to_thread=True)
    def inspect(
        self, request: Request, data: JSONBody[ShieldInspectRequest]
    ) -> ShieldInspectResponse:
        """Sanitización independiente: el mapa de reversión se destruye antes de responder."""
        state: AppState = request.app.state.aduana
        request_id = secrets.token_urlsafe(16)
        try:
            masked, meta = shield(request_id, data.raw_text, vault=state.vault, blind_citizen_id="")
        finally:
            state.vault.zeroize(request_id)
        return ShieldInspectResponse(
            masked_text=masked,
            pii_count=meta.pii_count,
            detected_types=meta.detected_types,
            rif_mod11_verified=meta.rif_mod11_verified,
            latency_ms=meta.latency_ms,
        )
