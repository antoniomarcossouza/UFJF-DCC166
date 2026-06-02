"""Análise de sensibilidade para o SAD Gaucher (sem custo - foco em acesso/adesão)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

IMIGLUCERASE = "Imiglucerase 400 U"
ALFATALI = "Alfataliglicerase 200 U"


@dataclass(frozen=True)
class SensitivityPoint:
    """Um ponto da curva de sensibilidade."""

    parametro: float | int
    kpi: float
    descricao: str


def _filter_period(
    df: pd.DataFrame,
    *,
    uf: str | None,
    ano_inicio: int,
    ano_fim: int,
    medicamento: str | None = None,
    uf_col: str = "cd_uf_residencia",
) -> pd.DataFrame:
    out = df.copy()
    if "dt_ano_mes" in out.columns:
        anos = out["dt_ano_mes"].astype(str).str.slice(0, 4).astype(int)
        out = out[(anos >= ano_inicio) & (anos <= ano_fim)]
    if uf and uf != "BR" and uf_col in out.columns:
        out = out[out[uf_col] == uf]
    if medicamento and "nm_medicamento" in out.columns:
        out = out[out["nm_medicamento"] == medicamento]
    return out


def sens_continuidade_por_gap(
    df_pac_mes: pd.DataFrame,
    gap_max_meses: int,
    *,
    uf: str | None = None,
    medicamento: str | None = None,
    ano_inicio: int = 2016,
    ano_fim: int = 2025,
) -> float:
    """
    Taxa de pacientes com continuidade: nenhum intervalo entre competências
    consecutivas excede gap_max_meses (mesma linha terapêutica).
    """
    df = _filter_period(
        df_pac_mes,
        uf=uf,
        ano_inicio=ano_inicio,
        ano_fim=ano_fim,
        medicamento=medicamento,
    )
    if df.empty:
        return 0.0

    violacoes = df.groupby(["cd_paciente_hash", "nm_medicamento"], observed=True)[
        "nu_gap_meses_desde_anterior"
    ].apply(lambda s: (s.dropna() > gap_max_meses).any())
    n_pacientes = violacoes.shape[0]
    if n_pacientes == 0:
        return 0.0
    n_continuos = (~violacoes).sum()
    return 100.0 * n_continuos / n_pacientes


def sweep_continuidade_por_gap(
    df_pac_mes: pd.DataFrame,
    gaps: range | list[int] | None = None,
    **kwargs,
) -> list[SensitivityPoint]:
    """Varre gap_max_meses e retorna taxa de continuidade para cada valor."""
    if gaps is None:
        gaps = range(1, 13)
    return [
        SensitivityPoint(
            parametro=g,
            kpi=sens_continuidade_por_gap(df_pac_mes, g, **kwargs),
            descricao=f"Gap máximo {g} mês(es) entre dispensações",
        )
        for g in gaps
    ]


def sens_sla_autorizacao(
    df_autoriz: pd.DataFrame,
    dias_alvo: int,
    *,
    uf: str | None = None,
    medicamento: str | None = None,
    ano_inicio: int = 2016,
    ano_fim: int = 2025,
) -> float:
    """
    % de registros mensais (peso qt_registros) com p50 de dias solicitação->autorização
    dentro de dias_alvo. Proxy agregado quando não há microdados linha a linha.
    """
    df = _filter_period(
        df_autoriz,
        uf=uf,
        ano_inicio=ano_inicio,
        ano_fim=ano_fim,
        medicamento=medicamento,
    )
    if df.empty or df["qt_registros"].sum() == 0:
        return 0.0
    dentro = df["qt_dias_p50"] <= dias_alvo
    return 100.0 * df.loc[dentro, "qt_registros"].sum() / df["qt_registros"].sum()


def sweep_sla_autorizacao(
    df_autoriz: pd.DataFrame,
    dias_range: range | list[int] | None = None,
    **kwargs,
) -> list[SensitivityPoint]:
    """Varre dias-alvo de SLA e retorna % dentro do prazo."""
    if dias_range is None:
        dias_range = range(5, 31, 5)
    return [
        SensitivityPoint(
            parametro=d,
            kpi=sens_sla_autorizacao(df_autoriz, d, **kwargs),
            descricao=f"Prazo-alvo {d} dias (solicitação → autorização)",
        )
        for d in dias_range
    ]


def sens_cobertura_estimada(
    df_pac_mes: pd.DataFrame,
    fator_subdiagnostico: float,
    *,
    uf: str | None = None,
    medicamento: str | None = None,
    ano_inicio: int = 2016,
    ano_fim: int = 2025,
) -> float:
    """
    Estima pacientes na coorte se fator_subdiagnostico > 1 (ex.: 1.2 = +20% não detectados).
    Coorte ativa = pacientes distintos no último ano do recorte.
    """
    df = _filter_period(
        df_pac_mes,
        uf=uf,
        ano_inicio=ano_inicio,
        ano_fim=ano_fim,
        medicamento=medicamento,
    )
    if df.empty:
        return 0.0
    fator = max(1.0, fator_subdiagnostico)
    ultimo_ano = df["dt_ano_mes"].astype(str).str.slice(0, 4).astype(int).max()
    df_ultimo = df[
        df["dt_ano_mes"].astype(str).str.slice(0, 4).astype(int) == ultimo_ano
    ]
    n_ativos = df_ultimo["cd_paciente_hash"].nunique()
    return n_ativos * fator


def sweep_cobertura_estimada(
    df_pac_mes: pd.DataFrame,
    fatores: np.ndarray | list[float] | None = None,
    **kwargs,
) -> list[SensitivityPoint]:
    """Varre fator de subdiagnóstico (1.0 = baseline)."""
    if fatores is None:
        fatores = np.round(np.arange(1.0, 2.01, 0.1), 1)
    return [
        SensitivityPoint(
            parametro=round(float(f), 2),
            kpi=sens_cobertura_estimada(df_pac_mes, float(f), **kwargs),
            descricao=f"Fator subdiagnóstico {f:.1f}x sobre coorte ativa",
        )
        for f in fatores
    ]


def elasticidade_relativa(
    pontos: list[SensitivityPoint],
) -> float | None:
    """Elasticidade ponta a ponta: (ΔKPI/KPI) / (Δparam/param) entre extremos."""
    if len(pontos) < 2:
        return None
    p0, p1 = pontos[0], pontos[-1]
    if p0.parametro == p1.parametro or p0.kpi == 0:
        return None
    dk = (p1.kpi - p0.kpi) / p0.kpi
    dp = (float(p1.parametro) - float(p0.parametro)) / float(p0.parametro)
    if dp == 0:
        return None
    return dk / dp
