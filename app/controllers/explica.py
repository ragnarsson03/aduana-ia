"""POST /api/v1/explica/evaluate — explicabilidad de solo lectura (sin sellar ni persistir)."""

from __future__ import annotations

from litestar import Controller, post
from litestar.params import JSONBody

from app.rbac_guards import require_permission
from app.schemas import ExplicaEvaluateRequest, ExplicaEvaluateResponse
from app.security import api_guard
from core.config import API_PREFIX
from pipeline.stage5_explica import explain


class ExplicaController(Controller):
    path = f"{API_PREFIX}/explica"
    guards = [api_guard, require_permission("explica:read")]

    @post("/evaluate", status_code=200, sync_to_thread=False)
    def evaluate(self, data: JSONBody[ExplicaEvaluateRequest]) -> ExplicaEvaluateResponse:
        result = explain(data.features)
        return ExplicaEvaluateResponse(
            probability_score=result.probability_score,
            linear_shap_values=dict(result.linear_shap_values),
            model_recommendation=result.model_recommendation,
        )
