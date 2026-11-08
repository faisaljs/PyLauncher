"""Mojang library rule evaluation and platform detection."""

import platform


def os_name() -> str:
    """Return Mojang's OS name string: 'windows', 'osx', or 'linux'."""
    s = platform.system().lower()
    if s == "windows":
        return "windows"
    if s == "darwin":
        return "osx"
    return "linux"


def natives_arch() -> str:
    """Architecture string used for ${arch} substitution in natives names."""
    m = platform.machine().lower()
    if m in ("aarch64", "arm64"):
        return "arm64"
    if "64" in m:
        return "64"
    return "32"


def arch_matches(required: str) -> bool:
    """Check whether the local machine matches a rules[].os.arch value."""
    m = platform.machine().lower()
    if required == "x86":
        return m in ("i386", "i686", "x86")
    if required == "x86_64":
        return m in ("x86_64", "amd64")
    if required == "arm64":
        return m in ("aarch64", "arm64")
    if required == "32":
        return not ("64" in m or m == "amd64" or m == "aarch64")
    if required == "64":
        return "64" in m or m in ("amd64", "aarch64")
    return m == required


def _rule_matches(rule: dict) -> bool:
    """Check a single rule against the local platform."""
    os_rule = rule.get("os")
    if os_rule:
        if "name" in os_rule and os_rule["name"] != os_name():
            return False
        if "arch" in os_rule and not arch_matches(os_rule["arch"]):
            return False
    if rule.get("features"):
        # We don't enable demo mode, custom resolution, quickplay, etc.
        return False
    return True


def rules_allow(rules: list) -> bool:
    """Evaluate a Mojang rules list. First matching rule wins."""
    if not rules:
        return True
    for rule in rules:
        if _rule_matches(rule):
            return rule.get("action", "allow") == "allow"
    return False