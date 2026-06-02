from __future__ import annotations

import streamlit as st

from config import ANO_FIM, ANO_INICIO, PROCESSED
from data import load_marts, sidebar_filters
from tabs import (
    render_continuidade,
    render_metodologia,
    render_sensibilidade,
    render_visao_geral,
)


def main() -> None:
    st.set_page_config(
        page_title="TVC 1 DCC166",
        page_icon="📊",
        layout="wide",
    )
    st.title("SAD: Doença de Gaucher no SUS")
    st.caption(f"SIA-AM · {ANO_INICIO}-{ANO_FIM} · Análise de sensibilidade")

    if not (PROCESSED / "mart_apac_mensal.parquet").exists():
        st.error(
            "Marts não encontrados em `data/processed/`. "
            "Execute `notebooks/02_etl_mart.ipynb` para materializar os marts."
        )
        st.stop()

    apac, pac, aut = load_marts()
    ano_ini, ano_fim, uf, medicamento = sidebar_filters(apac)

    t1, t2, t3, t4 = st.tabs(
        ["Visão geral", "Continuidade", "Sensibilidade", "Metodologia"]
    )
    with t1:
        render_visao_geral(apac, pac, ano_ini, ano_fim, uf, medicamento)
    with t2:
        render_continuidade(pac, ano_ini, ano_fim, uf, medicamento)
    with t3:
        render_sensibilidade(pac, aut, ano_ini, ano_fim, uf, medicamento)
    with t4:
        render_metodologia()


if __name__ == "__main__":
    main()
