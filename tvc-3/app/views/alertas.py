"""Centro de alertas operacionais."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from config import OPERATIONAL_CAPTION
from soc_data import tick_stream


def render() -> None:
    st.title("Centro de Alertas")
    st.caption(OPERATIONAL_CAPTION)
    tick_stream()

    alerts = st.session_state.event_buffer.alerts()
    if not alerts:
        st.info("Nenhum alerta na janela operacional.")
        return

    display = pd.DataFrame(
        [
            {
                "Timestamp": e.timestamp.strftime("%H:%M:%S"),
                "Classe prevista": e.label_pred,
                "Confiança": e.attack_probability,
                "Nível de risco": e.risk_level,
            }
            for e in reversed(alerts)
        ]
    ).head(100)
    st.dataframe(display, width="stretch", hide_index=True)
