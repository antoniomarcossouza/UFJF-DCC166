"""Engenharia e seleção de atributos."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import mutual_info_classif

from utils.config import load_config
from utils.io import load_artifact, load_dataframe, save_artifact, save_json
from utils.logging import get_logger
from utils.paths import PROCESSED_DATA_DIR, REPORTS_DIR, ensure_dirs

logger = get_logger(__name__)


def correlation_filter(df: pd.DataFrame, threshold: float) -> list[str]:
    """Remove features altamente correlacionadas."""
    corr = df.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
    return to_drop


def compute_mutual_information(
    x: pd.DataFrame, y: pd.Series, seed: int
) -> pd.Series:
    """Calcula mutual information por feature."""
    scores = mutual_info_classif(x, y, random_state=seed)
    return pd.Series(scores, index=x.columns).sort_values(ascending=False)


def compute_feature_importance(
    x: pd.DataFrame, y: pd.Series, seed: int
) -> pd.Series:
    """Calcula importância via Random Forest."""
    model = RandomForestClassifier(
        n_estimators=100,
        random_state=seed,
        n_jobs=-1,
        class_weight="balanced",
    )
    model.fit(x, y)
    return pd.Series(model.feature_importances_, index=x.columns).sort_values(
        ascending=False
    )


def select_features() -> dict:
    """Executa seleção de atributos e documenta decisões."""
    config = load_config()
    ensure_dirs()
    seed = config["project"]["seed"]
    threshold = config["data"]["correlation_threshold"]

    train_df = load_dataframe(PROCESSED_DATA_DIR / "train.parquet")
    feature_cols = load_artifact(PROCESSED_DATA_DIR / "feature_columns.joblib")
    target = config["training"]["primary_task"]
    target_col = "label_binary" if target == "binary" else "label_multiclass"

    x = train_df[feature_cols]
    y = train_df[target_col]

    dropped_corr = correlation_filter(x, threshold)
    remaining = [col for col in feature_cols if col not in dropped_corr]
    x_filtered = x[remaining]

    mi_scores = compute_mutual_information(x_filtered, y, seed)
    rf_importance = compute_feature_importance(x_filtered, y, seed)

    selected_features = list(
        set(mi_scores.head(25).index).union(rf_importance.head(25).index)
    )
    selected_features = [col for col in remaining if col in selected_features]

    save_artifact(selected_features, PROCESSED_DATA_DIR / "selected_features.joblib")

    report = {
        "correlation_threshold": threshold,
        "dropped_by_correlation": dropped_corr,
        "mutual_information_top10": mi_scores.head(10).to_dict(),
        "feature_importance_top10": rf_importance.head(10).to_dict(),
        "selected_features": selected_features,
        "decision": (
            "Mantidas features presentes no top-25 de MI ou importância RF, "
            f"após remoção de correlação > {threshold}."
        ),
    }
    save_json(report, REPORTS_DIR / "feature_selection.json")

    md_path = REPORTS_DIR / "feature_selection.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(
        "# Seleção de Atributos\n\n"
        f"- Threshold de correlação: {threshold}\n"
        f"- Features removidas por correlação: {len(dropped_corr)}\n"
        f"- Features selecionadas: {len(selected_features)}\n\n"
        f"## Decisão\n\n{report['decision']}\n",
        encoding="utf-8",
    )
    logger.info("Seleção concluída: %d features", len(selected_features))
    return report


if __name__ == "__main__":
    select_features()
