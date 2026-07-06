"""Dashboard SOC para apoio à decisão em segurança IoT."""

from __future__ import annotations

from collections.abc import Callable

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

_PAGE_RENDERERS: dict[str, Callable[[], None]] = {
    "visao_geral": visao_geral.render,
    "tempo_real": tempo_real.render,
    "alertas": alertas.render,
    "explicabilidade": explicabilidade.render,
    "cenarios": cenarios.render,
    "performance": performance.render,
}

_SECTION_LABELS = {
    "operacional": "Monitoramento",
    "avaliacao": "Avaliação do modelo",
}


def _page_callable(item_id: str) -> Callable[[], None]:
    render = _PAGE_RENDERERS[item_id]

    if item_id not in OPERATIONAL_PAGE_IDS:
        return render

    def page() -> None:
        init_operational_state()
        render()

    page.__name__ = item_id
    return page


def _build_navigation():
    sections: dict[str, list[st.Page]] = {}
    for section_key, section_label in _SECTION_LABELS.items():
        pages = [
            st.Page(
                _page_callable(item.id),
                title=item.label,
                icon=item.icon,
                url_path=item.id,
                default=item.id == NAV_ITEMS[0].id,
            )
            for item in NAV_ITEMS
            if item.section == section_key
        ]
        if pages:
            sections[section_label] = pages

    return st.navigation(sections, expanded=True)


def main() -> None:
    page = _build_navigation()
    page.run()


if __name__ == "__main__":
    main()
