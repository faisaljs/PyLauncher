"""Tests for pylauncher.rules — platform detection and rule evaluation."""

import pytest

from pylauncher import rules


# ----------------------------------------------------------------------
# os_name / natives_arch — real platform calls
# ----------------------------------------------------------------------
@pytest.mark.parametrize("system,expected", [
    ("Windows", "windows"),
    ("Darwin",  "osx"),
    ("Linux",   "linux"),
])
def test_os_name(monkeypatch, system, expected):
    monkeypatch.setattr(rules.platform, "system", lambda: system)
    assert rules.os_name() == expected


@pytest.mark.parametrize("machine,expected", [
    ("x86_64",  "64"),
    ("AMD64",   "64"),
    ("aarch64", "arm64"),
    ("arm64",   "arm64"),
    ("i386",    "32"),
    ("i686",    "32"),
])
def test_natives_arch(monkeypatch, machine, expected):
    monkeypatch.setattr(rules.platform, "machine", lambda: machine)
    assert rules.natives_arch() == expected


# ----------------------------------------------------------------------
# arch_matches
# ----------------------------------------------------------------------
@pytest.mark.parametrize("machine,required,expected", [
    ("x86_64",  "x86_64", True),
    ("amd64",   "x86_64", True),
    ("aarch64", "x86_64", False),
    ("i686",    "x86",    True),
    ("x86_64",  "x86",    False),
    ("aarch64", "arm64",  True),
    ("x86_64",  "arm64",  False),
    ("x86_64",  "64",     True),
    ("i686",    "64",     False),
    ("i686",    "32",     True),
    ("x86_64",  "32",     False),
])
def test_arch_matches(monkeypatch, machine, required, expected):
    monkeypatch.setattr(rules.platform, "machine", lambda: machine)
    assert rules.arch_matches(required) is expected


# ----------------------------------------------------------------------
# rules_allow — monkeypatch os_name so tests are platform-independent
# ----------------------------------------------------------------------
@pytest.fixture
def fake_linux(monkeypatch):
    monkeypatch.setattr(rules, "os_name", lambda: "linux")
    monkeypatch.setattr(rules, "arch_matches", lambda arch: arch in ("x86_64", "64", "32"))
    return "linux"


@pytest.fixture
def fake_windows(monkeypatch):
    monkeypatch.setattr(rules, "os_name", lambda: "windows")
    monkeypatch.setattr(rules, "arch_matches", lambda arch: arch in ("x86_64", "64", "32"))
    return "windows"


def test_no_rules_allows():
    assert rules.rules_allow([]) is True
    assert rules.rules_allow(None) is True


def test_simple_allow(fake_linux):
    assert rules.rules_allow([{"action": "allow"}]) is True


def test_simple_disallow(fake_linux):
    assert rules.rules_allow([{"action": "disallow"}]) is False


def test_allow_matching_os(fake_linux):
    rule = {"action": "allow", "os": {"name": "linux"}}
    assert rules.rules_allow([rule]) is True


def test_allow_nonmatching_os(fake_linux):
    rule = {"action": "allow", "os": {"name": "windows"}}
    assert rules.rules_allow([rule]) is False


def test_disallow_matching_os(fake_linux):
    rule = {"action": "disallow", "os": {"name": "linux"}}
    assert rules.rules_allow([rule]) is False


def test_first_match_wins(fake_linux):
    # allow linux first — should return True even though the second rule disallows.
    rules_list = [
        {"action": "allow",    "os": {"name": "linux"}},
        {"action": "disallow", "os": {"name": "linux"}},
    ]
    assert rules.rules_allow(rules_list) is True


def test_first_nonmatch_falls_through(fake_linux):
    # First rule doesn't match; second does.
    rules_list = [
        {"action": "disallow", "os": {"name": "windows"}},
        {"action": "allow",    "os": {"name": "linux"}},
    ]
    assert rules.rules_allow(rules_list) is True


def test_feature_gated_rule_rejected(fake_linux):
    rule = {"action": "allow", "features": {"is_demo_user": True}}
    assert rules.rules_allow([rule]) is False


def test_arch_rule_matches(fake_linux):
    rule = {"action": "allow", "os": {"name": "linux", "arch": "x86_64"}}
    assert rules.rules_allow([rule]) is True


def test_arch_rule_misses(fake_linux):
    rule = {"action": "allow", "os": {"name": "linux", "arch": "arm64"}}
    assert rules.rules_allow([rule]) is False


def test_windows_os_detection(fake_windows):
    rule = {"action": "allow", "os": {"name": "windows"}}
    assert rules.rules_allow([rule]) is True
    rule2 = {"action": "allow", "os": {"name": "linux"}}
    assert rules.rules_allow([rule2]) is False