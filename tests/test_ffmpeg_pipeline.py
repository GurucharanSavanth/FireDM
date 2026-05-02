"""Tests for `firedm.ffmpeg_commands` + ffmpeg discovery service."""

from __future__ import annotations

import importlib
import json

from firedm.ffmpeg_commands import (
    build_audio_convert_command,
    build_hls_process_command,
    build_merge_command,
    dash_audio_extension_for,
)
from firedm.ffmpeg_service import locate_ffmpeg


def test_dash_extension_rules():
    assert dash_audio_extension_for("mp4") == "m4a"
    assert dash_audio_extension_for("webm") == "webm"
    assert dash_audio_extension_for("mkv") == "mkv"  # passthrough


def test_merge_command_has_stream_copy_fast_path():
    pair = build_merge_command(
        video_file="v.mp4", audio_file="a.m4a",
        output_file="out.mp4", ffmpeg_path="C:/ffmpeg/ffmpeg.exe",
    )
    assert "-c copy" in pair.fast, "fast merge must use stream copy"
    assert "-c copy" not in pair.slow
    assert '"out.mp4"' in pair.fast
    assert '"v.mp4"' in pair.fast and '"a.m4a"' in pair.fast
    assert "-y" in pair.fast  # overwrite without prompt


def test_merge_command_quotes_paths_with_spaces():
    pair = build_merge_command(
        video_file="C:/Program Files/videos/v.mp4",
        audio_file="C:/Program Files/audio/a.m4a",
        output_file="C:/Program Files/out/final.mp4",
        ffmpeg_path="C:/Program Files/ffmpeg/ffmpeg.exe",
    )
    # each path quoted — argv stays intact after shlex.split
    import shlex
    fast_argv = shlex.split(pair.fast)
    assert any("Program Files" in part and part.endswith("v.mp4") for part in fast_argv)
    assert any("Program Files" in part and part.endswith("a.m4a") for part in fast_argv)


def test_hls_process_command_whitelists_protocols():
    pair = build_hls_process_command(
        m3u8_path="local.m3u8", output_file="out.mp4",
        ffmpeg_path="ffmpeg",
    )
    assert "-protocol_whitelist" in pair.fast
    assert "file,http,https,tcp,tls,crypto" in pair.fast
    assert "-allowed_extensions ALL" in pair.fast
    assert 'file:out.mp4' in pair.fast


def test_audio_convert_command_acodec_copy_fast_path():
    pair = build_audio_convert_command(
        input_file="x.m4a", output_file="x.mp3", ffmpeg_path="ffmpeg",
    )
    assert "-acodec copy" in pair.fast
    assert "-acodec copy" not in pair.slow


def test_ffmpeg_service_reports_not_found_when_missing(tmp_path):
    """When every search path is empty, service returns a `not found`
    result rather than raising or falling back to a hardcoded path.

    `path_lookup` is stubbed to None so the test is hermetic on hosts that
    happen to have ffmpeg on PATH (e.g. dev machines with a Winget install).
    """
    info = locate_ffmpeg(
        saved_path="",
        search_dirs=(str(tmp_path),),
        operating_system="Windows",
        path_lookup=lambda _name: None,
        include_winget=False,
    )
    assert info.found is False
    assert info.path == ""
    assert info.usable is False
    assert info.failure == "not found"


def test_verify_ffmpeg_pipeline_json_includes_ffmpeg_and_ffprobe_health(monkeypatch, tmp_path):
    verify_script = importlib.import_module("scripts.verify_ffmpeg_pipeline")
    monkeypatch.setattr(verify_script, "ARTIFACTS", tmp_path)
    monkeypatch.setattr(
        verify_script,
        "collect_media_tool_health",
        lambda **_: {
            "ffmpeg": {
                "found": True,
                "path": "C:/Tools/ffmpeg.exe",
                "version": "8.1",
                "usable": True,
                "failure": "",
                "returncode": 0,
            },
            "ffprobe": {
                "found": False,
                "path": "",
                "version": "",
                "usable": False,
                "failure": "not found",
                "returncode": None,
            },
        },
    )

    assert verify_script.main() == 0
    data = json.loads((tmp_path / "ffmpeg_pipeline_result.json").read_text(encoding="utf-8"))
    assert data["ffmpeg"]["usable"] is True
    assert data["ffprobe"]["usable"] is False
    assert data["ffprobe"]["failure"] == "not found"


def test_verify_ffmpeg_pipeline_exit_code_depends_on_ffmpeg_only(monkeypatch, tmp_path):
    verify_script = importlib.import_module("scripts.verify_ffmpeg_pipeline")
    monkeypatch.setattr(verify_script, "ARTIFACTS", tmp_path)
    monkeypatch.setattr(
        verify_script,
        "collect_media_tool_health",
        lambda **_: {
            "ffmpeg": {
                "found": True,
                "path": "C:/Tools/ffmpeg.exe",
                "version": "8.1",
                "usable": True,
                "failure": "",
                "returncode": 0,
            },
            "ffprobe": {
                "found": False,
                "path": "",
                "version": "",
                "usable": False,
                "failure": "not found",
                "returncode": None,
            },
        },
    )

    assert verify_script.main() == 0
