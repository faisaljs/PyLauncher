import os

from pylauncher import args
from pylauncher.download import library_url, parse_library_name

from .conftest import (
    assert_no_unresolved,
    make_legacy_version_data,
    make_modern_version_data,
)


def test_parse_library_name_no_classifier():
    assert parse_library_name("org.lwjgl:lwjgl:3.3.2") == ("org.lwjgl", "lwjgl", "3.3.2", None)


def test_parse_library_name_with_classifier():
    assert parse_library_name("org.lwjgl:lwjgl:3.3.2:natives-linux") == (
        "org.lwjgl", "lwjgl", "3.3.2", "natives-linux",
    )


def test_library_url_format():
    url = library_url("org.lwjgl", "lwjgl", "3.3.2")
    assert url == "https://libraries.minecraft.net/org/lwjgl/lwjgl/3.3.2/lwjgl-3.3.2.jar"


def test_library_url_with_classifier():
    url = library_url("org.lwjgl", "lwjgl", "3.3.2", "natives-linux")
    assert url.endswith("lwjgl-3.3.2-natives-linux.jar")


def test_classpath_contains_client_jar(game_dir):
    data = make_modern_version_data()
    client = game_dir / "versions" / "1.20.4" / "1.20.4.jar"
    cp = args.build_classpath(data, game_dir, client)
    entries = cp.split(os.pathsep)
    assert str(client) in entries


def test_classpath_includes_existing_libraries(game_dir):
    data = make_modern_version_data()
    lib_path = "org/lwjgl/lwjgl/3.3.2/lwjgl-3.3.2.jar"
    full = game_dir / "libraries" / lib_path
    full.parent.mkdir(parents=True)
    full.write_bytes(b"fake")
    data["libraries"] = [{
        "name": "org.lwjgl:lwjgl:3.3.2",
        "downloads": {"artifact": {"path": lib_path, "url": "http://x", "sha1": "0" * 40}},
    }]
    client = game_dir / "versions" / "1.20.4" / "1.20.4.jar"
    cp = args.build_classpath(data, game_dir, client)
    assert str(full) in cp.split(os.pathsep)


def test_classpath_skips_missing_libraries(game_dir):
    data = make_modern_version_data()
    data["libraries"] = [{
        "name": "some.group:artifact:1.0",
        "downloads": {"artifact": {"path": "some/group/artifact/1.0/artifact-1.0.jar",
                                    "url": "http://x", "sha1": "0" * 40}},
    }]
    client = game_dir / "versions" / "1.20.4" / "1.20.4.jar"
    cp = args.build_classpath(data, game_dir, client)
    assert cp == str(client)


def test_jvm_args_no_unresolved_placeholders(game_dir):
    data = make_modern_version_data()
    natives = game_dir / "natives" / "1.20.4"
    out = args.build_jvm_args(data, game_dir, natives, memory_mb=2048)
    assert_no_unresolved(out)


def test_jvm_args_has_memory_flags(game_dir):
    data = make_modern_version_data()
    natives = game_dir / "natives" / "1.20.4"
    out = args.build_jvm_args(data, game_dir, natives, memory_mb=4096)
    assert "-Xmx4096M" in out
    assert any(a.startswith("-Xms") for a in out)


def test_jvm_args_classpath_substituted(game_dir):
    data = make_modern_version_data()
    natives = game_dir / "natives" / "1.20.4"
    out = args.build_jvm_args(data, game_dir, natives, memory_mb=2048)
    assert "-cp" in out
    cp_idx = out.index("-cp")
    cp_value = out[cp_idx + 1]
    assert str(game_dir / "versions" / "1.20.4" / "1.20.4.jar") in cp_value


def test_jvm_args_natives_dir_substituted(game_dir):
    data = make_modern_version_data()
    natives = game_dir / "natives" / "1.20.4"
    out = args.build_jvm_args(data, game_dir, natives, memory_mb=2048)
    assert any(str(natives) in a for a in out)


def test_jvm_args_legacy_fallback(game_dir):
    data = make_legacy_version_data("1.7.10")
    vdir = game_dir / "versions" / "1.7.10"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "1.7.10.jar").write_bytes(b"fake")
    natives = game_dir / "natives" / "1.7.10"
    natives.mkdir(parents=True, exist_ok=True)
    out = args.build_jvm_args(data, game_dir, natives, memory_mb=1024)
    assert any(a.startswith("-Djava.library.path=") for a in out)
    assert "-cp" in out
    assert "-Xmx1024M" in out


def test_game_args_no_unresolved_placeholders(game_dir):
    data = make_modern_version_data()
    out = args.build_game_args(data, game_dir, "Steve", "00000000-0000-3000-8000-000000000000")
    assert_no_unresolved(out)


def test_game_args_username_uuid(game_dir):
    data = make_modern_version_data()
    uuid = "0db08d0c-5b90-38c6-a245-a9ab38856c46"
    out = args.build_game_args(data, game_dir, "NotGriaz", uuid)
    assert "--username" in out
    assert "NotGriaz" in out
    assert "--uuid" in out
    assert uuid in out


def test_game_args_access_token_zero(game_dir):
    data = make_modern_version_data()
    out = args.build_game_args(data, game_dir, "Steve", "00000000-0000-3000-8000-000000000000")
    idx = out.index("--accessToken")
    assert out[idx + 1] == "0"


def test_game_args_assets_dir(game_dir):
    data = make_modern_version_data()
    out = args.build_game_args(data, game_dir, "Steve", "00000000-0000-3000-8000-000000000000")
    idx = out.index("--assetsDir")
    assert out[idx + 1] == str(game_dir / "assets")


def test_game_args_legacy_minecraft_arguments(game_dir):
    data = make_legacy_version_data("1.7.10")
    uuid = "0db08d0c-5b90-38c6-a245-a9ab38856c46"
    out = args.build_game_args(data, game_dir, "Steve", uuid)
    assert_no_unresolved(out)
    assert "Steve" in out
    assert uuid in out