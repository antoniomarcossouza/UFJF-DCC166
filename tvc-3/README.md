# IoT Security SAD

Sistema de Apoio à Decisão para Segurança em Redes IoT baseado no dataset CIC-IoT-2023.

## Requisitos

- Python 3.13
- [uv](https://docs.astral.sh/uv/)

## Instalação

```bash
uv sync --extra dev
```

## Pipeline offline (ML)

Todo o treinamento ocorre offline. O dashboard consome apenas artefatos prontos.

```bash
make prepare    # amostragem + pré-processamento
make features   # seleção de atributos
make train      # treino dos 4 modelos + balanceamento
make tune       # Optuna (RF, XGBoost, LightGBM)
make explain    # SHAP
make pipeline   # prepare + features + train + explain
```

## Dashboard operacional (SOC)

```bash
make dashboard
# ou
uv run streamlit run app/app.py
```

O dashboard **não** permite treinamento, tuning ou upload de dados.

## MLflow UI

Para visualizar experimentos, métricas e artefatos registrados durante o treino:

```bash
make mlflow
# ou
uv run mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db
```

Abra no navegador: **http://localhost:5000**

## Relatório científico (SBC)

```bash
make report
```

## Estrutura

```
app/               # dashboard Streamlit (SOC)
data/raw/          # CSVs originais
data/processed/    # datasets processados
models/            # melhor modelo e metadados
reports/           # artefatos de ML e SHAP
mlruns/            # experimentos MLflow
src/               # código de produção
notebooks/         # exploração e demonstração
report/            # artigo LaTeX SBC
```

## Pergunta-problema

Como apoiar a tomada de decisão de administradores de redes IoT na identificação, monitoramento e priorização de ameaças de segurança utilizando modelos de aprendizado de máquina?
