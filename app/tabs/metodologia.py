from __future__ import annotations

import streamlit as st

from config import ANO_FIM, ANO_INICIO


def render() -> None:
    st.markdown(
        f"""
### Fonte e recorte
- Base: SIA - grupo AM (APAC de medicamentos), via [PySUS](https://pysus.readthedocs.io/).
- Período: {ANO_INICIO}-{ANO_FIM}, Brasil.
- Procedimentos Gaucher: Imiglucerase, Alfavelaglicerase, Alfataliglicerase (TRE); Miglustate (ISS).

### Materialização (`data/processed/`)
- Agregação DuckDB a partir de `data/raw/` (notebook `02_etl_mart.ipynb`)

### Modelagem analítica de sensibilidade
Indicadores de continuidade, mix e prazo de autorização.



### Limitações
- Sem mortalidade (SIM), desfechos clínicos ou custo.
- Continuidade operacional != adesão clínica individual.

### Referência
Borin et al. (2024). Gaucher disease in Brazil. DOI [10.3389/fphar.2024.1433970](https://doi.org/10.3389/fphar.2024.1433970).
"""
    )
