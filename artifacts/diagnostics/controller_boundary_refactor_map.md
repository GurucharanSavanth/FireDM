# Controller Boundary Refactor Map (Commit 7)

Mapping of each responsibility that used to live inside
`controller.create_video_playlist` (and scattered helpers) to its new home.

| Responsibility | Before | After |
| --- | --- | --- |
| Fetch extractor info for a URL | `video.get_media_info(url)` — still | `video.get_media_info(url)` |
| Decide primary vs. fallback extractor | open-coded inside `load_extractor_engines` daemon threads (race) | `ExtractorService.choose_extractor_name` + `_reselect_active_locked` (deterministic) |
| Wait for extractor to be ready | `while not ytdl: time.sleep(1)` (unbounded) | `ExtractorService.wait_until_ready(timeout=45.0)` |
| Decide whether info is a playlist | inline `_type` / `"entries"` check in `create_video_playlist` | `playlist_builder.build_playlist_from_info` reads `_type` / `entries` once |
| Normalize bare-id playlist entries | inline `webpage_url or url or id` (produced bare ids) | `playlist_entry.normalize_entry` |
| Construct Video/ObservableVideo per entry | inline in `create_video_playlist` loop | `playlist_builder._build_playlist_entries` using an injected `observable_factory` |
| Contain per-entry failure | absent — one raise killed the playlist | try/except around factory call + structured skip event |
| Propagate `playlist_title` / `playlist_url` | inline (kept) | same, moved inside `_build_playlist_entries` |
| Pull thumbnail for single entry | inline | still in `controller.create_video_playlist` (I/O side-effect belongs to controller) |
| Build stream menu | `Video._process_streams` (kept) | `Video._process_streams`, per-format try/except |
| Pair DASH audio container | inline `m4a` vs `webm` conditional | `ffmpeg_commands.dash_audio_extension_for` |
| Build ffmpeg merge argv | f-string inside `merge_video_audio` | `ffmpeg_commands.build_merge_command` returns `FfmpegCommandPair` |
| Build HLS ffmpeg argv | f-string inside `post_process_hls.process_file` | `ffmpeg_commands.build_hls_process_command` |
| Build audio-convert argv | f-string inside `convert_audio` | `ffmpeg_commands.build_audio_convert_command` |
| Emit failure telemetry | bare `except` swallow | `pipeline_event` / `pipeline_exception` at every boundary |

## What was intentionally left alone

- The Controller's background threads, queue handling, and observer
  wiring. Those are orthogonal to the P0 video path and a separate
  slice.
- `tkview.py` GUI surface. Out of P0 scope.
- `brain.py`, `worker.py` download engine. Per-segment telemetry is
  queued.

## Test coverage of the new boundaries

| Module | Test | Assertion |
| --- | --- | --- |
| `playlist_entry.py` | `tests/test_playlist_entry_normalization.py` | 8 normalization cases |
| `playlist_builder.py` | `tests/test_controller_video_integration.py` | single + playlist + skipped-entry flows |
| `ffmpeg_commands.py` | `tests/test_ffmpeg_pipeline.py` | command structure, quoting, protocol whitelist |
| `extractor_adapter.py` (ExtractorService) | `tests/test_extractor_service.py` + `tests/test_extractor_default_selection.py` | primary-first policy, race proof |
| `video.py` (Video/Stream) | `tests/test_single_video_flow.py`, `tests/test_stream_selection.py` | None-bitrate tolerance, DASH pairing |

## How this unblocks Commit 8

- Every boundary now returns a typed object (`PlaylistBuildResult`,
  `FfmpegCommandPair`, `NormalizedEntry`, `ExtractorModule`) instead of
  implicit mutation of module globals.
- Structured events (`[pipeline] stage=...`) let `test_matrix.md` in
  Commit 8 assert the exact flow.

## Gate decision

- Single-video flow path: `controller.create_video_playlist` → shrank
  from 62 to 38 lines; all extractor-walking moved to builder.
- Playlist entry handling: dedicated module with 100% normalization
  coverage in unit tests.
- ffmpeg command construction: zero string-build f-strings remain in
  `video.py`; all go through `ffmpeg_commands.py`.
- Full regression suite (72 tests) still green.

**C7 gate: PASS.**
