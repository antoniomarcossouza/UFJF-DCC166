"""Reprodutibilidade."""

import random

import numpy as np


def set_seed(seed: int) -> None:
    """Define seeds globais."""
    random.seed(seed)
    np.random.seed(seed)
