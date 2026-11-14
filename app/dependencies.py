"""Estado compartido de la aplicación (un grafo de objetos por proceso)."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.config import Settings
from core.ephemeral_vault import EphemeralVault
from core.keyring import KeyRing
from core.protocols import StorageRepositoryProtocol
from pipeline.stage0_consent import RateGuard
from pipeline.stage4_ledger import SQLiteLedgerRepository


@dataclass(slots=True)
class AppState:
    settings: Settings
    keys: KeyRing
    vault: EphemeralVault
    rate_guard: RateGuard
    repo: StorageRepositoryProtocol
    api_token: str = field(repr=False)


def build_state(
    settings: Settings,
    keys: KeyRing,
    api_token: str,
    repo: StorageRepositoryProtocol | None = None,
) -> AppState:
    return AppState(
        settings=settings,
        keys=keys,
        vault=EphemeralVault(),
        rate_guard=RateGuard(settings.rate_limit_per_minute),
        repo=repo or SQLiteLedgerRepository(str(settings.db_path)),
        api_token=api_token,
    )
