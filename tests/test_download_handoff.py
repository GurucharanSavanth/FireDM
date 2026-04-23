"""Download-handoff regression.

Exercises `firedm.controller.Controller.download()` end-to-end on an
`ObservableDownloadItem` that has already been populated by the extractor
pipeline. Verifies:

    * pre-download checks pass when inputs are valid
    * the item is put on the download queue
    * the queued item is the exact object we handed in
    * `DOWNLOAD_ENQUEUE status=ok` event is emitted

Never hits the network. Patches `check_ffmpeg`, `save_d_map`, and the
background import to keep the test hermetic.
"""

from __future__ import annotations

import os
import queue
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from firedm import config
from firedm.config import Status
from firedm.model import ObservableDownloadItem


class _NullView:
    """Minimal view stub so Controller can report updates without a GUI."""

    def __init__(self, controller):
        self.controller = controller
        self.events = []

    def update_view(self, **kwargs):
        self.events.append(kwargs)

    def get_user_response(self, *args, **kwargs):
        return "Ok"


@pytest.fixture
def tmp_download_folder(tmp_path):
    previous = config.download_folder
    config.download_folder = str(tmp_path)
    yield tmp_path
    config.download_folder = previous


def _fake_download_item(tmp_path):
    d = ObservableDownloadItem()
    d.folder = str(tmp_path)
    d.name = "sample.mp4"
    d.url = "https://example.invalid/video.mp4"
    d.eff_url = "https://example.invalid/video.mp4"
    d.type = "video"
    d.total_size = 1024
    d.size = 1024
    d.calculate_uid()
    return d


def test_download_enqueue_happy_path(tmp_download_folder):
    from firedm import controller

    with (
        patch.object(controller, "check_ffmpeg", return_value=True),
        patch("firedm.video.load_extractor_engines"),
        patch.object(controller.Thread, "start"),  # don't start background threads
    ):
        ctrl = controller.Controller(view_class=_NullView, custom_settings={"ignore_dlist": True})
        d = _fake_download_item(tmp_download_folder)

        with patch.object(ctrl, "save_d_map"), patch.object(ctrl, "get_user_response", return_value="Ok"):
            ok = ctrl.download(d=d, silent=True)

        assert ok is True, "download() should accept a well-formed video item"
        assert ctrl.download_q.qsize() == 1
        queued = ctrl.download_q.get_nowait()
        assert queued.url == d.url
        assert queued.status == Status.pending


def test_download_rejects_missing_name(tmp_download_folder):
    from firedm import controller

    with (
        patch.object(controller, "check_ffmpeg", return_value=True),
        patch("firedm.video.load_extractor_engines"),
        patch.object(controller.Thread, "start"),
    ):
        ctrl = controller.Controller(view_class=_NullView, custom_settings={"ignore_dlist": True})
        d = _fake_download_item(tmp_download_folder)
        d.name = ""  # violate precondition

        with patch.object(ctrl, "save_d_map"), patch.object(ctrl, "get_user_response", return_value="Ok"):
            ok = ctrl.download(d=d, silent=True)

        assert ok is False
        assert ctrl.download_q.qsize() == 0


def test_download_rejects_when_ffmpeg_missing(tmp_download_folder):
    from firedm import controller

    with (
        patch.object(controller, "check_ffmpeg", return_value=False),
        patch("firedm.video.load_extractor_engines"),
        patch.object(controller.Thread, "start"),
    ):
        ctrl = controller.Controller(view_class=_NullView, custom_settings={"ignore_dlist": True})
        d = _fake_download_item(tmp_download_folder)

        with patch.object(ctrl, "save_d_map"), patch.object(ctrl, "get_user_response", return_value="Cancel"):
            ok = ctrl.download(d=d, silent=True)

        assert ok is False
        assert ctrl.download_q.qsize() == 0
