"""Busca de hiperparâmetros com Optuna."""

from __future__ import annotations

from typing import Any

import mlflow
import numpy as np
import optuna
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from models.evaluate import evaluate_classifier, log_evaluation_artifacts
from models.train import apply_balancing, load_training_frames
from utils.config import load_config
from utils.io import load_artifact, save_artifact, save_json
from utils.logging import get_logger
from utils.mlflow_utils import log_model
from utils.paths import MODELS_DIR, MLRUNS_DIR, ensure_dirs
from utils.seeds import set_seed

logger = get_logger(__name__)
optuna.logging.set_verbosity(optuna.logging.WARNING)


def _objective_factory(
    model_name: str,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    seed: int,
    balancing: str,
) -> Any:
    x_bal, y_bal, class_weight = apply_balancing(x_train, y_train, balancing, seed)

    def objective(trial: optuna.Trial) -> float:
        if model_name == "random_forest":
            model = RandomForestClassifier(
                n_estimators=trial.suggest_int("n_estimators", 100, 400),
                max_depth=trial.suggest_int("max_depth", 4, 20),
                min_samples_split=trial.suggest_int("min_samples_split", 2, 10),
                class_weight=class_weight,
                random_state=seed,
                n_jobs=-1,
            )
        elif model_name == "xgboost":
            model = XGBClassifier(
                n_estimators=trial.suggest_int("n_estimators", 100, 400),
                max_depth=trial.suggest_int("max_depth", 3, 12),
                learning_rate=trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                subsample=trial.suggest_float("subsample", 0.6, 1.0),
                random_state=seed,
                n_jobs=-1,
                eval_metric="logloss",
                verbosity=0,
            )
        elif model_name == "lightgbm":
            model = LGBMClassifier(
                n_estimators=trial.suggest_int("n_estimators", 100, 400),
                num_leaves=trial.suggest_int("num_leaves", 16, 128),
                learning_rate=trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                class_weight=class_weight,
                random_state=seed,
                n_jobs=-1,
                verbosity=-1,
            )
        else:
            raise ValueError(model_name)

        model.fit(x_bal, y_bal)
        y_pred = model.predict(x_val)
        return float(f1_score(y_val, y_pred, average="macro", zero_division=0))

    return objective


def run_tuning() -> dict[str, Any]:
    """Executa estudos Optuna independentes."""
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
    mlflow.set_experiment(config["mlflow"]["experiment_name"] + "-tuning")

    n_trials = config["training"]["n_optuna_trials"]
    balancing = "class_weight"
    summary: dict[str, Any] = {}

    for model_name in ("random_forest", "xgboost", "lightgbm"):
        study = optuna.create_study(direction="maximize", study_name=model_name)
        study.optimize(
            _objective_factory(
                model_name, x_train, y_train, x_val, y_val, seed, balancing
            ),
            n_trials=n_trials,
        )
        best_params = study.best_params
        with mlflow.start_run(run_name=f"tuned_{model_name}"):
            mlflow.log_params({"model": model_name, **best_params, "balancing": balancing})
            if model_name == "random_forest":
                model = RandomForestClassifier(
                    **best_params,
                    class_weight="balanced",
                    random_state=seed,
                    n_jobs=-1,
                )
            elif model_name == "xgboost":
                model = XGBClassifier(
                    **best_params,
                    random_state=seed,
                    n_jobs=-1,
                    eval_metric="logloss",
                    verbosity=0,
                )
            else:
                model = LGBMClassifier(
                    **best_params,
                    class_weight="balanced",
                    random_state=seed,
                    n_jobs=-1,
                    verbosity=-1,
                )
            x_bal, y_bal, _ = apply_balancing(x_train, y_train, balancing, seed)
            model.fit(x_bal, y_bal)
            test_metrics = evaluate_classifier(model, x_test, y_test)
            mlflow.log_metrics({f"test_{k}": v for k, v in test_metrics.items()})
            log_evaluation_artifacts(model, x_test, y_test, prefix=f"tuned_{model_name}")
            log_model(model, model_name)
            summary[model_name] = {
                "best_params": best_params,
                "best_val_f1": study.best_value,
                "test_metrics": test_metrics,
            }

    best_name = max(summary, key=lambda k: summary[k]["test_metrics"]["f1"])
    best_model_entry = summary[best_name]
    with mlflow.start_run(run_name="best_tuned_model"):
        if best_name == "random_forest":
            final_model = RandomForestClassifier(
                **best_model_entry["best_params"],
                class_weight="balanced",
                random_state=seed,
                n_jobs=-1,
            )
        elif best_name == "xgboost":
            final_model = XGBClassifier(
                **best_model_entry["best_params"],
                random_state=seed,
                n_jobs=-1,
                eval_metric="logloss",
                verbosity=0,
            )
        else:
            final_model = LGBMClassifier(
                **best_model_entry["best_params"],
                class_weight="balanced",
                random_state=seed,
                n_jobs=-1,
                verbosity=-1,
            )
        x_bal, y_bal, _ = apply_balancing(x_train, y_train, balancing, seed)
        final_model.fit(x_bal, y_bal)
        test_metrics = evaluate_classifier(final_model, x_test, y_test)
        mlflow.log_metrics({f"test_{k}": v for k, v in test_metrics.items()})
        log_evaluation_artifacts(final_model, x_test, y_test, prefix="best_tuned")
        log_model(final_model, best_name)
        save_artifact(final_model, MODELS_DIR / "best_model.joblib")
        save_artifact(features, MODELS_DIR / "features.joblib")
        metadata = {
            "best_model": best_name,
            "balancing": balancing,
            "metrics": test_metrics,
            "target": target_col,
            "classes": label_encoder.classes_.tolist(),
            "tuning_summary": summary,
        }
        save_json(metadata, MODELS_DIR / "training_summary.json")

    logger.info("Melhor modelo tunado: %s", best_name)
    return metadata


if __name__ == "__main__":
    run_tuning()
