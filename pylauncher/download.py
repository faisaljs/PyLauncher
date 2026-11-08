import hashlib
import json
import zipfile
from pathlib import Path

import requests

from .rules import natives_arch, os_name, rules_allow

LIBRARIES_BASE = "https://libraries.minecraft.net/"
RESOURCES_BASE = "https://resources.download.minecraft.net/"
USER_AGENT = "PyLauncher/0.1.0"


def file_sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download_file(url: str, dest: Path, sha1: str = None, retries: int = 3) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and sha1 and file_sha1(dest) == sha1:
        return False
    if dest.exists() and not sha1:
        return False

    for attempt in range(retries):
        try:
            r = requests.get(url, stream=True, timeout=60, headers={"User-Agent": USER_AGENT})
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
            if sha1 and file_sha1(dest) != sha1:
                dest.unlink(missing_ok=True)
                continue
            return True
        except Exception as e:
            if attempt == retries - 1:
                raise RuntimeError(f"Failed to download {url}: {e}")
    return False


def parse_library_name(name: str):
    parts = name.split(":")
    group, artifact, version = parts[0], parts[1], parts[2]
    classifier = parts[3] if len(parts) > 3 else None
    return group, artifact, version, classifier


def library_url(group: str, artifact: str, version: str, classifier: str = None) -> str:
    gp = group.replace(".", "/")
    fn = f"{artifact}-{version}"
    if classifier:
        fn += f"-{classifier}"
    fn += ".jar"
    return f"{LIBRARIES_BASE}{gp}/{artifact}/{version}/{fn}"


def _extract_natives(jar: Path, dest: Path, extract_rules: dict) -> None:
    excludes = extract_rules.get("exclude", [])
    with zipfile.ZipFile(jar, "r") as zf:
        for member in zf.namelist():
            if any(member.startswith(ex) for ex in excludes):
                continue
            if member.endswith((".dll", ".so", ".dylib")):
                zf.extract(member, dest)


def download_client(version_data: dict, game_dir: Path) -> tuple:
    v = version_data["id"]
    info = version_data["downloads"]["client"]
    path = game_dir / "versions" / v / f"{v}.jar"
    downloaded = download_file(info["url"], path, sha1=info["sha1"])
    return path, downloaded


def download_libraries(version_data: dict, game_dir: Path, progress_cb=None) -> tuple:
    libs = game_dir / "libraries"
    natives = game_dir / "natives" / version_data["id"]
    natives.mkdir(parents=True, exist_ok=True)

    cached = downloaded = 0
    allowed = [l for l in version_data.get("libraries", []) if rules_allow(l.get("rules", []))]
    total = len(allowed)

    for i, lib in enumerate(allowed, 1):
        if progress_cb:
            progress_cb(i, total)

        g, a, v, _ = parse_library_name(lib["name"])
        dl = lib.get("downloads", {})
        art = dl.get("artifact")
        has_natives = "natives" in lib

        if art:
            main_path = libs / art["path"]
            ok = download_file(art["url"], main_path, sha1=art.get("sha1"))
        elif has_natives:
            ok = None
        else:
            main_path = libs / g.replace(".", "/") / a / v / f"{a}-{v}.jar"
            ok = download_file(library_url(g, a, v), main_path)

        if ok is True:
            downloaded += 1
        elif ok is False:
            cached += 1

        if has_natives:
            classifier = lib["natives"].get(os_name())
            if not classifier:
                continue
            classifier = classifier.replace("${arch}", natives_arch())

            try:
                if art and "classifiers" in dl and classifier in dl["classifiers"]:
                    nat = dl["classifiers"][classifier]
                    nat_path = libs / nat["path"]
                    download_file(nat["url"], nat_path, sha1=nat.get("sha1"))
                    _extract_natives(nat_path, natives, lib.get("extract", {}))
                else:
                    nat_path = libs / g.replace(".", "/") / a / v / f"{a}-{v}-{classifier}.jar"
                    download_file(library_url(g, a, v, classifier), nat_path)
                    _extract_natives(nat_path, natives, lib.get("extract", {}))
            except RuntimeError as e:
                print(f"  warning: native unavailable for {lib['name']}: {e}")

    return cached, downloaded


def download_assets(version_data: dict, game_dir: Path, verbose: bool = True, progress_cb=None) -> tuple:
    info = version_data.get("assetIndex")
    if not info:
        return 0, 0

    idx_id = info["id"]
    idx_dir = game_dir / "assets" / "indexes"
    obj_dir = game_dir / "assets" / "objects"
    idx_dir.mkdir(parents=True, exist_ok=True)
    obj_dir.mkdir(parents=True, exist_ok=True)

    idx_path = idx_dir / f"{idx_id}.json"
    download_file(info["url"], idx_path, sha1=info.get("sha1"))

    with open(idx_path, "r", encoding="utf-8") as f:
        idx = json.load(f)

    total = len(idx["objects"])
    cached = downloaded = 0
    if verbose:
        print(f"  assets: {total} objects")

    for i, obj in enumerate(idx["objects"].values(), 1):
        h = obj["hash"]
        p = h[:2]
        ok = download_file(f"{RESOURCES_BASE}{p}/{h}", obj_dir / p / h, sha1=h)
        if ok:
            downloaded += 1
        else:
            cached += 1
        if progress_cb:
            progress_cb(i, total)
        if verbose and (i % 500 == 0 or i == total):
            print(f"    {i}/{total}")

    return cached, downloaded