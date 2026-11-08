from pathlib import Path
from unittest.mock import patch

import pytest

from pylauncher import download


@pytest.fixture
def fake_version_data(tmp_path: Path) -> dict:
    return {
        "id": "1.7.10",
        "libraries": [
            {"name": "com.example:simple:1.0"},
            {
                "name": "org.lwjgl.lwjgl:lwjgl-platform:2.9.1",
                "natives": {"linux": "natives-linux",
                            "windows": "natives-windows",
                            "osx": "natives-osx"},
            },
            {
                "name": "modern:lib:2.0",
                "downloads": {"artifact": {
                    "path": "modern/lib/2.0/lib-2.0.jar",
                    "url": "http://example/lib-2.0.jar",
                    "sha1": "0" * 40,
                }},
            },
        ],
    }


def test_natives_only_library_skips_base_jar(fake_version_data, tmp_path):
    with patch.object(download, "download_file", return_value=True) as dl, \
         patch.object(download, "_extract_natives"):
        download.download_libraries(fake_version_data, tmp_path)

    urls = [call.args[0] for call in dl.call_args_list]
    for url in urls:
        assert not url.endswith("/lwjgl-platform-2.9.1.jar"), \
            f"tried to download nonexistent base jar: {url}"
    assert any("lwjgl-platform-2.9.1-natives-" in url for url in urls)


def test_regular_library_base_jar_downloaded(fake_version_data, tmp_path):
    with patch.object(download, "download_file", return_value=True) as dl, \
         patch.object(download, "_extract_natives"):
        download.download_libraries(fake_version_data, tmp_path)

    urls = [call.args[0] for call in dl.call_args_list]
    assert any("/com/example/simple/1.0/simple-1.0.jar" in url for url in urls)


def test_modern_library_uses_artifact_url(fake_version_data, tmp_path):
    with patch.object(download, "download_file", return_value=True) as dl, \
         patch.object(download, "_extract_natives"):
        download.download_libraries(fake_version_data, tmp_path)

    urls = [call.args[0] for call in dl.call_args_list]
    assert "http://example/lib-2.0.jar" in urls