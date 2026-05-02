from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scripts" / "release"
sys.path.insert(0, str(SCRIPT_DIR))

import build_id  # noqa: E402


def test_parse_valid_build_ids():
    assert build_id.parse_build_id("20260427_V1").date == "20260427"
    assert build_id.parse_build_id("20260427_V12").index == 12


@pytest.mark.parametrize(
    "value",
    ["2026-04-27_V1", "20260427_v1", "20260427_V0", "20260230_V1", "20260427_V"],
)
def test_reject_invalid_build_ids(value):
    assert not build_id.validate_build_id(value)
    with pytest.raises(ValueError):
        build_id.parse_build_id(value)


def test_first_build_returns_v1(tmp_path):
    selected = build_id.select_build_id(date="20260427", dist_dir=tmp_path)

    assert selected.build_id == "20260427_V1"
    assert selected.tag == "build-20260427_V1"
    assert selected.release_name == "FireDM 20260427_V1"


def test_existing_v1_returns_v2(tmp_path):
    artifact = tmp_path / "installers" / "FireDM_Setup_20260427_V1_dev_win_x64.exe"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("x", encoding="utf-8")

    selected = build_id.select_build_id(date="20260427", dist_dir=tmp_path)

    assert selected.build_id == "20260427_V2"


def test_existing_sparse_ids_return_next_highest(tmp_path):
    for existing in ("20260427_V1", "20260427_V2", "20260427_V5"):
        path = tmp_path / "portable" / f"FireDM_{existing}_dev_win_x64_portable.zip"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")

    assert build_id.select_build_id(date="20260427", dist_dir=tmp_path).build_id == "20260427_V6"


def test_manifest_build_id_is_discovered(tmp_path):
    manifest = tmp_path / "FireDM_release_manifest_20260427_V3.json"
    manifest.write_text(json.dumps({"build_id": "20260427_V3"}), encoding="utf-8")

    assert build_id.select_build_id(date="20260427", dist_dir=tmp_path).build_id == "20260427_V4"


def test_local_tag_discovery_affects_next(monkeypatch, tmp_path):
    monkeypatch.setattr(build_id, "discover_local_tag_build_ids", lambda: {"20260427_V5"})

    assert build_id.select_build_id(date="20260427", dist_dir=tmp_path).build_id == "20260427_V6"


def test_remote_and_github_release_discovery_are_opt_in(monkeypatch, tmp_path):
    monkeypatch.setattr(build_id, "discover_remote_tag_build_ids", lambda: {"20260427_V2"})
    monkeypatch.setattr(build_id, "discover_github_release_build_ids", lambda: {"20260427_V4"})

    selected = build_id.select_build_id(
        date="20260427",
        dist_dir=tmp_path,
        include_remote_tags=True,
        include_github_releases=True,
    )

    assert selected.build_id == "20260427_V5"


def test_github_release_discovery_parses_gh_output(monkeypatch):
    monkeypatch.setattr(build_id.shutil, "which", lambda name: "gh" if name == "gh" else None)

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args[0],
            0,
            stdout='[{"tagName":"build-20260427_V7","name":"FireDM 20260427_V7"}]',
            stderr="",
        )

    monkeypatch.setattr(build_id.subprocess, "run", fake_run)

    assert build_id.discover_github_release_build_ids() == {"20260427_V7"}


def test_explicit_build_id_collision_fails_without_allow_overwrite(tmp_path):
    artifact = tmp_path / "installers" / "FireDM_Setup_20260427_V1_dev_win_x64.exe"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="already exists"):
        build_id.select_build_id(build_id="20260427_V1", dist_dir=tmp_path)

    selected = build_id.select_build_id(build_id="20260427_V1", allow_overwrite=True, dist_dir=tmp_path)
    assert selected.collision_status == "overwrite-allowed"


def test_date_override_must_match_explicit_build_id(tmp_path):
    with pytest.raises(ValueError, match="does not match"):
        build_id.select_build_id(date="20260428", build_id="20260427_V1", dist_dir=tmp_path)
