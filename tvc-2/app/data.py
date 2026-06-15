import pandas as pd
import streamlit as st
from config import PROCESSED

# Mapeamento de IDs numéricos para rótulos de exibição
CAMPANHA_NOMES = {916: "A", 936: "B", 1178: "C"}
_NOMES_PARA_ID = {v: k for k, v in CAMPANHA_NOMES.items()}


@st.cache_data
def load_marts():
    """
    Lê os três CSVs de data/processed/ sem alterar os valores originais.
    O mapeamento de 916/936/1178 para A/B/C é feito apenas na camada
    de exibição (gráficos e filtros), nunca nos dados em memória.
    """
    ads    = pd.read_csv(PROCESSED / "mart_ads_performance.csv")
    agg    = pd.read_csv(PROCESSED / "mart_aggregated.csv")
    params = pd.read_csv(PROCESSED / "mart_roi_parameters.csv")
    return ads, agg, params


def sidebar_filters(ads):
    """
    Renderiza o filtro de campanha na barra lateral.
    Exibe os rótulos amigáveis (A, B, C) mas retorna o ID numérico
    original para uso na filtragem dos DataFrames.
    """
    st.sidebar.header("Filtros")

    ids_disponiveis = sorted(ads["xyz_campaign_id"].unique())
    opcoes = ["Todas"] + [
        f"Campanha {CAMPANHA_NOMES.get(int(c), str(c))}"
        for c in ids_disponiveis
    ]
    escolha = st.sidebar.selectbox("Campanha", opcoes)

    if escolha == "Todas":
        return None

    label = escolha.split(" ")[1]           # extrai "A", "B" ou "C"
    return _NOMES_PARA_ID.get(label)        # devolve 916, 936 ou 1178


def filtrar(df, campanha_id):
    """Filtra pelo ID numérico original; retorna tudo se None."""
    if campanha_id is None:
        return df
    return df[df["xyz_campaign_id"] == campanha_id].copy()