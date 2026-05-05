from __future__ import annotations

import stat
import sys
import tarfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "scripts" / "release"
sys.path.insert(0, str(SCRIPT_DIR))

import build_linux  # noqa: E402
import validate_linux_payload  # noqa: E402
import validate_linux_portable  # noqa: E402


def test_linux_build_script_exists_and_is_executable():
    script = REPO_ROOT / "scripts" / "linux-build.sh"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "scripts/release/build_linux.py" in text
    assert "PyInstaller is not a cross-compiler" in text
    assert "scripts/release/check_dependencies.py" in text
    assert "select-build-code" in text


def test_linux_pyinstaller_spec_exists():
    spec = REPO_ROOT / "scripts" / "firedm-linux.spec"
    assert spec.is_file()
    text = spec.read_text(encoding="utf-8")
    assert "FireDM" in text
    assert "tkinter" in text
    assert "console=False" in text
    assert "console=True" in text


def test_build_linux_script_uses_versioning_and_naming():
    text = (SCRIPT_DIR / "build_linux.py").read_text(encoding="utf-8")
    assert "linux_archive_name" in text
    assert "linux_payload_root" in text
    assert "make_build_info" in text
    assert "write_build_info" in text
    assert "select_build_id" in text
    assert "PyInstaller is not a cross-compiler" in text


def test_validate_linux_payload_required_files():
    required = set(validate_linux_payload.REQUIRED_FILES)
    assert "firedm" in required
    assert "FireDM-GUI" in required
    assert "_internal/certifi/cacert.pem" in required
    assert "payload-manifest.json" in required


def test_validate_linux_portable_executable_bit_check(tmp_path):
    root = tmp_path / "FireDM"
    root.mkdir()
    for rel in validate_linux_portable.REQUIRED_FILES:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
    (root / "firedm").write_text("exe", encoding="utf-8")
    (root / "FireDM-GUI").write_text("gui", encoding="utf-8")
    (root / "payload-manifest.json").write_text('{"build_id":"20260427_V1"}', encoding="utf-8")
    (root / "firedm").chmod(0o755)
    (root / "FireDM-GUI").chmod(0o755)

    payload = validate_linux_portable.validate_root(root, skip_smoke=True)
    # On Linux: executable bit is required and must be set.
    # On non-Linux: check is non-required (warning only), so required_missing is empty.
    assert payload["summary"]["required_missing"] == []


def test_validate_linux_portable_missing_executable_bit_fails(tmp_path):
    root = tmp_path / "FireDM"
    root.mkdir()
    for rel in validate_linux_portable.REQUIRED_FILES:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
    (root / "firedm").write_text("exe", encoding="utf-8")
    (root / "FireDM-GUI").write_text("gui", encoding="utf-8")
    (root / "payload-manifest.json").write_text('{"build_id":"20260427_V1"}', encoding="utf-8")
    (root / "firedm").chmod(0o644)
    (root / "FireDM-GUI").chmod(0o644)

    payload = validate_linux_portable.validate_root(root, skip_smoke=True)
    if sys.platform == "linux":
        # On Linux the bit is required — must appear in required_missing.
        missing = payload["summary"]["required_missing"]
        assert any("executable bit" in name for name in missing)
    else:
        # On non-Linux the check is non-required (warning); required_missing stays empty.
        warnings = payload["summary"]["warnings"]
        assert any("executable bit" in name for name in warnings)


def test_safe_extract_rejects_path_escape(tmp_path):
    archive = tmp_path / "evil.tar.gz"
    target_root = tmp_path / "extract"
    payload = tmp_path / "FireDM"
    payload.mkdir()
    (payload / "firedm").write_text("ok", encoding="utf-8")
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(payload, arcname="FireDM")
        info = tarfile.TarInfo(name="../escape.txt")
        data = b"escape"
        info.size = len(data)
        import io
        tar.addfile(info, io.BytesIO(data))

    target_root.mkdir()
    with pytest.raises(SystemExit, match="escapes extraction root"):
        validate_linux_portable.safe_extract(archive, target_root)
