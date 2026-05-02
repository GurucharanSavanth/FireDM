from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scripts" / "release"
sys.path.insert(0, str(SCRIPT_DIR))

import github_release  # noqa: E402
from common import file_sha256  # noqa: E402


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def create_manifest_tree(tmp_path: Path, *, channel: str = "dev", signed: bool = False) -> Path:
    build_id = "20260427_V1"
    dist = tmp_path / "dist"
    installer = write(dist / "installers" / f"FireDM_Setup_{build_id}_{channel}_win_x64.exe", "installer")
    installer_manifest = write(
        dist / "installers" / f"FireDM_Setup_{build_id}_{channel}_win_x64.manifest.json",
        "{}",
    )
    portable = write(dist / "portable" / f"FireDM_{build_id}_{channel}_win_x64_portable.zip", "portable")
    licenses = write(dist / "licenses" / f"license-inventory_{build_id}.json", "{}")
    notes = write(dist / f"FireDM_release_notes_{build_id}.md", "notes")
    manifest_path = dist / f"FireDM_release_manifest_{build_id}.json"
    artifacts = [
        ("installer", installer, signed),
        ("installerManifest", installer_manifest, False),
        ("portableZip", portable, False),
        ("licenseInventory", licenses, False),
        ("releaseNotes", notes, False),
    ]
    manifest = {
        "version": "2022.2.5",
        "build_id": build_id,
        "build_date": "20260427",
        "build_index": 1,
        "tag_name": f"build-{build_id}",
        "release_name": f"FireDM {build_id}",
        "channel": channel,
        "arch": "x64",
        "workingTreeDirty": False,
        "validation": {"payload": "passed", "installer": "passed"},
        "checksumsPath": f"checksums/SHA256SUMS_{build_id}.txt",
        "artifacts": [
            {
                "kind": kind,
                "path": str(path.relative_to(dist)).replace("\\", "/"),
                "arch": "x64",
                "size": path.stat().st_size,
                "sha256": file_sha256(path),
                "signed": is_signed,
            }
            for kind, path, is_signed in artifacts
        ],
    }
    write(manifest_path, json.dumps(manifest, indent=2))
    checksum_lines = [f"# build_id: {build_id}"]
    for _, path, _ in artifacts:
        checksum_lines.append(f"{file_sha256(path)}  {path.relative_to(dist).as_posix()}")
    checksum_lines.append(f"{file_sha256(manifest_path)}  {manifest_path.relative_to(dist).as_posix()}")
    write(dist / "checksums" / f"SHA256SUMS_{build_id}.txt", "\n".join(checksum_lines) + "\n")
    return manifest_path


def test_dry_run_plan_does_not_publish(monkeypatch, tmp_path):
    manifest = create_manifest_tree(tmp_path)
    called = False

    def fake_run(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("publish should not run during build_plan")

    monkeypatch.setattr(github_release.subprocess, "run", fake_run)

    plan = github_release.build_plan(manifest)

    assert plan.tag == "build-20260427_V1"
    assert plan.title == "FireDM 20260427_V1"
    assert plan.prerelease is True
    assert called is False


def test_missing_artifact_fails(tmp_path):
    manifest = create_manifest_tree(tmp_path)
    (manifest.parent / "portable" / "FireDM_20260427_V1_dev_win_x64_portable.zip").unlink()

    with pytest.raises(SystemExit, match="missing"):
        github_release.build_plan(manifest)


def test_checksum_mismatch_fails(tmp_path):
    manifest = create_manifest_tree(tmp_path)
    installer = manifest.parent / "installers" / "FireDM_Setup_20260427_V1_dev_win_x64.exe"
    installer.write_text("changed", encoding="utf-8")

    with pytest.raises(SystemExit, match="Checksum mismatch"):
        github_release.build_plan(manifest)


def test_checksum_target_not_in_manifest_fails(tmp_path):
    manifest = create_manifest_tree(tmp_path)
    extra = write(manifest.parent / "portable" / "FireDM_20260427_V1_dev_win_x64_extra.zip", "extra")
    checksums = manifest.parent / "checksums" / "SHA256SUMS_20260427_V1.txt"
    with checksums.open("a", encoding="utf-8") as handle:
        handle.write(f"{file_sha256(extra)}  {extra.relative_to(manifest.parent).as_posix()}\n")

    with pytest.raises(SystemExit, match="not listed in release manifest"):
        github_release.build_plan(manifest)


def test_stale_artifact_without_build_id_fails(tmp_path):
    manifest = create_manifest_tree(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    stale = write(manifest.parent / "installers" / "FireDM_Setup_2022.2.5_dev_win_x64.exe", "stale")
    payload["artifacts"][0]["path"] = stale.relative_to(manifest.parent).as_posix()
    payload["artifacts"][0]["sha256"] = file_sha256(stale)
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SystemExit, match="stale artifact"):
        github_release.build_plan(manifest)


def test_stable_channel_requires_signed_installer(monkeypatch, tmp_path):
    manifest = create_manifest_tree(tmp_path, channel="stable", signed=False)
    monkeypatch.setattr(github_release, "git_value", lambda args: "")

    with pytest.raises(SystemExit, match="signed installer"):
        github_release.build_plan(manifest, allow_dirty=True)


def test_stable_signed_release_not_prerelease_by_default(monkeypatch, tmp_path):
    manifest = create_manifest_tree(tmp_path, channel="stable", signed=True)
    monkeypatch.setattr(github_release, "git_value", lambda args: "")

    plan = github_release.build_plan(manifest, allow_dirty=True)

    assert plan.prerelease is False
