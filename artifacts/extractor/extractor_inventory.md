# Extractor Inventory

| Item | Version | Mainline? | Notes |
| --- | --- | --- | --- |
| `yt_dlp` | `2026.03.17` | Yes | Primary extractor, selected by `ExtractorService` |
| `yt-dlp-ejs` | `0.8.0` | Yes | Installed through `yt-dlp[default]` for YouTube JS challenge support |
| Deno | `2.7.13` | Yes | External JS runtime; discovered from Winget package dir |
| `youtube_dl` | `2021.12.17` | No | Deprecated optional compatibility fallback only |
| ffmpeg | `8.1-essentials_build-www.gyan.dev` | Yes | External binary; passed to yt-dlp via `ffmpeg_location` |

Mainline rule: no request should use `youtube_dl` when `yt_dlp` is importable.
