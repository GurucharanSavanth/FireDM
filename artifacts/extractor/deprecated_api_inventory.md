# Deprecated Extractor API Inventory

Captured after Commit 3.

## Deprecated package in mainline

| Item | Before | After Commit 3 |
| --- | --- | --- |
| `youtube_dl` as default extractor | default when `config.active_video_extractor` was `"youtube_dl"` (and de-facto winner of the daemon-thread race on fast machines) | never default; `choose_extractor_name` promotes `yt_dlp` whenever it is loaded |
| `youtube_dl.extractor.common.InfoExtractor._parse_m3u8_formats` hardcoded in HLS refresh | required `youtube_dl` to be importable or HLS refresh crashed | resolves through `ExtractorService.active_module()`; `yt_dlp.extractor.common.InfoExtractor._parse_m3u8_formats` used when primary is active |
| `while not ytdl: time.sleep(1)` readiness spin | unbounded; hung silently if imports failed | bounded `ExtractorService.wait_until_ready(timeout=45.0)` with a structured `extractor_ready fail` event on timeout |
| `load_user_extractors(engine=youtube_dl)` default arg | depended on `youtube_dl` being loaded at module import time | default arg retained for BC, but call-sites pass the loaded engine explicitly and the body early-returns when `config.sett_folder` is unresolved |

## Deprecated APIs still referenced (isolated behind adapter)

| Symbol | Where | Rationale for keeping |
| --- | --- | --- |
| `InfoExtractor._parse_m3u8_formats` (private) | `video.py :: pre_process_hls` | No public substitute; both `yt_dlp` and `youtube_dl` expose it. Tracked for future replacement when yt_dlp publishes a public HLS parser. |
| `youtube_dl.utils.random_user_agent` | `video.py :: load_extractor_engines (fallback)` | Only invoked inside the fallback load path; primary path uses yt_dlp's built-in UA rotation. Low churn. |
| `std_headers['Referer'] = ...` | `video.py :: get_ytdl_options` | Module-global in both extractor families; the only supported way to set a Referer before an `extract_info` call. Guarded with try/except + structured logging. |

## What is allowed going forward

- Import `yt_dlp` directly anywhere mainline code needs extraction.
- Access the active extractor via `ExtractorService.active_module()`.
- Access legacy `video.ytdl` — it mirrors the service and is kept for
  backwards-compat call sites.

## What is no longer allowed

- New `from youtube_dl import …` lines outside
  `firedm/video.py :: load_extractor_engines` and `load_user_extractors`.
- New references to `youtube_dl.extractor.*` symbols in the mainline path.
- Any code that assumes `config.active_video_extractor` is authoritative
  without going through `ExtractorService` or `choose_extractor_name`.

## Follow-up

- Remove `youtube_dl` from `pyproject.toml` once user-extractor plugin
  telemetry (if ever added) confirms nobody still ships `youtube_dl`-only
  plugins. Until then the package stays declared but unused in the default
  path.
- Teach `load_user_extractors` to accept plugins that declare the engine
  they subclass, so future plugins can target `yt_dlp` exclusively.
