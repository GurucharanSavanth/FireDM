from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scripts" / "release"
sys.path.insert(0, str(SCRIPT_DIR))

import merge_release_manifest  # noqa: E402
from common import file_sha256  # noqa: E402


def write(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def make_per_platform_manifest(dist: Path, build_id: str, platform: str, channel: str = "dev"):
    if platform == "windows":
        artifact = dist / "installers" / f"FireDM_Setup_{build_id}_{channel}_win_x64.exe"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("installer", encoding="utf-8")
        kind = "installer"
        validation = {"payload": "passed", "installer": "passed", "portable": "passed"}
    else:
        artifact = dist / "portable-linux" / f"FireDM_{build_id}_{channel}_linux_x64.tar.gz"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("linux-tar", encoding="utf-8")
        kind = "linuxPortableArchive"
        validation = {"linux_payload": "passed", "linux_portable": "passed"}
    manifest = {
        "version": "2022.2.5",
        "build_id": build_id,
        "build_code": build_id,
        "build_date": "20260427",
        "build_index": 1,
        "tag_name": f"build-{build_id}",
        "release_name": f"FireDM {build_id}",
        "channel": channel,
        "platform": platform,
        "checksumsPath": f"checksums/SHA256SUMS_{build_id}.txt",
        "validation": validation,
        "blockedArtifacts": {"appImage" if platform == "linux" else "msi": "blocked"},
        "artifacts": [
            {
                "kind": kind,
                "path": str(artifact.relative_to(dist)).replace("\\", "/"),
                "platform": platform,
                "arch": "x64",
                "size": artifact.stat().st_size,
                "sha256": file_sha256(artifact),
                "signed": False,
            }
        ],
    }
    out = write(dist / f"FireDM_release_manifest_{build_id}_{platform}.json", manifest)
    return out, manifest


def test_merge_cross_platform_combines_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(merge_release_manifest, "DIST_DIR", tmp_path)
    build_id = "20260427_V1"
    win_path, _ = make_per_platform_manifest(tmp_path, build_id, "windows")
    linux_path, _ = make_per_platform_manifest(tmp_path, build_id, "linux")
    output = tmp_path / f"FireDM_release_manifest_{build_id}.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "merge_release_manifest.py",
            "--build-id",
            build_id,
            "--windows-manifest",
            str(win_path),
            "--linux-manifest",
            str(linux_path),
            "--output",
            str(output),
            "--workflow",
            "tests",
        ],
    )
    merge_release_manifest.main()

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["build_id"] == build_id
    assert payload["build_code"] == build_id
    assert sorted(payload["platforms"]) == ["linux", "windows"]
    kinds = {a["kind"] for a in payload["artifacts"]}
    assert "installer" in kinds
    assert "linuxPortableArchive" in kinds
    assert payload["validation"]["installer"] == "passed"
    assert payload["validation"]["linux_portable"] == "passed"
    assert "msi" in payload["blocked"]
    assert "appImage" in payload["blocked"]
    assert payload["checksumsPath"] == f"checksums/SHA256SUMS_{build_id}.txt"


def test_merge_rejects_mismatched_build_id(tmp_path, monkeypatch):
    monkeypatch.setattr(merge_release_manifest, "DIST_DIR", tmp_path)
    win_path, _ = make_per_platform_manifest(tmp_path, "20260427_V1", "windows")
    linux_path, _ = make_per_platform_manifest(tmp_path, "20260427_V2", "linux")
    output = tmp_path / "out.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "merge_release_manifest.py",
            "--build-id",
            "20260427_V1",
            "--windows-manifest",
            str(win_path),
            "--linux-manifest",
            str(linux_path),
            "--output",
            str(output),
        ],
    )
    with pytest.raises(SystemExit, match="build_id mismatch"):
        merge_release_manifest.main()


def test_merge_rejects_invalid_build_id(tmp_path, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "merge_release_manifest.py",
            "--build-id",
            "not-valid",
        ],
    )
    with pytest.raises(SystemExit, match="Invalid build id"):
        merge_release_manifest.main()


def test_merge_requires_at_least_one_input(tmp_path, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "merge_release_manifest.py",
            "--build-id",
            "20260427_V1",
        ],
    )
    with pytest.raises(SystemExit, match="at least one"):
        merge_release_manifest.main()
