"""
SAD — Doença de Gaucher no SUS (SIA-AM)
Dashboard Streamlit com análise de sensibilidade (TVC 1.3).
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from sensitivity import (
    elasticidade_relativa,
    sens_continuidade_por_gap,
    sens_cobertura_estimada,
    sens_mix_biossimilar,
    sens_sla_autorizacao,
    sweep_continuidade_por_gap,
    sweep_cobertura_estimada,
    sweep_mix_biossimilar,
    sweep_sla_autorizacao,
)

ANO_INICIO = 2016
ANO_FIM = 2026

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED = BASE_DIR / "data" / "processed"

UF_NOMES = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}


@st.cache_data
def load_marts() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    apac = pd.read_parquet(PROCESSED / "mart_apac_mensal.parquet")
    pac = pd.read_parquet(PROCESSED / "mart_paciente_mes.parquet")
    aut = pd.read_parquet(PROCESSED / "mart_autorizacao.parquet")
    return apac, pac, aut


def _anos_disponiveis(df: pd.DataFrame) -> list[int]:
    return sorted(df["dt_ano_mes"].astype(str).str.slice(0, 4).astype(int).unique())


def sidebar_filters(
    apac: pd.DataFrame,
) -> tuple[int, int, str | None, str | None]:
    st.sidebar.header("Filtros")
    anos = _anos_disponiveis(apac)
    if not anos:
        anos = list(range(ANO_INICIO, ANO_FIM + 1))
    ano_ini = st.sidebar.selectbox("Ano inicial", anos, index=0)
    ano_fim = st.sidebar.selectbox("Ano final", anos, index=len(anos) - 1)
    if ano_ini > ano_fim:
        ano_ini, ano_fim = ano_fim, ano_ini

    ufs = sorted(apac["cd_uf_residencia"].dropna().unique())
    uf_opts = ["BR — Brasil"] + [f"{u} — {UF_NOMES.get(u, u)}" for u in ufs]
    uf_sel = st.sidebar.selectbox("UF residência", uf_opts)
    uf = None if uf_sel.startswith("BR") else uf_sel.split(" — ")[0]

    meds = ["Todos"] + sorted(apac["nm_medicamento"].dropna().unique().tolist())
    med_sel = st.sidebar.selectbox("Medicamento", meds)
    medicamento = None if med_sel == "Todos" else med_sel

    return ano_ini, ano_fim, uf, medicamento


def filter_apac(
    df: pd.DataFrame,
    ano_ini: int,
    ano_fim: int,
    uf: str | None,
    medicamento: str | None,
) -> pd.DataFrame:
    out = df.copy()
    anos = out["dt_ano_mes"].astype(str).str.slice(0, 4).astype(int)
    out = out[(anos >= ano_ini) & (anos <= ano_fim)]
    if uf:
        out = out[out["cd_uf_residencia"] == uf]
    if medicamento:
        out = out[out["nm_medicamento"] == medicamento]
    return out


def filter_pac(
    df: pd.DataFrame,
    ano_ini: int,
    ano_fim: int,
    uf: str | None,
    medicamento: str | None,
) -> pd.DataFrame:
    out = df.copy()
    anos = out["dt_ano_mes"].astype(str).str.slice(0, 4).astype(int)
    out = out[(anos >= ano_ini) & (anos <= ano_fim)]
    if uf:
        out = out[out["cd_uf_residencia"] == uf]
    if medicamento:
        out = out[out["nm_medicamento"] == medicamento]
    return out


def tab_visao_geral(
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

    st.subheader("Série mensal — pacientes ativos")
    serie = (
        fp.groupby("dt_ano_mes", observed=True)["cd_paciente_hash"]
        .nunique()
        .reset_index(name="qt_pacientes")
    )
    serie["dt_label"] = pd.to_datetime(serie["dt_ano_mes"].astype(str), format="%Y%m")
    fig = px.line(
        serie,
        x="dt_label",
        y="qt_pacientes",
        markers=True,
        labels={"dt_label": "Competência", "qt_pacientes": "Pacientes"},
    )
    fig.update_layout(height=380, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Mix de medicamentos (% APACs)")
        mix_df = (
            fa.groupby("nm_medicamento", observed=True)["qt_apacs"].sum().reset_index()
        )
        fig_mix = px.bar(
            mix_df.sort_values("qt_apacs", ascending=True),
            x="qt_apacs",
            y="nm_medicamento",
            orientation="h",
            labels={"qt_apacs": "APACs", "nm_medicamento": ""},
        )
        fig_mix.update_layout(height=360, showlegend=False)
        st.plotly_chart(fig_mix, use_container_width=True)

    with col_b:
        st.subheader("Pacientes por UF (residência)")
        uf_df = (
            fp.groupby("cd_uf_residencia", observed=True)["cd_paciente_hash"]
            .nunique()
            .reset_index(name="qt_pacientes")
        )
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
        st.plotly_chart(fig_uf, use_container_width=True)


def tab_continuidade(
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
    st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig2, use_container_width=True)


def tab_sensibilidade(
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

    kw = dict(uf=uf, ano_inicio=ano_ini, ano_fim=ano_fim)

    with sub1:
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
        st.plotly_chart(fig, use_container_width=True)
        el = elasticidade_relativa(pontos)
        if el is not None:
            st.info(f"Elasticidade relativa (extremos): {el:.2f}")

    with sub2:
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
            st.plotly_chart(fig, use_container_width=True)

    with sub3:
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
        st.plotly_chart(fig_sla, use_container_width=True)

    with sub4:
        st.markdown(
            "**Cenário didático:** fator de subdiagnóstico sobre coorte ativa "
            "(último ano do recorte) — não é prevalência epidemiológica."
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
        st.plotly_chart(fig_cov, use_container_width=True)


def tab_metodologia() -> None:
    st.markdown(
        f"""
