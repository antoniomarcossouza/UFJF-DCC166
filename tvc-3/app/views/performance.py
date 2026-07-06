"""Performance do modelo (avaliação offline)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from config import EVALUATION_BANNER
from soc_data import get_training_summary

from utils.paths import REPORTS_DIR

_CHART_FILES = (
    "confusion_matrix.png",
    "roc_curve.png",
    "pr_curve.png",
)

_CHART_INFO: dict[str, tuple[str, str]] = {
    "confusion_matrix.png": (
        "Matriz de confusão",
        "Cada célula indica quantos eventos do conjunto de teste têm uma dada "
        "classe real (eixo vertical) e uma dada classe predita (eixo horizontal). "
        "Valores na diagonal são acertos; fora dela, o modelo confundiu um tipo "
        "de tráfego com outro.",
    ),
    "roc_curve.png": (
        "Curva ROC",
        "Mostra o equilíbrio entre verdadeiros positivos (eixo vertical) e "
        "falsos positivos (eixo horizontal) ao variar o threshold de decisão. "
        "Curvas mais próximas do canto superior esquerdo indicam melhor "
        "separação entre ataque e tráfego benigno. A linha tracejada representa "
        "um classificador aleatório.",
    ),
    "pr_curve.png": (
        "Curva Precision-Recall",
        "Relaciona precision e recall para diferentes thresholds. É especialmente "
        "útil em conjuntos desbalanceados, como o de teste deste projeto. "
        "Quanto maior a área sob a curva (PR-AUC), melhor o modelo mantém "
        "precision elevada mesmo ao aumentar o recall.",
    ),
}


def _format_model_label(prefix: str) -> str:
    known = {
        "best_tuned": "Melhor modelo após tuning (Optuna)",
    }
    if prefix in known:
        return known[prefix]
    if prefix.startswith("tuned_"):
        name = prefix.removeprefix("tuned_").replace("_", " ").title()
        return f"{name} — candidato do tuning Optuna"
    if "_" in prefix:
        model, balancing = prefix.rsplit("_", 1)
        return (
            f"{model.replace('_', ' ').title()} "
            f"(balanceamento: {balancing.replace('_', ' ')})"
        )
    return prefix.replace("_", " ").title()


def _collect_model_charts(
    reports_dir: Path,
) -> list[tuple[str, list[tuple[Path, str, str]]]]:
    grouped: list[tuple[str, list[tuple[Path, str, str]]]] = []
    for model_dir in sorted(reports_dir.iterdir()):
        if not model_dir.is_dir() or model_dir.name == "shap":
            continue
        charts: list[tuple[Path, str, str]] = []
        for chart_file in _CHART_FILES:
            img_path = model_dir / chart_file
            if not img_path.exists():
                continue
            title, description = _CHART_INFO[chart_file]
            charts.append((img_path, title, description))
        if charts:
            grouped.append((_format_model_label(model_dir.name), charts))
    return grouped


def _render_chart_grid(charts: list[tuple[Path, str, str]]) -> None:
    for i in range(0, len(charts), 2):
        col_a, col_b = st.columns(2)
        for col, (img_path, title, description) in zip(
            (col_a, col_b), charts[i : i + 2]
        ):
            col.markdown(f"**{title}**")
            col.image(str(img_path))
            col.caption(description)


def render() -> None:
    st.title("Performance do Modelo")
    st.caption("Visualização de resultados finais sem treinamento.")
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

    model_charts = _collect_model_charts(REPORTS_DIR)
    if not model_charts:
        st.warning(
            "Nenhum gráfico de avaliação encontrado em `reports/`. "
            "Execute o pipeline de treino para gerá-los."
        )
        return

    st.subheader("Gráficos de avaliação no conjunto de teste")
    for model_label, charts in model_charts:
        st.markdown(f"#### {model_label}")
        _render_chart_grid(charts)
