"""Explicação SHAP de eventos no dashboard."""

from __future__ import annotations

import numpy as np
import pandas as pd
import shap

from models.predict import ModelPredictor


def _compute_shap_values(
    model, x_sample: np.ndarray, feature_names: list[str]
):
    """Calcula valores SHAP para um evento."""
    try:
        explainer = shap.TreeExplainer(model)
        values = explainer.shap_values(x_sample)
    except Exception:
        explainer = shap.Explainer(
            lambda x: model.predict_proba(x)[:, 0], x_sample
        )
        explanation = explainer(x_sample)
        values = explanation.values

    if isinstance(values, list):
        values = values[0]
    if values.ndim == 3:
        values = values[:, :, 0]
    return shap.Explanation(
        values=values,
        data=x_sample,
        feature_names=feature_names,
    )


def explain_event(
    row: pd.Series, predictor: ModelPredictor | None = None
) -> dict:
    """Gera explicação textual para um evento."""
    predictor = predictor or ModelPredictor()
    x = row[predictor.features].to_numpy(dtype=float).reshape(1, -1)
    shap_values = _compute_shap_values(predictor.model, x, predictor.features)
    contributions = dict(
        zip(predictor.features, shap_values.values[0].tolist(), strict=False)
    )
    top = sorted(
        contributions.items(), key=lambda item: abs(item[1]), reverse=True
    )[:3]
    factors = ", ".join(f"{name} ({value:+.3f})" for name, value in top)
    prediction = predictor.predict_row(row)
    text = (
        f"A classificação como {prediction.label} "
        f"foi fortemente influenciada por {factors}"
        ", compatível com padrões observados em tráfego malicioso."
    )
    return {
        "text": text,
        "contributions": contributions,
        "top_features": top,
        "probability": prediction.probability,
    }
