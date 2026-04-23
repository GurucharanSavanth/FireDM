"""End-to-end playlist flow regression tests.

Patches `get_media_info` so the tests never hit the network. Verifies:
    * partial / id-only entries are normalized to real URLs
    * bad entries are skipped without dropping the whole playlist
    * playlist metadata (title, playlist_url) propagates to every Video
    * per-entry processing succeeds and populates streams
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from firedm import config


@pytest.fixture
def tmp_download_folder(tmp_path):
    previous = config.download_folder
    config.download_folder = str(tmp_path)
    yield tmp_path
    config.download_folder = previous


def _entry_full_url():
    return {"id": "abc1234567X", "title": "entry A", "ie_key": "Youtube",
            "webpage_url": "https://www.youtube.com/watch?v=abc1234567X",
            "url": "https://www.youtube.com/watch?v=abc1234567X"}


def _entry_id_only():
    """Shape seen in the wild: process=False yt_dlp playlist entries."""
    return {"id": "def2345678Y", "title": "entry B", "ie_key": "Youtube"}


def _entry_broken():
    return {"title": "entry C (no id, no url)"}


def _playlist_info():
    return {
        "_type": "playlist", "title": "Sample",
        "webpage_url": "https://www.youtube.com/playlist?list=PL_X",
        "entries": [_entry_full_url(), _entry_id_only(), _entry_broken()],
    }


def _per_entry_info():
    return {
        "id": "xxx", "title": "processed",
        "webpage_url": "https://www.youtube.com/watch?v=xxx",
        "subtitles": {}, "automatic_captions": {}, "http_headers": {},
        "formats": [
            {"format_id": "22", "url": "https://example.invalid/v.mp4",
             "ext": "mp4", "width": 1280, "height": 720,
             "vcodec": "avc1", "acodec": "mp4a", "abr": 96.0, "tbr": 1400.0,
             "filesize": 1024, "protocol": "https"},
        ],
    }


def test_playlist_handles_mixed_entries(tmp_download_folder):
    from firedm.controller import create_video_playlist

    pl_info = _playlist_info()
    per_entry = _per_entry_info()

    def fake_get_media_info(url=None, info=None, ytdloptions=None, interrupt=False):
        if url == pl_info["webpage_url"]:
            return pl_info
        return per_entry

    with (
        patch("firedm.controller.get_media_info", side_effect=fake_get_media_info),
        patch("firedm.video.get_media_info", side_effect=fake_get_media_info),
    ):
        pl = create_video_playlist(pl_info["webpage_url"])

    assert len(pl) == 2, "broken entry should be skipped, others kept"

    assert pl[0].url == "https://www.youtube.com/watch?v=abc1234567X"
    # id-only entry should be normalized to a full URL
    assert pl[1].url == "https://www.youtube.com/watch?v=def2345678Y"


def test_playlist_propagates_title_and_url_to_every_entry(tmp_download_folder):
    from firedm.controller import create_video_playlist

    pl_info = _playlist_info()
    per_entry = _per_entry_info()

    def fake_get_media_info(url=None, info=None, ytdloptions=None, interrupt=False):
        if url == pl_info["webpage_url"]:
            return pl_info
        return per_entry

    with (
        patch("firedm.controller.get_media_info", side_effect=fake_get_media_info),
        patch("firedm.video.get_media_info", side_effect=fake_get_media_info),
    ):
        pl = create_video_playlist(pl_info["webpage_url"])

    for v in pl:
        assert v.playlist_title == "Sample"
        assert v.playlist_url == pl_info["webpage_url"]


def test_playlist_per_item_processing_populates_streams(tmp_download_folder):
    from firedm import video
    from firedm.controller import create_video_playlist

    pl_info = _playlist_info()
    per_entry = _per_entry_info()

    def fake_get_media_info(url=None, info=None, ytdloptions=None, interrupt=False):
        if url == pl_info["webpage_url"]:
            return pl_info
        return per_entry

    with (
        patch("firedm.controller.get_media_info", side_effect=fake_get_media_info),
        patch("firedm.video.get_media_info", side_effect=fake_get_media_info),
    ):
        pl = create_video_playlist(pl_info["webpage_url"])
        for v in pl:
            video.process_video(v)

    assert all(v.all_streams for v in pl)
    assert all(v.processed for v in pl)


def test_playlist_single_bad_entry_does_not_abort_list(tmp_download_folder):
    """Explicit regression: if building one Video raises, the rest must stay."""
    from firedm import controller

    pl_info = _playlist_info()
    per_entry = _per_entry_info()

    call_count = {"n": 0}

    class FlakyObservableVideo(controller.ObservableVideo):
        def __init__(self, url, vid_info=None, observer_callbacks=None):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise RuntimeError("simulated construction failure")
            super().__init__(url, vid_info=vid_info, observer_callbacks=observer_callbacks)

    def fake_get_media_info(url=None, info=None, ytdloptions=None, interrupt=False):
        if url == pl_info["webpage_url"]:
            return pl_info
        return per_entry

    with (
        patch.object(controller, "ObservableVideo", FlakyObservableVideo),
        patch("firedm.controller.get_media_info", side_effect=fake_get_media_info),
        patch("firedm.video.get_media_info", side_effect=fake_get_media_info),
    ):
        pl = controller.create_video_playlist(pl_info["webpage_url"])

    # first entry raised → skipped; second entry (id-only) succeeded;
    # third entry (broken) filtered by normalizer.
    assert len(pl) == 1
    assert pl[0].url == "https://www.youtube.com/watch?v=def2345678Y"
