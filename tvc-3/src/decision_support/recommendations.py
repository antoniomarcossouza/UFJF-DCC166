"""Motor de recomendações para apoio à decisão."""

from __future__ import annotations

from dataclasses import dataclass

from decision_support.risk_scoring import RiskAssessment, classify_risk


@dataclass
class Recommendation:
    risk: RiskAssessment
    actions: list[str]
    priority: str


def generate_recommendations(score: float) -> Recommendation:
    """Traduz score de risco em ações operacionais."""
    risk = classify_risk(score)
    if risk.level == "Crítico":
        actions = [
            "Bloquear dispositivo de origem",
            "Gerar incidente crítico no SOC",
            "Isolar segmento de rede afetado",
        ]
        priority = "P1"
    elif risk.level == "Alto":
        actions = [
            "Iniciar investigação imediata",
            "Elevar monitoramento do ativo",
            "Notificar analista responsável",
        ]
        priority = "P2"
    elif risk.level == "Médio":
        actions = [
            "Monitorar continuamente o tráfego",
            "Correlacionar com eventos recentes",
        ]
        priority = "P3"
    else:
        actions = [
            "Registrar evento para auditoria",
            "Manter observação passiva",
        ]
        priority = "P4"
    return Recommendation(risk=risk, actions=actions, priority=priority)
