"""The orchestrator: install and launch."""

import subprocess
import sys
from pathlib import Path

from .args import build_game_args, build_jvm_args
from .download import download_assets, download_client, download_libraries
from .manifest import fetch_manifest, fetch_version
from .uuid import offline_uuid

DEFAULT_GAME_DIR = Path.home() / ".pylauncher"


def list_installed(game_dir: Path) -> list:
    versions_dir = game_dir / "versions"
    if not versions_dir.exists():
        return []
    out = []
    for d in sorted(versions_dir.iterdir()):
        if d.is_dir() and (d / f"{d.name}.jar").exists():
            out.append(d.name)
    return out


def install(version_id: str, game_dir: Path = None, quiet: bool = False) -> None:
    game_dir = Path(game_dir) if game_dir else DEFAULT_GAME_DIR
    game_dir.mkdir(parents=True, exist_ok=True)

    if not quiet:
        print(f"Installing Minecraft {version_id}")
        print(f"  game dir: {game_dir}")

    manifest = fetch_manifest(game_dir)
    version_data = fetch_version(version_id, manifest, game_dir)

    if not quiet:
        print("  downloading client jar...")
    _, dl = download_client(version_data, game_dir)

    if not quiet:
        print("  downloading libraries + natives...")
    lib_cached, lib_dl = download_libraries(version_data, game_dir)
    if not quiet:
        print(f"    {lib_cached} cached, {lib_dl} downloaded")

    if not quiet:
        print("  downloading assets...")
    a_cached, a_dl = download_assets(version_data, game_dir, verbose=not quiet)
    if not quiet:
        print(f"    {a_cached} cached, {a_dl} downloaded")

    if not quiet:
        print(f"Done. {version_id} is ready to launch.")


def launch(
    version_id: str,
    username: str,
    game_dir: Path = None,
    java: str = "java",
    memory_mb: int = 2048,
    auto_install: bool = True,
) -> int:
    game_dir = Path(game_dir) if game_dir else DEFAULT_GAME_DIR

    if version_id not in list_installed(game_dir):
        if not auto_install:
            print(f"Version {version_id} is not installed. Run: pylauncher install {version_id}",
                  file=sys.stderr)
            return 1
        print(f"Version {version_id} not installed. Installing first...")
        install(version_id, game_dir)

    manifest = fetch_manifest(game_dir)
    version_data = fetch_version(version_id, manifest, game_dir)

    uuid = offline_uuid(username)
    natives = game_dir / "natives" / version_id
    jvm = build_jvm_args(version_data, game_dir, natives, memory_mb)
    game = build_game_args(version_data, game_dir, username, uuid)
    main_class = version_data.get("mainClass", "net.minecraft.client.main.Main")

    cmd = [java] + jvm + [main_class] + game

    print(f"Launching {version_id} as {username} (uuid {uuid})")
    try:
        proc = subprocess.run(cmd, cwd=str(game_dir))
        return proc.returncode
    except FileNotFoundError:
        print(f"Java not found: '{java}'. Use --java to point at a JDK.", file=sys.stderr)
        return 1