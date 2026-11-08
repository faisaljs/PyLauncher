"""Shared fixtures and helpers for PyLauncher tests."""

import re
from pathlib import Path

import pytest


def assert_no_unresolved(args: list) -> None:
    """Raise if any argument still contains a ${...} placeholder."""
    for arg in args:
        m = re.search(r"\$\{[^}]+\}", arg)
        assert m is None, f"Unresolved placeholder {m.group(0)!r} in {arg!r}"


def make_modern_version_data(version_id: str = "1.20.4") -> dict:
    """A minimal but realistic version JSON with arguments.jvm + arguments.game."""
    return {
        "id": version_id,
        "type": "release",
        "mainClass": "net.minecraft.client.main.Main",
        "libraries": [],
        "downloads": {"client": {"url": "http://example/client.jar", "sha1": "0" * 40}},
        "assetIndex": {"id": "17"},
        "arguments": {
            "jvm": [
                "-Djava.library.path=${natives_directory}",
                "-cp",
                "${classpath}",
                "-Dlauncher.name=${launcher_name}",
                "-Dlauncher.version=${launcher_version}",
            ],
            "game": [
                "--username", "${auth_player_name}",
                "--version", "${version_name}",
                "--gameDir", "${game_directory}",
                "--assetsDir", "${assets_root}",
                "--assetIndex", "${assets_index_name}",
                "--uuid", "${auth_uuid}",
                "--accessToken", "${auth_access_token}",
                "--userType", "${user_type}",
                "--versionType", "${version_type}",
            ],
        },
    }


def make_legacy_version_data(version_id: str = "1.7.10") -> dict:
    """A pre-1.13 version JSON: no arguments block, minecraftArguments string."""
    return {
        "id": version_id,
        "type": "release",
        "mainClass": "net.minecraft.client.main.Main",
        "libraries": [],
        "downloads": {"client": {"url": "http://example/client.jar", "sha1": "0" * 40}},
        "assetIndex": {"id": "legacy"},
        "minecraftArguments": (
            "--username ${auth_player_name} "
            "--version ${version_name} "
            "--gameDir ${game_directory} "
            "--assetsDir ${assets_root} "
            "--assetIndex ${assets_index_name} "
            "--uuid ${auth_uuid} "
            "--accessToken ${auth_access_token} "
            "--userType ${user_type}"
        ),
    }


@pytest.fixture
def game_dir(tmp_path: Path) -> Path:
    """A fake game directory with the client jar stub in place."""
    gd = tmp_path / "game"
    vdir = gd / "versions" / "1.20.4"
    vdir.mkdir(parents=True)
    (vdir / "1.20.4.jar").write_bytes(b"fake client jar")
    (gd / "natives" / "1.20.4").mkdir(parents=True)
    (gd / "libraries").mkdir(parents=True)
    return gd