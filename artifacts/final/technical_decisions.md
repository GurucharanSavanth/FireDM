# Technical Decisions

## 1. Should `yt_dlp` be the primary extractor?

Yes. The maintained extractor stack is `yt-dlp[default]>=2026.3.17` with
`yt-dlp-ejs` and Deno. `youtube_dl` is no longer safe as a default YouTube path.

## 2. What happens to `youtube_dl`?

It remains optional compatibility only. It is in `[legacy]`, may be loaded if
installed, and is never selected while `yt_dlp` is importable.

## 3. How is readiness enforced?

`ExtractorService.wait_until_ready(timeout=45.0)` gates video requests. Timeout
paths emit structured pipeline events instead of spinning forever.

## 4. How is playlist entry normalization handled?

`firedm/playlist_entry.py::normalize_entry` owns URL reconstruction. YouTube
bare IDs are rebuilt into watch URLs; unsupported ambiguous entries are rejected
with diagnostics instead of guessed.

## 5. How are failures surfaced?

`firedm/pipeline_logger.py` emits stage/status/key-value events for extractor
load/select, metadata fetch, playlist parse, stream build/select, enqueue, and
ffmpeg merge.

## 6. How are ffmpeg failures diagnosable?

`firedm/ffmpeg_commands.py` owns command construction. `ffmpeg_service` locates
the binary from explicit paths, `PATH`, or Winget package dirs. `video.py` passes
the located path to yt-dlp via `ffmpeg_location`.

## 7. What refactor was necessary?

The smallest maintainable split is:

- `extractor_adapter.py` for active extractor state
- `playlist_entry.py` for entry normalization
- `playlist_builder.py` for info-dict walking
- `ffmpeg_commands.py` and `ffmpeg_service.py` for media tooling
- `tool_discovery.py` for external executable discovery
- `pipeline_logger.py` for observability

## 8. Exact primary dependency

`yt-dlp[default]>=2026.3.17`. Verified installed versions:
`yt_dlp==2026.03.17`, `yt-dlp-ejs==0.8.0`.

## 9. Deprecated surfaces retired or isolated

- `youtube_dl` default selection: retired
- `youtube_dl` default dependency: retired
- direct `youtube_dl.extractor.*` HLS hardcode: removed
- fallback random-user-agent path: isolated to optional fallback load

## 10. Old internals no longer allowed in mainline

New code must not import `youtube_dl` directly, read
`config.active_video_extractor` as authority, or call `youtube_dl.extractor.*`
outside the adapter/fallback boundary.

## 11. Version policy

Use lower-bound policy on the verified maintained family:
`yt-dlp[default]>=2026.3.17`. Monthly extractor bumps must pass
`scripts/run_regression_suite.py`, `scripts/repro_youtube_bug.py`, and packaged
diagnostics.
