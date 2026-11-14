"""Etapa 5 — EXPLICA: regresión logística white-box + SHAP lineal (RF-18..RF-20, CA-04)."""

from __future__ import annotations

from collections.abc import Mapping

from core.context import ExplicaResult, RecommendationType


def explain(
    features: Mapping[str, float],
    human_decision: RecommendationType | None,
    override_justification: str | None,
) -> ExplicaResult:
    """Determinista, sin ``random``. Gatillo 4 — pendiente."""
    raise NotImplementedError("Gatillo 4: explain pendiente (specs/04_explica.spec.md)")
