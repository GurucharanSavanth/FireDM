# Remaining Risks

## High

### R-H1: Private `_parse_m3u8_formats` dependency

`firedm/video.py :: pre_process_hls/refresh_urls` calls
`active.extractor.common.InfoExtractor._parse_m3u8_formats`. This is a
private method on both `yt_dlp` and `youtube_dl`; both currently expose
it but may rename or change its signature without notice.

**Mitigation today:** adapter abstraction (`EXTRACTOR_SERVICE.active_module()`)
means only one place needs to change, and the call is wrapped in a
log-and-skip.

**Future slice:** replace with yt_dlp's public HLS helper when one
ships, or reimplement the minimum subset of the m3u8 parse we use.

### R-H2: `tkview.py` has 29 bare `except:` blocks

None are on the P0 YouTube path, but any of them can silently swallow
future regressions in the GUI-driven flows (user clicks Download → nothing
happens). The modernization of `tkview.py` is a separate, large slice.

**Mitigation today:** the pipeline events let us correlate "user said
nothing happened" with what the pipeline actually did, without relying on
`tkview.py` reporting.

## Medium

### R-M1: `yt_dlp` upstream drift

`yt_dlp` releases monthly. Each release can:

- change info-dict field semantics (why `abr=None` surfaced in the first
  place);
- drop formats YouTube stops serving;
- rename private extractor symbols (e.g. `_parse_m3u8_formats`).

**Mitigation today:** `_coerce_number` normalizes all numeric fields;
`_process_streams` wraps per-format construction; `run_regression_suite.py`
catches the obvious breaks.

**Future:** add a nightly CI job that bumps `yt_dlp` to latest and runs
the full suite + live repro.

### R-M2: ffmpeg on PATH / external dependency

Windows packaged builds still expect `ffmpeg.exe` on PATH or beside the
exe. Users without it hit a `FFMPEG is missing` message during download
(surfaced, but still a hard requirement).

**Mitigation today:** Settings dialog offers to download ffmpeg from
a known mirror.

**Future (deferred):** decide whether to bundle ffmpeg in the release
zip, acknowledging license impact. Tracked in `docs/known-issues.md`.

### R-M3: `load_user_extractors` only registers `youtube_dl` plugins

The helper still imports user-supplied `.py` files under
`<settings>/extractors/` and subclasses `youtube_dl.InfoExtractor`. If we
ever remove `youtube_dl`, those plugins silently stop loading.

**Mitigation today:** fallback extractor still loads, plugins still work.

**Future slice:** either deprecate the user-plugin feature with a
migration notice, or add `yt_dlp.InfoExtractor` support.

## Low

### R-L1: Controller constructor starts threads at import time

Integration tests (`tests/test_download_handoff.py`) patch
`controller.Thread.start` to avoid this. A dedicated service object
owning those threads would be cleaner but is out of P0 scope.

### R-L2: Bare `except:` in `Stream.get_stream` / `Stream.quality`

These are intentional today — they're guards on selection-loop filtering
that must not cascade into GUI. Left as-is; noted here for awareness.

### R-L3: Non-English title templates

`Video.get_title` uses `ydl.prepare_filename` which can emit characters
illegal on Windows filesystems; `validate_file_name` normalizes this but
edge cases (e.g. trailing periods) may still surface. Not exercised by
the automated suite.

## Deferred (non-risk, tracking only)

- `pycurl` transport boundary — kept; modernization is a separate slice
  (see `docs/dependency-strategy.md`).
- `config.py` global mutability — incremental cleanup only where touched.
- `scripts/exe_build/*` legacy cx_Freeze — left in-repo for historical
  reference but no longer supported.

## How to retire risks

Each risk above maps to a future commit or issue:

- R-H1 → issue: "replace InfoExtractor._parse_m3u8_formats with public equivalent"
- R-H2 → issue: "tkview.py bare-except audit"
- R-M1 → CI nightly bump + regression run
- R-M2 → release-process decision
- R-M3 → plugin migration path
