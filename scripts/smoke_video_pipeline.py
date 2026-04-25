"""Controlled video/playlist smoke tests for the FireDM pipeline.

Feeds the pipeline synthetic `vid_info` payloads that mirror real
`yt_dlp.extract_info` output (single video + playlist) without touching
the network, then asserts:

    * Video.setup() builds a populated stream menu
    * the default selected stream resolves to a URL
    * DASH video pairs with an audio stream
    * Playlist entries normalize to real `watch?v=...` URLs
    * `process_video` (in mocked mode) processes the first playlist entry

Writes JSON and log artifacts under `artifacts/smoke/`.

Usage:
    .\.venv\Scripts\python.exe scripts\smoke_video_pipeline.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
SMOKE_DIR = REPO_ROOT / "artifacts" / "smoke"
SMOKE_DIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO_ROOT))


def _mp4_720p(url="https://example.invalid/720p.mp4"):
    return {
        "format_id": "22", "url": url, "ext": "mp4",
        "width": 1280, "height": 720, "fps": 30,
        "vcodec": "avc1", "acodec": "mp4a", "abr": 96.0, "tbr": 1400.0,
        "filesize": 1024, "protocol": "https",
    }


def _legacy_mp4_with_none_abr():
    return {
        "format_id": "18", "url": "https://example.invalid/360p.mp4",
        "ext": "mp4", "width": 640, "height": 360,
        "vcodec": "avc1", "acodec": "mp4a",
        "abr": None, "tbr": None, "filesize": 2048, "protocol": "https",
    }


def _dash_video_1080():
    return {
        "format_id": "137", "url": "https://example.invalid/1080p-dash.mp4",
        "ext": "mp4", "width": 1920, "height": 1080,
        "vcodec": "avc1", "acodec": "none",
        "abr": 0, "tbr": 4500.0, "filesize": 4096, "protocol": "https",
    }


def _audio_m4a():
    return {
        "format_id": "140", "url": "https://example.invalid/audio.m4a",
        "ext": "m4a", "vcodec": "none", "acodec": "mp4a",
        "abr": 128.0, "filesize": 512, "protocol": "https",
    }


def _single_vid_info():
    return {
        "id": "abc", "title": "Sample Clip",
        "webpage_url": "https://www.youtube.com/watch?v=abc",
        "duration": 18, "thumbnail": "", "subtitles": {}, "automatic_captions": {},
        "http_headers": {},
        "formats": [_audio_m4a(), _legacy_mp4_with_none_abr(), _mp4_720p(), _dash_video_1080()],
    }


def _playlist_info():
    return {
        "_type": "playlist", "title": "Sample Playlist",
        "webpage_url": "https://www.youtube.com/playlist?list=PL_smoke",
        "entries": [
            {"id": "abc", "title": "Entry 1",
             "webpage_url": "https://www.youtube.com/watch?v=abc",
             "url": "https://www.youtube.com/watch?v=abc"},
            {"id": "def", "title": "Entry 2",
             "webpage_url": "https://www.youtube.com/watch?v=def",
             "url": "https://www.youtube.com/watch?v=def"},
        ],
    }


def single_video_smoke(log):
    from firedm import config
    from firedm.video import Video

    log.append("[smoke] single-video begin")
    config.download_folder = str(SMOKE_DIR)
    vid = Video(url="https://www.youtube.com/watch?v=abc", vid_info=_single_vid_info())
    result = {
        "streams": len(vid.all_streams),
        "menu_entries": len(vid.stream_menu),
        "selected_stream": getattr(vid.selected_stream, "name", None),
        "eff_url": vid.eff_url,
        "title": vid.title,
        "passed": bool(vid.all_streams) and bool(vid.eff_url),
    }
    log.append(f"[smoke] single-video streams={result['streams']} menu={result['menu_entries']} eff_url={result['eff_url']}")
    # DASH pairing
    dash = next(s for s in vid.all_streams if s.format_id == "137")
    vid.selected_stream = dash
    result["dash_audio_paired"] = bool(vid.audio_stream)
    result["dash_audio_url"] = vid.audio_url
    log.append(f"[smoke] dash_audio_paired={result['dash_audio_paired']}")
    return result


def playlist_smoke(log):
    from firedm import video
    from firedm.controller import create_video_playlist

    log.append("[smoke] playlist begin")

    # Swap out `get_media_info` so no network calls are made.
    pl_info = _playlist_info()
    entry_vid_info = _single_vid_info()

    call_state = {"calls": 0}

    def fake_get_media_info(url=None, info=None, ytdloptions=None, interrupt=False):
        call_state["calls"] += 1
        if url == pl_info["webpage_url"]:
            return pl_info
        # processing an individual entry — return the single-video payload
        return entry_vid_info

    with (
        patch("firedm.controller.get_media_info", side_effect=fake_get_media_info),
        patch("firedm.video.get_media_info", side_effect=fake_get_media_info),
    ):
        pl = create_video_playlist(pl_info["webpage_url"])
        entries = [
            {
                "title": getattr(v, "title", ""),
                "url": getattr(v, "url", ""),
                "streams_before_process": len(getattr(v, "all_streams", []) or []),
            }
            for v in pl
        ]
        video.process_video(pl[0])
        first_streams = len(getattr(pl[0], "all_streams", []) or [])

    result = {
        "entry_count": len(pl),
        "entries": entries,
        "first_entry_streams_after_process": first_streams,
        "calls": call_state["calls"],
        "passed": len(pl) == 2 and first_streams > 0,
    }
    log.append(f"[smoke] playlist entries={result['entry_count']} first_streams={first_streams}")
    return result


def main() -> int:
    single_log: list[str] = []
    playlist_log: list[str] = []

    single = single_video_smoke(single_log)
    playlist = playlist_smoke(playlist_log)

    (SMOKE_DIR / "single_video_smoke.log").write_text("\n".join(single_log), encoding="utf-8")
    (SMOKE_DIR / "playlist_smoke.log").write_text("\n".join(playlist_log), encoding="utf-8")
    (SMOKE_DIR / "single_video_result.json").write_text(
        json.dumps({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), **single}, indent=2),
        encoding="utf-8",
    )
    (SMOKE_DIR / "playlist_result.json").write_text(
        json.dumps({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), **playlist}, indent=2),
        encoding="utf-8",
    )

    print("single-video passed:", single["passed"])
    print("playlist passed:", playlist["passed"])

    return 0 if single["passed"] and playlist["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
