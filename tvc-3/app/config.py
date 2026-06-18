"""Constantes e configuração do dashboard."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


@dataclass(frozen=True)
class NavItem:
    id: str
    icon: str
    label: str
    section: str  # "operacional" | "avaliacao"

    @property
    def sidebar_label(self) -> str:
        return f"{self.icon}  {self.label}"


NAV_ITEMS: list[NavItem] = [
    NavItem("visao_geral", "📊", "Visão Geral", "operacional"),
    NavItem("tempo_real", "⚡", "Tempo Real", "operacional"),
    NavItem("alertas", "🚨", "Alertas", "operacional"),
    NavItem("explicabilidade", "🔍", "Explicabilidade", "operacional"),
    NavItem("cenarios", "🔧", "What-If", "avaliacao"),
    NavItem("performance", "📈", "Performance", "avaliacao"),
]

NAV_BY_ID = {item.id: item for item in NAV_ITEMS}
OPERATIONAL_PAGE_IDS = {
    item.id for item in NAV_ITEMS if item.section == "operacional"
}

OPERATIONAL_CAPTION = (
    "Simulação operacional — mix 50% benigno / 50% ataque. "
    "Não reflete o conjunto de teste."
)

EVALUATION_BANNER = (
    "Avaliação offline no conjunto de teste (desbalanceado: ~97% ataque). "
    "Use para calibrar threshold, não para interpretar tráfego operacional."
)

# Desativa toolbar, zoom por scroll, pan e duplo-clique para reset
PLOTLY_CONFIG = {
    "displayModeBar": False,
    "scrollZoom": False,
    "doubleClick": False,
    "staticPlot": True,
}


def status_color(status: str) -> str:
    return "#2ecc71" if status == "BENIGN" else "#e74c3c"
