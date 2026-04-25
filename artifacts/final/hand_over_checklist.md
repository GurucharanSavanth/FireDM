# Maintainer Handover Checklist

## Quickstart

```powershell
.\.venv\Scripts\activate.ps1
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\run_regression_suite.py
.\.venv\Scripts\python.exe scripts\repro_youtube_bug.py
.\.venv\Scripts\python.exe scripts\collect_runtime_diagnostics.py
```

## Release Checklist

- [ ] `.\.venv\Scripts\python.exe -m pytest -q` - expect 101 passed or newer
      (post-2026-04-25 revival: observer-isolation regression, HLS
      parser-compat regression, hermetic ffmpeg-discovery test, and
      pipeline URL-redaction regression added).
- [ ] `.\.venv\Scripts\python.exe -m ruff check firedm\FireDM.py firedm\app_paths.py firedm\extractor_adapter.py firedm\ffmpeg_service.py firedm\tool_discovery.py firedm\setting.py firedm\update.py tests`
- [ ] `.\.venv\Scripts\python.exe -m mypy`
- [ ] `.\.venv\Scripts\python.exe scripts\run_regression_suite.py` - expect 71 passed or newer
      (regression suite TARGETS now include `tests/test_observer_isolation.py`,
      `tests/test_hls_parser_compat.py`, and
      `tests/test_pipeline_logger_redaction.py`).
- [ ] `.\.venv\Scripts\python.exe scripts\repro_youtube_bug.py` - single-video and playlist pass.
- [ ] `powershell -ExecutionPolicy Bypass -File .\scripts\windows-build.ps1`
- [ ] `.\.venv\Scripts\python.exe scripts\verify_packaged_video_flow.py`

## Code Map

| Need | File |
| --- | --- |
| Extractor selection | `firedm/extractor_adapter.py` |
| yt-dlp options, stream building, ffmpeg handoff | `firedm/video.py` |
| Playlist URL normalization | `firedm/playlist_entry.py` |
| Playlist walking | `firedm/playlist_builder.py` |
| FFmpeg command construction | `firedm/ffmpeg_commands.py` |
| FFmpeg discovery | `firedm/ffmpeg_service.py` |
| Deno/ffmpeg Winget fallback discovery | `firedm/tool_discovery.py` |
| Pipeline event vocabulary | `firedm/pipeline_logger.py` |

## Key Invariants

- `yt_dlp` is the runtime default whenever importable.
- `youtube_dl` is optional legacy fallback only.
- `yt-dlp[default]` must stay in the default dependency surface.
- Deno and ffmpeg discovery must not rely only on shell `PATH`.
- Playlist processing must survive one bad entry.
- Stream construction must tolerate `None` numeric fields.

## First Triage Steps

1. Run `scripts/collect_runtime_diagnostics.py`.
2. Confirm `extractor_service.active == "yt_dlp"`.
3. Confirm Deno and ffmpeg paths are present.
4. Run `scripts/repro_youtube_bug.py`.
5. Inspect `[pipeline]` logs around the last `start` event without an `ok` or `fail`.
