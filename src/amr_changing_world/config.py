from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return value


def config_path(name: str) -> Path:
    return repository_root() / "config" / name

