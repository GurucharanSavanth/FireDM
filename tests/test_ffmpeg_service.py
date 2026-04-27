import subprocess
from pathlib import Path

from firedm import config, controller
from firedm.ffmpeg_service import (
    collect_media_tool_health,
    locate_ffmpeg,
    locate_ffprobe,
    parse_ffmpeg_version,
    parse_ffprobe_version,
    resolve_ffmpeg_path,
    resolve_ffprobe_path,
)


def test_parse_ffmpeg_version():
    output = "ffmpeg version 6.1 Copyright (c) 2000-2024 the FFmpeg developers"

    assert parse_ffmpeg_version(output) == "6.1"


def test_parse_ffprobe_version():
    output = "ffprobe version 6.1 Copyright (c) 2007-2024 the FFmpeg developers"

    assert parse_ffprobe_version(output) == "6.1"


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
    result = resolve_ffmpeg_path(operating_system="Windows", path_lookup=lambda _: r"C:\Tools\ffmpeg.exe")

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


def test_missing_ffmpeg_returns_not_found(tmp_path):
    info = locate_ffmpeg(
        search_dirs=[tmp_path],
        operating_system="Windows",
        path_lookup=lambda _: None,
        include_winget=False,
    )

    assert info.found is False
    assert info.usable is False
    assert info.failure == "not found"
    assert info.returncode is None


def test_missing_ffprobe_returns_not_found(tmp_path):
    info = locate_ffprobe(
        search_dirs=[tmp_path],
        operating_system="Windows",
        path_lookup=lambda _: None,
        include_winget=False,
    )

    assert info.found is False
    assert info.usable is False
    assert info.failure == "not found"


def test_locate_ffmpeg_reads_version_and_marks_usable(tmp_path):
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
    assert info.usable is True
    assert info.path == str(ffmpeg_path.resolve())
    assert info.version == "7.0"
    assert info.returncode == 0


def test_locate_ffprobe_reads_version_from_ffmpeg_sibling(tmp_path):
    ffmpeg_path = tmp_path / "ffmpeg.exe"
    ffprobe_path = tmp_path / "ffprobe.exe"
    ffmpeg_path.write_text("", encoding="utf-8")
    ffprobe_path.write_text("", encoding="utf-8")

    info = locate_ffprobe(
        ffmpeg_path=str(ffmpeg_path),
        operating_system="Windows",
        path_lookup=lambda _: None,
        include_winget=False,
        runner=lambda cmd: subprocess.CompletedProcess(
            cmd,
            0,
            stdout="ffprobe version 7.0 Copyright (c) 2007-2024 the FFmpeg developers",
            stderr="",
        ),
    )

    assert info.found is True
    assert info.usable is True
    assert info.path == str(ffprobe_path.resolve())
    assert info.version == "7.0"


def test_bad_custom_ffmpeg_path_is_rejected(tmp_path):
    fallback = tmp_path / "ffmpeg.exe"
    fallback.write_text("", encoding="utf-8")
    calls = []

    info = locate_ffmpeg(
        saved_path=str(tmp_path / "missing.exe"),
        search_dirs=[tmp_path],
        operating_system="Windows",
        runner=lambda cmd: calls.append(cmd),
    )

    assert info.found is False
    assert info.usable is False
    assert info.failure == "custom path not found"
    assert calls == []


def test_path_with_spaces_is_passed_as_one_argv_element(tmp_path):
    tool_dir = tmp_path / "tools with spaces"
    tool_dir.mkdir()
    ffmpeg_path = tool_dir / "ffmpeg.exe"
    ffmpeg_path.write_text("", encoding="utf-8")
    calls = []

    info = locate_ffmpeg(
        saved_path=str(ffmpeg_path),
        operating_system="Windows",
        runner=lambda cmd: (
            calls.append(cmd)
            or subprocess.CompletedProcess(
                cmd,
                0,
                stdout="ffmpeg version 8.0 Copyright (c) 2000-2024 the FFmpeg developers",
                stderr="",
            )
        ),
    )

    assert info.usable is True
    assert calls == [[str(ffmpeg_path.resolve()), "-version"]]


def test_dash_prefixed_filename_is_passed_as_argv_path(tmp_path):
    ffmpeg_path = tmp_path / "-ffmpeg.exe"
    ffmpeg_path.write_text("", encoding="utf-8")
    calls = []

    info = locate_ffmpeg(
        saved_path=str(ffmpeg_path),
        operating_system="Windows",
        runner=lambda cmd: (
            calls.append(cmd)
            or subprocess.CompletedProcess(
                cmd,
                0,
                stdout="ffmpeg version 8.0 Copyright (c) 2000-2024 the FFmpeg developers",
                stderr="",
            )
        ),
    )

    assert info.usable is True
    assert calls == [[str(ffmpeg_path.resolve()), "-version"]]