### Fonte e recorte
- **Base:** SIA — grupo **AM** (APAC de medicamentos), via [PySUS](https://pysus.readthedocs.io/).
- **Período:** {ANO_INICIO}–{ANO_FIM}, Brasil.
- **Procedimentos Gaucher:** Imiglucerase, Alfavelaglicerase, Alfataliglicerase (TRE); Miglustate (ISS).

### Materialização (`data/processed/`)
- Agregação DuckDB a partir de `data/raw/` (notebook `02_etl_mart.ipynb`).
- **Privacidade:** CNS substituído por hash SHA-256 (10 caracteres hex).

### Modelagem analítica — sensibilidade
Sem custo na AM (`vl_apac_aprovada` zerado); indicadores de **continuidade**, **mix** e **prazo de autorização**.

| Variável | Indicador |
|----------|-----------|
| Gap máximo entre dispensações | % pacientes contínuos |
| % migração Imiglucerase → biossimilar | Volume de APACs por fármaco |
| Prazo-alvo de autorização | % registros dentro do SLA (proxy p50) |
| Fator de subdiagnóstico | Coorte ativa estimada |

### Limitações
- Sem mortalidade (SIM), desfeitos clínicos ou custo real (necessário SIA-PA/SIGTAP).
- Continuidade operacional ≠ adesão clínica individual.
- Referência externa: Borin et al. (2024), *Front. Pharmacol.* — coorte nacional 16 anos.

### Referência
Borin et al. (2024). Gaucher disease in Brazil. DOI [10.3389/fphar.2024.1433970](https://doi.org/10.3389/fphar.2024.1433970).
        """
    )


def main() -> None:
    st.set_page_config(
        page_title="SAD Gaucher — SUS",
        page_icon="📊",
        layout="wide",
    )
    st.title("SAD — Doença de Gaucher no SUS")
    st.caption(
        f"Sistema de apoio à decisão · SIA-AM · {ANO_INICIO}–{ANO_FIM} · "
        "Análise de sensibilidade"
    )

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
        tab_visao_geral(apac, pac, ano_ini, ano_fim, uf, medicamento)
    with t2:
        tab_continuidade(pac, ano_ini, ano_fim, uf, medicamento)
    with t3:
        tab_sensibilidade(apac, pac, aut, ano_ini, ano_fim, uf)
    with t4:
        tab_metodologia()


if __name__ == "__main__":
    main()
