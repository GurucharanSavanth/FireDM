# Known Issues And Deferred Work

## Still high-risk
- `firedm/controller.py`, `firedm/video.py`, and `firedm/tkview.py` remain large and responsibility-heavy.
- Download-state coordination still relies on mutable shared objects and legacy thread signaling.
- GUI behavior is only partially automated; critical GUI flows still need manual smoke validation.
- Detailed boundaries and staged extraction plan: [legacy-refactor-plan.md](legacy-refactor-plan.md).

## Packaging limitations
- Windows packages currently expect `ffmpeg` on `PATH` or copied beside the app.
- If `ffmpeg` is missing, the GUI opens ffmpeg install guidance instead of downloading stale binaries from the historical upstream repository.
- Winget ffmpeg package folders can be access-denied to non-interactive agent shells; in that case FireDM cannot enumerate the package contents and maintainers should add ffmpeg to `PATH` or copy `ffmpeg.exe` beside the app before release validation.
- Packaged Windows builds do not support in-place self-update. Upgrade by replacing the distribution with a newer release.
- PyInstaller still emits a tkinter/Tcl detection warning on the verified Windows baseline. The manual Tcl/Tk collection in `scripts/firedm-win.spec` is intentional, and `scripts/windows-build.ps1` fails if the expected packaged Tk assets are missing.

## Python support status
- verified: Python `3.10.11` on Windows
- not yet locally verified in this modernization pass: Python `3.11`
- Python `3.12` is blocked locally by the broken Microsoft Store launcher in this workspace
- package metadata is constrained to `>=3.10,<3.11` until 3.11/3.12 validation passes

## Manual validation still required
- Full GUI interaction: launch `FireDM-GUI.exe`, paste URL, inspect queue/progress/cancel/resume behavior.
- Real downloads: run at least one small direct-file download and verify final file, retry/resume, and checksum behavior.
- Playlist network behavior: run one single-video URL and one playlist URL through yt-dlp extraction and GUI handoff.
- ffmpeg post-processing: run one DASH/HLS item requiring merge/conversion, then repeat with ffmpeg temporarily unavailable to verify missing-tool reporting.

## Extractor policy
- `yt_dlp` is primary
- `youtube_dl` is retained only for compatibility until its remaining value is re-evaluated with real download/regression coverage

## Deferred engineering work
- split controller orchestration into smaller services
- formalize download-state transitions with typed enums/models
- isolate `pycurl` transport more aggressively away from generic utility code
- add mocked integration tests for controller/download lifecycle and extractor adapter behavior
- per-segment stall watchdog for early-batch workers in `firedm/brain.py` (only the last batch currently sets pycurl `LOW_SPEED_LIMIT`/`LOW_SPEED_TIME`; see `artifacts/final/remaining_risks.md` R-M4)
- replace remaining `firedm/tkview.py` render-tick `except:` swallows with a single rate-limited diagnostic helper; see `artifacts/final/remaining_risks.md` R-H2

## Closed in 2026-04-25 revival pass
- ffmpeg discovery test was non-hermetic (passed `include_winget=False` but not a hermetic `path_lookup`, so a Winget-installed ffmpeg on `PATH` made the test fail on dev machines). `tests/test_ffmpeg_pipeline.py::test_ffmpeg_service_reports_not_found_when_missing` now passes a stub `path_lookup`.
- `firedm/model.py` `Observable._notify` rewrote `try: ... except: raise` (which aborted observer iteration on the first failing callback and bubbled out of every property setter) into per-callback isolation that surfaces failures via `pipeline_logger.pipeline_exception`. New regression: `tests/test_observer_isolation.py`.
- `firedm/video.py` `refresh_urls` (HLS pre-process) called the removed-in-yt-dlp-2026 `_parse_m3u8_formats` symbol and would crash with `AttributeError` once a real DASH/HLS download triggered it. Adapted to the surviving `_parse_m3u8_formats_and_subtitles` (modern, requires bound `InfoExtractor` instance with `YoutubeDL` parent) with fallback to the legacy symbol for `youtube_dl` installs. Failures now log via `pipeline_exception('hls_url_refresh', ...)`. New regression: `tests/test_hls_parser_compat.py`.
- `requirements.txt` floors synced with `pyproject.toml` (plyer, certifi, pycurl, pystray, packaging, distro) so `pip install -r requirements.txt` and `pip install -e .` resolve to the same dependency surface.
- Pipeline structured logs now redact credential-bearing URL query parameters (token/signature/key/auth/session/cookie/password-style fields) while preserving host/path diagnostics. New regression: `tests/test_pipeline_logger_redaction.py`.
