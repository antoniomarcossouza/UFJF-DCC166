"""Inferência com modelos treinados."""

from __future__ import annotations

from dataclasses import dataclass

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

    def _is_benign_label(self, label: str) -> bool:
        return label.upper() in {"BENIGN", "BENIGNTRAFFIC"}

    def _attack_probability(
        self, label: str, probabilities: dict[str, float]
    ) -> float:
        if "ATTACK" in probabilities:
            return probabilities["ATTACK"]
        benign_prob = next(
            (
                prob
                for cls, prob in probabilities.items()
                if self._is_benign_label(cls)
            ),
            0.0,
        )
        if benign_prob > 0:
            return 1.0 - benign_prob
        if self._is_benign_label(label):
            return 1.0 - max(probabilities.values(), default=0.0)
        return max(probabilities.values(), default=0.0)

    def predict_row(self, row: pd.Series) -> PredictionResult:
        x = row[self.features].to_numpy(dtype=float).reshape(1, -1)
        raw_pred = self.model.predict(x)[0]
        label = self._decode(raw_pred)
        proba = None
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(x)[0]
        probabilities = (
            {
                str(cls): float(p)
                for cls, p in zip(self.classes_, proba, strict=False)
            }
            if proba is not None
            else {label: 1.0}
        )
        attack_prob = self._attack_probability(label, probabilities)
        return PredictionResult(
            label=label,
            probability=float(attack_prob),
            probabilities=probabilities,
            is_attack=not self._is_benign_label(label),
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
                benign_idx = next(
                    (
                        i
                        for i, cls in enumerate(self.classes_)
                        if self._is_benign_label(str(cls))
                    ),
                    None,
                )
                if benign_idx is not None:
                    output["attack_probability"] = 1.0 - proba[:, benign_idx]
                else:
                    output["attack_probability"] = proba.max(axis=1)
        else:
            output["attack_probability"] = (
                pd.Series(labels).map(
                    lambda lbl: not self._is_benign_label(lbl)
                )
            ).astype(float)
        output["is_attack"] = output["predicted_label"].map(
            lambda lbl: not self._is_benign_label(str(lbl))
        )
        return output


def load_test_data() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED_DATA_DIR / "test.parquet")
