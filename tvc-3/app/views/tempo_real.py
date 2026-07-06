"""Monitoramento em tempo real."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from config import OPERATIONAL_CAPTION, status_color
from plots import plotly_chart
from soc_data import operational_dataframe, tick_stream
from utils.config import load_config

_REFRESH_SECONDS = load_config()["simulation"]["interval_seconds"]
_TABLE_HEIGHT = 420
_VISIBLE_EVENTS = 50


def _build_display_df(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
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


def _style_display(display: pd.DataFrame) -> pd.io.formats.style.Styler:
    return display.style.map(
        lambda v: (
            f"color: {status_color(v)}" if v in {"BENIGN", "ATTACK"} else ""
        ),
        subset=["Status"],
    )


@st.fragment(run_every=_REFRESH_SECONDS)
def _live_panel() -> None:
    paused = st.toggle(
        "Pausar atualização",
        value=False,
        help="Congela a tabela para leitura sem novos eventos.",
    )

    if not paused:
        tick_stream()

    df = (
        operational_dataframe()
        .sort_values("timestamp", ascending=False)
        .head(_VISIBLE_EVENTS)
    )

    alerts = int(df["is_attack"].sum()) if not df.empty else 0
    benign = len(df) - alerts
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Eventos na tabela", len(df))
    c2.metric("Alertas", alerts)
    c3.metric("Benignos", benign)
    c4.metric(
        "Atualizado às",
        datetime.now().strftime("%H:%M:%S"),
    )

    st.markdown(f"**Últimos {_VISIBLE_EVENTS} eventos**")
    if df.empty:
        st.info("Aguardando eventos na simulação...")
        return

    display = _build_display_df(df)
    st.dataframe(
        _style_display(display),
        height=_TABLE_HEIGHT,
        width="stretch",
        hide_index=True,
    )

    if len(display) > 1:
        timeline = display.iloc[::-1].copy()
        timeline["idx"] = range(len(timeline))
        timeline["attack_flag"] = (timeline["Status"] == "ATTACK").astype(int)
        timeline["cum_attacks"] = timeline["attack_flag"].cumsum()
        fig = px.line(
            timeline,
            x="idx",
            y="cum_attacks",
            labels={
                "idx": "Eventos (mais antigo → recente)",
                "cum_attacks": "Alertas acumulados",
            },
            title="Alertas acumulados na janela visível",
        )
        plotly_chart(fig, width="stretch")


def render() -> None:
    st.title("Monitoramento em Tempo Real")
    st.caption(
        f"{OPERATIONAL_CAPTION} Atualização automática a cada "
        f"{_REFRESH_SECONDS:g}s."
    )
    _live_panel()
