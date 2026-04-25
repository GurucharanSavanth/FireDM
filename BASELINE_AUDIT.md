# Baseline Audit

## Snapshot
- Repository: FireDM
- Baseline branch: `master`
- Baseline head: `88240da7f005c9a7a49a4e2d7f6928fd7fddf043`
- Working state already includes local Windows bootstrap docs and initial CLI smoke tests
- Primary verified host during audit: Windows 11 x64, Python 3.10.11 virtualenv

## Repository Structure
- `firedm/`: application runtime code
- `firedm/FireDM.py`: startup and CLI/GUI mode dispatch
- `firedm/controller.py`: main orchestration layer
- `firedm/brain.py`, `firedm/worker.py`, `firedm/downloaditem.py`: download pipeline
- `firedm/video.py`: extractor integration, HLS/DASH/ffmpeg post-processing
- `firedm/tkview.py`, `firedm/cmdview.py`, `firedm/view.py`: GUI and CLI views
- `firedm/config.py`, `firedm/setting.py`: global defaults and persistence
- `firedm/utils.py`: mixed transport, subprocess, logging, JSON, filesystem helpers
- `scripts/exe_build/`: legacy Windows cx_Freeze packaging
- `scripts/appimage/`: legacy Linux AppImage packaging
- `docs/`: developer/user docs and Windows bootstrap docs
- `tests/`: currently minimal CLI smoke coverage

## Entrypoints And Runtime Modes
- Root script: `firedm.py`
- Module entrypoint: `python -m firedm`
- Console entrypoint from package metadata: `firedm = firedm.FireDM:main`
- Runtime modes:
  - GUI by default when no args are passed
  - CLI mode when args are passed
  - interactive terminal mode via `--interactive`
  - import warmup mode via `--imports-only`

## Dependency Model
- Declared in `requirements.txt` and duplicated in `setup.py` / `dependency.py`
- Current runtime deps:
  - `plyer`
  - `certifi`
  - `youtube_dl`
  - `yt_dlp`
  - `pycurl`
  - `Pillow`
  - `pystray`
  - `awesometkinter`
  - `packaging`
  - `distro` on Linux
- Native/binary dependency:
  - `ffmpeg` required for DASH/HLS merge, conversions, metadata, subtitles
- `pycurl` is still a hard runtime dependency and is referenced directly in `utils.py`, `worker.py`, and `tkview.py`

## Packaging Assumptions
- Packaging is still legacy `setup.py`-only
- No `pyproject.toml`
- Python metadata still advertises only 3.6-3.8
- Windows frozen build assumes cx_Freeze and bundled `ffmpeg.exe`
- Linux release assumes AppImage with overlay update path
- Updater logic distinguishes frozen/AppImage/source runtime at execution time

## OS And Platform Assumptions
- Windows-first logic exists but is spread across modules
- Linux and macOS branches are embedded directly in runtime modules
- Key Windows assumptions:
  - `APPDATA`/Roaming settings location
  - `where ffmpeg`
  - hidden subprocess startup info
  - `stdout`/`stderr` dummy fallback for Win32 GUI builds
  - Win32 file timestamp update via `ctypes.windll`
- Key Linux assumptions:
  - `.config/FireDM`
  - `which ffmpeg`
  - AppIndicator and ibus handling
  - AppImage update folder

## ffmpeg Handling
- Primary detection currently in `controller.check_ffmpeg()`
- Search order:
  1. previously saved `config.ffmpeg_actual_path`
  2. app current directory
  3. global settings folder
  4. system `PATH`
- ffmpeg is invoked by string-built commands in `video.py` and `utils.run_command()`
- Windows bootstrap already verified detection on `PATH`
- Failure path is user-visible but not isolated behind a service boundary

## pycurl Handling
- `utils.py` owns general `pycurl` configuration and ad hoc request helpers
- `worker.py` uses persistent `pycurl.Curl()` instances directly
- transport behavior is not abstracted; `pycurl` leaks into generic helper layer
- multithreading safety partially depends on `pycurl.NOSIGNAL`
- near-term keep is viable, but transport boundary is missing

## Extractor Handling
- `video.py` imports both `youtube_dl` and `yt_dlp` asynchronously in background threads
- default extractor is `yt_dlp`
- extractor selection is held in global `config.active_video_extractor`
- direct extractor internals are used in several places:
  - `YoutubeDL.extract_info`
  - `process_ie_result`
  - direct patching/wrapping of urlopen / parser functions
- current model is functional but brittle across extractor updates

## Persistence Model
- `setting.py` chooses local writable repo/app folder before global settings folder
- persisted files:
  - `setting.cfg`
  - `downloads.dat`
  - `thumbnails.dat`
  - `user_themes.cfg`
- persistence is JSON-based
- configuration is still driven by mutable module globals in `config.py`
- imports of `setting.py` mutate `config.global_sett_folder` and `config.sett_folder`

