"""Dashboard SOC para apoio à decisão em segurança IoT."""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from decision_support.recommendations import generate_recommendations
from decision_support.risk_scoring import classify_risk
from explainability.shap_analysis import explain_event
from models.predict import ModelPredictor, load_test_data
from simulation.traffic_stream import TrafficStream
from utils.io import load_json
from utils.paths import MODELS_DIR, REPORTS_DIR

st.set_page_config(
    page_title="IoT Security SAD",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = [
    "Visão Geral",
    "Monitoramento em Tempo Real",
    "Centro de Alertas",
    "Explicabilidade",
    "Apoio à Decisão",
    "Simulação de Cenários",
    "Performance do Modelo",
]


@st.cache_resource
def get_predictor() -> ModelPredictor:
    return ModelPredictor()


@st.cache_data
def get_test_predictions() -> pd.DataFrame:
    predictor = get_predictor()
    test_df = load_test_data()
    return predictor.predict_batch(test_df)


@st.cache_data
def get_training_summary() -> dict:
    path = MODELS_DIR / "training_summary.json"
    if path.exists():
        return load_json(path)
    return {}


def _status_color(status: str) -> str:
    return "#2ecc71" if status == "BENIGN" else "#e74c3c"


def page_overview() -> None:
    st.title("Visão Geral do SOC IoT")
    preds = get_test_predictions()
    total = len(preds)
    attacks = int(preds["is_attack"].sum())
    benign_pct = (1 - attacks / total) * 100 if total else 0.0
    risk_scores = preds["attack_probability"]
    overall_risk = float(risk_scores.mean())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Eventos processados", f"{total:,}")
    c2.metric("Ataques detectados", f"{attacks:,}")
    c3.metric("Tráfego benigno", f"{benign_pct:.1f}%")
    c4.metric("Score de risco geral", f"{overall_risk:.2%}")

    col_a, col_b = st.columns(2)
    attack_dist = preds[preds["is_attack"]]["Label"].value_counts().head(10)
    with col_a:
        fig = px.bar(
            x=attack_dist.index.astype(str),
            y=attack_dist.values,
            labels={"x": "Tipo", "y": "Quantidade"},
            title="Distribuição de ataques",
        )
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        fig2 = px.histogram(
            preds,
            x="attack_probability",
            nbins=30,
            title="Distribuição de probabilidade de ataque",
        )
        st.plotly_chart(fig2, use_container_width=True)


def page_realtime() -> None:
    st.title("Monitoramento em Tempo Real")
    st.caption("Simulação contínua de tráfego de rede — sem entrada do usuário.")

    if "events" not in st.session_state:
        st.session_state.events = []
    if "stream" not in st.session_state:
        st.session_state.stream = TrafficStream(get_predictor())

    placeholder = st.empty()
    for _ in range(5):
        event = st.session_state.stream.next_event()
        st.session_state.events.insert(
            0,
            {
                "Timestamp": event.timestamp.strftime("%H:%M:%S"),
                "Probabilidade": f"{event.probability:.2%}",
                "Classe": event.label_pred,
                "Status": event.status,
            },
        )
        st.session_state.events = st.session_state.events[:50]
        time.sleep(0.3)

    df = pd.DataFrame(st.session_state.events)
    styled = df.style.map(
        lambda v: f"color: {_status_color(v)}" if v in {"BENIGN", "ATTACK"} else "",
        subset=["Status"],
    )
    placeholder.dataframe(styled, use_container_width=True, hide_index=True)

    if len(st.session_state.events) > 1:
        timeline = pd.DataFrame(st.session_state.events[::-1])
        timeline["idx"] = range(len(timeline))
        timeline["attack_flag"] = (timeline["Status"] == "ATTACK").astype(int)
        timeline["cum_attacks"] = timeline["attack_flag"].cumsum()
        fig = px.line(
            timeline,
            x="idx",
            y="cum_attacks",
            title="Ataques acumulados ao longo do tempo",
        )
        st.plotly_chart(fig, use_container_width=True)

    time.sleep(1)
    st.rerun()


def page_alerts() -> None:
    st.title("Centro de Alertas")
    preds = get_test_predictions()
    alerts = preds[preds["is_attack"]].copy()
    alerts["risk"] = alerts["attack_probability"].apply(
        lambda s: classify_risk(float(s)).level
    )
    alerts["confidence"] = alerts["attack_probability"]
    display = alerts[
        ["Label", "predicted_label", "confidence", "risk"]
    ].head(100)
    display = display.rename(
        columns={
            "Label": "Tipo de ataque",
            "predicted_label": "Classe prevista",
            "confidence": "Confiança",
            "risk": "Nível de risco",
        }
    )
    st.dataframe(display, use_container_width=True, hide_index=True)


def page_explainability() -> None:
    st.title("Explicabilidade")
    preds = get_test_predictions()
    attack_rows = preds[preds["is_attack"]].head(5)
    predictor = get_predictor()

    shap_dir = REPORTS_DIR / "shap"
    for img_name in ("summary_plot.png", "beeswarm_plot.png", "dependence_plot.png"):
        img_path = shap_dir / img_name
        if img_path.exists():
            st.image(str(img_path), caption=img_name.replace("_", " ").title())

    for _, row in attack_rows.iterrows():
        explanation = explain_event(row, predictor)
        st.subheader(f"Evento — probabilidade {explanation['probability']:.2%}")
        st.write(explanation["text"])
        contrib_df = pd.DataFrame(
            list(explanation["contributions"].items()),
            columns=["Feature", "Contribuição"],
        ).sort_values("Contribuição", key=abs, ascending=False).head(10)
        fig = px.bar(contrib_df, x="Contribuição", y="Feature", orientation="h")
        st.plotly_chart(fig, use_container_width=True)


def page_decision_support() -> None:
    st.title("Apoio à Decisão")
    st.caption("Motor de regras que transforma previsões em recomendações operacionais.")

    preds = get_test_predictions()
    high_risk = preds[preds["attack_probability"] >= 0.6].sort_values(
        "attack_probability", ascending=False
    ).head(20)

    for _, row in high_risk.iterrows():
        rec = generate_recommendations(float(row["attack_probability"]))
        with st.expander(
            f"[{rec.priority}] Risco {rec.risk.level} — {row['attack_probability']:.2%}",
            expanded=rec.risk.level in {"Crítico", "Alto"},
        ):
            st.write(f"**Score:** {rec.risk.score:.2%}")
            st.write(f"**Nível:** {rec.risk.level}")
            st.write("**Ações recomendadas:**")
            for action in rec.actions:
                st.markdown(f"- {action}")


def page_scenarios() -> None:
    st.title("Simulação de Cenários (What-If)")
    st.caption("Análise de sensibilidade do limiar de decisão para apoio à decisão.")

    preds = get_test_predictions()
    y_true = (preds["label_binary"] != "BENIGN").astype(int)
    scores = preds["attack_probability"]

    threshold = st.select_slider(
        "Threshold de decisão",
        options=[0.50, 0.70, 0.90],
        value=0.70,
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
    st.plotly_chart(fig, use_container_width=True)


def page_performance() -> None:
    st.title("Performance do Modelo")
    st.caption("Visualização de resultados finais — sem treinamento.")

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
    for pattern in ("**/confusion_matrix.png", "**/roc_curve.png", "**/pr_curve.png"):
        for img in sorted(reports_dir.glob(pattern))[:3]:
            st.image(str(img), caption=img.parent.name)


def main() -> None:
    st.sidebar.title("IoT Security SAD")
    st.sidebar.markdown("Sistema operacional de monitoramento")
    page = st.sidebar.radio("Navegação", PAGES)

    if page == PAGES[0]:
        page_overview()
    elif page == PAGES[1]:
        page_realtime()
    elif page == PAGES[2]:
        page_alerts()
    elif page == PAGES[3]:
        page_explainability()
    elif page == PAGES[4]:
        page_decision_support()
    elif page == PAGES[5]:
        page_scenarios()
    else:
        page_performance()


if __name__ == "__main__":
    main()
