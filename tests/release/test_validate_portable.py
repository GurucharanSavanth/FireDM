from __future__ import annotations

import sys
import zipfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scripts" / "release"
sys.path.insert(0, str(SCRIPT_DIR))

import validate_portable  # noqa: E402


def make_portable_root(root: Path) -> Path:
    for rel in validate_portable.REQUIRED_FILES:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
    (root / "firedm.exe").write_text("exe", encoding="utf-8")
    (root / "FireDM-GUI.exe").write_text("gui", encoding="utf-8")
    (root / "README_PORTABLE.txt").write_text("portable", encoding="utf-8")
    (root / "build-metadata.json").write_text('{"build_id":"20260427_V1"}', encoding="utf-8")
    (root / "payload-manifest.json").write_text('{"build_id":"20260427_V1"}', encoding="utf-8")
    return root


def test_validate_portable_root_success_with_optional_ffmpeg_warning(tmp_path, monkeypatch):
    root = make_portable_root(tmp_path / "FireDM")
    monkeypatch.setattr(validate_portable.shutil, "which", lambda name: None)
    monkeypatch.setattr(validate_portable.platform, "system", lambda: "Linux")

    payload = validate_portable.validate_root(root)

    assert payload["summary"]["required_missing"] == []
    assert "ffmpeg" in payload["summary"]["warnings"]
    assert "ffprobe" in payload["summary"]["warnings"]


def test_validate_portable_missing_required_file_fails_summary(tmp_path, monkeypatch):
    root = make_portable_root(tmp_path / "FireDM")
    (root / "firedm.exe").unlink()
    monkeypatch.setattr(validate_portable.platform, "system", lambda: "Linux")

    payload = validate_portable.validate_root(root)

    assert "firedm.exe" in payload["summary"]["required_missing"]


def test_validate_portable_archive_extracts_safely(tmp_path, monkeypatch):
    root = make_portable_root(tmp_path / "src")
    archive = tmp_path / "portable.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        for path in root.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(root).as_posix())
    monkeypatch.setattr(validate_portable.platform, "system", lambda: "Linux")

    args = type("Args", (), {"root": None, "archive": str(archive)})
    extracted, temp = validate_portable.resolve_root(args)
    try:
        payload = validate_portable.validate_root(extracted)
    finally:
        assert temp is not None
        temp.cleanup()

    assert payload["summary"]["required_missing"] == []
