import streamlit as st
from roi_model import calc_roi, simular_cenario, tabela_cenarios
from plots import grafico_cenarios


def render(ads, params):
    """
    Aba What-If — o usuário ajusta dois sliders e vê o ROI simulado
    em tempo real, além da tabela com os quatro cenários fixos.
    """
    avg_order_value = st.sidebar.number_input(
        "Valor médio por pedido (USD)",
        min_value=1.0,
        max_value=500.0,
        value=float(params["avg_order_value"].iloc[0]),
        step=5.0,
        help="Receita estimada por conversão aprovada. Ajuste conforme o seu negócio.",
    )

    base_spent      = ads["spent"].sum()
    base_conversoes = ads["approved_conversion"].sum()
    roi_base        = calc_roi(base_spent, base_conversoes, avg_order_value)

    st.subheader("Situação atual")
    c1, c2, c3 = st.columns(3)
    c1.metric("Investimento base",  f"$ {base_spent:,.2f}")
    c2.metric("Conversões base",    f"{int(base_conversoes):,}")
    c3.metric("ROI base",           f"{roi_base:.1%}")

    st.divider()
    st.subheader("Simular cenário personalizado")
    st.caption(
        "Mova os controles abaixo para ver o impacto no ROI. "
        "O modelo assume que as conversões escalam linearmente com o orçamento."
    )

    col_l, col_r = st.columns(2)
    with col_l:
        fator_budget = st.slider(
            "Fator de investimento",
            min_value=0.1, max_value=3.0, value=1.0, step=0.1,
            help="1.0 = sem alteração | 1.5 = 50% a mais | 0.5 = metade do orçamento",
        )
    with col_r:
        fator_conv = st.slider(
            "Fator de conversão",
            min_value=0.1, max_value=3.0, value=1.0, step=0.1,
            help="Simula melhorias na taxa de conversão independentes do orçamento.",
        )

    roi_simulado = simular_cenario(base_spent, base_conversoes, fator_budget, fator_conv, avg_order_value)
    delta        = roi_simulado - roi_base

    st.metric(
        "ROI simulado",
        value=f"{roi_simulado:.1%}",
        delta=f"{delta:+.1%} vs. base",
    )

    st.divider()
    st.subheader("Quatro cenários fixos")
    st.caption("Cenários padronizados calculados sobre os dados do filtro atual.")

    df_cen = tabela_cenarios(base_spent, base_conversoes, avg_order_value)
    df_cen["ROI"] = df_cen["ROI"].apply(lambda v: f"{v:.1%}")
    st.dataframe(df_cen, use_container_width=True, hide_index=True)

    grafico_cenarios(tabela_cenarios(base_spent, base_conversoes, avg_order_value))
