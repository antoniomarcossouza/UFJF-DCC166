"""Amostragem estratificada de tráfego para simulação operacional."""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.config import load_config


class TrafficMixer:
    """Sorteia linhas do dataset com mix configurável benigno/ataque."""

    def __init__(
        self,
        df: pd.DataFrame,
        benign_ratio: float | None = None,
        seed: int | None = None,
    ) -> None:
        config = load_config()
        self.benign_ratio = (
            benign_ratio
            if benign_ratio is not None
            else config["simulation"]["benign_ratio"]
        )
        seed = seed if seed is not None else config["project"]["seed"]
        self._rng = np.random.default_rng(seed)

        benign_mask = df["label_binary"] == "BENIGN"
        self._benign_indices = df.index[benign_mask].to_numpy()
        self._attack_indices = df.index[~benign_mask].to_numpy()
        self._df = df

        if len(self._benign_indices) == 0 or len(self._attack_indices) == 0:
            raise ValueError(
                "Dataset precisa conter linhas benignas e de ataque."
            )

    def next_index(self) -> int:
        """Retorna índice de uma linha sorteada conforme benign_ratio."""
        pick_benign = self._rng.random() < self.benign_ratio
        if pick_benign:
            return int(self._rng.choice(self._benign_indices))
        return int(self._rng.choice(self._attack_indices))

    def next_row(self) -> tuple[int, pd.Series]:
        idx = self.next_index()
        return idx, self._df.loc[idx]
