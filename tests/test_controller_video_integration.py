"""Integration tests across controller ↔ video ↔ playlist_builder seams.

Uses the new `playlist_builder.build_playlist_from_info` directly so these
tests stay independent of the controller's heavy Queue/Thread machinery.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from firedm import config
from firedm.playlist_builder import build_playlist_from_info


@pytest.fixture
def tmp_download_folder(tmp_path):
    previous = config.download_folder
    config.download_folder = str(tmp_path)
    yield tmp_path
    config.download_folder = previous


def _single_info():
    return {
        "id": "x", "title": "t",
        "webpage_url": "https://example.invalid/x",
        "duration": 10, "thumbnail": "", "subtitles": {}, "automatic_captions": {},
        "http_headers": {},
        "formats": [
            {"format_id": "22", "url": "https://example.invalid/v.mp4",
             "ext": "mp4", "width": 1280, "height": 720,
             "vcodec": "avc1", "acodec": "mp4a", "abr": 96.0, "tbr": 1400.0,
             "filesize": 1024, "protocol": "https"},
        ],
    }


def _pl_info():
    return {
        "_type": "playlist", "title": "Sample",
        "webpage_url": "https://example.invalid/list",
        "entries": [
            {"id": "abc1234567X", "title": "A", "ie_key": "Youtube",
             "webpage_url": "https://www.youtube.com/watch?v=abc1234567X"},
            {"id": "def2345678Y", "title": "B", "ie_key": "Youtube"},
        ],
    }


def test_builder_returns_single_video(tmp_download_folder):
    from firedm.model import ObservableVideo

    r = build_playlist_from_info(
        "https://example.invalid/x",
        _single_info(),
        observable_factory=ObservableVideo,
    )
    assert r.kind == "single"
    assert len(r.videos) == 1
    assert r.videos[0].url == "https://example.invalid/x"
    assert r.videos[0].processed is True


def test_builder_returns_playlist_entries(tmp_download_folder):
    from firedm.model import ObservableVideo

    r = build_playlist_from_info(
        "https://example.invalid/list",
        _pl_info(),
        observable_factory=ObservableVideo,
    )
    assert r.kind == "playlist"
    assert len(r.videos) == 2
    # normalization propagated the full URL onto the id-only entry
    assert r.videos[1].url == "https://www.youtube.com/watch?v=def2345678Y"
    assert r.videos[0].playlist_title == "Sample"


def test_builder_records_skipped_bad_entries(tmp_download_folder):
    from firedm.model import ObservableVideo

    info = _pl_info()
    info["entries"].append({"not_a_dict_field": True})  # missing id/url
    info["entries"].append("not a dict at all")

    r = build_playlist_from_info(
        info["webpage_url"], info, observable_factory=ObservableVideo,
    )
    assert len(r.videos) == 2
    assert r.skipped == 2


def test_controller_create_video_playlist_delegates_to_builder(tmp_download_folder):
    from firedm.controller import create_video_playlist

    def fake_get_media_info(url=None, info=None, ytdloptions=None, interrupt=False):
        # called twice: once for initial fetch, once to populate formats
        return info or _single_info() if info is not None else _single_info()

    def fake_thumbnail(self):
        self.thumbnail = b""  # pretend we pulled it

    with (
        patch("firedm.controller.get_media_info", side_effect=fake_get_media_info),
        patch("firedm.video.get_media_info", side_effect=fake_get_media_info),
        patch("firedm.video.Video.get_thumbnail", fake_thumbnail),
    ):
        pl = create_video_playlist("https://example.invalid/x")

    assert len(pl) == 1
    assert pl[0].url == "https://example.invalid/x"
    assert pl[0].processed is True
