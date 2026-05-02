# Video Pipeline Architecture

After Commits 3-7 the YouTube / video pipeline has clear, testable seams.
This document describes the layering so a new maintainer can follow a
single URL from user input to download queue.

## Module map

```
user URL
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ firedm/controller.py                                        │
│                                                             │
│   Controller.process_url(url)                               │
│   Controller.download(d)   → download_q (Queue)             │
│   create_video_playlist(url) ─ orchestrator only            │
└─────────────────────────────────────────────────────────────┘
       │                           │                │
       │ get_media_info()          │ build_playlist_from_info()
       ▼                           ▼                │
┌──────────────────┐  ┌──────────────────────────┐  │
│ firedm/video.py  │  │ firedm/playlist_builder  │  │
│                  │  │  .py                     │  │
│ get_media_info   │  │                          │  │
│ process_video    │  │ build_playlist_from_info │  │
│ load_extractor_  │  │  → PlaylistBuildResult   │  │
│  engines         │  │                          │  │
│ Video / Stream   │  │ normalize_entry hook     │  │
└──────────────────┘  └──────────────────────────┘  │
       │                           │                │
       │ uses                      │ uses           │
       ▼                           ▼                ▼
┌──────────────────┐  ┌──────────────────────────┐  ┌─────────────────────┐
│ firedm/extractor │  │ firedm/playlist_entry.py │  │ firedm/ffmpeg_      │
│  _adapter.py     │  │                          │  │  commands.py        │
│                  │  │ normalize_entry() rule   │  │                     │
│ ExtractorService │  │                          │  │ build_merge_command │
│ choose_extractor │  │                          │  │ build_hls_process_  │
│  _name           │  │                          │  │  command            │
│ SUPPORTED_       │  │                          │  │ build_audio_        │
│  EXTRACTORS      │  │                          │  │  convert_command    │
└──────────────────┘  └──────────────────────────┘  │ dash_audio_         │
       │                                            │  extension_for      │
       ▼                                            └─────────────────────┘
┌──────────────────┐
│ yt_dlp (primary) │
│ youtube_dl       │
│  (fallback)      │
└──────────────────┘
```

## Responsibilities

| Module | Owns | Does not own |
| --- | --- | --- |
| `controller.py` | queue lifecycle, observer fanout, ffmpeg check, download enqueue, thumbnail orchestration | walking extractor dicts, HLS m3u8 parsing, ffmpeg argv construction, extractor init |
| `playlist_builder.py` | turning an extractor info dict into Video-like objects with per-entry error containment | extractor I/O, network calls, thumbnail fetch |
| `playlist_entry.py` | normalizing a single entry dict into a `NormalizedEntry` (full URL + source field) | constructing Video objects |
| `video.py` | Video / Stream model, extractor calls (`get_media_info`, `process_video`), HLS pre/post-processing, subtitle download | ffmpeg command strings, playlist-shape parsing, extractor selection policy |
| `extractor_adapter.py` | choosing which extractor is active, loading modules, readiness gate | running extraction, HTTP |
| `ffmpeg_commands.py` | argv construction for merge / HLS / audio convert, DASH container pairing rules | invoking ffmpeg, discovering the binary |
| `ffmpeg_service.py` | discovering ffmpeg on disk and probing its version | constructing commands |
| `pipeline_logger.py` | structured `[pipeline] stage=<> status=<>` event line via `utils.log` | business decisions |

## Lifecycle of a single-video download

1. GUI / CLI calls `Controller.process_url(url)` → `create_video_playlist(url)`.
2. `get_media_info` blocks on `ExtractorService.wait_until_ready(45)`, then calls `ydl.extract_info(url, process=False)` with narrow exception handling.
3. Single-video branch re-fetches with `process=True` to populate `formats`.
4. `build_playlist_from_info(url, info, observable_factory=ObservableVideo)` constructs exactly one `ObservableVideo`.
5. `Video.setup()` → `_process_streams()` calls `Stream(fmt)` per format (each wrapped in try/except so one bad format cannot abort the menu).
6. Default stream is selected; `select_audio()` pairs DASH video with a compatible container via `dash_audio_extension_for`.
7. GUI renders `stream_menu`. User clicks Download.
8. `Controller.download(d)` runs `_pre_download_checks` (ffmpeg present, folder writeable, name valid, no duplicate UID).
9. On success, `d` is placed on `self.download_q` and `pipeline_event("download_enqueue", "ok")` fires.
10. `download_q_handler` (background thread) dequeues and hands off to `brain`.
11. On completion, DASH streams hit `merge_video_audio` which uses `build_merge_command`.

## Lifecycle of a playlist download

1-3. Same extractor path.
4. `build_playlist_from_info` sees `_type == "playlist"` and iterates `entries`.
5. Each entry → `normalize_entry()` → full URL or skipped (skipped counts are reported in the structured event).
6. Each surviving entry → `observable_factory(url, v_info)` wrapped in try/except; failures are logged and the next entry continues.
7. GUI renders a playlist menu keyed by `Video.title`.
8. User selects items; `Controller.download_playlist(download_info)` calls `process_video(d)` per item before enqueue.

## Global state, after

- `video.ytdl` still exists as a compatibility mirror of `ExtractorService.active_module()`. New code should prefer the service.
- `config.active_video_extractor` is still consulted at startup but cannot override the primary-first policy.
- `config.ffmpeg_actual_path` / `config.ffmpeg_version` are filled by `controller.check_ffmpeg` once per startup.

## What is deliberately not done

- `tkview.py` (~5k lines) is untouched. UI refactor is out of P0 scope.
- `brain.py` / `worker.py` still use ad-hoc logging below the pipeline events. Per-segment telemetry is a future slice.
- No attempt to replace `pycurl`. Transport boundary work stays queued.

## How to extend the pipeline safely

- **New extractor (e.g. a custom site wrapper):** add the name to
  `SUPPORTED_EXTRACTORS`, teach `load_extractor_engines` to import it, let
  `ExtractorService.choose_extractor_name` pick it if primary is missing.
- **New post-processing step:** add a builder in `ffmpeg_commands.py`,
  call it from a narrow function in `video.py` that emits `ffmpeg_merge`
  events.
- **New playlist source quirk:** add a case to `_rebuild_from_id` in
  `playlist_entry.py` with a unit test alongside existing ones.
