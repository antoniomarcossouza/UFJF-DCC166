"""Visão geral operacional do SOC."""

from __future__ import annotations

import plotly.express as px
import streamlit as st
from config import OPERATIONAL_CAPTION
from plots import plotly_chart
from soc_data import operational_dataframe, tick_stream


def render() -> None:
    st.title("Visão Geral do SOC IoT")
    st.caption(OPERATIONAL_CAPTION)
    tick_stream()

    df = operational_dataframe()
    total = len(df)
    alerts = int(df["is_attack"].sum()) if total else 0
    benign_pct = float((~df["is_attack"]).mean() * 100) if total else 0.0
    alert_scores = df.loc[df["is_attack"], "attack_probability"]
    overall_risk = float(alert_scores.mean()) if len(alert_scores) else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Eventos na janela", f"{total:,}")
    c2.metric("Alertas gerados", f"{alerts:,}")
    c3.metric("Taxa classificada como benigno", f"{benign_pct:.1f}%")
    c4.metric("Risco médio dos alertas", f"{overall_risk:.2%}")

    col_a, col_b = st.columns(2)
    alert_df = df[df["is_attack"]]
    with col_a:
        if alert_df.empty:
            st.info("Nenhum alerta na janela atual.")
        else:
            alert_dist = alert_df["label_pred"].value_counts()
            fig = px.bar(
                x=alert_dist.index.astype(str),
                y=alert_dist.values,
                labels={"x": "Classe prevista", "y": "Quantidade"},
                title="Distribuição de alertas",
            )
            plotly_chart(fig, width="stretch")
    with col_b:
        fig2 = px.histogram(
            df,
            x="attack_probability",
            nbins=30,
            title="Distribuição de probabilidade de ataque (janela)",
        )
        plotly_chart(fig2, width="stretch")
