"""Estado compartido de la aplicación (un grafo de objetos por proceso)."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.config import LLM_TIMEOUT_SECONDS, Settings
from core.ephemeral_vault import EphemeralVault
from core.keyring import KeyRing
from core.protocols import StorageRepositoryProtocol
from pipeline.auth import SessionStore, SQLiteAuthRepository
from pipeline.llm_adapter import CircuitBreaker, OfflineDeterministicAdapter
from pipeline.orchestrator import GatewayPipeline
from pipeline.stage0_consent import RateGuard
from pipeline.stage4_ledger import SQLiteLedgerRepository

AUTH_RATE_LIMIT_PER_MINUTE = 5


@dataclass(slots=True)
class AppState:
    settings: Settings
    keys: KeyRing
    vault: EphemeralVault
    rate_guard: RateGuard
    auth_rate_guard: RateGuard
    session_store: SessionStore
    repo: StorageRepositoryProtocol
    auth_repo: SQLiteAuthRepository
    api_token: str = field(repr=False)
    pipeline: GatewayPipeline


def build_state(
    settings: Settings,
    keys: KeyRing,
    api_token: str,
    repo: StorageRepositoryProtocol | None = None,
    pipeline: GatewayPipeline | None = None,
) -> AppState:
    vault = EphemeralVault()
    rate_guard = RateGuard(settings.rate_limit_per_minute)
    auth_rate_guard = RateGuard(AUTH_RATE_LIMIT_PER_MINUTE)
    session_store = SessionStore()
    repository = repo or SQLiteLedgerRepository(str(settings.db_path))
    auth_repo = SQLiteAuthRepository(str(settings.db_path), keys=keys)
    if pipeline is None:
        fallback = OfflineDeterministicAdapter()
        breaker = CircuitBreaker(fallback, fallback, timeout_s=LLM_TIMEOUT_SECONDS)
        pipeline = GatewayPipeline(
            keys=keys,
            vault=vault,
            repo=repository,
            llm=breaker,
            rate_guard=rate_guard,
        )
    return AppState(
        settings=settings,
        keys=keys,
        vault=vault,
        rate_guard=rate_guard,
        auth_rate_guard=auth_rate_guard,
        session_store=session_store,
        repo=repository,
        auth_repo=auth_repo,
        api_token=api_token,
        pipeline=pipeline,
    )
