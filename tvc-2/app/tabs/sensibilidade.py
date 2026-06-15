import numpy as np
import streamlit as st
from roi_model import calc_roi, curva_roi_por_budget
from plots import grafico_curva_sensibilidade


def render(ads, params):
    """
    Aba Sensibilidade — mostra como o ROI reage a variações no
    investimento e num segundo painel varia ticket e taxa de conversão.
    """
    avg_order_value = float(params["avg_order_value"].iloc[0])

    base_spent      = ads["spent"].sum()
    base_conversoes = ads["approved_conversion"].sum()

    # ── Curva de sensibilidade ao orçamento ───────────────────────────
    st.subheader("ROI em função do investimento")
    st.caption(
        "Cada ponto representa o ROI se o orçamento atual fosse "
        "multiplicado pelo fator indicado no eixo X."
    )

    df_curva = curva_roi_por_budget(base_spent, base_conversoes, avg_order_value)
    grafico_curva_sensibilidade(df_curva)

    st.divider()

    # ── Heatmap ticket × taxa de conversão ───────────────────────────
    st.subheader("Tabela de sensibilidade: ticket médio × taxa de conversão")
    st.caption(
        "Cada célula mostra o ROI para uma combinação de valor por pedido "
        "e taxa de conversão, mantendo o investimento atual fixo."
    )

    col_l, col_r = st.columns(2)
    with col_l:
        ticket_min = st.number_input("Ticket mínimo (USD)", value=10.0,  step=5.0)
        ticket_max = st.number_input("Ticket máximo (USD)", value=150.0, step=5.0)
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

    import pandas as pd
    df_heat = pd.DataFrame(tabela).T
    df_heat.index.name = "Taxa conv."
    st.dataframe(df_heat, use_container_width=True)
    st.caption("Linhas = taxa de conversão | Colunas = ticket médio por pedido")
