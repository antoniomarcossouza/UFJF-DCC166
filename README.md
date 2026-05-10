# UFJF-DCC166

Estrutura base inspirada no Cookiecutter Data Science, com ingestao de dados do SIA (base `AM`) usando PySUS e consulta simples com DuckDB.

## Requisitos

- WSL (Ubuntu recomendado)
- `uv` instalado no ambiente Linux
- Python 3.11

## Estrutura de pastas

```
.
├── data/
│   ├── external/
│   ├── interim/
│   ├── processed/
│   └── raw/
├── docs/
├── models/
├── notebooks/
├── references/
├── reports/
│   └── figures/
└── src/
    └── ufjf_dcc166/
```

## Setup no WSL

No terminal do WSL, na raiz do projeto:

```bash
uv sync
uv run python -m ipykernel install --user --name ufjf-dcc166 --display-name "Python (ufjf-dcc166)"
uv run jupyter lab
```

## Notebooks

- `notebooks/ingestao_sia_am.ipynb`
  - Lista e baixa arquivos do grupo `AM` (SIA) apenas de `MG` e `2025` para `data/sia_am/mg_2025`.
- `notebooks/duckdb_query_sia_am.ipynb`
  - Renomeia colunas segundo layout `AMUFAAMM.DBF` + padrao Arcelor, filtra os 4 procedimentos para Doenca de Gaucher e executa uma EDA completa: qualidade dos dados, mix de medicamentos, demografia, antropometria/IMC, custo, continuidade de tratamento, CIDs, correlacoes Pearson/Spearman e testes (Qui-quadrado, Shapiro-Wilk, Kruskal-Wallis, Mann-Whitney).

## Referencias

- [PySUS - SIA FTP Database](https://pysus.readthedocs.io/en/latest/databases/SIA.html)
- Borin et al. (2024). *Gaucher disease in Brazil: a comprehensive 16 year retrospective study on survival, cost, and treatment insights*. Frontiers in Pharmacology. [DOI 10.3389/fphar.2024.1433970](https://doi.org/10.3389/fphar.2024.1433970)