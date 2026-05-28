from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from data import filter_pac
from plots import show_plotly
from sensitivity import sens_continuidade_por_gap


def render(
    pac: pd.DataFrame,
    ano_ini: int,
    ano_fim: int,
    uf: str | None,
    medicamento: str | None,
) -> None:
    fp = filter_pac(pac, ano_ini, ano_fim, uf, medicamento)
    gaps = fp["nu_gap_meses_desde_anterior"].dropna()

    st.subheader("Distribuição de gaps entre competências")
    fig = px.histogram(
        gaps,
        nbins=20,
        labels={"value": "Meses desde dispensa anterior"},
    )
    fig.update_layout(height=360, showlegend=False)
    show_plotly(fig)

    st.caption(
        "Gap = meses entre competências consecutivas do mesmo paciente e medicamento. "
        "Primeira competência do paciente não entra no histograma."
    )

    st.subheader("Continuidade por medicamento (gap ≤ 2 meses)")
    rows = []
    for med in fp["nm_medicamento"].dropna().unique():
        sub = fp[fp["nm_medicamento"] == med]
        taxa = sens_continuidade_por_gap(
            sub, 2, uf=None, ano_inicio=ano_ini, ano_fim=ano_fim
        )
        rows.append({"nm_medicamento": med, "pc_continuidade": taxa})
    if rows:
        df_cont = pd.DataFrame(rows)
        fig2 = px.bar(
            df_cont,
            x="nm_medicamento",
            y="pc_continuidade",
            labels={"pc_continuidade": "% continuidade", "nm_medicamento": ""},
        )
        fig2.update_layout(height=340)
        show_plotly(fig2)
