import subprocess
from pathlib import Path

from firedm.ffmpeg_service import locate_ffmpeg, parse_ffmpeg_version, resolve_ffmpeg_path


def test_parse_ffmpeg_version():
    output = "ffmpeg version 6.1 Copyright (c) 2000-2024 the FFmpeg developers"

    assert parse_ffmpeg_version(output) == "6.1"


def test_resolve_ffmpeg_path_prefers_saved_path(tmp_path):
    ffmpeg_path = tmp_path / "ffmpeg.exe"
    ffmpeg_path.write_text("", encoding="utf-8")

    result = resolve_ffmpeg_path(saved_path=str(ffmpeg_path), operating_system="Windows")

    assert result == str(ffmpeg_path.resolve())


def test_resolve_ffmpeg_path_uses_search_dirs(tmp_path):
    search_dir = tmp_path / "bin"
    search_dir.mkdir()
    ffmpeg_path = search_dir / "ffmpeg.exe"
    ffmpeg_path.write_text("", encoding="utf-8")

    result = resolve_ffmpeg_path(search_dirs=[search_dir], operating_system="Windows")

    assert result == str(ffmpeg_path.resolve())


def test_resolve_ffmpeg_path_uses_system_lookup():
    result = resolve_ffmpeg_path(
        operating_system="Windows",
        path_lookup=lambda _: r"C:\Tools\ffmpeg.exe",
    )

    assert result == str(Path(r"C:\Tools\ffmpeg.exe").resolve())


def test_resolve_ffmpeg_path_uses_winget_fallback(tmp_path):
    package_bin = tmp_path / "Gyan.FFmpeg" / "ffmpeg-8.1" / "bin"
    package_bin.mkdir(parents=True)
    ffmpeg_path = package_bin / "ffmpeg.exe"
    ffmpeg_path.write_text("", encoding="utf-8")

    result = resolve_ffmpeg_path(
        operating_system="Windows",
        path_lookup=lambda _: None,
        winget_package_root=tmp_path,
    )

    assert result == str(ffmpeg_path.resolve())


def test_locate_ffmpeg_reads_version(tmp_path):
    ffmpeg_path = tmp_path / "ffmpeg.exe"
    ffmpeg_path.write_text("", encoding="utf-8")

    info = locate_ffmpeg(
        saved_path=str(ffmpeg_path),
        operating_system="Windows",
        runner=lambda cmd: subprocess.CompletedProcess(
            cmd,
            0,
            stdout="ffmpeg version 7.0 Copyright (c) 2000-2024 the FFmpeg developers",
            stderr="",
        ),
    )

    assert info.found is True
    assert info.path == str(ffmpeg_path.resolve())
    assert info.version == "7.0"
