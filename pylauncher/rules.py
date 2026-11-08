import platform


def os_name() -> str:
    s = platform.system().lower()
    if s == "windows":
        return "windows"
    if s == "darwin":
        return "osx"
    return "linux"


def natives_arch() -> str:
    m = platform.machine().lower()
    if m in ("aarch64", "arm64"):
        return "arm64"
    if "64" in m:
        return "64"
    return "32"


def arch_matches(required: str) -> bool:
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
    os_rule = rule.get("os")
    if os_rule:
        if "name" in os_rule and os_rule["name"] != os_name():
            return False
        if "arch" in os_rule and not arch_matches(os_rule["arch"]):
            return False
    if rule.get("features"):
        return False
    return True


def rules_allow(rules: list) -> bool:
    if not rules:
        return True
    result = False
    for rule in rules:
        if _rule_matches(rule):
            result = rule.get("action", "allow") == "allow"
    return result