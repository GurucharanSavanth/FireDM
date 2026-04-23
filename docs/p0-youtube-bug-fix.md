# P0 YouTube Bug — Fix Summary

Companion to `docs/p0-youtube-bug-baseline.md` (the reproduction report)
and `artifacts/final/root_cause_analysis.md` (the detailed RCA).

## User-visible outcome

- Pasting a YouTube single-video URL populates the stream menu and
  downloads.
- Pasting a YouTube playlist URL populates every selectable entry (with
  any malformed entries skipped, not taking down the list with them).

## Single-line diagnosis

`Stream.__init__` multiplied `abr` (which `yt_dlp` now reports as `None`
for some formats) by `1024`, raising `TypeError`. The error propagated
out of `Video.__init__` and was swallowed by a broad `except Exception`
in `controller.create_video_playlist`, so the user saw "no video streams
detected" with no diagnostics.

## Fix components

1. **`firedm/video.py` — `Stream.__init__`** now calls a
   `_coerce_number(value, default)` helper for `abr`, `tbr`, `width`,
   `height`. `None` / unexpected types coerce to the default; real
   numbers pass through. `self.rawbitrate = self.abr * 1024` is safe now
   because `self.abr` is guaranteed numeric.

2. **`firedm/video.py` — `Video._process_streams`** wraps each
   `Stream(fmt)` call in try/except, emits a structured
   `stream_build status=fail format_id=...` event, and continues. One
   bad format no longer breaks the whole menu.

3. **`firedm/video.py` — `Video.get_title`** falls back to `simpletitle`
   when no extractor module is loaded (prevents `NoneType.YoutubeDL`
   crashes in headless tooling).

4. **`firedm/extractor_adapter.py` — `ExtractorService`** makes
   extractor init deterministic: `yt_dlp` is always preferred when
   loaded, the `wait_until_ready(timeout)` gate replaces the unbounded
   `while not ytdl: time.sleep(1)` spin, and a legacy persisted
   `active_video_extractor="youtube_dl"` can no longer demote the
   runtime to the deprecated extractor.

5. **`firedm/video.py` — HLS helper** reads
   `extract_m3u8_formats` from whichever extractor is active via the
   service, not hardcoded `youtube_dl.extractor.common`.

6. **`firedm/video.py` — `load_user_extractors`** early-returns when
   `config.sett_folder` is unresolved so headless callers don't kill
   the daemon import thread with a `NoneType os.path.join` crash.

7. **`firedm/playlist_entry.py`** centralizes entry URL normalization.
   YouTube-shape bare ids are rebuilt into full URLs; unknown
   extractors with opaque ids are explicitly rejected rather than
   silently guessing.

8. **`firedm/playlist_builder.py`** owns the playlist walk, emits
   `playlist_entry_normalize` + `playlist_parse` events, and contains
   per-entry construction failures.

9. **`firedm/pipeline_logger.py`** supplies
   `pipeline_event(stage, status, **fields)` used throughout the
   extractor / playlist / stream / ffmpeg / enqueue boundaries.

10. **`firedm/ffmpeg_commands.py`** isolates every ffmpeg argv string so
    command construction is unit-testable without running the binary.

## Regression protection

- `tests/test_single_video_flow.py :: test_single_video_builds_streams_even_with_none_bitrate`
  reproduces the `abr=None` format shape and asserts no crash.
- `tests/test_extractor_default_selection.py` pins the primary-first
  policy.
- `tests/test_legacy_extractor_fallback.py` pins every fallback path.
- `tests/test_playlist_flow.py :: test_playlist_single_bad_entry_does_not_abort_list`
  pins the per-entry containment.
- `scripts/verify_extractor_default.py` asserts runtime state from the
  packaged binary or source.

## Proof of fix

- `scripts/repro_youtube_bug.py` against real YouTube single video:
  **all five stages green** (see `artifacts/repro/single_video_repro.log`).
- `scripts/smoke_video_pipeline.py` single-video: **passed=True**
- `scripts/smoke_video_pipeline.py` playlist: **passed=True**
- Full test suite: **83 passed, 0 failed**.
- Packaged build: **4/4 checks passed**
  (`artifacts/packaged/packaged_video_flow_result.json`).

## If this regresses

1. Run `scripts/run_regression_suite.py` — look for the failing test;
   the matrix in `artifacts/regression/test_matrix.md` tells you
   which behavior it owns.
2. Run `scripts/collect_runtime_diagnostics.py` and attach the
   resulting `artifacts/diagnostics/runtime_snapshot.json` to any
   issue.
3. Check `artifacts/repro/repro_summary.json` — if single-video is
   still passing but playlist is not, the fault is likely in
   `playlist_builder` or `playlist_entry`.
