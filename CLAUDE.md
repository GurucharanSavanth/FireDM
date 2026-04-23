# FireDM Agent Memory

## Mission
Modernize FireDM into a maintainable, Windows-first desktop download manager without breaking core behavior. Work incrementally. Do not do a big-bang rewrite.

## Current State
- Windows bootstrap is complete and verified.
- Source build is working.
- Editable install is working.
- Packaged Windows build is working with PyInstaller.
- Core startup, settings-path, ffmpeg lookup, extractor loading, and updater policy now have explicit seams.
- Test suite exists and passes, but coverage is still focused on modernized seams and startup logic.

## Verified Baseline
- Host target: Windows 10/11 x64
- Verified Python: `3.10.11`
- Repo-local venv: `.\.venv`
- Preferred interpreter: `.\.venv\Scripts\python.exe`
- `pycurl`: verified via official Windows wheel `7.45.7`
- `yt-dlp`: verified `2026.3.17` with `yt-dlp-ejs 0.8.0`
- Deno: verified `2.7.13`
- `ffmpeg`: verified externally on Windows; Winget package fallback works when shell `PATH` is stale
- Source smoke passed:
  - `python -m firedm --help`
  - `python firedm.py --imports-only`
- Packaged smoke passed:
  - `dist\FireDM\firedm.exe --help`
  - `dist\FireDM\FireDM-GUI.exe` launches

## Do Not Re-Solve
Unless a new blocker appears, do not spend time again on:
- Python install
- pycurl Windows build pain
- ffmpeg install strategy
- editable install setup
- basic GUI/CLI bootstrap

Bootstrap work is already captured in:
- `bootstrap/windows-dev-setup.md`
- `bootstrap/environment-manifest.json`
- `docs/windows-bootstrap.md`
- `docs/windows-bootstrap-log.md`
- `docs/windows-bootstrap-manifest.json`

## Modernized Files And Seams
- `firedm/FireDM.py`
  - explicit stdio fallback
  - explicit GUI mode detection
  - import diagnostics helper
  - fixed `--show-settings`
- `firedm/app_paths.py`
  - global/local settings folder resolution
- `firedm/setting.py`
  - now delegates path selection
- `firedm/ffmpeg_service.py`
  - ffmpeg path resolution and version probing
- `firedm/tool_discovery.py`
  - app-dir, `PATH`, and Winget executable discovery
- `firedm/controller.py`
  - ffmpeg lookup uses service seam
  - packaged updater now routes to release-page flow
- `firedm/extractor_adapter.py`
  - extractor import/selection boundary
- `firedm/video.py`
  - extractor selection now goes through adapter seam
- `firedm/update.py`
  - packaged Windows builds no longer attempt unsafe in-place Python package patching
- `pyproject.toml`
  - primary packaging metadata
- `setup.py`
  - compatibility shim only
- `scripts/firedm-win.spec`
  - PyInstaller spec
- `scripts/windows-build.ps1`
  - Windows packaging script
- `bootstrap/bootstrap.ps1`
  - repo-local dev bootstrap

## Preferred Commands
Use these exact commands first:

```powershell
.\bootstrap\bootstrap.ps1
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check firedm\FireDM.py firedm\app_paths.py firedm\extractor_adapter.py firedm\ffmpeg_service.py firedm\tool_discovery.py firedm\setting.py firedm\update.py tests
.\.venv\Scripts\python.exe -m build
.\scripts\windows-build.ps1
```

## Packaging Decisions
- `pyproject.toml` is the primary build metadata.
- PyInstaller is the preferred Windows packager.
- cx_Freeze scripts remain only as historical reference.
- Packaged Windows builds are **release-replace**, not self-updating in place.
- `ffmpeg` and Deno are still external by default. Packaged app checks app paths, `PATH`, then Winget package dirs.

## Dependency Decisions
- Keep `pycurl`. Do not remove without proving download-engine parity.
- `yt-dlp[default]` is primary.
- `youtube_dl` stays only as optional legacy compatibility mode.
- Extractor logic should continue moving behind `extractor_adapter.py`.

## Current Test And Quality State
- Maintained runner: `pytest`
- Current passing count: run `pytest -q`; latest focused video regression suite passed with `63` tests.
- Current lint gate is intentionally narrow:
  - `firedm/FireDM.py`
  - `firedm/app_paths.py`
  - `firedm/extractor_adapter.py`
  - `firedm/ffmpeg_service.py`
  - `firedm/tool_discovery.py`
  - `firedm/setting.py`
  - `firedm/update.py`
  - `tests/`
- Full-repo Ruff is not ready yet because legacy bulk modules still have hundreds of issues.

## Important Docs To Read Before Deep Refactors
- `BASELINE_AUDIT.md`
- `docs/architecture.md`
- `docs/dependency-strategy.md`
- `docs/testing.md`
- `docs/windows-build.md`
- `docs/known-issues.md`

## High-Risk Legacy Hot Spots
- `firedm/controller.py`
- `firedm/video.py`
- `firedm/tkview.py`
- `firedm/utils.py`
- `firedm/brain.py`
- `firedm/worker.py`

These are still large, stateful, and side-effect-heavy. Refactor in small slices.

## Best Next Slices
1. Split `controller.py` into smaller services without changing public behavior.
2. Add mocked integration tests for controller/download lifecycle.
3. Refactor `video.py` further around extractor and ffmpeg command boundaries.
4. Add manual + mocked validation around real media post-processing.
5. Validate Python `3.11` end-to-end.
6. Decide whether Windows releases should bundle `ffmpeg` or continue external-only.

## Known Gotchas
- Agent shells may have stale `PATH`. If packaged or source checks say `ffmpeg` is missing, verify the real install path before changing code.
- Source runs prefer a local writable settings folder; fallback is `%APPDATA%\.FireDM`.
- GUI behavior is still only partially automated.
- Avoid expanding global mutable config state further.
- Avoid adding more direct extractor or pycurl sprawl into generic utility modules.

## Working Rules For Future Agents
- Keep changes incremental and test-backed.
- Preserve user-visible behavior unless change is required and documented.
- For every bug fix, add a focused regression test if a stable seam exists.
- If a change is manual-validation-only, say so explicitly.
- Prefer building on the new seams instead of deepening old ad hoc patterns.
