from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scripts" / "release"
sys.path.insert(0, str(SCRIPT_DIR))

import generate_checksums  # noqa: E402
from common import (  # noqa: E402
    checksum_file_name,
    installer_manifest_file_name,
    installer_name,
    license_inventory_name,
    portable_name,
    release_manifest_name,
    release_notes_name,
)


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_artifact_names_include_build_id():
    build_id = "20260427_V1"

    assert installer_name(build_id, "dev", "x64") == "FireDM_Setup_20260427_V1_dev_win_x64.exe"
    assert portable_name(build_id, "dev", "x64") == "FireDM_20260427_V1_dev_win_x64_portable.zip"
    assert release_manifest_name(build_id) == "FireDM_release_manifest_20260427_V1.json"
    assert checksum_file_name(build_id) == "SHA256SUMS_20260427_V1.txt"
    assert license_inventory_name(build_id) == "license-inventory_20260427_V1.json"


def test_checksum_generation_is_scoped_to_build_id(monkeypatch, tmp_path):
    build_id = "20260427_V1"
    dist = tmp_path / "dist"
    installers = dist / "installers"
    portable = dist / "portable"
    licenses = dist / "licenses"
    checksums = dist / "checksums"

    installer = write(installers / installer_name(build_id, "dev", "x64"), "installer")
    installer_manifest = write(installers / installer_manifest_file_name(build_id, "dev", "x64"), "{}")
    payload = write(installers / f"FireDM_{build_id}_dev_win_x64_payload.zip", "payload")
    portable = write(portable / portable_name(build_id, "dev", "x64"), "zip")
    license_inventory = write(licenses / license_inventory_name(build_id), "{}")
    notes = write(dist / release_notes_name(build_id), "notes")
    manifest_artifacts = [installer, installer_manifest, payload, portable, license_inventory, notes]
    write(
        dist / release_manifest_name(build_id),
        json.dumps(
            {
                "build_id": build_id,
                "artifacts": [{"path": path.relative_to(dist).as_posix()} for path in manifest_artifacts],
            }
        ),
    )
    write(installers / "FireDM_Setup_20260427_V2_dev_win_x64.exe", "other")

    monkeypatch.setattr(generate_checksums, "DIST_DIR", dist)
    monkeypatch.setattr(generate_checksums, "INSTALLERS_DIR", installers)
    monkeypatch.setattr(generate_checksums, "PORTABLE_DIR", portable)
    monkeypatch.setattr(generate_checksums, "LICENSES_DIR", licenses)
    monkeypatch.setattr(generate_checksums, "CHECKSUMS_DIR", checksums)
    monkeypatch.setattr(generate_checksums, "ensure_dir", lambda path: Path(path).mkdir(parents=True, exist_ok=True))

    monkeypatch.setattr("sys.argv", ["generate_checksums.py", "--root", str(dist), "--build-id", build_id])
    generate_checksums.main()

    checksum_file = checksums / checksum_file_name(build_id)
    text = checksum_file.read_text(encoding="utf-8")
    assert f"# build_id: {build_id}" in text
    assert "20260427_V1" in text
    assert f"FireDM_{build_id}_dev_win_x64_payload.zip" in text
    assert "20260427_V2" not in text
    assert (checksums / "SHA256SUMS.txt").read_text(encoding="utf-8") == text
