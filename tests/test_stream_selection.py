"""Stream-selection + DASH pairing regression tests."""

from __future__ import annotations

import pytest

from firedm import config
from firedm.video import Stream, Video


def _fmt(**over):
    base = {
        "format_id": "0", "url": "https://example.invalid/a",
        "ext": "mp4", "width": 640, "height": 360,
        "vcodec": "avc1", "acodec": "mp4a", "abr": 96.0, "tbr": 1000.0,
        "filesize": 1024, "protocol": "https",
    }
    base.update(over)
    return base


def _vid_info(*formats):
    return {
        "id": "x", "title": "t",
        "webpage_url": "https://example.invalid/x",
        "duration": 10, "thumbnail": "", "subtitles": {}, "automatic_captions": {},
        "http_headers": {}, "formats": list(formats),
    }


def test_audio_only_stream_has_audio_mediatype():
    s = Stream(_fmt(format_id="140", vcodec="none", acodec="mp4a", ext="m4a"))
    assert s.mediatype == "audio"


def test_dash_video_selects_m4a_audio_for_mp4(tmp_path):
    config.download_folder = str(tmp_path)
    info = _vid_info(
        _fmt(format_id="137", vcodec="avc1", acodec="none", ext="mp4",
             width=1920, height=1080, tbr=4500.0, abr=0),
        _fmt(format_id="140", vcodec="none", acodec="mp4a", ext="m4a",
             width=0, height=0, abr=128.0, tbr=128.0),
        _fmt(format_id="251", vcodec="none", acodec="opus", ext="webm",
             width=0, height=0, abr=160.0, tbr=160.0),
    )
    v = Video(url=info["webpage_url"], vid_info=info)
    # select the 1080p DASH video explicitly
    v.selected_stream = next(s for s in v.all_streams if s.format_id == "137")
    assert v.audio_stream is not None
    assert v.audio_stream.extension == "m4a", "mp4 video must pair with m4a audio"


def test_dash_video_selects_webm_audio_for_webm(tmp_path):
    config.download_folder = str(tmp_path)
    info = _vid_info(
        _fmt(format_id="248", vcodec="vp9", acodec="none", ext="webm",
             width=1920, height=1080, tbr=2500.0, abr=0),
        _fmt(format_id="140", vcodec="none", acodec="mp4a", ext="m4a",
             width=0, height=0, abr=128.0, tbr=128.0),
        _fmt(format_id="251", vcodec="none", acodec="opus", ext="webm",
             width=0, height=0, abr=160.0, tbr=160.0),
    )
    v = Video(url=info["webpage_url"], vid_info=info)
    v.selected_stream = next(s for s in v.all_streams if s.format_id == "248")
    assert v.audio_stream is not None
    assert v.audio_stream.extension == "webm", "webm video must pair with webm audio"


def test_combined_mp4_stream_is_normal_mediatype(tmp_path):
    s = Stream(_fmt(format_id="22", vcodec="avc1", acodec="mp4a", ext="mp4"))
    assert s.mediatype == "normal"


def test_dash_video_resolution_reported(tmp_path):
    s = Stream(_fmt(format_id="137", vcodec="avc1", acodec="none",
                    width=1920, height=1080))
    assert s.resolution == "1920x1080"
    assert s.quality == 1080


def test_stream_quality_tolerates_none_height():
    """height=None must not raise; it is coerced to 0 and then resolved to
    the nearest standard quality bucket (never raises TypeError)."""
    s = Stream(_fmt(format_id="0", vcodec="avc1", acodec="none", height=None, width=None))
    # Any int from config.standard_video_qualities is acceptable — the
    # guarantee is "doesn't crash" not "returns 0 exactly".
    assert isinstance(s.quality, int)
