# Extractor Migration Policy

## Decision

`yt_dlp` is the primary and default extractor for every mainline code path.
`youtube_dl` is retained only as an opt-in legacy compatibility fallback and is
never selected automatically when `yt_dlp` is importable.

## Why

- `youtube_dl` is stale for current YouTube behavior and is unsafe as the
  default path for a production downloader.
- Official yt-dlp docs list Python 3.10+ support and strongly recommend
  ffmpeg/ffprobe, `yt-dlp-ejs`, and a JavaScript runtime for full YouTube
  support.
- The verified environment has `yt_dlp==2026.03.17`, `yt-dlp-ejs==0.8.0`,
  Deno `2.7.13`, and ffmpeg `8.1`.

## Runtime Policy

- `firedm/extractor_adapter.py` defines `PRIMARY_EXTRACTOR = "yt_dlp"` and
  `FALLBACK_EXTRACTOR = "youtube_dl"`.
- `choose_extractor_name(configured, available)` returns the primary whenever
  it is present, even if persisted settings request `youtube_dl`.
- `ExtractorService.wait_until_ready(timeout)` replaces timing-based startup
  luck.
- `firedm/video.py` keeps the legacy `video.ytdl` global mirrored from the
  service only for compatibility with old call sites.
- `get_ytdl_options()` passes discovered Deno through `js_runtimes` and
  discovered ffmpeg through `ffmpeg_location`.

## Dependency Policy

- Default install requires `yt-dlp[default]>=2026.3.17`.
- `youtube_dl>=2021.12.17` is available only through `pip install -e .[legacy]`.
- PyInstaller collects `yt_dlp`, `yt_dlp_ejs` data, and optional `youtube_dl`
  only when installed.
- Deno and ffmpeg remain external by default. Discovery checks explicit app
  paths, `PATH`, and Windows Winget package directories.

## Deprecation Boundary

Legacy extractor usage is allowed only for user compatibility plugins under
`<settings>/extractors/`. New code must not import or select `youtube_dl`
directly. All extractor selection goes through `ExtractorService`.

## Verification

- `scripts/verify_extractor_default.py` exits 0 and writes
  `artifacts/extractor/default_selection_proof.json`.
- `scripts/repro_youtube_bug.py` proves real YouTube single-video and playlist
  extraction on the `yt_dlp` path.
- `tests/test_extractor_default_selection.py` and
  `tests/test_legacy_extractor_fallback.py` pin the policy.
