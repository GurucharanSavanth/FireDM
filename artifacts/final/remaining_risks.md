# Remaining Risks

## High

### R-H1: Private HLS helper

`firedm/video.py` reaches the active extractor's HLS parser to refresh URLs
mid-download. yt-dlp 2026.x removed the original `_parse_m3u8_formats`
symbol; only `_parse_m3u8_formats_and_subtitles` survives, and it requires
a bound `InfoExtractor` instance with a `YoutubeDL` parent because it
calls `self.get_param('hls_split_discontinuity', ...)`. youtube_dl 2021.x
still ships the original name and accepts `None` as `self`.

Status: **Mitigated 2026-04-25 (revival pass).** `refresh_urls` now adapts
to either parser:
- modern path constructs `InfoExtractor(YoutubeDL({}))` and calls
  `_parse_m3u8_formats_and_subtitles`, unpacking the
  `(formats, subtitles)` tuple.
- legacy path keeps the old `_parse_m3u8_formats(None, ...)` static-style
  call for `youtube_dl` fallback installs.
- failures are surfaced through `pipeline_logger.pipeline_exception`
  with stage `hls_url_refresh` instead of bubbling out of HLS pre-process.

Tests: `tests/test_hls_parser_compat.py` asserts at least one parser is
present on the installed yt-dlp and that the modern parser returns the
expected `(formats, subtitles)` tuple shape with a bound IE instance.
Future yt-dlp removals of both names will fail the suite immediately.

Open: still calling a private upstream symbol. Long-term replacement
options are a public yt-dlp helper (none today) or a small local m3u8
parser. Re-evaluate every yt-dlp bump.

### R-H2: Legacy GUI exception swallowing

`firedm/tkview.py` still contains broad legacy exception handling outside
the P0 path. The 2026-04-25 audit catalogued the patterns:

| Category | Examples | Acceptable today? |
| --- | --- | --- |
| `clipboard_get()` polling fallback | `url_watchdog` line 157 | Yes — clipboard misses are routine; logging would spam every 2 s. |
| Widget `config(image=…)` / `config(text=…)` swallows | status_icon, play_button, name_lbl, vbar, bar, thumbnail | Yes — render-tick frequency makes structured logging noisy and adds no diagnostic value. |
| State swallows | `recent_folders.remove`, `change_colors` recursion, tab activation | Borderline — silent failures hide stale state but recoverable. |
| Tooltip `print(e)` and `bidi support` `print(e)` | line 408, line 58 | Replace with `log()` so output is captured by the project log. |

Mitigation today: pipeline events expose extractor / playlist / download
boundaries even when GUI reporting is weak; the observer notify path is
now per-callback isolated (see `firedm/model.py` `_notify`) so one broken
GUI subscriber no longer aborts every other subscriber's view update.

Open: the borderline state-swallow group still hides bugs. A future
refactor should replace those with `pipeline_exception` calls or with
explicit error-state surfacing. The render-tick group should stay
swallowed but should be moved behind a small helper that records a
single rate-limited diagnostic per session, not per call.

## Medium

### R-M1: yt-dlp upstream drift

YouTube changes often. The verified family is `yt-dlp[default]>=2026.3.17`,
but future releases can change info-dict shape or format availability.

Mitigation: run `scripts/run_regression_suite.py` and
`scripts/repro_youtube_bug.py` before accepting extractor bumps.

Status (2026-04-25): both scripts pass against `yt-dlp 2026.3.17` and
`yt-dlp-ejs 0.8.0`; YouTube extraction round-trips (Deno-backed JS
challenge solver in use, 49 streams returned for the canary URL).

### R-M2: External Deno and ffmpeg

Deno and ffmpeg are not bundled by default. FireDM now discovers app-local
paths, `PATH`, and Winget package directories, but a user without either
tool still needs installation guidance.

Future decision: bundle one or both in Windows releases, after license and
size review.

Status (2026-04-25): on the verified Windows baseline both tools are
installed via Winget (`Gyan.FFmpeg.Essentials`, `DenoLand.Deno`) and the
discovery scan returns the correct Winget package paths even when shell
`PATH` is stale. README "External Tools" and "Troubleshooting" sections
reflect this.

### R-M3: Legacy user extractor plugins

User plugins that subclass `youtube_dl.InfoExtractor` remain fallback-only
debt.

Mitigation: `[legacy]` extra remains available. Future work should support
`yt_dlp.InfoExtractor` plugin registration or formally remove the feature.

### R-M4: Worker stall watchdog only on last batch

`firedm/brain.py` enables pycurl `LOW_SPEED_LIMIT` / `LOW_SPEED_TIME`
(`minimum_speed=20*1024`, `timeout=10`) only when the remaining job count
fits inside `allowable_connections` (the "last workers batch" branch at
brain.py:510-514). Earlier segments run with `minimum_speed=None`,
relying on parallelism to mask any individual stall.

Risk: a single hung early segment ties up its worker until the user pauses
the download or until the batch shrinks. With slow hosts and few
connections this can effectively freeze the download.

Future work: add a per-segment last-byte-received watchdog with a
configurable timeout (`config.segment_stall_timeout`) and a dedicated
retry path. Touching `brain.py` requires careful threading review and
regression coverage; deferred until real-network resume/progress tests
exist (see Deferred below).

### R-M5: Legacy non-pipeline URL logging

Structured pipeline events now redact credential-bearing URL query
parameters through `firedm/pipeline_logger.py`, and HLS/download start
logs use the same helper on the highest-risk media URL lines. Some legacy
plain `log()` paths still receive user URLs directly, including batch URL
echoes, CLI/proxy help text, and lower-priority thumbnail/subtitle paths.

Risk: if a user pastes a signed direct-download URL into those legacy paths,
the raw query string may still appear in verbose logs.

Mitigation today: all new pipeline URL fields and HLS refresh failures are
redacted; `tests/test_pipeline_logger_redaction.py` covers signed query
parameters in fields and exception detail text.

Future work: route all URL-bearing `log()` calls through the redaction
helper or a small `log_url()` wrapper. This should be done as a focused
logging pass because the legacy GUI uses plain log output for user-visible
messages.

## Deferred

- Split `controller.py` download/video orchestration further.
- Add real-download resume/progress tests with a local HTTP server.
- Validate Python 3.11 end-to-end.
- Decide bundled ffmpeg/Deno release policy.
- Replace remaining tkview render-tick swallows with a single rate-limited
  diagnostic (R-H2 follow-up).
- Per-segment stall watchdog for early-batch workers (R-M4 follow-up).
- Decide future of `youtube_dl.InfoExtractor` plugin compatibility
  (R-M3 follow-up).
- Convert remaining legacy URL-bearing `log()` calls to the redaction
  helper without changing user-facing diagnostics (R-M5 follow-up).
