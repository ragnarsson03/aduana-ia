"""GET /api/v1/ledger/verify y (solo con ADUANA_DEMO_MODE=1) POST /api/v1/ledger/tamper-sim.

``tamper-sim`` opera sobre una COPIA en RAM de los bloques (``iter_blocks`` + ``dataclasses.replace``
+ ``verify_chain``); jamás muta el archivo del ledger ni sus triggers.
"""

from __future__ import annotations

from litestar import Controller, get, post
from litestar.params import JSONBody

from app.controllers import pending
from app.schemas import LedgerVerifyResponse, TamperSimRequest, TamperSimResponse
from app.security import api_guard
from core.config import API_PREFIX


class LedgerController(Controller):
    path = f"{API_PREFIX}/ledger"
    guards = [api_guard]

    @get("/verify", sync_to_thread=False)
    def verify(self) -> LedgerVerifyResponse:
        raise pending("Gatillo 3: verify_chain pendiente")


class DemoLedgerController(Controller):
    path = f"{API_PREFIX}/ledger"
    guards = [api_guard]

    @post("/tamper-sim", sync_to_thread=False)
    def tamper_sim(self, data: JSONBody[TamperSimRequest]) -> TamperSimResponse:
        raise pending("Gatillo 3: simulador de sabotaje pendiente")
