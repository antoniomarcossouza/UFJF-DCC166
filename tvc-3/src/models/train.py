"""Treinamento de modelos com pipeline compartilhado."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any

import mlflow
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from lightgbm import LGBMClassifier
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from models.evaluate import evaluate_classifier, log_evaluation_artifacts
from utils.config import load_config
from utils.io import load_artifact, load_dataframe, save_artifact, save_json
from utils.logging import get_logger
from utils.mlflow_utils import log_model
from utils.paths import MLRUNS_DIR, MODELS_DIR, PROCESSED_DATA_DIR, ensure_dirs
from utils.seeds import set_seed

logger = get_logger(__name__)
warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names",
    category=UserWarning,
)


@dataclass
class TrainingResult:
    model_name: str
    balancing: str
    metrics: dict[str, float]
    model: Any


def get_model_registry(seed: int) -> dict[str, Any]:
    """Retorna instâncias base dos modelos obrigatórios."""
    return {
        "logistic_regression": LogisticRegression(
            max_iter=5000,
            random_state=seed,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            random_state=seed,
            n_jobs=-1,
        ),
        "xgboost": XGBClassifier(
            n_estimators=200,
            random_state=seed,
            n_jobs=-1,
            eval_metric="logloss",
            verbosity=0,
        ),
        "lightgbm": LGBMClassifier(
            n_estimators=200,
            random_state=seed,
            n_jobs=-1,
            verbosity=-1,
        ),
    }


def apply_balancing(
    x: np.ndarray,
    y: np.ndarray,
    strategy: str,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any] | None]:
    """Aplica estratégia de balanceamento."""
    if strategy == "none":
        return x, y, None
    if strategy == "class_weight":
        return x, y, "balanced"
    if strategy == "smote":
        smote = SMOTE(random_state=seed)
        x_res, y_res = smote.fit_resample(x, y)
        return x_res, y_res, None
    raise ValueError(f"Estratégia desconhecida: {strategy}")


def _configure_class_weight(model: Any, class_weight: Any) -> Any:
    if class_weight is None:
        return model
    model = clone(model)
    if hasattr(model, "class_weight"):
        model.set_params(class_weight=class_weight)
    elif hasattr(model, "scale_pos_weight"):
        model.set_params(scale_pos_weight=1.0)
    return model


def load_training_frames(
    target: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    """Carrega splits e features selecionadas."""
    train_df = load_dataframe(PROCESSED_DATA_DIR / "train.parquet")
    val_df = load_dataframe(PROCESSED_DATA_DIR / "val.parquet")
    test_df = load_dataframe(PROCESSED_DATA_DIR / "test.parquet")
    features_path = PROCESSED_DATA_DIR / "selected_features.joblib"
    if features_path.exists():
        features = load_artifact(features_path)
    else:
        features = load_artifact(PROCESSED_DATA_DIR / "feature_columns.joblib")
    return train_df, val_df, test_df, features


def train_all() -> dict[str, Any]:
    """Treina todos os modelos e estratégias de balanceamento."""
    config = load_config()
    seed = config["project"]["seed"]
    set_seed(seed)
    ensure_dirs()

    target_col = (
        "label_binary"
        if config["training"]["primary_task"] == "binary"
        else "label_multiclass"
    )
    train_df, val_df, test_df, features = load_training_frames(target_col)

    x_train = train_df[features].to_numpy()
    y_train_raw = train_df[target_col].to_numpy()
    x_val = val_df[features].to_numpy()
    y_val_raw = val_df[target_col].to_numpy()
    x_test = test_df[features].to_numpy()
    y_test_raw = test_df[target_col].to_numpy()

    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(y_train_raw)
    y_val = label_encoder.transform(y_val_raw)
    y_test = label_encoder.transform(y_test_raw)
    save_artifact(label_encoder, MODELS_DIR / "label_encoder.joblib")

    mlflow.set_tracking_uri(config["mlflow"]["tracking_uri"])
    MLRUNS_DIR.mkdir(parents=True, exist_ok=True)
    mlflow.set_experiment(config["mlflow"]["experiment_name"])

    results: list[dict[str, Any]] = []
    best_result: TrainingResult | None = None

    for balancing in config["training"]["balancing_strategies"]:
        x_bal, y_bal, class_weight = apply_balancing(
            x_train, y_train, balancing, seed
        )
        for model_name, base_model in get_model_registry(seed).items():
            model = _configure_class_weight(base_model, class_weight)
            with mlflow.start_run(run_name=f"{model_name}_{balancing}"):
                mlflow.log_params(
                    {
                        "model": model_name,
                        "balancing": balancing,
                        "target": target_col,
                        "n_features": len(features),
                    }
                )
                model.fit(x_bal, y_bal)
                val_metrics = evaluate_classifier(model, x_val, y_val)
                test_metrics = evaluate_classifier(model, x_test, y_test)
                mlflow.log_metrics(
                    {f"val_{k}": v for k, v in val_metrics.items()}
                )
                mlflow.log_metrics(
                    {f"test_{k}": v for k, v in test_metrics.items()}
                )
                log_evaluation_artifacts(
                    model,
                    x_test,
                    y_test,
                    prefix=f"{model_name}_{balancing}",
                )
                log_model(model, model_name)

                result = TrainingResult(
                    model_name=model_name,
                    balancing=balancing,
                    metrics=test_metrics,
                    model=model,
                )
                results.append(
                    {
                        "model": model_name,
                        "balancing": balancing,
                        "metrics": test_metrics,
                    }
                )
                if (
                    best_result is None
                    or result.metrics["f1"] > best_result.metrics["f1"]
                ):
                    best_result = result

    assert best_result is not None
    save_artifact(best_result.model, MODELS_DIR / "best_model.joblib")
    save_artifact(features, MODELS_DIR / "features.joblib")
    metadata = {
        "best_model": best_result.model_name,
        "balancing": best_result.balancing,
        "metrics": best_result.metrics,
        "target": target_col,
        "classes": label_encoder.classes_.tolist(),
        "all_results": results,
    }
    save_json(metadata, MODELS_DIR / "training_summary.json")
    logger.info(
        "Melhor modelo: %s (%s) F1=%.4f",
        best_result.model_name,
        best_result.balancing,
        best_result.metrics["f1"],
    )
    return metadata


if __name__ == "__main__":
    train_all()
