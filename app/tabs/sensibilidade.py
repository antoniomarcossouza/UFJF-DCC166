from __future__ import annotations

from typing import TypedDict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from plots import show_plotly
from sensitivity import (
    elasticidade_relativa,
    sens_cobertura_estimada,
    sens_continuidade_por_gap,
    sens_mix_biossimilar,
    sens_sla_autorizacao,
    sweep_continuidade_por_gap,
    sweep_cobertura_estimada,
    sweep_mix_biossimilar,
    sweep_sla_autorizacao,
)


class _FiltrosSens(TypedDict):
    uf: str | None
    ano_inicio: int
    ano_fim: int


def render(
    apac: pd.DataFrame,
    pac: pd.DataFrame,
    aut: pd.DataFrame,
    ano_ini: int,
    ano_fim: int,
    uf: str | None,
) -> None:
    st.markdown(
        "**Análise de sensibilidade (Atividade 1.3):** variação sistemática de "
        "*uma* variável de política por vez e impacto em indicadores de acesso/adesão."
    )

    sub1, sub2, sub3, sub4 = st.tabs(
        [
            "Gap → Continuidade",
            "Mix de medicamentos",
            "SLA de autorização",
            "Cobertura estimada",
        ]
    )

    kw: _FiltrosSens = {"uf": uf, "ano_inicio": ano_ini, "ano_fim": ano_fim}

    with sub1:
        _render_gap(pac, kw)
    with sub2:
        _render_mix(apac, kw)
    with sub3:
        _render_sla(aut, kw)
    with sub4:
        _render_cobertura(pac, kw)


def _render_gap(pac: pd.DataFrame, kw: _FiltrosSens) -> None:
    st.markdown(
        "**Regra:** paciente contínuo se todos os intervalos entre competências "
        "consecutivas (mesmo fármaco) ≤ *gap máximo*."
    )
    gap_slider = st.slider("Gap máximo (meses)", 1, 4, 2)
    taxa = sens_continuidade_por_gap(pac, gap_slider, **kw)
    st.metric("Taxa de continuidade", f"{taxa:.1f}%")

    pontos = sweep_continuidade_por_gap(pac, **kw)
    df_curve = pd.DataFrame(
        [{"gap_max_meses": p.parametro, "pc_continuidade": p.kpi} for p in pontos]
    )
    fig = px.line(
        df_curve,
        x="gap_max_meses",
        y="pc_continuidade",
        markers=True,
        labels={"gap_max_meses": "Gap máximo (meses)", "pc_continuidade": "%"},
    )
    fig.update_layout(height=360)
    show_plotly(fig)
    el = elasticidade_relativa(pontos)
    if el is not None:
        st.info(f"Elasticidade relativa (extremos): {el:.2f}")


def _render_mix(apac: pd.DataFrame, kw: _FiltrosSens) -> None:
    st.markdown(
        "**Cenário:** migrar % das APACs de Imiglucerase para Alfataliglicerase "
        "(volume total constante; sem custo na AM)."
    )
    pct = st.slider("% migração Imiglucerase → Alfataliglicerase", 0, 100, 0, 5)
    mix = sens_mix_biossimilar(apac, pct, **kw)
    if mix:
        st.bar_chart(pd.Series(mix))

    df_sweep = sweep_mix_biossimilar(apac, **kw)
    if not df_sweep.empty:
        fig = go.Figure()
        for col in [c for c in df_sweep.columns if c != "pct_migracao"]:
            fig.add_trace(
                go.Scatter(
                    x=df_sweep["pct_migracao"],
                    y=df_sweep[col],
                    mode="lines",
                    name=col,
                )
            )
        fig.update_layout(
            xaxis_title="% migração",
            yaxis_title="APACs (cenário)",
            height=380,
        )
        show_plotly(fig)


def _render_sla(aut: pd.DataFrame, kw: _FiltrosSens) -> None:
    st.markdown(
        "**Indicador:** % dos registros mensais (peso `qt_registros`) com "
        "mediana de dias solicitação→autorização ≤ prazo-alvo."
    )
    dias = st.slider("Prazo-alvo (dias)", 5, 30, 15)
    pct_sla = sens_sla_autorizacao(aut, dias, **kw)
    st.metric("% dentro do SLA (proxy agregado)", f"{pct_sla:.1f}%")

    pontos_sla = sweep_sla_autorizacao(aut, **kw)
    df_sla = pd.DataFrame(
        [{"dias_alvo": p.parametro, "pc_dentro_sla": p.kpi} for p in pontos_sla]
    )
    fig_sla = px.line(
        df_sla,
        x="dias_alvo",
        y="pc_dentro_sla",
        markers=True,
        labels={"dias_alvo": "Dias-alvo", "pc_dentro_sla": "%"},
    )
    fig_sla.update_layout(height=360)
    show_plotly(fig_sla)


def _render_cobertura(pac: pd.DataFrame, kw: _FiltrosSens) -> None:
    st.markdown(
        "**Cenário didático:** fator de subdiagnóstico sobre coorte ativa "
        "(último ano do recorte) - não é prevalência epidemiológica."
    )
    fator = st.slider("Fator subdiagnóstico", 1.0, 2.0, 1.0, 0.1)
    n_est = sens_cobertura_estimada(pac, fator, **kw)
    st.metric("Pacientes estimados (coorte ativa × fator)", f"{n_est:,.0f}")

    pontos_cov = sweep_cobertura_estimada(pac, **kw)
    df_cov = pd.DataFrame(
        [{"fator": p.parametro, "n_pacientes": p.kpi} for p in pontos_cov]
    )
    fig_cov = px.line(
        df_cov,
        x="fator",
        y="n_pacientes",
        markers=True,
        labels={"fator": "Fator", "n_pacientes": "Pacientes"},
    )
    fig_cov.update_layout(height=360)
    show_plotly(fig_cov)
