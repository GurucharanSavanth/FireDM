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
