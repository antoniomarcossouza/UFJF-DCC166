"""Carregamento de configuração."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from utils.paths import CONFIG_PATH, PROJECT_ROOT


def _resolve_paths(config: dict[str, Any]) -> dict[str, Any]:
    paths = config.get("paths", {})
    for key, value in list(paths.items()):
        path = Path(value)
        if not path.is_absolute():
            paths[key] = str(PROJECT_ROOT / path)
    return config


@lru_cache(maxsize=1)
def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Carrega o arquivo YAML de configuração."""
    path = config_path or CONFIG_PATH
    with path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    return _resolve_paths(config)
