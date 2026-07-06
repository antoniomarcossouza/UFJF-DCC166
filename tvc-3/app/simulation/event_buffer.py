"""Buffer rolante de eventos operacionais do dashboard."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime

import pandas as pd
from risk_scoring import classify_risk

from simulation.traffic_stream import TrafficEvent


@dataclass
class BufferedEvent:
    timestamp: datetime
    row_index: int
    label_pred: str
    attack_probability: float
    is_attack: bool
    risk_level: str
    row: pd.Series

    @classmethod
    def from_traffic_event(
        cls, event: TrafficEvent, row: pd.Series
    ) -> BufferedEvent:
        risk = classify_risk(event.probability)
        return cls(
            timestamp=event.timestamp,
            row_index=event.row_index,
            label_pred=event.label_pred,
            attack_probability=event.probability,
            is_attack=event.status == "ATTACK",
            risk_level=risk.level,
            row=row,
        )


class EventBuffer:
    """FIFO com capacidade fixa para janela operacional."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self._events: deque[BufferedEvent] = deque(maxlen=capacity)

    def push(self, event: BufferedEvent) -> None:
        self._events.append(event)

    def extend(self, events: list[BufferedEvent]) -> None:
        for event in events:
            self.push(event)

    def __len__(self) -> int:
        return len(self._events)

    def __iter__(self):
        return iter(self._events)

    def to_dataframe(self) -> pd.DataFrame:
        if not self._events:
            return pd.DataFrame(
                columns=[
                    "timestamp",
                    "row_index",
                    "label_pred",
                    "attack_probability",
                    "is_attack",
                    "risk_level",
                ]
            )
        return pd.DataFrame(
            [
                {
                    "timestamp": e.timestamp,
                    "row_index": e.row_index,
                    "label_pred": e.label_pred,
                    "attack_probability": e.attack_probability,
                    "is_attack": e.is_attack,
                    "risk_level": e.risk_level,
                }
                for e in self._events
            ]
        )

    def alerts(self) -> list[BufferedEvent]:
        return [e for e in self._events if e.is_attack]

    def recent_alerts(self, n: int) -> list[BufferedEvent]:
        return [e for e in reversed(self._events) if e.is_attack][:n]
