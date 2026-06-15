import streamlit as st
from roi_model import goal_seek_investimento, alocar_orcamento, calc_roi
from plots import grafico_alocacao


def render(ads_completo, ads_filtrado, params):
    """
    Aba Otimização — duas seções:
    1. Goal-seek: quanto investir para atingir um ROI-alvo.
    2. Alocação ótima entre campanhas (usa dados não filtrados).

    'ads_completo' = todas as campanhas (para a otimização de alocação)
    'ads_filtrado' = dados do filtro atual (para o goal-seek)
    """
    avg_order_value = float(params["avg_order_value"].iloc[0])

    # ── 1. Meta de ROI (goal-seek) ────────────────────────────────────
    st.subheader("Meta de ROI — quanto investir?")
    st.caption(
        "Informe o ROI que deseja atingir e o modelo calcula o "
        "investimento necessário, mantendo a taxa de conversão atual."
    )

    base_spent      = ads_filtrado["spent"].sum()
    base_conversoes = ads_filtrado["approved_conversion"].sum()
    roi_atual       = calc_roi(base_spent, base_conversoes, avg_order_value)

    col_a, col_b = st.columns(2)
    with col_a:
        roi_alvo = st.number_input(
            "ROI alvo (ex.: 0.5 = 50%)",
            min_value=-1.0, max_value=10.0,
            value=round(roi_atual + 0.1, 2),
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
            "Investimento necessário",
            value=f"$ {investimento_necessario:,.2f}",
            delta=f"$ {delta:+,.2f} vs. atual",
        )
    else:
        st.warning(
            "Não foi possível encontrar um investimento para esse ROI alvo. "
            "Tente um valor menor ou verifique os dados filtrados."
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
