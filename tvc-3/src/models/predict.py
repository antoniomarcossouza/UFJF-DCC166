"""Inferência com modelos treinados."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from utils.io import load_artifact, load_json
from utils.paths import MODELS_DIR, PROCESSED_DATA_DIR


@dataclass
class PredictionResult:
    label: str
    probability: float
    probabilities: dict[str, float]
    is_attack: bool


class ModelPredictor:
    """Carrega modelo e scaler para inferência."""

    def __init__(self) -> None:
        self.model = load_artifact(MODELS_DIR / "best_model.joblib")
        self.features = load_artifact(MODELS_DIR / "features.joblib")
        self.metadata = load_json(MODELS_DIR / "training_summary.json")
        encoder_path = MODELS_DIR / "label_encoder.joblib"
        if encoder_path.exists():
            self.label_encoder = load_artifact(encoder_path)
            self.classes_ = list(self.label_encoder.classes_)
        else:
            self.label_encoder = None
            self.classes_ = list(getattr(self.model, "classes_", []))

    def _decode(self, encoded) -> str:
        if self.label_encoder is not None:
            return str(self.label_encoder.inverse_transform([int(encoded)])[0])
        return str(encoded)

    def predict_row(self, row: pd.Series) -> PredictionResult:
        x = row[self.features].to_numpy(dtype=float).reshape(1, -1)
        raw_pred = self.model.predict(x)[0]
        label = self._decode(raw_pred)
        proba = None
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(x)[0]
        probabilities = (
            {str(cls): float(p) for cls, p in zip(self.classes_, proba)}
            if proba is not None
            else {label: 1.0}
        )
        attack_prob = probabilities.get("ATTACK", 0.0)
        if attack_prob == 0.0 and label != "BENIGN":
            attack_prob = max(probabilities.values())
        return PredictionResult(
            label=label,
            probability=float(attack_prob if label != "BENIGN" else 1 - attack_prob),
            probabilities=probabilities,
            is_attack=label != "BENIGN",
        )

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        x = df[self.features].to_numpy(dtype=float)
        raw_labels = self.model.predict(x)
        labels = [self._decode(v) for v in raw_labels]
        output = df.copy()
        output["predicted_label"] = labels
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(x)
            if "ATTACK" in self.classes_:
                attack_idx = list(self.classes_).index("ATTACK")
                output["attack_probability"] = proba[:, attack_idx]
            else:
                output["attack_probability"] = proba.max(axis=1)
        else:
            output["attack_probability"] = (pd.Series(labels) != "BENIGN").astype(float)
        output["is_attack"] = output["predicted_label"] != "BENIGN"
        return output


def load_test_data() -> pd.DataFrame:
  return pd.read_parquet(PROCESSED_DATA_DIR / "test.parquet")
