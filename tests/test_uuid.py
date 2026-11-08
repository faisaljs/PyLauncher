"""Tests for pylauncher.uuid.offline_uuid."""

import re

import pytest

from pylauncher.uuid import offline_uuid


# Golden value captured from a real launch on this machine.
# If this ever changes, the offline UUID scheme has broken and
# offline worlds / servers will stop recognizing the player.
def test_known_value_notgriaz():
    assert offline_uuid("NotGriaz") == "0db08d0c-5b90-38c6-a245-a9ab38856c46"


def test_deterministic():
    assert offline_uuid("Steve") == offline_uuid("Steve")
    assert offline_uuid("Alex") == offline_uuid("Alex")


def test_different_names_differ():
    assert offline_uuid("Steve") != offline_uuid("Alex")
    assert offline_uuid("Notch") != offline_uuid("notch")  # case sensitive


def test_format():
    u = offline_uuid("Anyone")
    assert re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", u)


def test_version_bits():
    # Third group must start with '3' (version 3 = name-based MD5).
    u = offline_uuid("Steve")
    assert u.split("-")[2][0] == "3"


def test_variant_bits():
    # Fourth group must start with 8, 9, a, or b (IETF variant).
    u = offline_uuid("Steve")
    assert u.split("-")[3][0] in "89ab"