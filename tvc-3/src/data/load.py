"""Carregamento e amostragem estratificada do dataset CIC-IoT-2023."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from utils.config import load_config
from utils.io import save_dataframe
from utils.logging import get_logger
from utils.paths import PROCESSED_DATA_DIR, ensure_dirs
from utils.seeds import set_seed

logger = get_logger(__name__)


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nomes de colunas."""
    df = df.copy()
    df.columns = [col.strip().replace(" ", "_") for col in df.columns]
    if "label" in df.columns and "Label" not in df.columns:
        df = df.rename(columns={"label": "Label"})
    return df


def normalize_label(value: str) -> str:
    """Normaliza rótulos para comparação consistente."""
    return str(value).strip().upper().replace(" ", "_")


def map_labels(series: pd.Series, mapping: dict[str, str]) -> pd.Series:
    """Aplica mapeamento de rótulos com normalização de caixa."""
    normalized_mapping = {normalize_label(k): v for k, v in mapping.items()}
    return series.map(
        lambda x: normalized_mapping.get(normalize_label(x), "UNKNOWN")
    )


def _sample_chunk(chunk: pd.DataFrame, frac: float, seed: int) -> pd.DataFrame:
    if frac >= 1.0:
        return chunk
    if "Label" not in chunk.columns:
        return chunk.sample(frac=frac, random_state=seed)
    parts: list[pd.DataFrame] = []
    for _label, group in chunk.groupby("Label", group_keys=False):
        n = max(1, int(round(len(group) * frac)))
        n = min(n, len(group))
        parts.append(group.sample(n=n, random_state=seed))
    return pd.concat(parts, ignore_index=True)


def load_and_sample_raw(
    raw_dir: Path | None = None,
    sample_frac: float | None = None,
    chunk_size: int | None = None,
    seed: int | None = None,
    output_path: Path | None = None,
) -> pd.DataFrame:
    """Lê CSVs brutos em chunks e gera amostra estratificada."""
    config = load_config()
    raw_dir = Path(raw_dir or config["paths"]["raw_data"])
    sample_frac = (
        sample_frac
        if sample_frac is not None
        else config["data"]["sample_frac"]
    )
    chunk_size = chunk_size or config["data"]["chunk_size"]
    seed = seed if seed is not None else config["project"]["seed"]
    output_path = output_path or (PROCESSED_DATA_DIR / "dataset.parquet")

    set_seed(seed)
    ensure_dirs()

    files = sorted(raw_dir.glob("Merged*.csv"))
    if not files:
        raise FileNotFoundError(
            f"Nenhum arquivo Merged*.csv encontrado em {raw_dir}"
        )

    sampled_parts: list[pd.DataFrame] = []
    for file_path in files:
        logger.info("Processando %s", file_path.name)
        for chunk in pd.read_csv(
            file_path, chunksize=chunk_size, low_memory=False
        ):
            chunk = normalize_column_names(chunk)
            sampled = _sample_chunk(chunk, sample_frac, seed)
            if not sampled.empty:
                sampled_parts.append(sampled)

    if not sampled_parts:
        raise RuntimeError("Amostragem não produziu registros.")

    dataset = pd.concat(sampled_parts, ignore_index=True)
    dataset["Label"] = dataset["Label"].astype(str).map(normalize_label)

    binary_map = config["labels"]["binary"]
    multiclass_map = config["labels"]["multiclass"]
    dataset["label_binary"] = map_labels(dataset["Label"], binary_map)
    dataset["label_multiclass"] = map_labels(dataset["Label"], multiclass_map)

    unknown = dataset[dataset["label_binary"] == "UNKNOWN"]
    if not unknown.empty:
        unknown_labels = sorted(unknown["Label"].unique().tolist())
        logger.warning("Rótulos não mapeados: %s", unknown_labels[:10])

    save_dataframe(dataset, output_path)
    logger.info("Dataset salvo em %s (%d linhas)", output_path, len(dataset))
    return dataset


if __name__ == "__main__":
    load_and_sample_raw()
