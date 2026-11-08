import json
from pathlib import Path

DEFAULT_CONFIG = {
    "username": "Player",
    "default_version": "1.20.4",
    "memory_mb": 2048,
    "java": "java",
    "per_version": {},
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
    merged.setdefault("per_version", {})
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


def effective_settings(cfg: dict, version_id: str) -> dict:
    base = {
        "java": cfg.get("java", "java"),
        "memory_mb": cfg.get("memory_mb", 2048),
    }
    override = cfg.get("per_version", {}).get(version_id, {})
    base.update({k: v for k, v in override.items() if v is not None})
    return base


def set_version_override(cfg: dict, version_id: str, java: str = None, memory_mb: int = None) -> dict:
    per = dict(cfg.get("per_version", {}))
    entry = dict(per.get(version_id, {}))
    if java is not None:
        entry["java"] = java
    if memory_mb is not None:
        entry["memory_mb"] = memory_mb
    per[version_id] = entry
    cfg = dict(cfg)
    cfg["per_version"] = per
    return cfg