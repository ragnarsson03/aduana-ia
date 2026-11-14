"""Tests de aceptación para CA-04 (EXPLICA: regresión logística white-box + SHAP lineal).

Verifica:
1. Descomposición exacta y axioma de eficiencia SHAP (error < 1e-9).
2. Evaluación en media poblacional y vector cero.
3. Grid determinista completo sin variación ni uso de random().
4. Confirmación humana vs Override con justificación (>= 20 chars).
5. Validación estricta de esquemas y rechazo de NaN/inf.
6. Sigmoide numéricamente estable para valores extremos (+/-1000).
7. Coherencia sobre data/synthetic_tramites.csv.
"""

from __future__ import annotations

import csv
import itertools
import math
from pathlib import Path
from unittest.mock import patch

import pytest

from core.config import LOGIT_RECONSTRUCTION_TOLERANCE, PROJECT_ROOT
from core.errors import OverrideJustificationError
from pipeline.stage5_explica import (
    INSTITUTIONAL_MODEL,
    ORACLE_MODEL,
    explain,
    stable_sigmoid,
)


def test_exact_decomposition() -> None:
    """Verifica el caso de prueba especificado en specs/04_explica.spec.md §Casos.

    Modelo de prueba:
        β0 = -0.5
        β = (1, -2, 0.5, 0, 3)
        μ = (0.5, 0.5, 0.5, 0.5, 0.5)
    Vector:
        x = (1, 0, 2, 0, 1)
    Esperado:
        c = (1, 0, 1, 0, 3), z = 4.5, P = 1 / (1 + exp(-4.5))
        φ = (0.5, 1, 0.75, 0, 1.5), base_SHAP = 0.75
        Reconstrucción con error < 1e-9.
    """
    x = {"f1": 1.0, "f2": 0.0, "f3": 2.0, "f4": 0.0, "f5": 1.0}
    res = explain(x, human_decision="PRIORIDAD_ALTA", override_justification=None)

    assert res.model_type == "oraculo_benchmark_v1"
    assert res.intercept_b0 == -0.5
    assert math.isclose(res.logit_z, 4.5, abs_tol=1e-12)

    expected_p = 1.0 / (1.0 + math.exp(-4.5))
    assert math.isclose(res.probability_score, expected_p, abs_tol=1e-12)

    # Contribuciones directas: c_j = β_j * x_j
    assert math.isclose(res.feature_contributions_bx["f1"], 1.0, abs_tol=1e-12)
    assert math.isclose(res.feature_contributions_bx["f2"], 0.0, abs_tol=1e-12)
    assert math.isclose(res.feature_contributions_bx["f3"], 1.0, abs_tol=1e-12)
    assert math.isclose(res.feature_contributions_bx["f4"], 0.0, abs_tol=1e-12)
    assert math.isclose(res.feature_contributions_bx["f5"], 3.0, abs_tol=1e-12)

    # Valores SHAP lineales: φ_j = β_j * (x_j - μ_j)
    assert math.isclose(res.linear_shap_values["f1"], 0.5, abs_tol=1e-12)
    assert math.isclose(res.linear_shap_values["f2"], 1.0, abs_tol=1e-12)
    assert math.isclose(res.linear_shap_values["f3"], 0.75, abs_tol=1e-12)
    assert math.isclose(res.linear_shap_values["f4"], 0.0, abs_tol=1e-12)
    assert math.isclose(res.linear_shap_values["f5"], 1.5, abs_tol=1e-12)

    # Error de reconstrucción < 1e-9
    assert res.logit_reconstruction_error < LOGIT_RECONSTRUCTION_TOLERANCE
    assert res.model_recommendation == "PRIORIDAD_ALTA"
    assert res.human_override is False


def test_at_population_mean() -> None:
    """En la media poblacional x = μ, todos los SHAP lineales deben ser exactamente cero."""
    x_mean = {"f1": 0.5, "f2": 0.5, "f3": 0.5, "f4": 0.5, "f5": 0.5}
    res = explain(x_mean)

    for name in ("f1", "f2", "f3", "f4", "f5"):
        assert math.isclose(res.linear_shap_values[name], 0.0, abs_tol=1e-12)

    # z = base_SHAP = 0.75
    assert math.isclose(res.logit_z, 0.75, abs_tol=1e-12)
    assert res.logit_reconstruction_error < LOGIT_RECONSTRUCTION_TOLERANCE


def test_zero_vector() -> None:
    """Vector cero: contribuciones directas deben ser 0 y z debe ser igual al intercepto."""
    x_zero = {"f1": 0.0, "f2": 0.0, "f3": 0.0, "f4": 0.0, "f5": 0.0}
    res = explain(x_zero)

    for name in ("f1", "f2", "f3", "f4", "f5"):
        assert res.feature_contributions_bx[name] == 0.0

    assert math.isclose(res.logit_z, -0.5, abs_tol=1e-12)
    assert math.isclose(res.probability_score, 1.0 / (1.0 + math.exp(0.5)), abs_tol=1e-12)
    assert res.logit_reconstruction_error < LOGIT_RECONSTRUCTION_TOLERANCE


