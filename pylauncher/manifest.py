"""Fetch the Mojang version manifest and per-version JSON files."""

import json
from pathlib import Path

import requests

from .download import USER_AGENT

VERSION_MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"


def fetch_manifest(game_dir: Path, refresh: bool = False) -> dict:
    game_dir.mkdir(parents=True, exist_ok=True)
    path = game_dir / "version_manifest.json"
    if path.exists() and not refresh:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    r = requests.get(VERSION_MANIFEST_URL, timeout=60, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    data = r.json()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


def fetch_version(version_id: str, manifest: dict, game_dir: Path) -> dict:
    vdir = game_dir / "versions" / version_id
    vdir.mkdir(parents=True, exist_ok=True)
    path = vdir / f"{version_id}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    entry = next((v for v in manifest["versions"] if v["id"] == version_id), None)
    if not entry:
        raise ValueError(f"Version '{version_id}' not found in manifest")

    r = requests.get(entry["url"], timeout=60, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    data = r.json()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data