"""Loads config.yaml, shared by capture_worker, dashboard, and cleanup."""

from __future__ import annotations

from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = BASE_DIR / "config.yaml"


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    with open(path, "r") as f:
        cfg = yaml.safe_load(f)

    storage = cfg.setdefault("storage", {})
    captures_dir = Path(storage.get("captures_dir", "captures"))
    db_path = Path(storage.get("database_path", "captures.db"))
    if not captures_dir.is_absolute():
        captures_dir = BASE_DIR / captures_dir
    if not db_path.is_absolute():
        db_path = BASE_DIR / db_path
    storage["captures_dir"] = str(captures_dir)
    storage["database_path"] = str(db_path)

    return cfg
