"""GET /api/v1/ledger/verify y (solo con ADUANA_DEMO_MODE=1) POST /api/v1/ledger/tamper-sim.

``tamper-sim`` opera sobre una COPIA en RAM de los bloques (``iter_blocks`` +
``dataclasses.replace`` + ``verify_chain``); jamás muta el archivo del ledger ni sus triggers.
"""

from __future__ import annotations

import time
from dataclasses import replace

from litestar import Controller, Request, get, post
from litestar.exceptions import ClientException, HTTPException
from litestar.params import FromPath, JSONBody

from app.dependencies import AppState
from app.rbac_guards import require_permission
from app.schemas import (
    LedgerVerifyResponse,
    ReceiptResponse,
    TamperSimRequest,
    TamperSimResponse,
)
from app.security import api_guard
from core.config import API_PREFIX
from core.crypto import block_hash, canonical_block_payload
from pipeline.stage4_ledger import verify_chain


class LedgerController(Controller):
    path = f"{API_PREFIX}/ledger"
    guards = [api_guard]

    @get("/verify", guards=[require_permission("ledger:audit")], sync_to_thread=True)
    def verify(self, request: Request) -> LedgerVerifyResponse:
        t0 = time.perf_counter()
        state: AppState = request.app.state.aduana
        blocks = list(state.repo.iter_blocks())
        head_hash = blocks[-1].block_hash if blocks else None

        verification = verify_chain(blocks, keys=state.keys)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        return LedgerVerifyResponse(
            is_valid=verification.is_valid,
            blocks_checked=verification.blocks_checked,
            corrupted_block_index=verification.corrupted_block_index,
            failure_reason=verification.failure_reason,
            head_hash=head_hash,
            latency_ms=latency_ms,
        )


class ReceiptController(Controller):
    """Solo con RBAC activo. Sin PII ni payload: únicamente el estado criptográfico."""

    path = f"{API_PREFIX}/ledger"
    guards = [api_guard]

    @get(
        "/receipt/{codigo:str}",
        guards=[require_permission("ledger:receipt")],
        sync_to_thread=True,
    )
    def receipt(self, request: Request, codigo: FromPath[str]) -> ReceiptResponse:
        state: AppState = request.app.state.aduana
        block = state.repo.find_by_receipt_code(codigo)
        if block is None:
            raise HTTPException(status_code=404, detail="ERR_NOT_FOUND")  # sin eco del código
        valid = verify_chain(list(state.repo.iter_blocks()), keys=state.keys).is_valid
        return ReceiptResponse(
            codigo=block.citizen_receipt_code,
            block_index=block.block_index,
            block_hash=block.block_hash,
            cadena_valida=valid,
            liberacion_autorizada=valid and block.security_verdict == "CLEAN",
        )


class DemoLedgerController(Controller):
    path = f"{API_PREFIX}/ledger"
    guards = [api_guard]

    @post(
        "/tamper-sim",
        status_code=200,
        guards=[require_permission("ledger:audit")],
        sync_to_thread=True,
    )
    def tamper_sim(self, request: Request, data: JSONBody[TamperSimRequest]) -> TamperSimResponse:
        state: AppState = request.app.state.aduana
        blocks = list(state.repo.iter_blocks())
        target_idx = data.block_index

        if not (0 <= target_idx < len(blocks)):
            raise ClientException(
                detail=f"block_index {target_idx} fuera de rango (0..{len(blocks) - 1})",
                status_code=400,
            )

        target_block = blocks[target_idx]

        if data.scenario == "flip_payload_bit":
            old_h = target_block.payload_hash
            flipped = ("1" if old_h[0] == "0" else "0") + old_h[1:]
            blocks[target_idx] = replace(target_block, payload_hash=flipped)

        elif data.scenario == "recompute_sha_without_key":
            old_h = target_block.payload_hash
            flipped = ("1" if old_h[0] == "0" else "0") + old_h[1:]
            temp_block = replace(target_block, payload_hash=flipped)
            payload_bytes = canonical_block_payload(
                temp_block,
                index=temp_block.block_index,
                prev_hash=temp_block.prev_hash,
                key_id=temp_block.key_id,
            )
            recomputed = block_hash(payload_bytes)
            # Deja la firma HMAC original sin la clave
            blocks[target_idx] = replace(temp_block, block_hash=recomputed)

        elif data.scenario == "break_prev_link":
            blocks[target_idx] = replace(target_block, prev_hash="f" * 64)

        elif data.scenario == "flip_override":
            blocks[target_idx] = replace(
                target_block, human_override=not target_block.human_override
            )

        t0 = time.perf_counter()
        verification = verify_chain(blocks, keys=state.keys)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        detection = LedgerVerifyResponse(
            is_valid=verification.is_valid,
            blocks_checked=verification.blocks_checked,
            corrupted_block_index=verification.corrupted_block_index,
            failure_reason=verification.failure_reason,
            head_hash=blocks[-1].block_hash if blocks else None,
            latency_ms=latency_ms,
        )

        return TamperSimResponse(
            simulated=True,
            scenario=data.scenario,
            tampered_block_index=target_idx,
            detection=detection,
        )
