import platform
import shutil
from pathlib import Path


def _linux_candidates() -> list:
    out = []
    for base_str in ("/usr/lib/jvm", str(Path.home() / ".local" / "jdks")):
        base = Path(base_str)
        if base.exists():
            for d in sorted(base.iterdir()):
                if d.is_dir():
                    j = d / "bin" / "java"
                    if j.exists():
                        out.append(str(j))
    return out


def _macos_candidates() -> list:
    base = Path("/Library/Java/JavaVirtualMachines")
    out = []
    if base.exists():
        for d in sorted(base.iterdir()):
            j = d / "Contents" / "Home" / "bin" / "java"
            if j.exists():
                out.append(str(j))
    return out


def _windows_candidates() -> list:
    out = []
    for base_str in ("C:/Program Files/Java", "C:/Program Files/Eclipse Adoptium"):
        base = Path(base_str)
        if base.exists():
            for d in sorted(base.iterdir()):
                j = d / "bin" / "java.exe"
                if j.exists():
                    out.append(str(j))
    return out


def discover_java() -> list:
    system = platform.system().lower()
    if system == "linux":
        paths = _linux_candidates()
    elif system == "darwin":
        paths = _macos_candidates()
    elif system == "windows":
        paths = _windows_candidates()
    else:
        paths = []

    on_path = shutil.which("java")
    if on_path and on_path not in paths:
        paths.insert(0, on_path)
    return paths