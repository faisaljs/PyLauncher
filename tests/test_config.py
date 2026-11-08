from pylauncher.config import effective_settings, set_version_override


def test_effective_no_override():
    cfg = {"java": "java", "memory_mb": 2048, "per_version": {}}
    eff = effective_settings(cfg, "1.20.4")
    assert eff == {"java": "java", "memory_mb": 2048}


def test_effective_with_override():
    cfg = {
        "java": "java",
        "memory_mb": 2048,
        "per_version": {"1.21.11": {"java": "/jdk21/java", "memory_mb": 4096}},
    }
    eff = effective_settings(cfg, "1.21.11")
    assert eff["java"] == "/jdk21/java"
    assert eff["memory_mb"] == 4096


def test_effective_partial_override():
    cfg = {
        "java": "java",
        "memory_mb": 2048,
        "per_version": {"1.21.11": {"memory_mb": 4096}},
    }
    eff = effective_settings(cfg, "1.21.11")
    assert eff["java"] == "java"
    assert eff["memory_mb"] == 4096


def test_set_version_override_new():
    cfg = {"java": "java", "memory_mb": 2048, "per_version": {}}
    cfg2 = set_version_override(cfg, "1.20.4", java="/jdk17/java", memory_mb=3072)
    assert cfg2["per_version"]["1.20.4"]["java"] == "/jdk17/java"
    assert cfg2["per_version"]["1.20.4"]["memory_mb"] == 3072


def test_set_version_override_partial():
    cfg = {"per_version": {"1.20.4": {"java": "/jdk17/java"}}}
    cfg2 = set_version_override(cfg, "1.20.4", memory_mb=4096)
    assert cfg2["per_version"]["1.20.4"]["java"] == "/jdk17/java"
    assert cfg2["per_version"]["1.20.4"]["memory_mb"] == 4096