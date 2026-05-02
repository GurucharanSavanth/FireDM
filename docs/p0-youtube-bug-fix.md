# P0 YouTube Bug Fix

## User-Visible Outcome

YouTube single-video URLs and playlist URLs now pass the source diagnostic path
on the maintained extractor stack. The real repro harness confirms:

- single video metadata extraction
- stream menu creation
- selected stream URL resolution
- playlist extraction
- playlist entry normalization
- first playlist item metadata and stream processing

## Root Cause

The legacy pipeline had multiple faults:

- `Stream.__init__` assumed numeric bitrate fields. Current `yt_dlp` can return
  `None` for fields such as `abr`, causing a `TypeError`.
- Playlist and stream failures were hidden behind broad exception handling.
- Extractor selection was timing-sensitive and could fall back to the stale
  `youtube_dl` path.
- Current YouTube extraction needs `yt-dlp-ejs` plus a JS runtime; the previous
  dependency policy did not require or diagnose that stack.
- ffmpeg existed on the machine but not in the agent shell `PATH`, so yt-dlp
  could warn even though FireDM's baseline had ffmpeg installed.

## Fix

- `ExtractorService` makes `yt_dlp` deterministic default.
- `yt-dlp[default]>=2026.3.17` is the default dependency.
- `youtube_dl` moved to optional `[legacy]`.
- Deno is discovered and passed to yt-dlp as `js_runtimes`.
- ffmpeg is discovered from app paths, `PATH`, or Winget dirs and passed to
  yt-dlp as `ffmpeg_location`.
- Stream numeric fields are coerced at the boundary.
- Per-format and per-playlist-entry failures are logged and contained.
- Playlist URL normalization moved to `firedm/playlist_entry.py`.

## Proof

- `scripts/repro_youtube_bug.py` exit 0:
  `artifacts/repro/repro_summary.json`
- `scripts/verify_extractor_default.py` exit 0:
  `artifacts/extractor/default_selection_proof.json`
- `scripts/verify_ffmpeg_pipeline.py` exit 0:
  `artifacts/ffmpeg/ffmpeg_pipeline_result.json`
- `scripts/run_regression_suite.py` exit 0:
  `artifacts/regression/regression_suite_result.json`

## Regression Guard

Relevant tests:

- `tests/test_single_video_flow.py`
- `tests/test_playlist_flow.py`
- `tests/test_playlist_entry_normalization.py`
- `tests/test_extractor_default_selection.py`
- `tests/test_legacy_extractor_fallback.py`
- `tests/test_ffmpeg_pipeline.py`
- `tests/test_download_handoff.py`
