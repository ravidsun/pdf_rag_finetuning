"""Configuration helpers."""

from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_PATH = Path("config/settings.yaml")


def load_settings(config_path: Path | None = None) -> dict[str, Any]:
    """Load YAML configuration into a dictionary."""
    path = config_path or DEFAULT_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Missing configuration file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)
