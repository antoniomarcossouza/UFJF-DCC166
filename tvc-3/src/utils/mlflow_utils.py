"""Integração com MLflow."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import joblib
import mlflow


def log_model(model: Any, model_name: str) -> None:
    """Registra modelo serializado como artefato."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"{model_name}.joblib"
        joblib.dump(model, path)
        mlflow.log_artifact(str(path), artifact_path="model")
