"""Explicabilidade de alertas."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from config import OPERATIONAL_CAPTION
from plots import plotly_chart
from soc_data import get_predictor, tick_stream

from explain import explain_event
from utils.paths import REPORTS_DIR


def render() -> None:
    st.title("Explicabilidade")
    st.caption(OPERATIONAL_CAPTION)
    tick_stream()

    predictor = get_predictor()
    shap_dir = REPORTS_DIR / "shap"
    st.markdown("**Análise offline (conjunto de teste)**")
    for img_name in (
        "summary_plot.png",
        "beeswarm_plot.png",
        "dependence_plot.png",
    ):
        img_path = shap_dir / img_name
        if img_path.exists():
            st.image(str(img_path), caption=img_name.replace("_", " ").title())

    st.markdown("**Explicações de alertas recentes (janela operacional)**")
    attack_events = st.session_state.event_buffer.recent_alerts(5)
    if not attack_events:
        st.info("Nenhum alerta recente para explicar.")
        return

    for event in attack_events:
        explanation = explain_event(event.row, predictor)
        st.subheader(
            f"Evento — probabilidade {explanation['probability']:.2%}"
        )
        st.write(explanation["text"])
        contrib_df = (
            pd.DataFrame(
                list(explanation["contributions"].items()),
                columns=["Feature", "Contribuição"],
            )
            .sort_values("Contribuição", key=abs, ascending=False)
            .head(10)
        )
        fig = px.bar(
            contrib_df, x="Contribuição", y="Feature", orientation="h"
        )
        plotly_chart(fig, width="stretch")
