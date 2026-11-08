from unittest.mock import patch

from pylauncher.gui import java_discovery


def test_discover_java_linux_returns_list(monkeypatch):
    monkeypatch.setattr(java_discovery.platform, "system", lambda: "Linux")
    with patch.object(java_discovery, "_linux_candidates", return_value=["/a/java"]), \
         patch.object(java_discovery.shutil, "which", return_value="/on/path/java"):
        result = java_discovery.discover_java()
    assert "/on/path/java" in result
    assert "/a/java" in result
    assert result[0] == "/on/path/java"


def test_discover_java_no_path_java(monkeypatch):
    monkeypatch.setattr(java_discovery.platform, "system", lambda: "Linux")
    with patch.object(java_discovery, "_linux_candidates", return_value=["/a/java"]), \
         patch.object(java_discovery.shutil, "which", return_value=None):
        result = java_discovery.discover_java()
    assert result == ["/a/java"]


def test_discover_java_empty(monkeypatch):
    monkeypatch.setattr(java_discovery.platform, "system", lambda: "Linux")
    with patch.object(java_discovery, "_linux_candidates", return_value=[]), \
         patch.object(java_discovery.shutil, "which", return_value=None):
        result = java_discovery.discover_java()
    assert result == []


def test_discover_java_unknown_platform(monkeypatch):
    monkeypatch.setattr(java_discovery.platform, "system", lambda: "Plan9")
    with patch.object(java_discovery.shutil, "which", return_value=None):
        result = java_discovery.discover_java()
    assert result == []


def test_discover_java_dedupes_path(monkeypatch):
    monkeypatch.setattr(java_discovery.platform, "system", lambda: "Linux")
    with patch.object(java_discovery, "_linux_candidates", return_value=["/on/path/java"]), \
         patch.object(java_discovery.shutil, "which", return_value="/on/path/java"):
        result = java_discovery.discover_java()
    assert result.count("/on/path/java") == 1