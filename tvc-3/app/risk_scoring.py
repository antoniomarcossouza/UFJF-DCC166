"""Pontuação de risco para alertas do dashboard."""

from __future__ import annotations

from dataclasses import dataclass

from utils.config import load_config


@dataclass
class RiskAssessment:
    score: float
    level: str


def classify_risk(
    score: float, thresholds: dict[str, float] | None = None
) -> RiskAssessment:
    """Classifica risco em Baixo/Médio/Alto/Crítico."""
    config = load_config()
    thresholds = thresholds or config["risk"]
    if score >= thresholds["critical"]:
        level = "Crítico"
    elif score >= thresholds["high"]:
        level = "Alto"
    elif score >= thresholds["medium"]:
        level = "Médio"
    else:
        level = "Baixo"
    return RiskAssessment(score=score, level=level)
