# UFJF-DCC166

Sistema de Apoio à Decisão (SAD) para tratamento da **Doença de Gaucher** no SUS, com dados do SIA (base `AM`) via PySUS, materialização em Parquet e dashboard **Streamlit** com **análise de sensibilidade**.

## Requisitos

- WSL (Ubuntu recomendado) ou Linux
- [uv](https://docs.astral.sh/uv/) e Python 3.11

## Estrutura

```
.
├── app/
│   └── streamlit_app.py      # Dashboard SAD (TVC 1.3)
├── data/
│   ├── processed/            # Marts versionados (Parquet) — usados pelo Streamlit
│   └── raw/                  # AM bruto (não versionado; gerado pela ingestão)
├── notebooks/
│   ├── 00_ingestao.ipynb     # Download SIA-AM 2016–2025
│   ├── 01_eda_am.ipynb       # EDA Gaucher
│   └── 02_etl_mart.ipynb     # Materialização dos marts
└── src/ufjf_dcc166/
    ├── queries.py            # SQL DuckDB + build_marts
    └── sensitivity.py        # Análise de sensibilidade
```

## Setup

```bash
uv sync
uv run python -m ipykernel install --user --name ufjf-dcc166 --display-name "Python (ufjf-dcc166)"
```

## Pipeline de dados

1. **Ingestão** (WSL, pode demorar):

   ```bash
   uv run jupyter lab notebooks/00_ingestao.ipynb
   ```

   Baixa AM **2016–2025**, Brasil, para `data/raw/`.

2. **ETL → marts** — execute `notebooks/02_etl_mart.ipynb` (ou `uv run python -c "from pathlib import Path; from ufjf_dcc166.queries import run_etl; run_etl(Path('.'))"`). Gera em `data/processed/`:

   - `mart_apac_mensal.parquet`
   - `mart_paciente_mes.parquet` (CNS com hash)
   - `mart_autorizacao.parquet`

3. **Commit** dos arquivos em `data/processed/` para o repositório (necessário para o Streamlit Cloud).

## Dashboard Streamlit (local)

```bash
uv run streamlit run app/streamlit_app.py
```

Abas: **Visão geral**, **Continuidade**, **Sensibilidade** (gap, mix, SLA, cobertura), **Metodologia**.

## Deploy no Streamlit Cloud

1. Faça push do repositório com os Parquets em `data/processed/`.
2. Em [share.streamlit.io](https://share.streamlit.io): **New app** → repositório → branch.
3. **Main file path:** `app/streamlit_app.py`
4. **Requirements file:** `requirements.txt` (na raiz; gerado com `uv export --no-hashes -o requirements.txt` após `uv sync`).

## Modelagem analítica (Atividade 1.3)

Análise de **sensibilidade** sobre indicadores derivados só da AM (sem custo PA):

| Parâmetro variado | Indicador |
|-------------------|-----------|
| Gap máximo entre dispensações | % pacientes com continuidade |
| % migração Imiglucerase → biossimilar | Volume de APACs por fármaco |
| Prazo-alvo de autorização | % registros dentro do SLA |
| Fator de subdiagnóstico | Coorte ativa estimada |

## Referências

- [PySUS — SIA](https://pysus.readthedocs.io/en/latest/databases/SIA.html)
- Borin et al. (2024). *Gaucher disease in Brazil*. Front. Pharmacol. [DOI 10.3389/fphar.2024.1433970](https://doi.org/10.3389/fphar.2024.1433970)
