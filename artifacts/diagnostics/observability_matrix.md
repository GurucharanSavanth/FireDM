# Observability Matrix (Commit 2)

Every stage below now emits a `[pipeline] stage=<stage> status=<status> key=value ...`
line through the existing `log()` sink, via `firedm/pipeline_logger.py`. These
are grep-able from CLI logs and GUI log view, and assertable from tests.

| Stage | Emitted from | Status values | Key fields |
| --- | --- | --- | --- |
| `extractor_load` | `video.load_extractor_engines` (both threads) + `_load_user_extractors_safely` | `start` / `ok` / `fail` | `engine`, `version`, `load_seconds`, `phase` |
| `extractor_ready` | `video.get_media_info` (waiting on `ytdl`) | `start` / `ok` / `fail` | `active`, `configured`, `waited_seconds` |
| `extractor_select` | `video.set_default_extractor` | `ok` / `fail` | `active`, `module` |
| `metadata_fetch` | `video.get_media_info` (narrowed excepts) + `video.process_video` | `start` / `ok` / `fail` / `skip` | `url`, `phase`, `streams` |
| `playlist_parse` | `controller.create_video_playlist` | `start` / `ok` / `fail` | `url`, `entries`, `kind` (`single` \| `playlist`) |
| `playlist_entry_normalize` | reserved (`controller.create_video_playlist` — populated fully in Commit 5) | | |
| `stream_build` | `video.Video._process_streams` (per-format guard) | `start` / `fail` | `url`, `formats`, `format_id`, `idx` |
| `stream_select` | reserved for `controller.select_stream` (Commit 7) | | |
| `download_enqueue` | `controller.Controller.download` | `ok` / `fail` | `uid`, `name`, `type` |
| `download_start` | reserved for `brain.brain` (Commit 7) | | |
| `ffmpeg_discover` | `controller.check_ffmpeg` | `ok` / `fail` | `path`, `version`, `searched` |
| `ffmpeg_merge` | reserved for `video.merge_video_audio` (Commit 6) | | |

## Proof the events fire

Rerun of `scripts/repro_youtube_bug.py` after Commit 2 shows the line form in
both logs, e.g.:

```
[pipeline] stage=extractor_load status=start engine=yt_dlp
[pipeline] stage=extractor_load status=ok engine=yt_dlp version=2026.03.17 load_seconds=0.37
[pipeline] stage=extractor_select status=ok active=yt_dlp module=yt_dlp
[pipeline] stage=playlist_parse status=start url=https://www.youtube.com/watch?v=jNQXAC9IVRw
[pipeline] stage=stream_build status=start url=https://www.youtube.com/watch?v=jNQXAC9IVRw formats=11
[pipeline] stage=stream_build status=fail format_id=18 idx=8 :: TypeError: unsupported operand type(s) for *: 'NoneType' and 'int'
[pipeline] stage=playlist_parse status=ok url=https://www.youtube.com/watch?v=jNQXAC9IVRw entries=1 kind=single
```

`artifacts/repro/single_video_repro.log` and `artifacts/repro/playlist_repro.log`
now contain the same events. Assertions in Commits 4-8 will use these tags.

## What remains silent

- `brain.brain` / `worker.thread_manager` (Commit 7 boundary work)
- per-segment `worker` failures (kept out of Commit 2 scope — noisy and high-churn)
- GUI toast surface — still handled by existing `showpopup=True` paths

## Structural change

- `firedm/pipeline_logger.py` — new, no external deps, safe to import inside
  daemon threads before settings are initialized.
- `firedm/video.py` and `firedm/controller.py` — instrumented at boundaries;
  no business-logic change **except** `Video._process_streams` now skips a
  single malformed format instead of letting it abort the entire menu build.
  That skip is considered defensive observability (the failure is logged as
  a structured `fail` event). Commit 4 replaces the skip with a proper
  `None`-tolerant `Stream.__init__`.
