"""Gerador de eventos de tráfego para simulação operacional."""

from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd

from models.predict import ModelPredictor
from simulation.traffic_mixer import TrafficMixer
from utils.config import load_config
from utils.io import load_dataframe
from utils.paths import PROCESSED_DATA_DIR


@dataclass
class TrafficEvent:
    timestamp: datetime
    row_index: int
    label_true: str
    label_pred: str
    probability: float
    status: str
    attack_type: str
    row: pd.Series


class TrafficStream:
    """Emula chegada contínua de eventos de rede com mix estratificado."""

    def __init__(self, predictor: ModelPredictor | None = None) -> None:
        self.config = load_config()
        self.predictor = predictor or ModelPredictor()
        self.test_df = load_dataframe(PROCESSED_DATA_DIR / "test.parquet")
        self._mixer = TrafficMixer(self.test_df)

    def next_event(self) -> TrafficEvent:
        idx, row = self._mixer.next_row()
        prediction = self.predictor.predict_row(row)
        status = "ATTACK" if prediction.is_attack else "BENIGN"
        return TrafficEvent(
            timestamp=datetime.now(timezone.utc),
            row_index=idx,
            label_true=str(row.get("label_binary", "UNKNOWN")),
            label_pred=prediction.label,
            probability=prediction.probability,
            status=status,
            attack_type=str(row.get("Label", prediction.label)),
            row=row,
        )

    def stream(self, max_events: int | None = None) -> Iterator[TrafficEvent]:
        limit = max_events or self.config["simulation"]["max_events"]
        for _ in range(limit):
            yield self.next_event()
            time.sleep(self.config["simulation"]["interval_seconds"])
