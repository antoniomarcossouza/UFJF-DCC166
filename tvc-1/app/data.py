from __future__ import annotations

import pandas as pd
import streamlit as st

from config import ANO_FIM, ANO_INICIO, PROCESSED, UF_NOMES


@st.cache_data
def load_marts() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    apac = pd.read_parquet(PROCESSED / "mart_apac_mensal.parquet")
    pac = pd.read_parquet(PROCESSED / "mart_paciente_mes.parquet")
    aut = pd.read_parquet(PROCESSED / "mart_autorizacao.parquet")
    return apac, pac, aut


def anos_disponiveis(df: pd.DataFrame) -> list[int]:
    return sorted(df["dt_ano_mes"].astype(str).str.slice(0, 4).astype(int).unique())


def sidebar_filters(
    apac: pd.DataFrame,
) -> tuple[int, int, str | None, str | None]:
    st.sidebar.header("Filtros")
    anos = anos_disponiveis(apac)
    if not anos:
        anos = list(range(ANO_INICIO, ANO_FIM + 1))
    ano_ini = st.sidebar.selectbox("Ano inicial", anos, index=0)
    ano_fim = st.sidebar.selectbox("Ano final", anos, index=len(anos) - 1)
    if ano_ini > ano_fim:
        ano_ini, ano_fim = ano_fim, ano_ini

    ufs = sorted(apac["cd_uf_residencia"].dropna().unique())
    uf_opts = ["BR - Brasil"] + [f"{u} - {UF_NOMES.get(u, u)}" for u in ufs]
    uf_sel = st.sidebar.selectbox("UF residência", uf_opts)
    uf = None if uf_sel.startswith("BR") else uf_sel.split(" - ")[0]

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


def nunique_pacientes(df: pd.DataFrame, by: str | list[str]) -> pd.DataFrame:
    """groupby + agg → DataFrame (evita union Series|DataFrame nos stubs do pandas)."""
    return df.groupby(by, observed=True, as_index=False).agg(
        qt_pacientes=("cd_paciente_hash", "nunique")
    )
