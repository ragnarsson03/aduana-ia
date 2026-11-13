"""GET /api/v1/health/system — solo estado mínimo, sin autenticación (sin fingerprinting)."""

from __future__ import annotations

from litestar import Controller, Request, get

from app.dependencies import AppState
from app.schemas import HealthResponse
from core.config import API_PREFIX


class HealthController(Controller):
    path = f"{API_PREFIX}/health"

    @get("/system", sync_to_thread=False)
    def system(self, request: Request) -> HealthResponse:
        state: AppState = request.app.state.aduana
        return HealthResponse(
            status="ok",
            ledger_mode="ephemeral" if state.settings.ledger_ephemeral else "persistent",
            implemented_stages=("structure",),
        )
