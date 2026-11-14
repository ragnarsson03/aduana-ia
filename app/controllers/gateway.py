"""POST /api/v1/gateway/process y POST /api/v1/shield/inspect."""

from __future__ import annotations

import secrets

from litestar import Controller, Request, post
from litestar.params import JSONBody

from app.controllers import pending
from app.dependencies import AppState
from app.schemas import GatewayProcessRequest, ShieldInspectRequest, ShieldInspectResponse
from app.security import api_guard
from core.config import API_PREFIX
from pipeline.stage1_shield import shield


class GatewayController(Controller):
    path = f"{API_PREFIX}/gateway"
    guards = [api_guard]

    @post("/process", sync_to_thread=False)
    def process(self, data: JSONBody[GatewayProcessRequest]) -> dict[str, str]:
        raise pending("Gatillo 6: pipeline completo pendiente")


class ShieldController(Controller):
    path = f"{API_PREFIX}/shield"
    guards = [api_guard]

    @post("/inspect", sync_to_thread=True)  # trabajo CPU: no bloquear el event loop
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
