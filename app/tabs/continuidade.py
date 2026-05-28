from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data import filter_pac
from plots import show_plotly
from sensitivity import sens_continuidade_por_gap


def _gap_distrib_df(
    gaps: pd.Series, max_meses: int = 12
) -> tuple[pd.DataFrame, list[object]]:
    """Contagens por mês inteiro de gap (0..max_meses e cauda 13+)."""
    g = gaps.dropna().astype(int)
    n_total = len(g)
    vc = g.value_counts()
    rows: list[dict[str, object]] = []
    for m in range(max_meses + 1):
        qt = int(vc.get(m, 0))
        rows.append(
            {
                "mes_gap": str(m),
                "qt": qt,
                "pc": 100.0 * qt / n_total if n_total else 0.0,
            }
        )
    tail = int((g > max_meses).sum())
    rows.append(
        {
            "mes_gap": "13+",
            "qt": tail,
            "pc": 100.0 * tail / n_total if n_total else 0.0,
        }
    )
    labels = [r["mes_gap"] for r in rows]
    return pd.DataFrame(rows), labels


def _fig_distribuicao_gaps(df_hist: pd.DataFrame, labels: list[str]):
    """Barras por mês inteiro; escala log; todas as categorias incluindo 13+."""
    qt = df_hist["qt"].to_numpy(dtype=float)
    # Log não aceita 0: altura mínima 1 só para desenhar; hover usa contagem real.
    y_plot = np.where(qt > 0, qt, 1.0)
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=y_plot,
            customdata=df_hist[["qt", "pc"]].to_numpy(),
            hovertemplate=(
                "Gap: %{x}<br>"
                "%{customdata[0]:,} transições (%{customdata[1]:.1f}%)"
                "<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        height=360,
        showlegend=False,
        bargap=0.15,
        margin=dict(l=20, r=48, t=20, b=48),
        xaxis_title="Meses desde dispensa anterior",
    )
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=labels)
    fig.update_yaxes(
        type="log",
        title="Dispensações consecutivas (escala log)",
    )
    return fig


def render(
    pac: pd.DataFrame,
    ano_ini: int,
    ano_fim: int,
    uf: str | None,
    medicamento: str | None,
) -> None:
    st.markdown(
        """
**Competência** é o mês de referência da dispensa/APAC (`YYYYMM`). \n
**Gap** é o intervalo em meses de calendário entre a competência anterior e a atual,
para o mesmo paciente e o mesmo medicamento.

Esta aba mostra: \n
- 1. Com que frequência os gaps entre dispensações consecutivas são
curtos ou longos;
- 2. Em cada medicamento, qual fração de pacientes nunca ultrapassa
2 meses entre dispensações no período filtrado.
        """
    )

    fp = filter_pac(pac, ano_ini, ano_fim, uf, medicamento)
    gaps = fp["nu_gap_meses_desde_anterior"].dropna()

    st.subheader("Intervalo entre dispensações consecutivas")
    df_hist, labels = _gap_distrib_df(gaps)
    show_plotly(_fig_distribuicao_gaps(df_hist, labels))

    st.caption(
        "Cada barra conta transições entre duas competências consecutivas "
        "(mesmo paciente e medicamento), não pacientes. A primeira dispensa do paciente "
        "no medicamento não entra. Barras = meses inteiros; Eixo Y em escala log₁₀."
    )

    tbl = df_hist.rename(
        columns={
            "mes_gap": "Mês de gap",
            "qt": "N transições",
            "pc": "% do total",
        }
    ).copy()
    tbl["N transições"] = tbl["N transições"].map("{:,}".format)
    tbl["% do total"] = tbl["% do total"].map(lambda x: f"{x:.1f}%")
    with st.expander("Tabela de contagens por mês de gap"):
        st.dataframe(tbl, hide_index=True, height=490)

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

    st.caption(
        "Percentual de pacientes com aquele medicamento em que todos os gaps "
        "consecutivos no período filtrado são ≤ 2 meses. Um único intervalo maior "
        "classifica o paciente como sem continuidade."
    )
