import streamlit as st
from roi_model import goal_seek_investimento, alocar_orcamento, calc_roi
from plots import grafico_alocacao


def render(ads_completo, ads_filtrado, params):
    """
    Aba Otimização — duas seções:
    1. Goal-seek: quanto investir para atingir um ROI-alvo.
    2. Alocação ótima entre campanhas (usa dados não filtrados).
    """
    avg_order_value = float(params["avg_order_value"].iloc[0])

    # ── 1. Meta de ROI (goal-seek) ────────────────────────────────────
    st.subheader("Meta de ROI — quanto investir?")
    st.caption(
        "Informe o ROI que deseja atingir. O modelo calcula o investimento "
        "máximo permitido para atingi-lo, mantendo o número de vendas atual fixo. "
        "Quanto maior o ROI-alvo, menor será o investimento permitido."
    )

    base_spent      = ads_filtrado["spent"].sum()
    base_conversoes = ads_filtrado["approved_conversion"].sum()
    roi_atual       = calc_roi(base_spent, base_conversoes, avg_order_value)
    receita_total   = base_conversoes * avg_order_value
    roi_maximo      = calc_roi(base_spent * 0.001, base_conversoes, avg_order_value)

    col_a, col_b = st.columns(2)
    with col_a:
        roi_alvo = st.number_input(
            "ROI alvo (ex.: 0.5 = 50%)",
            min_value=0.0,
            max_value=round(roi_maximo * 0.95, 1),
            value=max(0.0, round(roi_atual, 2)),
            step=0.05,
            format="%.2f",
        )
    with col_b:
        st.metric("ROI atual", f"{roi_atual:.1%}")

    investimento_necessario = goal_seek_investimento(
        roi_alvo, base_spent, base_conversoes, avg_order_value
    )

    if investimento_necessario is not None:
        delta = investimento_necessario - base_spent
        st.metric(
            "Investimento máximo para atingir esse ROI",
            value=f"$ {investimento_necessario:,.2f}",
            delta=f"$ {delta:+,.2f} vs. atual",
        )
        st.caption(
            f"Com as {int(base_conversoes)} vendas atuais gerando "
            f"$ {receita_total:,.2f} em receita, gastar no máximo "
            f"$ {investimento_necessario:,.2f} garante ROI de {roi_alvo:.1%}."
        )
    else:
        roi_max_fmt = f"{roi_maximo:.0%}"
        st.warning(
            f"ROI alvo de {roi_alvo:.1%} não é atingível com os dados atuais. "
            f"O ROI máximo possível com {int(base_conversoes)} conversões e "
            f"receita de $ {receita_total:,.2f} é de aproximadamente {roi_max_fmt}. "
            f"Reduza o ROI alvo ou selecione uma campanha diferente no filtro lateral."
        )

    st.divider()

    # ── 2. Alocação ótima de orçamento ───────────────────────────────
    st.subheader("Alocação ótima entre campanhas")
    st.caption(
        "Distribui um orçamento total entre as campanhas proporcionalmente "
        "ao ROI histórico de cada uma. Campanhas com ROI negativo recebem zero."
    )

    total_budget = st.number_input(
        "Orçamento total a alocar (USD)",
        min_value=0.0,
        value=float(ads_completo["spent"].sum()),
        step=1000.0,
    )

    df_alloc = alocar_orcamento(ads_completo, total_budget, avg_order_value)

    col_t, col_g = st.columns(2)
    with col_t:
        st.dataframe(df_alloc, use_container_width=True, hide_index=True)
    with col_g:
        grafico_alocacao(df_alloc)

    st.caption(
        "A alocação proporcional ao ROI é uma heurística simples. "
        "Em projetos avançados, pode-se usar programação linear com "
        "restrições de retornos marginais decrescentes."
    )