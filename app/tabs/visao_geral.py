from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config import UF_NOMES
from data import filter_apac, filter_pac, nunique_pacientes
from plots import fig_serie_pacientes_ativos, show_plotly
from sensitivity import sens_continuidade_por_gap


def render(
    apac: pd.DataFrame,
    pac: pd.DataFrame,
    ano_ini: int,
    ano_fim: int,
    uf: str | None,
    medicamento: str | None,
) -> None:
    fa = filter_apac(apac, ano_ini, ano_fim, uf, medicamento)
    fp = filter_pac(pac, ano_ini, ano_fim, uf, medicamento)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("APACs (período)", f"{fa['qt_apacs'].sum():,.0f}")
    c2.metric("Pacientes distintos", f"{fp['cd_paciente_hash'].nunique():,.0f}")
    gap_def = 2
    c3.metric(
        f"Continuidade (gap ≤ {gap_def} m)",
        f"{sens_continuidade_por_gap(fp, gap_def, uf=uf, ano_inicio=ano_ini, ano_fim=ano_fim):.1f}%",
    )
    mix = fa.groupby("nm_medicamento", observed=True)["qt_apacs"].sum()
    if not mix.empty:
        c4.metric("Medicamento dominante", mix.idxmax())

    st.subheader("Série mensal - pacientes ativos")
    show_plotly(fig_serie_pacientes_ativos(pac, ano_ini, ano_fim, uf, medicamento))
    if medicamento is None:
        st.caption(
            "Linhas sólidas: pacientes distintos naquele medicamento no mês. "
            "Pontilhado: total distinto no mês (qualquer fármaco); soma das linhas "
            "pode exceder o total se houver paciente em mais de um medicamento."
        )

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Mix de medicamentos (% APACs)")
        mix_df = fa.groupby("nm_medicamento", observed=True, as_index=False).agg(
            qt_apacs=("qt_apacs", "sum")
        )
        fig_mix = px.bar(
            mix_df.sort_values("qt_apacs", ascending=True),
            x="qt_apacs",
            y="nm_medicamento",
            orientation="h",
            labels={"qt_apacs": "APACs", "nm_medicamento": ""},
        )
        fig_mix.update_layout(height=360, showlegend=False)
        show_plotly(fig_mix)

    with col_b:
        st.subheader("Pacientes por UF (residência)")
        uf_df = nunique_pacientes(fp, "cd_uf_residencia")
        uf_df["nm_uf"] = uf_df["cd_uf_residencia"].map(
            lambda u: UF_NOMES.get(str(u), str(u))
        )
        fig_uf = px.bar(
            uf_df.sort_values("qt_pacientes", ascending=True),
            x="qt_pacientes",
            y="nm_uf",
            orientation="h",
            labels={"qt_pacientes": "Pacientes", "nm_uf": "UF"},
        )
        fig_uf.update_layout(height=360)
        show_plotly(fig_uf)
