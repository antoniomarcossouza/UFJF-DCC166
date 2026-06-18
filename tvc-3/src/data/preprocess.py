"""Pré-processamento, validação e divisão dos dados."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from data.load import load_and_sample_raw
from utils.config import load_config
from utils.io import load_dataframe, save_artifact, save_dataframe, save_json
from utils.logging import get_logger
from utils.paths import PROCESSED_DATA_DIR, ensure_dirs
from utils.seeds import set_seed

logger = get_logger(__name__)


def validate_dataframe(
    df: pd.DataFrame, label_column: str = "Label"
) -> dict[str, Any]:
    """Valida schema e qualidade básica."""
    report: dict[str, Any] = {
        "rows": len(df),
        "columns": list(df.columns),
        "null_counts": df.isnull().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
    }
    if label_column in df.columns:
        report["label_distribution"] = (
            df[label_column].value_counts().to_dict()
        )
    return report


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicatas, infinitos e colunas com variância zero."""
    cleaned = df.copy()
    cleaned = cleaned.drop_duplicates()
    feature_cols = [
        col
        for col in cleaned.columns
        if col not in {"Label", "label_binary", "label_multiclass"}
    ]
    cleaned[feature_cols] = cleaned[feature_cols].replace(
        [np.inf, -np.inf], np.nan
    )
    cleaned = cleaned.dropna()
    numeric = cleaned[feature_cols].select_dtypes(include=[np.number])
    zero_var = numeric.columns[numeric.std() == 0].tolist()
    if zero_var:
        cleaned = cleaned.drop(columns=zero_var)
        logger.info("Removidas %d colunas com variância zero", len(zero_var))
    return cleaned


def split_dataset(
    df: pd.DataFrame,
    target_column: str,
    test_size: float,
    val_size: float,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Divide em treino, validação e teste de forma estratificada."""
    train_df, temp_df = train_test_split(
        df,
        test_size=test_size + val_size,
        random_state=seed,
        stratify=df[target_column],
    )
    relative_val = val_size / (test_size + val_size)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=1 - relative_val,
        random_state=seed,
        stratify=temp_df[target_column],
    )
    return (
        train_df.reset_index(drop=True),
        val_df.reset_index(drop=True),
        test_df.reset_index(drop=True),
    )


def preprocess(
    dataset_path: Path | None = None,
    target: str = "label_binary",
) -> dict[str, Any]:
    """Executa pipeline completo de pré-processamento."""
    config = load_config()
    seed = config["project"]["seed"]
    set_seed(seed)
    ensure_dirs()

    dataset_path = dataset_path or (PROCESSED_DATA_DIR / "dataset.parquet")
    if not dataset_path.exists():
        load_and_sample_raw()

    df = load_dataframe(dataset_path)
    validation_report = validate_dataframe(df)
    cleaned = clean_dataframe(df)

    train_df, val_df, test_df = split_dataset(
        cleaned,
        target_column=target,
        test_size=config["data"]["test_size"],
        val_size=config["data"]["val_size"],
        seed=seed,
    )

    feature_cols = [
        col
        for col in cleaned.columns
        if col not in {"Label", "label_binary", "label_multiclass"}
    ]

    scaler = StandardScaler()
    scaler.fit(train_df[feature_cols])

    for split_name, split_df in {
        "train": train_df,
        "val": val_df,
        "test": test_df,
    }.items():
        scaled = split_df.copy()
        scaled[feature_cols] = scaler.transform(split_df[feature_cols])
        save_dataframe(scaled, PROCESSED_DATA_DIR / f"{split_name}.parquet")

    save_artifact(scaler, PROCESSED_DATA_DIR / "scaler.joblib")
    save_artifact(feature_cols, PROCESSED_DATA_DIR / "feature_columns.joblib")

    metadata = {
        "target": target,
        "feature_columns": feature_cols,
        "validation_report": validation_report,
        "splits": {
            "train": len(train_df),
            "val": len(val_df),
            "test": len(test_df),
        },
    }

    save_json(metadata, PROCESSED_DATA_DIR / "preprocess_metadata.json")
    logger.info("Pré-processamento concluído: %s", metadata["splits"])
    return metadata


if __name__ == "__main__":
    preprocess()
