"""Estado compartido de la aplicación (un grafo de objetos por proceso)."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.config import Settings
from core.ephemeral_vault import EphemeralVault
from core.keyring import KeyRing
from pipeline.stage0_consent import RateGuard


@dataclass(slots=True)
class AppState:
    """El repositorio de ledger se añade en el Gatillo 3."""

    settings: Settings
    keys: KeyRing
    vault: EphemeralVault
    rate_guard: RateGuard
    api_token: str = field(repr=False)


def build_state(settings: Settings, keys: KeyRing, api_token: str) -> AppState:
    return AppState(
        settings=settings,
        keys=keys,
        vault=EphemeralVault(),
        rate_guard=RateGuard(settings.rate_limit_per_minute),
        api_token=api_token,
    )
