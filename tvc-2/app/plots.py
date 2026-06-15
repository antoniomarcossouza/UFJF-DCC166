import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from config import PLOTLY_CONFIG

_CAMP_LABEL = {916: "Campanha A", 936: "Campanha B", 1178: "Campanha C"}
_CORES = {"Campanha A": "#636EFA", "Campanha B": "#EF553B", "Campanha C": "#00CC96"}


def _show(fig):
    fig.update_layout(dragmode=False)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    st.plotly_chart(fig, config=PLOTLY_CONFIG, use_container_width=True)


def _add_label(df):
    """Cria coluna campanha_label com texto completo a partir do ID numérico."""
    df = df.copy()
    df["campanha_label"] = (
        df["xyz_campaign_id"]
        .apply(lambda x: _CAMP_LABEL.get(int(x), f"Campanha {x}"))
    )
    return df


def grafico_cenarios(df_cenarios):
    df = df_cenarios.copy()
    df["ROI_num"] = df["ROI"]
    fig = px.bar(
        df,
        x="Cenário",
        y="ROI_num",
        color="ROI_num",
        color_continuous_scale="RdYlGn",
        text=df["ROI_num"].apply(lambda v: f"{v:.1%}"),
        labels={"ROI_num": "ROI"},
        title="ROI estimado por cenário de orçamento",
    )
    fig.update_traces(textposition="outside")
    fig.update_coloraxes(showscale=False)
    _show(fig)


def grafico_curva_sensibilidade(df_curva):
    fig = px.line(
        df_curva,
        x="investimento",
        y="roi",
        markers=True,
        labels={"investimento": "Investimento (USD)", "roi": "ROI"},
        title="Sensibilidade do ROI ao investimento",
    )
    fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="ROI = 0")
    _show(fig)


def grafico_dispersao(df):
    """Grafico de dispersão de investimento x conversões aprovadas."""
    df = _add_label(df)
    fig = go.Figure()

    for label, grupo in df.groupby("campanha_label"):
        label = str(label)
        fig.add_trace(go.Scatter(
            x=grupo["spent"].tolist(),
            y=grupo["approved_conversion"].tolist(),
            mode="markers",
            name=label,
            marker=dict(color=_CORES.get(label, "#999999"), opacity=0.6, size=6),
        ))

    fig.update_layout(
        title="Investimento vs. Conversões",
        xaxis_title="Investimento (USD)",
        yaxis_title="Conversões aprovadas",
        legend_title="Campanha",
    )
    _show(fig)


def grafico_roi_por_campanha(df_agg):
    df = _add_label(df_agg).sort_values("roi_agregado")
    fig = go.Figure(go.Bar(
        x=df["roi_agregado"].tolist(),
        y=df["campanha_label"].tolist(),
        orientation="h",
        text=[f"{v:.1%}" for v in df["roi_agregado"]],
        textposition="outside",
        marker_color=[_CORES.get(str(l), "#999999") for l in df["campanha_label"]],
    ))
    fig.update_layout(
        title="ROI por campanha (visão completa)",
        xaxis_title="ROI agregado",
        yaxis_title="Campanha",
    )
    _show(fig)


def grafico_alocacao(df_alloc):
    fig = go.Figure(go.Pie(
        labels=df_alloc["Campanha"].tolist(),
        values=df_alloc["Alocação (USD)"].tolist(),
        textinfo="label+percent",
    ))
    fig.update_layout(title="Alocação de orçamento recomendada")
    _show(fig)