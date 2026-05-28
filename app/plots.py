from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import PLOTLY_CONFIG
from data import filter_pac, nunique_pacientes

# Paleta por teoria das cores (HSL equilibrado: S≈52%, L≈46%).
# TRE: harmonia análoga no setor frio (azul → ciano → violeta-azulado).
# Miglustate (ISS): complementar quente (~25°) - contraste semântico com os TRE.
# Total: neutro ardósia (baixa saturação), não compete com as séries.
_MED_SERIE_STYLE: dict[str, dict[str, str]] = {
    "Imiglucerase": {"color": "#3A9E8F", "symbol": "circle"},  # H≈206°
    "Alfavelaglicerase": {"color": "#C17B4A", "symbol": "square"},  # H≈172°
    "Alfataliglicerase": {"color": "#6F6EBB", "symbol": "diamond"},  # H≈238°
    "Miglustate": {"color": "#4A7EBB", "symbol": "triangle-up"},  # H≈26°
}
_SERIE_TOTAL_COLOR = "#64748B"
_MED_SERIE_FALLBACK_COLORS = ["#7A9BB8", "#5BA898", "#9A8FBB", "#C9956E"]
_MED_SERIE_FALLBACK_SYMBOLS = ["star", "x", "cross", "triangle-down"]


def _estilo_serie_med(nome: str, indice: int) -> dict[str, str]:
    for prefixo, estilo in _MED_SERIE_STYLE.items():
        if nome.startswith(prefixo):
            return estilo
    return {
        "color": _MED_SERIE_FALLBACK_COLORS[indice % len(_MED_SERIE_FALLBACK_COLORS)],
        "symbol": _MED_SERIE_FALLBACK_SYMBOLS[indice % len(_MED_SERIE_FALLBACK_SYMBOLS)],
    }


def _freeze_plotly(fig) -> None:
    """Desativa zoom/pan por arrasto e rolagem no gráfico."""
    fig.update_layout(dragmode=False)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)


def show_plotly(fig) -> None:
    _freeze_plotly(fig)
    st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)


def _trace_serie_med(sub: pd.DataFrame, nome: str, indice: int) -> go.Scatter:
    estilo = _estilo_serie_med(nome, indice)
    cor = estilo["color"]
    sub = sub.sort_values("dt_label")
    return go.Scatter(
        x=sub["dt_label"],
        y=sub["qt_pacientes"],
        mode="lines+markers",
        name=nome,
        line=dict(color=cor, width=2),
        marker=dict(
            symbol=estilo["symbol"],
            size=6,
            color=cor,
            line=dict(width=0.8, color="white"),
        ),
    )


def fig_serie_pacientes_ativos(
    pac: pd.DataFrame,
    ano_ini: int,
    ano_fim: int,
    uf: str | None,
    medicamento: str | None,
) -> go.Figure:
    """Série mensal: por medicamento (+ total pontilhado quando sem filtro de fármaco)."""
    labels = {
        "dt_label": "Competência",
        "qt_pacientes": "Pacientes",
        "nm_medicamento": "Medicamento",
    }

    if medicamento:
        fp = filter_pac(pac, ano_ini, ano_fim, uf, medicamento)
        serie = nunique_pacientes(fp, "dt_ano_mes")
        serie["dt_label"] = pd.to_datetime(serie["dt_ano_mes"].astype(str), format="%Y%m")
        fig = go.Figure(_trace_serie_med(serie, medicamento, 0))
        fig.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=30, b=20),
            showlegend=False,
            xaxis_title=labels["dt_label"],
            yaxis_title=labels["qt_pacientes"],
        )
        return fig

    fp = filter_pac(pac, ano_ini, ano_fim, uf, medicamento=None)
    serie_med = nunique_pacientes(fp, ["dt_ano_mes", "nm_medicamento"])
    serie_med["dt_label"] = pd.to_datetime(serie_med["dt_ano_mes"].astype(str), format="%Y%m")

    serie_total = nunique_pacientes(fp, "dt_ano_mes")
    serie_total["dt_label"] = pd.to_datetime(serie_total["dt_ano_mes"].astype(str), format="%Y%m")
    serie_total = serie_total.sort_values("dt_label")

    fig = go.Figure()
    for i, med in enumerate(sorted(serie_med["nm_medicamento"].unique())):
        sub = serie_med[serie_med["nm_medicamento"] == med]
        fig.add_trace(_trace_serie_med(sub, med, i))

    fig.add_trace(
        go.Scatter(
            x=serie_total["dt_label"],
            y=serie_total["qt_pacientes"],
            mode="lines",
            name="Total (distintos)",
            line=dict(dash="dot", color=_SERIE_TOTAL_COLOR, width=2),
        )
    )
    fig.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis_title=labels["dt_label"],
        yaxis_title=labels["qt_pacientes"],
    )
    return fig
