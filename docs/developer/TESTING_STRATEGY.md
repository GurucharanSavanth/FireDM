# Testing Strategy

Status: changed 2026-05-02.

## Current Scope
- implemented: `tests/test_download_engines.py` covers registry/model behavior for the new seam.
- observed: Existing tests cover extractor, ffmpeg, browser handoff, plugin registry, release scripts, and security helpers.

## Required As Phases Advance
- planned: Internal engine adapter tests with mocked pycurl/segments.
- planned: aria2c missing/bad path/version/RPC/redaction/path tests.
- planned: yt-dlp missing fields/no formats/audio/video/merge/ffmpeg/redaction tests.
- planned: updater tests for no update, update available, prerelease ignored, wrong asset, checksum mismatch, interruption, rate limit, TLS failure, rollback, and cancel.
- planned: stress tests for many jobs, stalled network, retry storm, cancel while writing, and shutdown during active job.
