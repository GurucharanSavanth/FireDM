# Testing

## Automated suite
FireDM now uses `pytest` for the maintained test path.

Run the full suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Quality checks

```powershell
.\.venv\Scripts\python.exe -m ruff check firedm\FireDM.py firedm\app_paths.py firedm\extractor_adapter.py firedm\ffmpeg_service.py firedm\tool_discovery.py firedm\setting.py firedm\update.py tests
.\.venv\Scripts\python.exe -m build --no-isolation
```

## Current automated coverage focus
- CLI argument parsing and startup smoke
- GUI routing without importing or launching the real Tk window
- settings-path resolution
- ffmpeg lookup/version parsing
- missing-ffmpeg help handoff
- extractor selection/loading seam
- updater policy regression checks
- archive extraction traversal protection

## Manual validation checklist
- launch GUI from source and confirm the main window appears
- confirm `setting.cfg` is created in the expected source checkout folder
- run a small HTTP file download
- run a single-video `yt_dlp` metadata fetch
- run a playlist URL and confirm playlist menu/download handoff
- verify ffmpeg post-processing on a DASH/HLS media download
- temporarily hide ffmpeg and verify missing-tool reporting opens guidance
- verify packaged `FireDM-GUI.exe` starts on Windows

## Python version policy

Automated validation currently supports Python 3.10 only. Python 3.11 and
3.12 must run the full test suite, import smoke, wheel/sdist build, and
Windows PyInstaller build before metadata or CI advertises them as supported.

## Test design rules
- no real network access in automated tests
- no real ffmpeg execution when a mocked subprocess is sufficient
- add a regression test for every confirmed bug fix when a stable boundary exists
- document manual-only coverage when GUI or binary coupling prevents reliable automation
- Ruff currently gates the modernized startup/settings/extractor/ffmpeg/update seam plus tests. Large untouched legacy modules remain outside automated lint until they are refactored.
