import re
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


def detect_java_major(java: str):
    try:
        r = subprocess.run([java, "-version"], capture_output=True, text=True, timeout=10)
        text = r.stderr or r.stdout
        m = re.search(r'version "(\d+)(?:\.(\d+))?', text)
        if not m:
            return None
        major = int(m.group(1))
        if major == 1 and m.group(2):
            return int(m.group(2))
        return major
    except Exception:
        return None


def required_java_major(version_data: dict) -> int:
    return version_data.get("javaVersion", {}).get("majorVersion", 8)


def install(version_id: str, game_dir: Path = None, quiet: bool = False, progress_cb=None) -> None:
    game_dir = Path(game_dir) if game_dir else DEFAULT_GAME_DIR
    game_dir.mkdir(parents=True, exist_ok=True)

    def emit(stage: str, current: int, total: int):
        if progress_cb:
            progress_cb(stage, current, total)

    if not quiet:
        print(f"Installing Minecraft {version_id}")
        print(f"  game dir: {game_dir}")

    emit("manifest", 0, 1)
    manifest = fetch_manifest(game_dir)
    version_data = fetch_version(version_id, manifest, game_dir)

    if not quiet:
        print("  downloading client jar...")
    emit("client", 0, 1)
    _, dl = download_client(version_data, game_dir)
    emit("client", 1, 1)

    if not quiet:
        print("  downloading libraries + natives...")
    def lib_progress(c, t):
        emit("libraries", c, t)
    lib_cached, lib_dl = download_libraries(version_data, game_dir, progress_cb=lib_progress)
    if not quiet:
        print(f"    {lib_cached} cached, {lib_dl} downloaded")

    if not quiet:
        print("  downloading assets...")
    def asset_progress(c, t):
        emit("assets", c, t)
    a_cached, a_dl = download_assets(
        version_data, game_dir, verbose=not quiet, progress_cb=asset_progress
    )
    if not quiet:
        print(f"    {a_cached} cached, {a_dl} downloaded")
        print(f"Done. {version_id} is ready to launch.")

    emit("done", 1, 1)


def launch(
    version_id: str,
    username: str,
    game_dir: Path = None,
    java: str = "java",
    memory_mb: int = 2048,
    auto_install: bool = True,
    stream_cb=None,
) -> int:
    game_dir = Path(game_dir) if game_dir else DEFAULT_GAME_DIR

    def out(line: str):
        if stream_cb:
            stream_cb(line.rstrip("\n"))
        else:
            print(line, end="")

    if version_id not in list_installed(game_dir):
        if not auto_install:
            msg = f"Version {version_id} is not installed. Run: pylauncher install {version_id}"
            if stream_cb:
                stream_cb(msg)
            else:
                print(msg, file=sys.stderr)
            return 1
        msg = f"Version {version_id} not installed. Installing first..."
        if stream_cb:
            stream_cb(msg)
        else:
            print(msg)
        install(version_id, game_dir)

    manifest = fetch_manifest(game_dir)
    version_data = fetch_version(version_id, manifest, game_dir)

    required = required_java_major(version_data)
    actual = detect_java_major(java)
    if actual is not None and actual < required:
        msg = (
            f"Warning: {version_id} requires Java {required}+, "
            f"but '{java}' is Java {actual}. "
            f"Use --java to point at a newer JDK."
        )
        if stream_cb:
            stream_cb(msg)
        else:
            print(msg, file=sys.stderr)

    uuid = offline_uuid(username)
    natives = game_dir / "natives" / version_id
    jvm = build_jvm_args(version_data, game_dir, natives, memory_mb)
    game = build_game_args(version_data, game_dir, username, uuid)
    main_class = version_data.get("mainClass", "net.minecraft.client.main.Main")

    cmd = [java] + jvm + [main_class] + game

    banner = f"Launching {version_id} as {username} (uuid {uuid})"
    if stream_cb:
        stream_cb(banner)
    else:
        print(banner)

    try:
        if stream_cb is None:
            proc = subprocess.run(cmd, cwd=str(game_dir))
            return proc.returncode

        proc = subprocess.Popen(
            cmd,
            cwd=str(game_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in proc.stdout:
            stream_cb(line.rstrip("\n"))
        return proc.wait()

    except FileNotFoundError:
        msg = f"Java not found: '{java}'. Use --java to point at a JDK."
        if stream_cb:
            stream_cb(msg)
        else:
            print(msg, file=sys.stderr)
        return 1