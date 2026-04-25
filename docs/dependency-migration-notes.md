# Dependency Migration Notes

## Video Extractor Stack

Old default path: `youtube_dl` and `yt_dlp` both installed, with legacy global state able to select either.

New default path: `yt-dlp[default]>=2026.3.17` is the primary dependency. The `default` extra brings the current optional packages required by modern YouTube support, including `yt-dlp-ejs`. Deno is discovered as an external runtime and passed to yt-dlp through `js_runtimes`.

Migration cost:

- `requirements.txt` removed default `youtube_dl`.
- `pyproject.toml` changed from `yt_dlp>=2024.12.0` to `yt-dlp[default]>=2026.3.17`.
- `scripts/firedm-win.spec` now collects `yt_dlp_ejs` data files.
- `firedm/video.py` now passes `js_runtimes` and `ffmpeg_location` to yt-dlp.

Compatibility:

- `youtube_dl` remains available only via `pip install -e .[legacy]`.
- Legacy fallback is still tested but never selected while `yt_dlp` is available.

## External Binaries

FFmpeg and Deno are external by policy. FireDM now detects binaries on `PATH`, explicit app paths, and Windows Winget package directories. This avoids mutating global PATH and makes agent/CI shells more reliable.

## Tooling

The project keeps `pip` + venv as the supported bootstrap. `uv` remains optional/deferred because the current bootstrap is already validated and changing env management would add process risk during P0 recovery.
