import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from roi_model import calc_roi


def render(ads, params):
    avg_order_value = float(params["avg_order_value"].iloc[0])

    base_spent      = ads["spent"].sum()
    base_conversoes = ads["approved_conversion"].sum()

    # ── Dispersão CPA × ROI por anúncio ──────────────────────────────
    st.caption(
        "A análise de sensibilidade identifica quais anúncios entregam o melhor "
        "retorno em relação ao que custam, e quais variáveis — preço do produto "
        "ou taxa de conversão — mais impactam o resultado final."
    )

    st.subheader("Custo por aquisição vs. ROI por anúncio")
    st.caption(
        "Cada ponto é um anúncio com pelo menos uma venda aprovada. "
        "Eixo horizontal: quanto custou cada venda naquele anúncio (CPA). "
        "Eixo vertical: o ROI gerado por aquele anúncio. "
        "Pontos no canto superior esquerdo são os mais eficientes — "
        "baixo custo por venda e alto retorno."
    )

    df_plot = ads[ads["approved_conversion"] > 0].copy()
    df_plot["cpa"] = df_plot["spent"] / df_plot["approved_conversion"]
    df_plot["roi"] = (
        (df_plot["approved_conversion"] * avg_order_value - df_plot["spent"])
        / df_plot["spent"]
    )
    df_plot["campanha_label"] = df_plot["xyz_campaign_id"].apply(
        lambda x: f"Campanha {({916: 'A', 936: 'B', 1178: 'C'}.get(int(x), str(x)))}"
    )

    cores = {"Campanha A": "#636EFA", "Campanha B": "#EF553B", "Campanha C": "#00CC96"}
    fig_disp = go.Figure()
    for label, grupo in df_plot.groupby("campanha_label"):
        fig_disp.add_trace(go.Scatter(
            x=grupo["cpa"].tolist(),
            y=grupo["roi"].tolist(),
            mode="markers",
            name=str(label),
            marker=dict(color=cores.get(str(label), "#999999"), opacity=0.6, size=7),
        ))
    fig_disp.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="ROI = 0")
    fig_disp.update_layout(
        title="Custo por aquisição (CPA) vs. ROI por anúncio",
        xaxis_title="CPA — custo de cada venda (USD)",
        yaxis_title="ROI do anúncio",
        legend_title="Campanha",
        dragmode=False,
    )
    fig_disp.update_xaxes(fixedrange=True)
    fig_disp.update_yaxes(fixedrange=True)
    st.plotly_chart(fig_disp, use_container_width=True,
                    config={"displayModeBar": False})

    st.divider()

    # ── Heatmap ticket × taxa de conversão ───────────────────────────
    st.subheader("Tabela de sensibilidade: ticket médio × taxa de conversão")
    st.caption(
        "Cada célula mostra o ROI para uma combinação de valor por pedido "
        "e taxa de conversão, mantendo o investimento atual fixo."
    )

    col_l, col_r = st.columns(2)
    with col_l:
        ticket_min = st.number_input("Preço mínimo (USD)", value=10.0,  step=5.0)
        ticket_max = st.number_input("Preço máximo (USD)", value=150.0, step=5.0)
    with col_r:
        taxa_min = st.number_input("Taxa conv. mínima", value=0.01, step=0.01, format="%.2f")
        taxa_max = st.number_input("Taxa conv. máxima", value=0.15, step=0.01, format="%.2f")

    tickets = np.linspace(ticket_min, ticket_max, 6).round(0).astype(int).tolist()
    taxas   = np.linspace(taxa_min,   taxa_max,   6).round(3).tolist()
    clicks  = ads["clicks"].sum()

    tabela = {}
    for taxa in taxas:
        linha = {}
        for ticket in tickets:
            conversoes = clicks * taxa
            roi        = calc_roi(base_spent, conversoes, ticket)
            linha[f"$ {ticket}"] = f"{roi:.1%}"
        tabela[f"{taxa:.3f}"] = linha

    df_heat = pd.DataFrame(tabela).T
    df_heat.index.name = "Taxa conv."
    st.dataframe(df_heat, use_container_width=True)
    st.caption("Linhas = taxa de conversão | Colunas = ticket médio por pedido")
