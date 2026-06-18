.PHONY: install prepare features train tune explain pipeline dashboard mlflow report

install:
	uv sync --extra dev

prepare:
	PYTHONPATH=src uv run python -m data.load
	PYTHONPATH=src uv run python -m data.preprocess

features:
	PYTHONPATH=src uv run python -m data.features

train:
	PYTHONPATH=src uv run python -m models.train

tune:
	PYTHONPATH=src uv run python -m tuning.optuna_search

explain:
	PYTHONPATH=src uv run python -m explainability.shap_analysis

pipeline: prepare features train tune explain

dashboard:
	uv run streamlit run app/streamlit_app.py

mlflow:
	uv run mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db

report:
	cd report && latexmk -pdf main.tex
