"""POST /api/v1/audit/fiscal — trazabilidad de un importador por índice ciego (``audit:fiscal``).

POST para no poner datos personales en la URL. Nunca devuelve el identificador ni el índice ciego.
"""

from __future__ import annotations

from litestar import Controller, Request, post
from litestar.exceptions import HTTPException
from litestar.params import JSONBody

from app.dependencies import AppState
from app.rbac_guards import require_permission
from app.schemas import AuditBlockOut, AuditFiscalRequest, AuditFiscalResponse
from app.security import api_guard
from core.auth import blind_identifier
from core.config import API_PREFIX


class AuditController(Controller):
    path = f"{API_PREFIX}/audit"
    guards = [api_guard, require_permission("audit:fiscal")]

    @post("/fiscal", status_code=200, sync_to_thread=True)
    def fiscal(self, request: Request, data: JSONBody[AuditFiscalRequest]) -> AuditFiscalResponse:
        state: AppState = request.app.state.aduana
        try:
            blind = blind_identifier(state.keys, data.identificador)
        except ValueError as exc:  # formato inválido (sin eco)
            raise HTTPException(status_code=422, detail="ERR_INVALID_IDENTIFIER") from exc
        return AuditFiscalResponse(
            blocks=[
                AuditBlockOut(
                    block_index=b.block_index,
                    citizen_receipt_code=b.citizen_receipt_code,
                    security_verdict=b.security_verdict,
                    timestamp_utc=b.timestamp_utc,
                    block_hash=b.block_hash,
                )
                for b in state.repo.iter_blocks_by_blind_id(blind)
            ]
        )
