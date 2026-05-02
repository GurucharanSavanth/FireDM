from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scripts" / "release"
sys.path.insert(0, str(SCRIPT_DIR))

import build_id  # noqa: E402
import common  # noqa: E402


def test_windows_artifact_names_include_build_code():
    code = "20260427_V1"
    assert common.installer_name(code, "dev", "x64") == "FireDM_Setup_20260427_V1_dev_win_x64.exe"
    assert common.portable_name(code, "dev", "x64") == "FireDM_20260427_V1_dev_win_x64_portable.zip"


def test_linux_artifact_names_include_build_code():
    code = "20260427_V1"
    assert common.linux_archive_name(code, "dev", "x64") == "FireDM_20260427_V1_dev_linux_x64.tar.gz"
    assert common.linux_portable_name(code, "dev", "x64") == "FireDM_20260427_V1_dev_linux_x64_portable.tar.gz"


def test_per_platform_manifest_naming():
    code = "20260427_V1"
    assert common.per_platform_release_manifest_name(code, "windows") == "FireDM_release_manifest_20260427_V1_windows.json"
    assert common.per_platform_release_manifest_name(code, "linux") == "FireDM_release_manifest_20260427_V1_linux.json"
    assert common.merged_release_manifest_name(code) == "FireDM_release_manifest_20260427_V1.json"


def test_linux_payload_root_uses_supported_arch_only():
    assert common.linux_payload_root("x64").as_posix().endswith("payloads-linux/linux-x64/FireDM")
    import argparse
    with pytest.raises((argparse.ArgumentTypeError, SystemExit)):
        common.linux_arch_to_payload("x86")


def test_same_build_code_across_platforms():
    code = build_id.format_build_id("20260427", 4)
    assert code == "20260427_V4"
    win = common.installer_name(code, "dev", "x64")
    linux = common.linux_archive_name(code, "dev", "x64")
    assert code in win and code in linux
    assert "win" in win and "linux" in linux


def test_explicit_build_code_collision_fails_per_platform(tmp_path):
    portable = tmp_path / "portable" / common.portable_name("20260427_V1", "dev", "x64")
    portable.parent.mkdir(parents=True)
    portable.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="already exists"):
        build_id.select_build_id(build_id="20260427_V1", dist_dir=tmp_path)
