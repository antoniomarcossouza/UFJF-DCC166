import streamlit as st
from data import load_marts, sidebar_filters, filtrar
from tabs import visao_geral, what_if, sensibilidade, otimizacao, sobre


st.set_page_config(
    page_title="Marketing ROI Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Avaliação de ROI de Marketing — Análise What-If")
st.caption("Dataset: Facebook Ads Conversion Tracking | Problema 11")


ads, agg, params = load_marts()

campanha_id  = sidebar_filters(ads)
ads_filtrado = filtrar(ads, campanha_id)

aba_sobre, aba_geral, aba_whatif, aba_sens, aba_otim = st.tabs([
    "ℹ️ Sobre",
    "Visão Geral",
    "What-If",
    "Sensibilidade",
    "Otimização",
])

with aba_sobre:
    sobre.render()

with aba_geral:
    visao_geral.render(ads_filtrado, agg, params)

with aba_whatif:
    what_if.render(ads_filtrado, params)

with aba_sens:
    sensibilidade.render(ads_filtrado, params)

with aba_otim:
    otimizacao.render(ads, ads_filtrado, params)