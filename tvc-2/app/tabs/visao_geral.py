import streamlit as st
from roi_model import calc_roi
from plots import grafico_dispersao, grafico_roi_por_campanha


def render(ads, agg, params):
    avg_order_value = params["avg_order_value"].iloc[0]

    total_spent      = ads["spent"].sum()
    total_conversoes = ads["approved_conversion"].sum()
    roi_atual        = calc_roi(total_spent, total_conversoes, avg_order_value)
    n_anuncios       = len(ads)

    st.caption(
        "Os valores refletem o conjunto de anúncios do período "
        "selecionado na barra lateral — escolha uma campanha específica ou "
        "mantenha 'Todas' para ver o desempenho consolidado."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Investimento total",   f"$ {total_spent:,.2f}")
    c2.metric("Conversões aprovadas", f"{int(total_conversoes):,}")
    c3.metric("ROI (período)",        f"{roi_atual:.1%}")
    c4.metric("Anúncios analisados",  f"{n_anuncios:,}")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.caption(
            "Cada ponto representa um anúncio. Anúncios com alto investimento "
            "e poucas conversões indicam ineficiência pontual na campanha."
        )
        grafico_dispersao(ads)
    with col_b:
        st.caption(
            "ROI calculado sobre os totais de cada campanha (receita total "
            "menos gasto total, dividido pelo gasto). Independente do filtro "
            "lateral — exibe sempre as três campanhas para comparação direta."
        )
        grafico_roi_por_campanha(agg)