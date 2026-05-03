# Troubleshooting

Status: changed 2026-05-02.

## Current Checks
- observed: Existing diagnostics and release validation scripts live under `scripts/` and `scripts/release/`.
- observed: `ffmpeg_service.py` and `tool_discovery.py` already isolate some external tool checks.

## Planned Doctor Output
- planned: Python/runtime, config path, portable mode, ffmpeg, ffprobe, aria2c, yt-dlp, extractor, update source, and engine health.
- planned: Copyable diagnostics bundle with redacted headers, cookies, tokens, proxy passwords, and signed URLs.
- blocked: Doctor command and health panel are not implemented yet.