## Concurrency Model
- Extensive thread-based concurrency, no centralized lifecycle abstraction
- Main background threads:
  - controller observer queue thread
  - download queue thread
  - scheduled downloads thread
  - completion watchdog thread
  - extractor preload threads
  - brain thread manager / file manager / progress reporter threads
  - worker threads per segment
- shared mutable state lives on `DownloadItem`/`ObservableDownloadItem`
- cancellation and shutdown rely on state polling and ad hoc flags
- daemon/non-daemon thread usage is inconsistent

## Current Test Baseline
- Current automated tests are minimal:
  - CLI parsing and `--show-settings`
  - module help smoke
- No pytest config yet
- No unit coverage for download pipeline, persistence, ffmpeg logic, updater, extractor adapter, or packaging

## Module Inventory And Refactor Classification

### Keep With Cleanup
- `firedm/__main__.py`
- `firedm/about.py`
- `firedm/view.py`
- `firedm/themes.py`
- `firedm/cmdview.py`

### Heavily Refactor
- `firedm/FireDM.py`
- `firedm/config.py`
- `firedm/setting.py`
- `firedm/utils.py`
- `firedm/controller.py`
- `firedm/video.py`
- `firedm/brain.py`
- `firedm/worker.py`
- `firedm/downloaditem.py`
- `firedm/update.py`

### Split Or Isolate Behind Service Boundary
- `firedm/controller.py`
  - ffmpeg verification
  - playlist/extractor orchestration
  - queue scheduling
  - persistence hooks
  - update checks
- `firedm/utils.py`
  - transport
  - subprocess
  - logging
  - JSON/filesystem helpers
- `firedm/video.py`
  - extractor adapter
  - ffmpeg post-processing
  - HLS/DASH parsing

### Deprecate Or Replace
- `scripts/exe_build/exe-fullbuild.py`
- `scripts/exe_build/exe-quickbuild.py`
- `scripts/appimage/*` for primary build path on Windows-first modernization
- `firedm/dependency.py` auto-installer flow as primary dependency strategy

## Debt Register

### Blocker
- No modern packaging metadata. Repo still depends on legacy `setup.py` metadata and outdated Python classifiers.
- Windows packaging strategy is legacy cx_Freeze-specific and unverified against modern Python.
- No transport boundary for `pycurl`; runtime-critical network logic is hard to unit test.
- `tkview.py` is ~5k lines and mixes GUI, settings, orchestration callbacks, and runtime diagnostics.
- `controller.py` is ~1.8k lines and mixes orchestration, ffmpeg checks, update flow, persistence triggers, and UI coordination.

### High
- Global mutable state in `config.py` is updated from many modules and at import time.
- `setting.py` mutates runtime globals during import and prefers writable local folder over stable app-data location.
- `video.py` depends on extractor internals and monkeypatch-style behavior; high upgrade fragility.
- Threading model has no formal lifecycle controller; multiple daemon threads risk abrupt shutdown and state races.
- `utils.py` mixes unrelated concerns and contains high `pycurl` and subprocess sprawl.
- Bare `except` usage is widespread in critical modules:
  - `tkview.py`: 29
  - `utils.py`: 14
  - `controller.py`: 9
  - `downloaditem.py`: 7
  - `brain.py`: 5
- Wildcard imports exist in runtime-critical modules:
  - `controller.py`
  - `tkview.py`

### Medium
- Duplicate dependency declarations across `requirements.txt`, `setup.py`, and `dependency.py`
- Source/update behavior still refers heavily to `youtube_dl` even though `yt_dlp` is default extractor
- Updater still includes self-modifying wheel extraction logic for frozen/AppImage layouts
- Logging is plain print-style callback fanout, not structured and hard to assert in tests
- Subprocess invocation frequently uses string-built commands and `shell=True` in build scripts
- Package docs and README still describe old Python/runtime assumptions

### Low
- Repeated legacy docstrings and stale branding text across modules
- Inconsistent naming (`pars_args`, `sett`, `d`, `vid`, etc.)
- Old compatibility comments for Python 3.6 and historical cx_Freeze quirks remain throughout code

## Baseline Decisions Required For Modernization
- Supported Python baseline should move to 3.11, with 3.10 kept as stabilization floor during migration
- `pycurl` should remain current engine, but be isolated behind a transport boundary
- `yt_dlp` should become primary supported extractor path
- `youtube_dl` should move toward optional legacy compatibility mode, not equal-status primary path
- Updater behavior should be reassessed; source self-update is low-value, frozen self-update needs hardening or deprecation
- cx_Freeze should be reevaluated against modern alternatives for Windows packaging

## Immediate Recommended Work Order
1. Add modern packaging metadata and supported Python policy
2. Introduce bootstrap/build/test docs and tracked bootstrap assets
3. Create test harness with pytest, smoke tests, and Windows CI
4. Extract platform/path settings service from `config.py` + `setting.py`
5. Extract subprocess + ffmpeg service from `utils.py` / `controller.py` / `video.py`
6. Add extractor adapter around `yt_dlp`/`youtube_dl`
7. Decompose controller and tighten download lifecycle boundaries
