"""Regression tests for the single-video URL path.

These tests never touch the network. They feed `Video` a synthetic
`vid_info` dict that mirrors what yt_dlp returns — including the
`abr=None` format that previously crashed `Stream.__init__` and caused
the user-reported P0 defect.
"""

from __future__ import annotations

import os

import pytest

from firedm import config
from firedm.video import Video, _coerce_number
from firedm.downloaditem import Segment  # noqa: F401 — keep package import cheap


def _mp4_720p():
    return {
        "format_id": "22",
        "url": "https://example.invalid/video_720p.mp4",
        "ext": "mp4",
        "width": 1280,
        "height": 720,
        "fps": 30,
        "vcodec": "avc1.64001F",
        "acodec": "mp4a.40.2",
        "abr": 96.0,
        "tbr": 1400.0,
        "filesize": 12345678,
        "protocol": "https",
        "http_headers": {"User-Agent": "test"},
    }


def _legacy_mp4_360p_with_none_bitrate():
    """This is the shape that triggered the P0 bug: abr=None, tbr=None."""
    return {
        "format_id": "18",
        "url": "https://example.invalid/video_360p.mp4",
        "ext": "mp4",
        "width": 640,
        "height": 360,
        "fps": 30,
        "vcodec": "avc1.42001E",
        "acodec": "mp4a.40.2",
        "abr": None,          # <-- the killer
        "tbr": None,          # <-- secondary
        "filesize": 4567890,
        "protocol": "https",
    }


def _audio_only_m4a():
    return {
        "format_id": "140",
        "url": "https://example.invalid/audio.m4a",
        "ext": "m4a",
        "vcodec": "none",
        "acodec": "mp4a.40.2",
        "abr": 128.0,
        "filesize": 345678,
        "protocol": "https",
    }


def _dash_video_1080p():
    return {
        "format_id": "137",
        "url": "https://example.invalid/video_1080p.mp4",
        "ext": "mp4",
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "vcodec": "avc1.640028",
        "acodec": "none",
        "abr": 0,
        "tbr": 4500.0,
        "filesize": 56789012,
        "protocol": "https",
    }


def _fake_vid_info():
    return {
        "id": "jNQXAC9IVRw",
        "title": "Me at the zoo",
        "webpage_url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        "duration": 18,
        "thumbnail": "",
        "formats": [
            _audio_only_m4a(),
            _legacy_mp4_360p_with_none_bitrate(),
            _mp4_720p(),
            _dash_video_1080p(),
        ],
        "http_headers": {"User-Agent": "test"},
        "subtitles": {},
        "automatic_captions": {},
    }


def test_coerce_number_handles_none():
    assert _coerce_number(None, 0) == 0
    assert _coerce_number(None, 0.0) == 0.0
    assert _coerce_number("42", 0) == 42
    assert _coerce_number("garbage", 0) == 0
    assert _coerce_number(3.14, 0) == 3.14


def test_single_video_builds_streams_even_with_none_bitrate(tmp_path):
    """P0 regression: `abr=None` must not crash `Stream.__init__`, must not
    cause the menu to drop the format, and must not abort the whole
    `_process_streams` call."""
    config.download_folder = str(tmp_path)
    vid_info = _fake_vid_info()

    video = Video(url="https://www.youtube.com/watch?v=jNQXAC9IVRw", vid_info=vid_info)

    # every format supplied should produce a stream — including format_id "18"
    produced_ids = {s.format_id for s in video.all_streams}
    for fmt in vid_info["formats"]:
        assert fmt["format_id"] in produced_ids, f"lost format {fmt['format_id']}"


def test_single_video_selects_default_stream(tmp_path):
    config.download_folder = str(tmp_path)
    video = Video(url="https://www.youtube.com/watch?v=jNQXAC9IVRw", vid_info=_fake_vid_info())

    sel = video.selected_stream
    assert sel is not None
    assert sel.url is not None
    # effective url mirrored onto the download item
    assert video.eff_url == sel.url


def test_single_video_stream_menu_is_populated(tmp_path):
    config.download_folder = str(tmp_path)
    video = Video(url="https://www.youtube.com/watch?v=jNQXAC9IVRw", vid_info=_fake_vid_info())

    assert video.stream_menu, "stream menu must not be empty"
    # sanity: format id 18 should appear in the menu map even though yt_dlp
    # reported a None bitrate for it.
    seen = {getattr(s, "format_id", None) for s in video.stream_menu_map if s is not None}
    assert "18" in seen


def test_single_video_title_and_name_populated(tmp_path):
    config.download_folder = str(tmp_path)
    video = Video(url="https://www.youtube.com/watch?v=jNQXAC9IVRw", vid_info=_fake_vid_info())

    assert video.title == "Me at the zoo"
    assert video.name.startswith("Me at the zoo")
    assert video.name.endswith(video.extension)


def test_single_video_selecting_dash_video_triggers_audio_pairing(tmp_path):
    config.download_folder = str(tmp_path)
    video = Video(url="https://www.youtube.com/watch?v=jNQXAC9IVRw", vid_info=_fake_vid_info())

    # find the 1080p DASH video stream by format_id
    dash = next(s for s in video.all_streams if s.format_id == "137")
    video.selected_stream = dash

    assert video.audio_stream is not None, "DASH video must pair with an audio stream"
    assert video.audio_url is not None


@pytest.mark.parametrize(
    "field", ["width", "height", "abr", "tbr"]
)
def test_stream_init_tolerates_none_in_numeric_fields(tmp_path, field):
    config.download_folder = str(tmp_path)
    info = _fake_vid_info()
    # poison one more field per run
    info["formats"][0][field] = None
    # must not raise
    Video(url="https://example.invalid/x", vid_info=info)
