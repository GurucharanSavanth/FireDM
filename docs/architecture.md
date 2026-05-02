# Architecture Overview

## Runtime shape
FireDM still has two entry surfaces:
- `python -m firedm` / `firedm` for CLI mode
- `python firedm.py` or packaged `FireDM-GUI.exe` for GUI-first startup

Startup lives in `firedm/FireDM.py`. GUI/CLI selection is argument-driven and now has explicit helpers for stdio fallback, mode detection, and import diagnostics.

## Core subsystems
- `firedm/controller.py`: high-level orchestration, view coordination, queue management, update checks, and download lifecycle entrypoints.
- `firedm/brain.py` + `firedm/worker.py`: segmented download pipeline and worker threads.
- `firedm/video.py`: extractor-facing media logic, stream preparation, subtitles, and ffmpeg-driven post-processing.
- `firedm/setting.py`: persisted settings and download-list storage.
- `firedm/config.py`: legacy global state. Retained for compatibility, but new seams should avoid adding more mutable globals.

## Modernized service seams
- `firedm/app_paths.py`: platform-aware settings-folder selection.
- `firedm/ffmpeg_service.py`: ffmpeg lookup and version probing.
- `firedm/extractor_adapter.py`: extractor import/selection boundary with `yt_dlp` as the preferred engine.

## Packaging strategy
Source installs use `pyproject.toml` + setuptools. Windows distribution now targets PyInstaller rather than the legacy cx_Freeze scripts. Packaged builds are treated as immutable artifacts; in-place package patching is no longer the supported Windows update path.

## Near-term refactor direction
- keep controller behavior stable while splitting transport, extraction, and persistence concerns behind testable helpers
- reduce import-time side effects
- migrate critical state transitions toward explicit typed models instead of open-coded string checks
