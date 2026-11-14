"""Estado compartido de la aplicación (un grafo de objetos por proceso)."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.config import LLM_TIMEOUT_SECONDS, Settings
from core.ephemeral_vault import EphemeralVault
from core.identity import IdentityService
from core.keyring import KeyRing
from core.protocols import StorageRepositoryProtocol
from core.rbac_db import UsuariosRepository
from pipeline.llm_adapter import CircuitBreaker, OfflineDeterministicAdapter
from pipeline.orchestrator import GatewayPipeline
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
    pipeline: GatewayPipeline
    identity: IdentityService | None = None
    users_repo: UsuariosRepository | None = None


def build_state(
    settings: Settings,
    keys: KeyRing,
    api_token: str,
    repo: StorageRepositoryProtocol | None = None,
    pipeline: GatewayPipeline | None = None,
) -> AppState:
    vault = EphemeralVault()
    rate_guard = RateGuard(settings.rate_limit_per_minute)
    repository = repo or SQLiteLedgerRepository(str(settings.db_path))
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
    users_repo: UsuariosRepository | None = None
    identity: IdentityService | None = None
    if settings.rbac_enabled:
        users_repo = UsuariosRepository(str(settings.users_db_path))
        identity = IdentityService(
            users_repo,
            keys,
            iterations=settings.pbkdf2_iterations,
            token_ttl_seconds=settings.token_ttl_seconds,
            max_failed_attempts=settings.max_failed_attempts,
            lockout_seconds=settings.lockout_seconds,
        )
    return AppState(
        settings=settings,
        keys=keys,
        vault=vault,
        rate_guard=rate_guard,
        repo=repository,
        api_token=api_token,
        pipeline=pipeline,
        identity=identity,
        users_repo=users_repo,
    )
