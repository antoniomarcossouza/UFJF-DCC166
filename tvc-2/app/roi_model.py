import numpy as np
import pandas as pd
from scipy.optimize import root_scalar

_CAMP_LABEL = {916: "Campanha A", 936: "Campanha B", 1178: "Campanha C"}


def calc_roi(spent, conversoes, avg_order_value):
    """ROI = (receita - custo) / custo."""
    if spent <= 0:
        return 0.0
    receita = conversoes * avg_order_value
    return (receita - spent) / spent


# ── What-If ───────────────────────────────────────────────────────────────────

def simular_cenario(base_spent, base_conversoes, fator_budget, fator_conv, avg_order_value):
    novo_spent       = base_spent      * fator_budget
    novas_conversoes = base_conversoes * fator_conv
    return calc_roi(novo_spent, novas_conversoes, avg_order_value)


def tabela_cenarios(base_spent, base_conversoes, avg_order_value):
    cenarios = [
        ("Corte de 50%",        0.50, 0.50),
        ("Manutenção (base)",   1.00, 1.00),
        ("Aumento de 50%",      1.50, 1.00),
        ("Dobrar investimento", 2.00, 1.00),
    ]
    linhas = []
    for nome, fb, fc in cenarios:
        spent      = base_spent      * fb
        conversoes = base_conversoes * fc
        receita    = conversoes      * avg_order_value
        roi        = calc_roi(spent, conversoes, avg_order_value)
        linhas.append({
            "Cenário":          nome,
            "Investimento":     round(spent, 2),
            "Conversões est.":  round(conversoes, 1),
            "Receita est.":     round(receita, 2),
            "ROI":              round(roi, 4),
        })
    return pd.DataFrame(linhas)


# ── Sensibilidade ─────────────────────────────────────────────────────────────

def curva_roi_por_budget(base_spent, base_conversoes, avg_order_value):
    fatores = np.arange(0.5, 2.1, 0.1)
    linhas  = []
    for f in fatores:
        spent      = base_spent * f
        conversoes = base_conversoes * f
        roi        = calc_roi(spent, conversoes, avg_order_value)
        linhas.append({
            "fator":        round(f, 1),
            "investimento": round(spent, 2),
            "roi":          round(roi, 4),
        })
    return pd.DataFrame(linhas)


# ── Meta (Goal-Seek) ──────────────────────────────────────────────────────────

def goal_seek_investimento(roi_alvo, base_spent, base_conversoes, avg_order_value):
    """
    Encontra o investimento necessário para atingir roi_alvo,
    mantendo o número de conversões FIXO no valor atual.

    Com conversões fixas, aumentar o gasto diminui o ROI e reduzir
    o gasto aumenta o ROI — a função é monótona e a bisseção converge.

    Interpretação: "quanto posso gastar no máximo para ainda atingir
    esse ROI, com a mesma quantidade de vendas de hoje?"
    """
    receita_fixa = base_conversoes * avg_order_value

    def objetivo(spent):
        if spent <= 0:
            return -roi_alvo
        roi = (receita_fixa - spent) / spent
        return roi - roi_alvo

    # O ROI só é positivo se receita > spent
    # Limite superior: um pouco abaixo da receita total (ROI quase zero)
    spent_max = receita_fixa * 0.9999
    spent_min = base_spent * 0.001

    # Verificar se o alvo é atingível: ROI em spent_min deve ser >= roi_alvo
    if objetivo(spent_min) < 0:
        return None  # alvo maior que o ROI máximo possível

    # Verificar se ROI em spent_max é menor que o alvo (deve ser negativo)
    if objetivo(spent_max) >= 0:
        return None  # alvo menor que o ROI mínimo possível

    try:
        sol = root_scalar(
            objetivo,
            bracket=[spent_min, spent_max],
            method="bisect",
        )
        return round(sol.root, 2) if sol.converged else None
    except ValueError:
        return None


# ── Otimização ────────────────────────────────────────────────────────────────

def alocar_orcamento(df, total_budget, avg_order_value):
    """
    Distribui o orçamento entre campanhas proporcionalmente ao ROI histórico.
    Usa o ID numérico original para agrupar e converte para rótulo só na saída.
    """
    roi_por_camp = df.groupby("xyz_campaign_id").apply(
        lambda g: calc_roi(
            g["spent"].sum(),
            g["approved_conversion"].sum(),
            avg_order_value,
        )
    ).clip(lower=0)

    total_roi = roi_por_camp.sum()
    if total_roi == 0:
        alocacao = pd.Series(
            total_budget / len(roi_por_camp),
            index=roi_por_camp.index,
        )
    else:
        alocacao = (roi_por_camp / total_roi) * total_budget

    linhas = []
    for camp_id in roi_por_camp.index:
        linhas.append({
            "Campanha":       _CAMP_LABEL.get(int(camp_id), f"Campanha {camp_id}"),
            "Alocação (USD)": round(float(alocacao[camp_id]), 2),
            "ROI histórico":  round(float(roi_por_camp[camp_id]), 4),
        })
    return pd.DataFrame(linhas)