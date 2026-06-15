import streamlit as st


def render():
    # ── Os dados ─────────────────────────────────────────────────────
    st.subheader("Os dados utilizados")
    st.markdown(
        """
        O conjunto de dados conta com **1.143 registros**, cada um
        representando um anúncio exibido para um grupo específico de
        usuários. As três campanhas disponíveis são identificadas neste
        painel como **Campanha A**, **Campanha B** e **Campanha C**.

        Para cada anúncio, estão disponíveis informações sobre quantas
        pessoas o viram, quantas clicaram, quanto foi investido e quantas
        realizaram uma compra. A partir dessas informações, foram calculadas
        métricas como ROI, taxa de conversão e custo por aquisição.

        **Nota metodológica:** o conjunto de dados original não contém o
        valor monetário de cada venda. Por isso, adotou-se um valor médio
        por pedido de **$ 50,00** como referência inicial. Esse valor pode
        ser ajustado na aba What-If para refletir diferentes realidades de
        negócio.
        """
    )

    st.divider()

    # ── Objetivo da página ────────────────────────────────────────────
    st.subheader("Objetivo deste painel")
    st.markdown(
        """
        O painel tem como objetivo **informar gestores e analistas de
        marketing sobre o desempenho das campanhas e os resultados
        esperados sob diferentes cenários de investimento**, permitindo
        que decisões de alocação de orçamento sejam tomadas com base em
        dados e não apenas em intuição.

        Cada aba do painel corresponde a um tipo de análise:

        - **Visão Geral** — diagnóstico do estado atual das campanhas
        - **What-If** — simulação de cenários de orçamento
        - **Sensibilidade** — identificação das variáveis que mais impactam o retorno
        - **Otimização** — cálculo da meta de investimento e distribuição ideal do orçamento
        """
    )

    st.divider()

    # ── Dicionário de termos ──────────────────────────────────────────
    st.subheader("Dicionário de termos")

    termos = {
        "ROI (Retorno sobre Investimento)": (
            "Mede o lucro gerado em relação ao valor investido. "
            "Calculado como (Receita − Custo) ÷ Custo. "
            "Um ROI de 1,0 significa que para cada real investido, um real de lucro foi gerado. "
            "ROI negativo indica prejuízo."
        ),
        "Conversão aprovada": (
            "Uma venda concretizada após o usuário ver e clicar no anúncio. "
            "É a métrica central do estudo — representa o resultado real das campanhas."
        ),
        "Taxa de conversão": (
            "Proporção entre o número de cliques no anúncio e o número de compras realizadas. "
            "Indica a eficiência do anúncio em transformar interesse em venda."
        ),
        "CPA (Custo por Aquisição)": (
            "Valor médio gasto em publicidade para gerar uma única venda. "
            "Quanto menor o CPA, mais barato é conquistar cada cliente."
        ),
        "Impressões": (
            "Número de vezes que o anúncio foi exibido na tela de um usuário. "
            "Uma mesma pessoa pode gerar múltiplas impressões ao ver o mesmo anúncio repetidamente."
        ),
        "Análise What-If": (
            "Técnica que simula o que aconteceria com o resultado caso uma variável fosse alterada. "
            "Exemplo: 'e se dobrássemos o orçamento — qual seria o ROI esperado?'"
        ),
        "Análise de Sensibilidade": (
            "Avalia o quanto o resultado final (ROI) muda conforme cada variável de entrada varia. "
            "Ajuda a identificar quais fatores têm mais impacto no desempenho."
        ),
        "Goal-Seek (Modelo de Metas)": (
            "Calcula o valor de entrada necessário para atingir um resultado desejado. "
            "Aqui, responde: 'quanto preciso investir para atingir X% de ROI?'"
        ),
        "Otimização de orçamento": (
            "Distribui um valor total de investimento entre as campanhas disponíveis "
            "de forma a maximizar o retorno, priorizando as campanhas com melhor histórico de ROI."
        ),
        "Valor médio por pedido (Ticket médio)": (
            "Receita média gerada por cada venda realizada. "
            "Como o dado real não está disponível no conjunto de dados, "
            "utiliza-se um valor estimado de $ 50,00, ajustável pelo usuário."
        ),
        "Campanha A / B / C": (
            "Identificadores das três campanhas de anúncios presentes nos dados. "
            "Os nomes originais foram mantidos em anonimato pela empresa. "
            "Cada campanha representa uma estratégia distinta de publicidade."
        ),
    }

    for termo, definicao in termos.items():
        with st.expander(termo):
            st.write(definicao)
