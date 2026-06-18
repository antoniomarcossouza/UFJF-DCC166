"""Caminhos do projeto."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "configs" / "config.yaml"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
MLRUNS_DIR = PROJECT_ROOT / "mlruns"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"


def ensure_dirs() -> None:
    """Garante que diretórios de saída existam."""
    for path in (PROCESSED_DATA_DIR, MODELS_DIR, REPORTS_DIR, MLRUNS_DIR):
        path.mkdir(parents=True, exist_ok=True)
