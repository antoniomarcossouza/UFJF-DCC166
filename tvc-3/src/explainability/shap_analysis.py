"""Análise SHAP."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from models.predict import ModelPredictor
from utils.config import load_config
from utils.io import load_dataframe, save_artifact
from utils.logging import get_logger
from utils.paths import PROCESSED_DATA_DIR, REPORTS_DIR, ensure_dirs

logger = get_logger(__name__)


def _compute_shap_values(
    model, x_sample: np.ndarray, feature_names: list[str]
):
    """Calcula valores SHAP para classificação binária (classe ATTACK)."""
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


def generate_shap_artifacts() -> Path:
    """Gera plots SHAP e salva valores para o dashboard."""
    config = load_config()
    ensure_dirs()
    sample_size = config["shap"]["sample_size"]
    output_dir = REPORTS_DIR / "shap"
    output_dir.mkdir(parents=True, exist_ok=True)

    predictor = ModelPredictor()
    test_df = load_dataframe(PROCESSED_DATA_DIR / "test.parquet")
    attack_df = test_df[test_df["label_binary"] != "BENIGN"]
    if attack_df.empty:
        attack_df = test_df
    sample_df = attack_df.sample(
        n=min(sample_size, len(attack_df)),
        random_state=config["project"]["seed"],
    )
    x_sample = sample_df[predictor.features].to_numpy(dtype=float)
    shap_values = _compute_shap_values(
        predictor.model, x_sample, predictor.features
    )

    plt.figure(figsize=(10, 6))
    shap.summary_plot(
        shap_values.values, sample_df[predictor.features], show=False
    )
    plt.tight_layout()
    plt.savefig(output_dir / "summary_plot.png", dpi=150, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(10, 6))
    shap.plots.beeswarm(shap_values, show=False)
    plt.tight_layout()
    plt.savefig(output_dir / "beeswarm_plot.png", dpi=150, bbox_inches="tight")
    plt.close()

    importances = np.abs(shap_values.values).mean(axis=0)
    top_idx = int(np.argmax(importances))
    top_feature = predictor.features[top_idx]
    plt.figure(figsize=(8, 5))
    shap.plots.scatter(
        shap_values[:, top_feature], color=shap_values, show=False
    )
    plt.tight_layout()
    plt.savefig(
        output_dir / "dependence_plot.png", dpi=150, bbox_inches="tight"
    )
    plt.close()

    importance = pd.Series(importances, index=predictor.features).sort_values(
        ascending=False
    )
    importance.to_csv(output_dir / "feature_importance.csv")
    plt.figure(figsize=(8, 6))
    importance.head(15).sort_values().plot(kind="barh")
    plt.title("Feature Importance (|SHAP|)")
    plt.tight_layout()
    plt.savefig(
        output_dir / "feature_importance.png", dpi=150, bbox_inches="tight"
    )
    plt.close()

    save_artifact(
        {
            "values": shap_values.values,
            "feature_names": predictor.features,
            "sample_index": sample_df.index.tolist(),
            "top_features": importance.head(5).to_dict(),
        },
        output_dir / "shap_bundle.joblib",
    )
    logger.info("Artefatos SHAP salvos em %s", output_dir)
    return output_dir


if __name__ == "__main__":
    generate_shap_artifacts()
