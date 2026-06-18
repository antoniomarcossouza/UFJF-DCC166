"""Utilitários de visualização do dashboard."""

from typing import Any

import streamlit as st
from config import PLOTLY_CONFIG


def plotly_chart(fig: Any, **kwargs) -> None:
    st.plotly_chart(fig, config=PLOTLY_CONFIG, **kwargs)
