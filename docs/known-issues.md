# Known Issues And Deferred Work

## Still high-risk
- `firedm/controller.py`, `firedm/video.py`, and `firedm/tkview.py` remain large and responsibility-heavy.
- Download-state coordination still relies on mutable shared objects and legacy thread signaling.
- GUI behavior is only partially automated; critical GUI flows still need manual smoke validation.

## Packaging limitations
- Windows packages currently expect `ffmpeg` on `PATH` or copied beside the app.
- Packaged Windows builds do not support in-place self-update. Upgrade by replacing the distribution with a newer release.

## Python support status
- verified: Python `3.10.11` on Windows
- not yet locally verified in this modernization pass: Python `3.11`
- Python `3.12` should be treated as evaluation-only until a full install, test, and packaging run passes

## Extractor policy
- `yt_dlp` is primary
- `youtube_dl` is retained only for compatibility until its remaining value is re-evaluated with real download/regression coverage

## Deferred engineering work
- split controller orchestration into smaller services
- formalize download-state transitions with typed enums/models
- isolate `pycurl` transport more aggressively away from generic utility code
- add mocked integration tests for controller/download lifecycle and extractor adapter behavior
