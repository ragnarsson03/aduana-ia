"""Matriz CA-01..CA-06 en rojo esperado: ``xfail(strict=True)`` hasta su gatillo.
(CA-01 vive en ``test_ca01_shield.py``; CA-02 en ``test_ca02_guardian.py``;
 CA-03 en ``test_ca03_ledger.py``; CA-05 en ``test_ca05_restrictive_storage.py``.)

Al implementar cada gatillo el XPASS estricto obliga a convertir el test en una prueba real.
"""

from __future__ import annotations

import asyncio

import pytest

from core.keyring import KeyRing
from pipeline.llm_adapter import CircuitBreaker, OfflineDeterministicAdapter
from pipeline.stage5_explica import explain

pending = pytest.mark.xfail(strict=True, raises=NotImplementedError)
KEYS = KeyRing(bytes(range(32)))


@pending
def test_ca04_explica_reconstructs_logit_within_1e9() -> None:
    explain({}, None, None)


@pending
def test_ca06_llm_failover_under_100ms() -> None:
    adapter = OfflineDeterministicAdapter()
    asyncio.run(CircuitBreaker(adapter, adapter).exchange("p"))
