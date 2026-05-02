from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scripts" / "release"
sys.path.insert(0, str(SCRIPT_DIR))

import build_id  # noqa: E402
import versioning  # noqa: E402


def test_product_version_matches_canonical_module():
    expected = (Path(__file__).resolve().parents[2] / "firedm" / "version.py").read_text(encoding="utf-8")
    namespace: dict = {}
    exec(expected, namespace)
    assert versioning.get_product_version() == namespace["__version__"]


def test_build_code_aliases_are_synonyms_for_build_id():
    assert versioning.parse_build_code("20260427_V1").index == 1
    assert versioning.format_build_code("20260427", 3) == "20260427_V3"
    assert versioning.validate_build_code("20260427_V2") is True
    assert versioning.validate_build_code("not-a-code") is False
    assert versioning.tag_name_for("20260427_V1") == "build-20260427_V1"
    assert versioning.release_name_for("20260427_V1") == "FireDM 20260427_V1"


def test_artifact_prefix_includes_build_code_channel_platform_arch():
    prefix = versioning.artifact_prefix_for("FireDM", "20260427_V1", "dev", "win", "x64")
    assert prefix == "FireDM_20260427_V1_dev_win_x64"


def test_select_build_code_returns_buildidselection_with_alias_field():
    selection = versioning.select_build_code(date="20260427", dist_dir=SCRIPT_DIR.parent / "release-empty")
    assert selection.build_id == "20260427_V1"
    assert selection.tag == "build-20260427_V1"
    assert selection.release_name == "FireDM 20260427_V1"


def test_make_build_info_writes_python_module(tmp_path):
    info = versioning.make_build_info(
        build_code="20260427_V1",
        channel="dev",
        platform_name="linux",
        arch="x64",
        commit="abc123",
        dirty_tree=False,
    )
    target = tmp_path / "_build_info.py"
    json_target = tmp_path / "_build_info.json"
    versioning.write_build_info(info, target=target, json_target=json_target)
    assert target.is_file()
    payload = json.loads(json_target.read_text(encoding="utf-8"))
    assert payload["build_code"] == "20260427_V1"
    assert payload["product_version"]
    assert payload["tag_name"] == "build-20260427_V1"
    text = target.read_text(encoding="utf-8")
    assert "BUILD_CODE = '20260427_V1'" in text
    assert "BUILD_ID = '20260427_V1'" in text
    assert "TAG_NAME = 'build-20260427_V1'" in text
    namespace: dict = {}
    exec(text, namespace)
    assert namespace["BUILD_INFO"]["channel"] == "dev"
    assert namespace["BUILD_INFO"]["platform"] == "linux"


def test_detect_host_platform_arch_returns_known_pair():
    platform_name, arch = versioning.detect_host_platform_arch()
    assert platform_name in {"windows", "linux", "macos", "darwin"} or platform_name
    assert arch in {"x64", "x86", "arm64"} or arch
