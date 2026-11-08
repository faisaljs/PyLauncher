import shutil

import pytest

from pylauncher.launcher import detect_java_major, required_java_major

from .conftest import make_legacy_version_data, make_modern_version_data


def test_required_java_modern():
    assert required_java_major(make_modern_version_data()) == 17


def test_required_java_legacy_defaults_to_8():
    assert required_java_major(make_legacy_version_data()) == 8


def test_required_java_missing_field_explicit():
    assert required_java_major({"id": "unknown", "type": "release"}) == 8


def test_required_java_java21_version():
    data = {"id": "26.4", "javaVersion": {"majorVersion": 21}}
    assert required_java_major(data) == 21


def test_detect_java_nonexistent_returns_none():
    assert detect_java_major("/this/path/does/not/exist/java") is None


@pytest.mark.skipif(shutil.which("java") is None, reason="no java on PATH")
def test_detect_java_real():
    major = detect_java_major("java")
    assert major is not None
    assert major >= 8