def test_deterministic_grid() -> None:
    """Evalúa el producto cartesiano de {0, 0.5, 1} en las 5 variables (243 combinaciones).

    Comprueba que para cada vector:
    1. El error de reconstrucción sea estrictamente < 1e-9.
    2. Dos ejecuciones consecutivas arrojen resultados exactamente idénticos (determinismo puro).
    """
    grid_vals = (0.0, 0.5, 1.0)
    for combo in itertools.product(grid_vals, repeat=5):
        vec = {f"f{i+1}": combo[i] for i in range(5)}
        res1 = explain(vec)
        res2 = explain(vec)

        assert res1.logit_reconstruction_error < LOGIT_RECONSTRUCTION_TOLERANCE
        assert res1.logit_z == res2.logit_z
        assert res1.probability_score == res2.probability_score
        assert res1.feature_contributions_bx == res2.feature_contributions_bx
        assert res1.linear_shap_values == res2.linear_shap_values


def test_no_random_dependency() -> None:
    """Inspecciona que el módulo no importe ni utilice random ni Math.random()."""
    import pipeline.stage5_explica as stage5

    assert "random" not in dir(stage5)
    with patch("random.random", side_effect=RuntimeError("Prohibido invocar random()")):
        res = explain({"f1": 1.0, "f2": 0.0, "f3": 0.0, "f4": 0.0, "f5": 0.0})
        assert res.logit_reconstruction_error < LOGIT_RECONSTRUCTION_TOLERANCE


def test_confirmation_vs_override() -> None:
    """Verifica confirmación humana vs override humano con justificación."""
    x = {"f1": 1.0, "f2": 0.0, "f3": 2.0, "f4": 0.0, "f5": 1.0}

    # 1. Sin decisión humana explícita: adopta provisionalmente la recomendación
    res_none = explain(x, human_decision=None)
    assert res_none.model_recommendation == "PRIORIDAD_ALTA"
    assert res_none.human_decision == "PRIORIDAD_ALTA"
    assert res_none.human_override is False

    # 2. Funcionario confirma la recomendación: override=False
    res_conf = explain(x, human_decision="PRIORIDAD_ALTA")
    assert res_conf.human_override is False
    assert res_conf.override_justification is None

    # 3. Funcionario discrepa sin justificación -> OverrideJustificationError
    with pytest.raises(OverrideJustificationError):
        explain(x, human_decision="REVISION_ESTANDAR", override_justification=None)

    with pytest.raises(OverrideJustificationError):
        explain(x, human_decision="REVISION_ESTANDAR", override_justification="")

    with pytest.raises(OverrideJustificationError):
        explain(x, human_decision="REVISION_ESTANDAR", override_justification="A" * 19)

    # 4. Funcionario discrepa con justificación válida (>= 20 caracteres)
    justification = "Se requiere revisión estándar por discrepancia documental en recaudos."
    res_override = explain(
        x, human_decision="REVISION_ESTANDAR", override_justification=justification
    )
    assert res_override.human_override is True
    assert res_override.human_decision == "REVISION_ESTANDAR"
    assert res_override.override_justification == justification

    # 5. Justificación excesiva (> 500 chars) rechazada
    with pytest.raises(OverrideJustificationError):
        explain(x, human_decision="REVISION_ESTANDAR", override_justification="B" * 501)


def test_feature_validation() -> None:
    """Verifica rechazo estricto de esquemas incorrectos, valores NaN e infinitos."""
    # Vacío
    with pytest.raises(ValueError, match="no puede estar vacío"):
        explain({})

    # Faltan variables
    with pytest.raises(ValueError, match="Faltantes"):
        explain({"f1": 1.0, "f2": 2.0})

    # Variables sobrantes
    with pytest.raises(ValueError, match="Sobrantes"):
        explain({"f1": 1.0, "f2": 2.0, "f3": 3.0, "f4": 4.0, "f5": 5.0, "extra": 9.9})

    # NaN
    with pytest.raises(ValueError, match="no finito"):
        explain({"f1": float("nan"), "f2": 0.0, "f3": 0.0, "f4": 0.0, "f5": 0.0})

    # Infinito
    with pytest.raises(ValueError, match="no finito"):
        explain({"f1": float("inf"), "f2": 0.0, "f3": 0.0, "f4": 0.0, "f5": 0.0})


def test_stable_sigmoid_extremes() -> None:
    """Verifica que stable_sigmoid no desborde con valores extremos."""
    assert math.isclose(stable_sigmoid(0.0), 0.5)
    assert stable_sigmoid(1000.0) == 1.0
    assert stable_sigmoid(-1000.0) == 0.0


def test_institutional_synthetic_dataset() -> None:
    """Verifica la evaluación del modelo institucional sobre data/synthetic_tramites.csv."""
    csv_file = PROJECT_ROOT / "data" / "synthetic_tramites.csv"
    assert csv_file.exists(), "data/synthetic_tramites.csv debe existir"

    with open(csv_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            count += 1
            features = {
                "tiempo_espera_dias": float(row["tiempo_espera_dias"]),
                "vulnerabilidad_socioeconomica": float(row["vulnerabilidad_socioeconomica"]),
                "completitud_recaudos": float(row["completitud_recaudos"]),
                "urgencia_medica": float(row["urgencia_medica"]),
                "complejidad_caso": float(row["complejidad_caso"]),
            }
            res = explain(features)
            assert res.model_type == "aduana_social_v1"
            assert res.logit_reconstruction_error < LOGIT_RECONSTRUCTION_TOLERANCE
            assert 0.0 <= res.probability_score <= 1.0

        assert count >= 50, f"Se esperaban al menos 50 trámites sintéticos, encontrados: {count}"
