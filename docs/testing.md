# Testing

## Automated suite
FireDM now uses `pytest` for the maintained test path.

Run the full suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Quality checks

```powershell
.\.venv\Scripts\python.exe -m ruff check firedm\FireDM.py firedm\app_paths.py firedm\extractor_adapter.py firedm\ffmpeg_service.py firedm\setting.py firedm\update.py tests
.\.venv\Scripts\python.exe -m build
```

## Current automated coverage focus
- CLI argument parsing and startup smoke
- settings-path resolution
- ffmpeg lookup/version parsing
- extractor selection/loading seam
- updater policy regression checks

## Manual validation checklist
- launch GUI from source and confirm the main window appears
- confirm `setting.cfg` is created in the expected source checkout folder
- run a small HTTP file download
- run a `yt_dlp`-backed media metadata fetch
- verify ffmpeg post-processing on a media download
- verify packaged `FireDM-GUI.exe` starts on Windows

## Test design rules
- no real network access in automated tests
- no real ffmpeg execution when a mocked subprocess is sufficient
- add a regression test for every confirmed bug fix when a stable boundary exists
- document manual-only coverage when GUI or binary coupling prevents reliable automation
- Ruff currently gates the modernized startup/settings/extractor/ffmpeg/update seam plus tests. Large untouched legacy modules remain outside automated lint until they are refactored.