def test_windows_exe_discovery_from_search_dirs(tmp_path):
    search_dir = tmp_path / "bin"
    search_dir.mkdir()
    ffmpeg_path = search_dir / "ffmpeg.exe"
    ffmpeg_path.write_text("", encoding="utf-8")

    result = resolve_ffmpeg_path(search_dirs=[search_dir], operating_system="Windows")

    assert result == str(ffmpeg_path.resolve())


def test_linux_no_extension_discovery_from_search_dirs(tmp_path):
    search_dir = tmp_path / "bin"
    search_dir.mkdir()
    ffmpeg_path = search_dir / "ffmpeg"
    ffmpeg_path.write_text("", encoding="utf-8")

    result = resolve_ffmpeg_path(search_dirs=[search_dir], operating_system="Linux")

    assert result == str(ffmpeg_path.resolve())


def test_resolve_ffprobe_uses_winget_fallback(tmp_path):
    package_bin = tmp_path / "Gyan.FFmpeg" / "ffmpeg-8.1" / "bin"
    package_bin.mkdir(parents=True)
    ffprobe_path = package_bin / "ffprobe.exe"
    ffprobe_path.write_text("", encoding="utf-8")

    result = resolve_ffprobe_path(
        operating_system="Windows",
        path_lookup=lambda _: None,
        winget_package_root=tmp_path,
    )

    assert result == str(ffprobe_path.resolve())


def test_broken_ffmpeg_returns_failure_without_crash(tmp_path):
    ffmpeg_path = tmp_path / "ffmpeg.exe"
    ffmpeg_path.write_text("", encoding="utf-8")

    info = locate_ffmpeg(
        saved_path=str(ffmpeg_path),
        operating_system="Windows",
        runner=lambda cmd: subprocess.CompletedProcess(
            cmd,
            2,
            stdout="",
            stderr="broken codec table",
        ),
    )

    assert info.found is True
    assert info.usable is False
    assert info.returncode == 2
    assert info.failure == "broken codec table"


def test_default_subprocess_probe_uses_argv_and_no_shell(monkeypatch, tmp_path):
    ffmpeg_path = tmp_path / "ffmpeg.exe"
    ffmpeg_path.write_text("", encoding="utf-8")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(
            cmd,
            0,
            stdout="ffmpeg version 8.1 Copyright (c) 2000-2024 the FFmpeg developers",
            stderr="",
        )

    monkeypatch.setattr("firedm.ffmpeg_service.subprocess.run", fake_run)

    info = locate_ffmpeg(saved_path=str(ffmpeg_path), operating_system="Windows")

    assert info.usable is True
    assert calls == [
        (
            [str(ffmpeg_path.resolve()), "-version"],
            {"capture_output": True, "text": True, "check": False},
        )
    ]


def test_collect_media_tool_health_reports_both_tools(tmp_path):
    ffmpeg_path = tmp_path / "ffmpeg.exe"
    ffprobe_path = tmp_path / "ffprobe.exe"
    ffmpeg_path.write_text("", encoding="utf-8")
    ffprobe_path.write_text("", encoding="utf-8")

    def runner(cmd):
        if Path(cmd[0]).name == "ffprobe.exe":
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout="ffprobe version 8.1 Copyright (c) 2007-2024 the FFmpeg developers",
                stderr="",
            )
        return subprocess.CompletedProcess(
            cmd,
            0,
            stdout="ffmpeg version 8.1 Copyright (c) 2000-2024 the FFmpeg developers",
            stderr="",
        )

    health = collect_media_tool_health(
        saved_ffmpeg_path=str(ffmpeg_path),
        operating_system="Windows",
        path_lookup=lambda _: None,
        include_winget=False,
        runner=runner,
    )

    assert health["ffmpeg"]["usable"] is True
    assert health["ffprobe"]["usable"] is True
    assert health["ffprobe"]["path"] == str(ffprobe_path.resolve())


def test_controller_opens_ffmpeg_help_url(monkeypatch):
    opened = []

    monkeypatch.setattr(controller, "open_webpage", opened.append)

    controller.Controller.open_ffmpeg_help(object())

    assert opened == [config.FFMPEG_DOWNLOAD_HELP_URL]
