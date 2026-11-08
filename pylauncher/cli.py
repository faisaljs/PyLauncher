import argparse
import sys
from pathlib import Path

from . import __version__
from .config import load_config, set_value
from .launcher import DEFAULT_GAME_DIR, install, launch, list_installed
from .manifest import fetch_manifest


def cmd_install(args) -> int:
    game_dir = Path(args.dir) if args.dir else DEFAULT_GAME_DIR
    install(args.version, game_dir, quiet=args.quiet)
    return 0


def cmd_launch(args) -> int:
    cfg = load_config()
    game_dir = Path(args.dir) if args.dir else DEFAULT_GAME_DIR
    version = args.version or cfg["default_version"]
    username = args.username or cfg["username"]
    java = args.java or cfg["java"]
    memory = args.memory or cfg["memory_mb"]
    return launch(version, username, game_dir, java, memory, auto_install=not args.no_install)


def cmd_list(args) -> int:
    game_dir = Path(args.dir) if args.dir else DEFAULT_GAME_DIR
    versions = list_installed(game_dir)
    if not versions:
        print("No versions installed.")
        return 0
    print("Installed:")
    for v in versions:
        print(f"  {v}")
    return 0


def cmd_available(args) -> int:
    game_dir = Path(args.dir) if args.dir else DEFAULT_GAME_DIR
    manifest = fetch_manifest(game_dir, refresh=args.refresh)
    installed = set(list_installed(game_dir))

    versions = manifest["versions"]
    if args.type:
        versions = [v for v in versions if v["type"] == args.type]

    print(f"{'':2}{'ID':<24} {'TYPE':<12} RELEASED")
    for v in versions:
        marker = "*" if v["id"] in installed else " "
        print(f"{marker:<2}{v['id']:<24} {v['type']:<12} {v['releaseTime'][:10]}")
    return 0


def cmd_config(args) -> int:
    if args.key and args.value is not None:
        set_value(args.key, args.value)
        print(f"{args.key} = {args.value}")
        return 0
    if args.key:
        cfg = load_config()
        if args.key not in cfg:
            print(f"Unknown key: {args.key}", file=sys.stderr)
            return 1
        print(cfg[args.key])
        return 0
    cfg = load_config()
    for k, v in cfg.items():
        print(f"{k} = {v}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pylauncher",
        description="PyLauncher — an offline-capable Minecraft Java Edition launcher.",
    )
    p.add_argument("--version", action="version", version=f"PyLauncher {__version__}")
    sub = p.add_subparsers(dest="command")

    pi = sub.add_parser("install", help="Download everything for a version")
    pi.add_argument("version", help="Minecraft version, e.g. 1.20.4")
    pi.add_argument("--dir", "-d", help="Game directory (default ~/.pylauncher)")
    pi.add_argument("--quiet", "-q", action="store_true", help="Silence progress output")
    pi.set_defaults(func=cmd_install)

    pl = sub.add_parser("launch", help="Launch the game (installs if needed)")
    pl.add_argument("version", nargs="?", help="Minecraft version (default from config)")
    pl.add_argument("--username", "-u", help="Offline username (default from config)")
    pl.add_argument("--dir", "-d", help="Game directory")
    pl.add_argument("--java", "-j", help="Path to java executable")
    pl.add_argument("--memory", "-m", type=int, help="Max memory in MB")
    pl.add_argument("--no-install", action="store_true", help="Fail if version not installed")
    pl.set_defaults(func=cmd_launch)

    pn = sub.add_parser("list", help="List installed versions")
    pn.add_argument("--dir", "-d")
    pn.set_defaults(func=cmd_list)

    pa = sub.add_parser("available", help="List versions available from Mojang")
    pa.add_argument("--dir", "-d")
    pa.add_argument("--refresh", action="store_true", help="Force re-fetch the manifest")
    pa.add_argument("--type", "-t",
                    choices=["release", "snapshot", "old_beta", "old_alpha"],
                    help="Filter by version type")
    pa.set_defaults(func=cmd_available)

    pc = sub.add_parser("config", help="Get or set configuration")
    pc.add_argument("key", nargs="?")
    pc.add_argument("value", nargs="?")
    pc.set_defaults(func=cmd_config)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)