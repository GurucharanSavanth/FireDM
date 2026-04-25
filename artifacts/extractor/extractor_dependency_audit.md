# Extractor Dependency Audit

Generated after extractor modernization refresh on 2026-04-23.

## Current Extractor Stack

| Package/tool | Version | Role | Policy |
| --- | --- | --- | --- |
| `yt_dlp` | `2026.03.17` | Primary extractor | Default/mainline |
| `yt-dlp-ejs` | `0.8.0` | YouTube JS challenge scripts | Required via `yt-dlp[default]` |
| Deno | `2.7.13` | External JS runtime | Recommended runtime; discovered from Winget |
| `youtube_dl` | `2021.12.17` | Legacy extractor | Optional fallback only |
| ffmpeg | `8.1-essentials_build-www.gyan.dev` | Media post-processing | External binary; passed to yt-dlp |

## Packaging Metadata

- `pyproject.toml`
  - `yt-dlp[default]>=2026.3.17`
  - `youtube_dl>=2021.12.17` only in optional extra `[legacy]`
- `requirements.txt`
  - default install includes `yt-dlp[default]`, not `youtube_dl`
- `scripts/firedm-win.spec`
  - collects `yt_dlp`, `yt_dlp_ejs` modules/data, and optional `youtube_dl`
    only when present

## Extractor API Surface

| Symbol | Caller | Status |
| --- | --- | --- |
| `ytdl.YoutubeDL(options)` | `firedm/video.py` | Public API retained |
| `ytdl.utils.std_headers` | Referer handling | Guarded legacy-compatible mutation |
| `youtube_dl.extractor.common.InfoExtractor._parse_m3u8_formats` | HLS refresh | Direct hardcode removed; active module used |
| `youtube_dl.utils.random_user_agent` | fallback load only | Deprecated fallback-only |
| `yt_dlp` `js_runtimes` option | `get_ytdl_options()` | Deno path passed explicitly |
| `yt_dlp` `ffmpeg_location` option | `get_ytdl_options()` | discovered ffmpeg passed explicitly |

## Evidence

- `artifacts/extractor/default_selection_proof.json`
- `artifacts/extractor/active_extractor_report.json`
- `artifacts/repro/repro_summary.json`
- `artifacts/diagnostics/runtime_snapshot.json`
