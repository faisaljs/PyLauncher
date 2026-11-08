import traceback
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import QObject, Signal

from ..launcher import install, launch, list_installed
from ..manifest import fetch_manifest


class Bridge(QObject):
    progress = Signal(str, int, int)
    log = Signal(str)
    finished = Signal(str)
    failed = Signal(str)
    game_line = Signal(str)
    game_exited = Signal(int)
    versions_loaded = Signal(list)


def run_load_versions(bridge: Bridge, game_dir) -> None:
    try:
        manifest = fetch_manifest(game_dir)
        installed = set(list_installed(game_dir))
        data = [
            (v["id"], v["type"], v["id"] in installed)
            for v in manifest["versions"]
        ]
        bridge.versions_loaded.emit(data)
    except Exception:
        bridge.failed.emit(traceback.format_exc())


def run_install(bridge: Bridge, version: str, game_dir) -> None:
    try:
        bridge.log.emit(f"Installing {version}...")

        def cb(stage: str, current: int, total: int):
            bridge.progress.emit(stage, current, total)

        install(version, game_dir, quiet=True, progress_cb=cb)
        bridge.log.emit(f"Done. {version} is ready to launch.")
        bridge.finished.emit(version)
    except Exception:
        bridge.failed.emit(traceback.format_exc())


def run_launch(
    bridge: Bridge,
    version: str,
    username: str,
    game_dir,
    java: str,
    memory: int,
) -> None:
    try:
        bridge.log.emit(f"--- Launching {version} as {username} ---")

        def stream(line: str):
            bridge.game_line.emit(line)

        rc = launch(
            version, username, game_dir, java, memory,
            auto_install=True, stream_cb=stream,
        )
        bridge.log.emit(f"--- Game exited with code {rc} ---")
        bridge.game_exited.emit(rc)
    except Exception:
        bridge.failed.emit(traceback.format_exc())


class WorkerPool:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, fn, *args, **kwargs):
        return self.executor.submit(fn, *args, **kwargs)

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)