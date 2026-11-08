"""Build the classpath, JVM arguments, and game arguments for a launch."""

import os
from pathlib import Path

from .download import parse_library_name
from .rules import rules_allow


def _replace(text: str, repl: dict) -> str:
    for k, v in repl.items():
        text = text.replace(k, v)
    return text


def build_classpath(version_data: dict, game_dir: Path, client_jar: Path) -> str:
    libs = game_dir / "libraries"
    entries = []
    for lib in version_data.get("libraries", []):
        if not rules_allow(lib.get("rules", [])):
            continue
        art = lib.get("downloads", {}).get("artifact")
        if art:
            p = libs / art["path"]
        else:
            g, a, v, _ = parse_library_name(lib["name"])
            p = libs / g.replace(".", "/") / a / v / f"{a}-{v}.jar"
        if p.exists():
            entries.append(str(p))
    entries.append(str(client_jar))
    return os.pathsep.join(entries)


def build_jvm_args(version_data: dict, game_dir: Path, natives_dir: Path, memory_mb: int) -> list:
    v = version_data["id"]
    client_jar = game_dir / "versions" / v / f"{v}.jar"
    classpath = build_classpath(version_data, game_dir, client_jar)

    repl = {
        "${natives_directory}": str(natives_dir),
        "${classpath}": classpath,
        "${classpath_separator}": os.pathsep,
        "${launcher_name}": "PyLauncher",
        "${launcher_version}": "0.1.0",
        "${version_name}": v,
        "${game_directory}": str(game_dir),
    }

    raw = version_data.get("arguments", {}).get("jvm", [])
    args = []
    for arg in raw:
        if isinstance(arg, str):
            args.append(_replace(arg, repl))
        elif isinstance(arg, dict):
            if rules_allow(arg.get("rules", [])):
                val = arg.get("value")
                if isinstance(val, str):
                    args.append(_replace(val, repl))
                elif isinstance(val, list):
                    args.extend(_replace(x, repl) for x in val)

    # Pre-1.13 versions have no arguments.jvm; build it manually.
    if not raw:
        args.append(f"-Djava.library.path={natives_dir}")
        args.extend(["-cp", classpath])

    args.append(f"-Xmx{memory_mb}M")
    args.append(f"-Xms{max(512, memory_mb // 4)}M")
    return args


def build_game_args(version_data: dict, game_dir: Path, username: str, uuid: str) -> list:
    repl = {
        "${auth_player_name}": username,
        "${version_name}": version_data["id"],
        "${game_directory}": str(game_dir),
        "${assets_root}": str(game_dir / "assets"),
        "${assets_index_name}": version_data.get("assetIndex", {}).get("id", "legacy"),
        "${auth_uuid}": uuid,
        "${auth_access_token}": "0",
        "${auth_session}": "token:0",
        "${clientid}": "0",
        "${auth_xuid}": "0",
        "${user_type}": "legacy",
        "${version_type}": version_data.get("type", "release"),
        "${user_properties}": "{}",
    }

    raw = version_data.get("arguments", {}).get("game", [])
    args = []
    for arg in raw:
        if isinstance(arg, str):
            args.append(_replace(arg, repl))
        elif isinstance(arg, dict):
            if rules_allow(arg.get("rules", [])):
                val = arg.get("value")
                if isinstance(val, str):
                    args.append(_replace(val, repl))
                elif isinstance(val, list):
                    args.extend(_replace(x, repl) for x in val)

    if "minecraftArguments" in version_data:
        legacy = version_data["minecraftArguments"].split()
        args.extend(_replace(x, repl) for x in legacy)

    return args