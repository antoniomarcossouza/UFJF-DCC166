from __future__ import annotations

import streamlit as st

from config import ANO_FIM, ANO_INICIO


def render() -> None:
    st.markdown(
        f"""
### Fonte e recorte
- **Base:** SIA - grupo **AM** (APAC de medicamentos), via [PySUS](https://pysus.readthedocs.io/).
- **Período:** {ANO_INICIO}-{ANO_FIM}, Brasil.
- **Procedimentos Gaucher:** Imiglucerase, Alfavelaglicerase, Alfataliglicerase (TRE); Miglustate (ISS).

### Materialização (`data/processed/`)
- Agregação DuckDB a partir de `data/raw/` (notebook `02_etl_mart.ipynb`).
- **Privacidade:** CNS substituído por hash SHA-256 (10 caracteres hex).

### Modelagem analítica - sensibilidade
Sem custo na AM (`vl_apac_aprovada` zerado); indicadores de **continuidade**, **mix** e **prazo de autorização**.

| Variável | Indicador |
|----------|-----------|
| Gap máximo entre dispensações | % pacientes contínuos |
| % migração Imiglucerase → biossimilar | Volume de APACs por fármaco |
| Prazo-alvo de autorização | % registros dentro do SLA (proxy p50) |
| Fator de subdiagnóstico | Coorte ativa estimada |

### Limitações
- Sem mortalidade (SIM), desfechos clínicos ou custo real (necessário SIA-PA/SIGTAP).
- Continuidade operacional ≠ adesão clínica individual.
- Referência externa: Borin et al. (2024), *Front. Pharmacol.* - coorte nacional 16 anos.

### Referência
Borin et al. (2024). Gaucher disease in Brazil. DOI [10.3389/fphar.2024.1433970](https://doi.org/10.3389/fphar.2024.1433970).
        """
    )
