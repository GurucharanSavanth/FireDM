# Repository Guidelines

## Maintainer Init
Use this file as `/init` state for continuing FireDM modernization. Bootstrap is complete. Do not spend more time re-solving environment setup unless a new blocker appears.

## Known-Good Windows Baseline
- Primary host: Windows 10/11 x64
- Verified Python: `3.10.11`
- Verified source env: repo-local `.venv`
- Verified transport: `pycurl 7.45.7` official Windows wheel
- Verified extractor: `yt-dlp 2026.3.17` with `yt-dlp-ejs 0.8.0`
- Verified JS runtime: `Deno 2.7.13`
- Verified external binary: `ffmpeg 8.1` on Windows; Winget fallback works when shell `PATH` is stale
- Verified source smoke: `python -m firedm --help`, `python firedm.py --imports-only`
- Verified packaged smoke: `dist\FireDM\firedm.exe --help`, `FireDM-GUI.exe` launches

## Preferred Commands
- Bootstrap dev env: `powershell -ExecutionPolicy Bypass -File .\bootstrap\bootstrap.ps1`
- Run tests: `.\.venv\Scripts\python.exe -m pytest -q`
- Lint modernized seam: `.\.venv\Scripts\python.exe -m ruff check firedm\FireDM.py firedm\app_paths.py firedm\extractor_adapter.py firedm\ffmpeg_service.py firedm\tool_discovery.py firedm\setting.py firedm\update.py tests`
- Build wheel/sdist: `.\.venv\Scripts\python.exe -m build`
- Build Windows package: `powershell -ExecutionPolicy Bypass -File .\scripts\windows-build.ps1`

## Packaging State
- Packaging is now driven by `pyproject.toml`; `setup.py` is a compatibility shim only.
- Preferred Windows distributor is PyInstaller via `scripts/firedm-win.spec`.
- Legacy `scripts/exe_build/*` and AppImage scripts remain historical reference, not preferred release paths.
- Packaged Windows builds are release-replace, not in-place self-updating.

## Modernized Seams
- `firedm/app_paths.py`: settings path resolution
- `firedm/ffmpeg_service.py`: ffmpeg lookup/version probing
- `firedm/tool_discovery.py`: app-dir/PATH/Winget executable discovery
- `firedm/extractor_adapter.py`: extractor loading/selection
- `firedm/FireDM.py`: startup helpers, GUI mode detection, import diagnostics
- `firedm/update.py`: packaged Windows updater policy guard

## Dependency Policy
- Keep `pycurl`; do not remove without proving transport parity.
- Treat `yt-dlp[default]` as primary extractor dependency.
- Keep `youtube_dl` only as optional legacy compatibility mode.
- `ffmpeg` and Deno are external by default; discovery checks app paths, `PATH`, then Winget package dirs.

## Current Quality Gates
- `pytest` is the maintained test runner.
- Full-repo Ruff is not enabled yet; only the modernized seam is lint-gated.
- Manual validation is still required for GUI flows, real downloads, extractor-network behavior, and ffmpeg post-processing.

## Important Docs
- `BASELINE_AUDIT.md`
- `bootstrap/windows-dev-setup.md`
- `bootstrap/environment-manifest.json`
- `docs/architecture.md`
- `docs/dependency-strategy.md`
- `docs/testing.md`
- `docs/windows-build.md`
- `docs/known-issues.md`

## High-Value Next Work
- Split `controller.py` into smaller services without breaking behavior.
- Add mocked integration tests for controller/download lifecycle and extractor behavior.
- Refactor `video.py` further around extractor and ffmpeg boundaries.
- Validate Python `3.11` end-to-end.
- Decide whether to bundle `ffmpeg` in Windows releases or keep external-only.

## Gotchas
- Agent shells may have stale `PATH`; if `ffmpeg` is "missing" in automation, verify the actual install path before changing code.
- Source runs prefer a local writable settings folder; global fallback is `%APPDATA%\.FireDM`.
- `tkview.py`, `controller.py`, and `video.py` are still large legacy hot spots; avoid big-bang rewrites.
