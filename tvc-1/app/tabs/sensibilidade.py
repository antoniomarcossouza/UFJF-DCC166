from __future__ import annotations

from typing import TypedDict

import pandas as pd
import plotly.express as px
import streamlit as st

from plots import show_plotly
from sensitivity import (
    elasticidade_relativa,
    sens_cobertura_estimada,
    sens_continuidade_por_gap,
    sens_sla_autorizacao,
    sweep_continuidade_por_gap,
    sweep_cobertura_estimada,
    sweep_sla_autorizacao,
)


class _FiltrosSens(TypedDict):
    uf: str | None
    medicamento: str | None
    ano_inicio: int
    ano_fim: int


def render(
    pac: pd.DataFrame,
    aut: pd.DataFrame,
    ano_ini: int,
    ano_fim: int,
    uf: str | None,
    medicamento: str | None,
) -> None:
    st.markdown(
        "Altere uma variável de política por vez e veja o que acontece com acesso e adesão nos indicadores abaixo."
    )
    if medicamento:
        st.caption(f"Recorte da sidebar: {medicamento}")

    sub1, sub2, sub3= st.tabs(
        [
            "Gap -> Continuidade",
            "SLA de autorização",
            "Cobertura estimada",
        ]
    )

    kw: _FiltrosSens = {
        "uf": uf,
        "medicamento": medicamento,
        "ano_inicio": ano_ini,
        "ano_fim": ano_fim,
    }

    with sub1:
        _render_gap(pac, kw)
    with sub2:
        _render_sla(aut, kw)
    with sub3:
        _render_cobertura(pac, kw)


def _render_gap(pac: pd.DataFrame, kw: _FiltrosSens) -> None:
    st.markdown(
        "Defina quantos meses sem dispensação ainda contam como continuidade. "
        "O indicador mostra a taxa de pares paciente e medicamento em que "
        "nenhum intervalo entre competências passa desse limite. "
        "Conta dispensações no SIA."
    )
    st.caption(
        "Regra: contínuo quando todos os intervalos entre dispensações "
        "seguidas ficam no máximo no gap escolhido."
    )
    gap_slider = st.slider("Gap máximo (meses)", 1, 12, 2)
    taxa = sens_continuidade_por_gap(pac, gap_slider, **kw)
    st.metric("Taxa de continuidade", f"{taxa:.1f}%")

    pontos = sweep_continuidade_por_gap(pac, gaps=range(1, 13), **kw)
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


def _render_sla(aut: pd.DataFrame, kw: _FiltrosSens) -> None:
    st.markdown(
        "Escolha um prazo em dias da solicitação à autorização da APAC. "
        "O percentual usa agregados mensais: mediana de dias dentro do prazo, "
        "com peso pelo número de registros em cada mês."
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
        "O SIA só traz quem teve dispensação registrada. "
        "Partimos dos pacientes distintos vistos no último ano do recorte "
        "(coorte ativa) e multiplicamos por um fator.\n\n"
        "Estimar como o tamanho da população em tratamento mudaria se parte dos casos não estivesse na base. "
        "Não é prevalência de Gaucher no país / UF."
    )
    fator = st.slider("Fator subdiagnóstico", 1.0, 2.0, 1.0, 0.1)
    n_est = sens_cobertura_estimada(pac, fator, **kw)
    st.metric("Pacientes estimados (coorte ativa x fator)", f"{n_est:,.0f}")
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
