"""Simulação de cenários (avaliação offline)."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from config import EVALUATION_BANNER
from plots import plotly_chart
from soc_data import get_test_predictions


def render() -> None:
    st.title("Simulação de Cenários (What-If)")
    st.info(EVALUATION_BANNER)

    preds = get_test_predictions()
    total = len(preds)
    benign_pct = float((preds["label_binary"] == "BENIGN").mean() * 100)
    st.caption(
        f"Conjunto de teste: {total:,} eventos:"
        f"{benign_pct:.1f}% benigno / {100 - benign_pct:.1f}% ataque (rótulos reais)."
    )

    y_true = (preds["label_binary"] != "BENIGN").astype(int)
    scores = preds["attack_probability"]

    threshold = st.select_slider(
        "Threshold de decisão",
        options=[round(i * 0.1, 1) for i in range(11)],
        value=0.7,
    )
    y_pred = (scores >= threshold).astype(int)
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Falsos positivos", fp)
    c2.metric("Falsos negativos", fn)
    c3.metric("Precision", f"{precision:.2%}")
    c4.metric("Recall", f"{recall:.2%}")

    fig = go.Figure(
        data=[
            go.Bar(name="FP", x=["Impacto"], y=[fp], marker_color="#e74c3c"),
            go.Bar(name="FN", x=["Impacto"], y=[fn], marker_color="#f39c12"),
        ]
    )
    fig.update_layout(title="Impacto do threshold", barmode="group")
    plotly_chart(fig, width="stretch")
