"""Dashboard SOC para apoio à decisão em segurança IoT."""

from __future__ import annotations

import streamlit as st
from config import NAV_ITEMS, OPERATIONAL_PAGE_IDS
from soc_data import init_operational_state
from views import (
    alertas,
    cenarios,
    explicabilidade,
    performance,
    tempo_real,
    visao_geral,
)

st.set_page_config(
    page_title="IoT Security SAD",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

_PAGE_RENDERERS = {
    "visao_geral": visao_geral.render,
    "tempo_real": tempo_real.render,
    "alertas": alertas.render,
    "explicabilidade": explicabilidade.render,
    "cenarios": cenarios.render,
    "performance": performance.render,
}


def main() -> None:
    if "page_id" not in st.session_state:
        st.session_state.page_id = NAV_ITEMS[0].id

    st.sidebar.title("IoT Security SAD")
    st.sidebar.caption("Centro de operações de segurança")

    operational = [item for item in NAV_ITEMS if item.section == "operacional"]
    evaluation = [item for item in NAV_ITEMS if item.section == "avaliacao"]

    st.sidebar.markdown("**Monitoramento**")
    for item in operational:
        if st.sidebar.button(
            item.sidebar_label,
            key=f"nav_{item.id}",
            use_container_width=True,
            type="primary"
            if st.session_state.get("page_id") == item.id
            else "secondary",
        ):
            st.session_state.page_id = item.id

    st.sidebar.divider()
    st.sidebar.markdown("**Avaliação do modelo**")
    for item in evaluation:
        if st.sidebar.button(
            item.sidebar_label,
            key=f"nav_{item.id}",
            use_container_width=True,
            type="primary"
            if st.session_state.get("page_id") == item.id
            else "secondary",
        ):
            st.session_state.page_id = item.id

    page_id = st.session_state.page_id

    if page_id in OPERATIONAL_PAGE_IDS:
        init_operational_state()

    _PAGE_RENDERERS[page_id]()


if __name__ == "__main__":
    main()
