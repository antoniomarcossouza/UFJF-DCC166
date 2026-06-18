"""Performance do modelo (avaliação offline)."""

from __future__ import annotations

import streamlit as st
from config import EVALUATION_BANNER
from soc_data import get_training_summary

from utils.paths import REPORTS_DIR


def render() -> None:
    st.title("Performance do Modelo")
    st.caption("Visualização de resultados finais — sem treinamento.")
    st.info(EVALUATION_BANNER)

    summary = get_training_summary()
    if summary:
        st.subheader("Melhor modelo selecionado")
        st.write(
            f"**Modelo:** {summary.get('best_model', 'N/A')} | "
            f"**Balanceamento:** {summary.get('balancing', 'N/A')}"
        )
        metrics = summary.get("metrics", {})
        cols = st.columns(len(metrics) or 1)
        for col, (name, value) in zip(cols, metrics.items()):
            col.metric(name.upper(), f"{value:.4f}")

    reports_dir = REPORTS_DIR
    for pattern in (
        "**/confusion_matrix.png",
        "**/roc_curve.png",
        "**/pr_curve.png",
    ):
        for img in sorted(reports_dir.glob(pattern))[:3]:
            st.image(str(img), caption=img.parent.name)
