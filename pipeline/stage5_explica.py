"""Etapa 5 — EXPLICA: regresión logística white-box + SHAP lineal (RF-18..RF-20, CA-04).

Gatillo 4:
- Inferencia y explicaciones 100% deterministas (sin random(), sin dependencias externas pesadas).
- Sigmoide numéricamente estable con bifurcación por signo de z para evitar desbordamientos.
- Desglose matemático exacto:
    c_j = β_j * x_j                      (contribución directa)
    φ_j = β_j * (x_j - μ_j)              (valor SHAP lineal centrado)
    base_SHAP = β_0 + Σ β_j * μ_j        (esperanza poblacional de z)
    z = base_SHAP + Σ φ_j = β_0 + Σ c_j  (axioma de eficiencia SHAP)
- Error de reconstrucción del logit < 1e-9 (LOGIT_RECONSTRUCTION_TOLERANCE).
- Decisión humana vinculante: override exige justificación >= 20 caracteres
  (OVERRIDE_MIN_JUSTIFICATION_CHARS) y <= 500 caracteres, lanzando OverrideJustificationError
  ante cualquier incumplimiento.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from core.config import (
    LOGIT_RECONSTRUCTION_TOLERANCE,
    OVERRIDE_MAX_JUSTIFICATION_CHARS,
    OVERRIDE_MIN_JUSTIFICATION_CHARS,
)
from core.context import ExplicaResult, RecommendationType
from core.errors import OverrideJustificationError


@dataclass(frozen=True, slots=True)
class ExplicaModel:
    """Parámetros matemáticos del modelo determinista white-box."""

    model_name: str
    intercept_b0: float
    weights: Mapping[str, float]
    population_means: Mapping[str, float]
    feature_names: tuple[str, ...]
    threshold_high: float = 0.70
    threshold_low: float = 0.30


# Modelo Oráculo de prueba matemática (especificado exactamente en specs/04_explica.spec.md §Casos)
ORACLE_MODEL: Final[ExplicaModel] = ExplicaModel(
    model_name="oraculo_benchmark_v1",
    intercept_b0=-0.5,
    weights={"f1": 1.0, "f2": -2.0, "f3": 0.5, "f4": 0.0, "f5": 3.0},
    population_means={"f1": 0.5, "f2": 0.5, "f3": 0.5, "f4": 0.5, "f5": 0.5},
    feature_names=("f1", "f2", "f3", "f4", "f5"),
    threshold_high=0.70,
    threshold_low=0.30,
)

# Modelo Institucional calibrado sobre data/synthetic_tramites.csv
INSTITUTIONAL_MODEL: Final[ExplicaModel] = ExplicaModel(
    model_name="aduana_social_v1",
    intercept_b0=-2.0,
    weights={
        "tiempo_espera_dias": 0.03,
        "vulnerabilidad_socioeconomica": 2.5,
        "completitud_recaudos": 1.2,
        "urgencia_medica": 3.0,
        "complejidad_caso": -0.8,
    },
    population_means={
        "tiempo_espera_dias": 62.5,
        "vulnerabilidad_socioeconomica": 0.49833333333333335,
        "completitud_recaudos": 0.735,
        "urgencia_medica": 0.25,
        "complejidad_caso": 0.515,
    },
    feature_names=(
        "tiempo_espera_dias",
        "vulnerabilidad_socioeconomica",
        "completitud_recaudos",
        "urgencia_medica",
        "complejidad_caso",
    ),
    threshold_high=0.70,
    threshold_low=0.30,
)


def stable_sigmoid(z: float) -> float:
    """Sigmoide numéricamente estable con bifurcación por signo para evitar OverflowError."""
    if z >= 0.0:
        return 1.0 / (1.0 + math.exp(-z))
    exp_z = math.exp(z)
    return exp_z / (1.0 + exp_z)


def resolve_model(
    features: Mapping[str, float], explicit_model: ExplicaModel | None = None
) -> ExplicaModel:
    """Determina qué modelo corresponde al conjunto de variables dadas."""
    if explicit_model is not None:
        return explicit_model

    if not features:
        raise ValueError("El diccionario de características no puede estar vacío.")

    feature_keys = set(features.keys())
    if feature_keys == set(ORACLE_MODEL.feature_names):
        return ORACLE_MODEL
    if feature_keys == set(INSTITUTIONAL_MODEL.feature_names):
        return INSTITUTIONAL_MODEL

    # Si comparte variables con un modelo conocido, asociarlo a ese modelo para reportar faltantes/sobrantes
    oracle_set = set(ORACLE_MODEL.feature_names)
    inst_set = set(INSTITUTIONAL_MODEL.feature_names)
    if feature_keys.issubset(oracle_set) or any(k in oracle_set for k in feature_keys):
        return ORACLE_MODEL
    if feature_keys.issubset(inst_set) or any(k in inst_set for k in feature_keys):
        return INSTITUTIONAL_MODEL

    raise ValueError(
        f"Esquema de variables no reconocido: {sorted(feature_keys)}. "
        f"Esquemas soportados: {sorted(ORACLE_MODEL.feature_names)} o "
        f"{sorted(INSTITUTIONAL_MODEL.feature_names)}."
    )


def explain(
    features: Mapping[str, float],
    human_decision: RecommendationType | None = None,
    override_justification: str | None = None,
    *,
    model: ExplicaModel | None = None,
) -> ExplicaResult:
    """Evalúa variables de forma determinista y devuelve la probabilidad y explicación SHAP."""
    # 1. Validación de valores numéricos finitos
    for name, val in features.items():
        if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
            raise ValueError(f"Característica '{name}' con valor no finito o inválido: {val}")

    # 2. Resolución de modelo y validación estricta de esquema
    active_model = resolve_model(features, model)
    expected_keys = set(active_model.feature_names)
    actual_keys = set(features.keys())
    if actual_keys != expected_keys:
        missing = expected_keys - actual_keys
        extra = actual_keys - expected_keys
        raise ValueError(
            f"El vector de características no coincide con el modelo '{active_model.model_name}'. "
            f"Faltantes: {sorted(missing)}, Sobrantes: {sorted(extra)}"
        )

    # 3. Cálculo de contribuciones directas y valores SHAP lineales
    feature_contributions_bx: dict[str, float] = {}
    linear_shap_values: dict[str, float] = {}

    sum_bx = 0.0
    sum_shap = 0.0
    base_shap = active_model.intercept_b0

    for name in active_model.feature_names:
        x_j = float(features[name])
        beta_j = active_model.weights[name]
        mu_j = active_model.population_means[name]

        # Contribución directa
        c_j = beta_j * x_j
        feature_contributions_bx[name] = c_j
        sum_bx += c_j

        # Valor SHAP lineal centrado
        phi_j = beta_j * (x_j - mu_j)
        linear_shap_values[name] = phi_j
        sum_shap += phi_j

        base_shap += beta_j * mu_j

    # 4. Cálculo del logit z y comprobación de axiomas de reconstrucción
    z_direct = active_model.intercept_b0 + sum_bx
    z_shap = base_shap + sum_shap

    error_direct = abs((active_model.intercept_b0 + sum_bx) - z_direct)
    error_shap = abs(z_shap - z_direct)
    reconstruction_error = max(error_direct, error_shap)

    if reconstruction_error >= LOGIT_RECONSTRUCTION_TOLERANCE:
        raise ValueError(
            f"Error de reconstrucción de logit ({reconstruction_error:.2e}) "
            f"supera la tolerancia permitida ({LOGIT_RECONSTRUCTION_TOLERANCE:.2e})"
        )

    # 5. Cálculo de probabilidad sigmoide y recomendación
    probability = stable_sigmoid(z_direct)

    if probability >= active_model.threshold_high:
        model_rec: RecommendationType = "PRIORIDAD_ALTA"
    elif probability < active_model.threshold_low:
        model_rec: RecommendationType = "RECAUDOS_INCOMPLETOS"
    else:
        model_rec: RecommendationType = "REVISION_ESTANDAR"

    # 6. Gestión de Decisión Humana y Override (RF-20)
    human_override = False
    clean_justification: str | None = None

    if human_decision is None:
        # No hay decisión humana explícita aún; se adopta provisionalmente la recomendación
        final_decision = model_rec
    elif human_decision == model_rec:
        # El funcionario confirma la recomendación del modelo
        final_decision = human_decision
    else:
        # Override humano: el funcionario discrepa de la recomendación del modelo
        human_override = True
        if override_justification is None:
            raise OverrideJustificationError(
                "El override humano exige una justificación escrita (RF-20)."
            )

        stripped = override_justification.strip()
        if len(stripped) < OVERRIDE_MIN_JUSTIFICATION_CHARS:
            raise OverrideJustificationError(
                f"La justificación de override debe contener al menos {OVERRIDE_MIN_JUSTIFICATION_CHARS} "
                f"caracteres (recibidos: {len(stripped)})."
            )
        if len(override_justification) > OVERRIDE_MAX_JUSTIFICATION_CHARS:
            raise OverrideJustificationError(
                f"La justificación de override no puede superar los {OVERRIDE_MAX_JUSTIFICATION_CHARS} "
                f"caracteres (recibidos: {len(override_justification)})."
            )

        clean_justification = stripped
        final_decision = human_decision

    return ExplicaResult(
        model_type=active_model.model_name,
        logit_z=z_direct,
        probability_score=probability,
        intercept_b0=active_model.intercept_b0,
        feature_values=dict(features),
        feature_contributions_bx=feature_contributions_bx,
        linear_shap_values=linear_shap_values,
        logit_reconstruction_error=reconstruction_error,
        model_recommendation=model_rec,
        human_decision=final_decision,
        human_override=human_override,
        override_justification=clean_justification,
    )
