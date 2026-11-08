"""User configuration stored at ~/.pylauncher/config.json."""

import json
from pathlib import Path

DEFAULT_CONFIG = {
    "username": "Player",
    "default_version": "1.20.4",
    "memory_mb": 2048,
    "java": "java",
}


def config_path() -> Path:
    return Path.home() / ".pylauncher" / "config.json"


def load_config() -> dict:
    path = config_path()
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return dict(DEFAULT_CONFIG)
    merged = dict(DEFAULT_CONFIG)
    merged.update(data)
    return merged


def save_config(cfg: dict) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def set_value(key: str, value: str) -> None:
    cfg = load_config()
    if key == "memory_mb":
        cfg[key] = int(value)
    else:
        cfg[key] = value
    save_config(cfg)