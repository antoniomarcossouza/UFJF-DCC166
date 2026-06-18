"""Monitoramento em tempo real."""

from __future__ import annotations

import time

import pandas as pd
import plotly.express as px
import streamlit as st
from config import OPERATIONAL_CAPTION, status_color
from plots import plotly_chart
from soc_data import operational_dataframe, push_next_event


def render() -> None:
    st.title("Monitoramento em Tempo Real")
    st.caption(OPERATIONAL_CAPTION)

    placeholder = st.empty()
    for _ in range(5):
        push_next_event()
        time.sleep(0.3)

    df = (
        operational_dataframe()
        .sort_values("timestamp", ascending=False)
        .head(50)
    )
    display = pd.DataFrame(
        {
            "Timestamp": pd.to_datetime(df["timestamp"]).dt.strftime(
                "%H:%M:%S"
            ),
            "Probabilidade": df["attack_probability"].map(
                lambda v: f"{v:.2%}"
            ),
            "Classe": df["label_pred"],
            "Status": df["is_attack"].map(
                lambda is_attack: "ATTACK" if is_attack else "BENIGN"
            ),
        }
    )
    styled = display.style.map(
        lambda v: (
            f"color: {status_color(v)}" if v in {"BENIGN", "ATTACK"} else ""
        ),
        subset=["Status"],
    )
    placeholder.dataframe(styled, width="stretch", hide_index=True)

    if len(display) > 1:
        timeline = display.iloc[::-1].copy()
        timeline["idx"] = range(len(timeline))
        timeline["attack_flag"] = (timeline["Status"] == "ATTACK").astype(int)
        timeline["cum_attacks"] = timeline["attack_flag"].cumsum()
        fig = px.line(
            timeline,
            x="idx",
            y="cum_attacks",
            title="Alertas acumulados ao longo do tempo",
        )
        plotly_chart(fig, width="stretch")

    time.sleep(1)
    st.rerun()
