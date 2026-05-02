from __future__ import annotations

import io
import tarfile
import zipfile

import pytest

from firedm.utils import safe_extract_tar, safe_extract_zip, zip_extract


def test_zip_extract_keeps_legacy_safe_path(tmp_path):
    archive = tmp_path / "safe.zip"
    target = tmp_path / "out"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("pkg/module.py", "value = 1")

    zip_extract(archive, target)

    assert (target / "pkg" / "module.py").read_text(encoding="utf-8") == "value = 1"


def test_safe_extract_zip_rejects_parent_traversal(tmp_path):
    archive = tmp_path / "bad.zip"
    target = tmp_path / "out"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("../escape.txt", "bad")

    with pytest.raises(ValueError, match="escapes target"):
        safe_extract_zip(archive, target)

    assert not (tmp_path / "escape.txt").exists()


def test_safe_extract_zip_rejects_windows_absolute_path(tmp_path):
    archive = tmp_path / "bad-windows.zip"
    target = tmp_path / "out"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr(r"C:\temp\escape.txt", "bad")

    with pytest.raises(ValueError, match="absolute"):
        safe_extract_zip(archive, target)


def test_safe_extract_tar_rejects_symlink_members(tmp_path):
    archive = tmp_path / "bad.tar"
    target = tmp_path / "out"
    info = tarfile.TarInfo("pkg/link")
    info.type = tarfile.SYMTYPE
    info.linkname = "../escape.txt"

    with tarfile.open(archive, "w") as tar:
        tar.addfile(info)

    with pytest.raises(ValueError, match="links are not allowed"):
        safe_extract_tar(archive, target)


def test_safe_extract_tar_allows_regular_member(tmp_path):
    archive = tmp_path / "safe.tar"
    target = tmp_path / "out"
    payload = b"value = 1"
    info = tarfile.TarInfo("pkg/module.py")
    info.size = len(payload)

    with tarfile.open(archive, "w") as tar:
        tar.addfile(info, io.BytesIO(payload))

    safe_extract_tar(archive, target)

    assert (target / "pkg" / "module.py").read_text(encoding="utf-8") == "value = 1"
