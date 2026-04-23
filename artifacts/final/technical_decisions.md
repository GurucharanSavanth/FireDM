# Technical Decisions

Each row answers one of the mandatory decisions listed in the prompt.

## 1. Should `yt_dlp` be the primary extractor?

**Yes.** `yt_dlp==2026.03.17` is actively maintained; `youtube_dl==2021.12.17`
is effectively unmaintained. Every mainline extraction path now goes
through the `ExtractorService` with `PRIMARY_EXTRACTOR = "yt_dlp"`.

## 2. Does the legacy extractor path remain supported fallback, optional compatibility path, or deprecated/removed?

**Optional compatibility fallback only.** It is:

- still declared in `pyproject.toml` for now;
- still loaded best-effort at startup so user `InfoExtractor` plugins
  keep working;
- never chosen as the runtime default when `yt_dlp` is importable.

## 3. How is extractor readiness enforced?

Via `ExtractorService.wait_until_ready(timeout=45.0)`. The previous
`while not ytdl: time.sleep(1)` spin is gone. Timeout emits a structured
`extractor_ready status=fail` event and the calling function returns
`None` explicitly.

## 4. How is playlist entry URL normalization handled robustly?

`firedm/playlist_entry.py :: normalize_entry` returns a `NormalizedEntry`
with `url`, `source_field`, `ie_key`, `was_normalized`. YouTube-shape
(11-char) bare ids are inferred as YouTube; Vimeo numeric ids are
inferred as Vimeo with `ie_key`; unknown combinations return `None`
rather than fabricating a URL.

## 5. How are failures surfaced instead of swallowed?

`firedm/pipeline_logger.py` emits
`[pipeline] stage=<stage> status=<ok|fail|warn|skip> key=value ...`
events through the app's existing `log()` sink. Boundaries instrumented:

- extractor load / select / ready
- metadata fetch
- playlist parse / entry normalize
- stream build / select
- ffmpeg discover / merge
- download enqueue

Swallowed exceptions inside `get_media_info`, `process_video`, and
`create_video_playlist` have been narrowed and every branch emits a
pipeline event.

## 6. How are ffmpeg merge failures made diagnosable?

`merge_video_audio` emits `ffmpeg_merge` events with:

- `start` — the argv triple (video, audio, output, ffmpeg path)
- `warn` — fast stream-copy failed, retrying transcode
- `ok` / `fail` — which strategy succeeded, or the final error

Command construction lives in `firedm/ffmpeg_commands.py` and is
unit-testable without running the binary
(`tests/test_ffmpeg_pipeline.py`).

## 7. What minimal architectural refactor is necessary to make this maintainable?

- `firedm/extractor_adapter.py :: ExtractorService` — one owner of
  "which extractor is active."
- `firedm/playlist_entry.py` — one rule for turning an entry dict into
  a URL.
- `firedm/playlist_builder.py` — one owner of "walk this info dict and
  return Videos."
- `firedm/ffmpeg_commands.py` — pure argv builders.
- `firedm/pipeline_logger.py` — one vocabulary for structured events.

The controller keeps orchestration (queue, observer, ffmpeg check,
thumbnail side-effects) but no longer owns dict walking or command
strings.

## 8. Which exact maintained extractor package/version family is the new primary dependency?

`yt_dlp` (primary). Baseline environment ships `yt_dlp==2026.03.17`.
`pyproject.toml` pins `yt_dlp>=2024.12.0` as a hard requirement.

## 9. Which deprecated extractor package(s) and API surfaces are retired, isolated, or removed?

- `youtube_dl` package — demoted from default extractor to
  compatibility-only fallback.
- `youtube_dl.extractor.common.InfoExtractor._parse_m3u8_formats`
  hardcode — replaced with `active.extractor.common.InfoExtractor._parse_m3u8_formats`
  resolved through the service.
- `youtube_dl.utils.random_user_agent` — still called, but only on the
  fallback load path.
- Races in `load_extractor_engines` — removed.

Full inventory: `artifacts/extractor/deprecated_api_inventory.md`.

## 10. Which old extractor internals are no longer allowed in the mainline code path?

- Direct `from youtube_dl import …` outside `load_extractor_engines`.
- Direct references to `youtube_dl.extractor.*` anywhere.
- Direct reads of `config.active_video_extractor` as the authority for
  "which extractor is active" (must go through
  `ExtractorService.active_name()`).

## 11. How does dependency pinning / version policy ensure the app keeps working when the extractor package updates?

- `pyproject.toml` pins lower bounds only; we always want the latest
  compatible `yt_dlp`.
- `_coerce_number` normalizes numeric drift at the boundary so new
  `None`-valued fields can't crash `Stream.__init__`.
- `_process_streams` contains per-format failures so any future format
  that still breaks gets skipped, not swallowed.
- `scripts/run_regression_suite.py` is the monthly-bump gate.
- `scripts/repro_youtube_bug.py` is the live-network gate.

## Supported Python baseline

- verified: 3.10.11
- declared in pyproject: `>=3.10,<3.13`
- not yet locally verified in this sprint: 3.11 and 3.12 — tracked in
  `docs/known-issues.md`.
