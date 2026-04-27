# 00 Baseline

Evidence labels: observed = local file/command output; inferred = local-code reasoning.

## Repo State
- observed repo path: `G:\Personal Builds\Revive-FireDM\FireDM - Branch`
- observed branch: `main`
- observed status: `## main...origin/main`
- observed dirty tracked files before this pass: `.gitignore`, `artifacts/extractor/default_selection_proof.json`, `artifacts/smoke/playlist_result.json`, `artifacts/smoke/single_video_result.json`, `firedm/brain.py`, `firedm/config.py`, `firedm/controller.py`, `firedm/setting.py`, `firedm/tkview.py`, `firedm/worker.py`, `pyproject.toml`, `scripts/firedm-win.spec`
- observed untracked files before this pass: `firedm/native_host.py`, `firedm/plugins/`, `tests/test_browser_integration.py`, `tests/test_drm_clearkey.py`, `tests/test_plugins.py`
- observed last commit: `836a54d _`
- observed remote: `origin https://github.com/GurucharanSavanth/FireDM.git`

## Runtime
- observed OS/runtime: `Windows-10-10.0.26200-SP0`, `win32`, `AMD64`
- observed shell: Windows PowerShell `5.1.26100.8115`
- observed `python --version`: `Python 3.10.11`
- observed repo venv: `.\.venv\Scripts\python.exe` exists and reports `Python 3.10.11`

## Package Layout
- observed source package: `firedm`
- observed entry files: `firedm.py`, `firedm/__main__.py`, `firedm/FireDM.py`
- observed plugin package: `firedm/plugins`
- observed tests: `tests/`, 151 collected tests
- observed packaging: `pyproject.toml`, `setup.py` shim, `scripts/firedm-win.spec`, `scripts/windows-build.ps1`, GitHub Actions workflows

## Validation Commands Detected
- observed docs/AGENTS commands: `.\.venv\Scripts\python.exe -m pytest -q`
- observed scoped lint command: `.\.venv\Scripts\python.exe -m ruff check firedm\FireDM.py firedm\app_paths.py firedm\extractor_adapter.py firedm\ffmpeg_service.py firedm\tool_discovery.py firedm\setting.py firedm\update.py tests`
- observed source smoke: `.\.venv\Scripts\python.exe -m firedm --help`
- observed import smoke: `.\.venv\Scripts\python.exe firedm.py --imports-only`
- observed build command: `.\.venv\Scripts\python.exe -m build --no-isolation`
- observed Windows package command: `powershell -ExecutionPolicy Bypass -File .\scripts\windows-build.ps1`

## Docs/Configs Read
- observed: `README.md`, `AGENTS.md`, `pyproject.toml`, `setup.py`, `docs/architecture.md`, `docs/testing.md`, `docs/windows-build.md`, `bootstrap/environment-manifest.json`, `scripts/firedm-win.spec`
- observed hot-path files read: `firedm/controller.py`, `firedm/native_host.py`, `firedm/plugins/*.py`, `firedm/worker.py`, `firedm/brain.py`, `firedm/config.py`, `firedm/setting.py`, `firedm/downloaditem.py`, `firedm/model.py`, `tests/test_browser_integration.py`, `tests/test_drm_clearkey.py`, `tests/test_plugins.py`

## Initial Warnings/Errors
- observed `git diff --stat` emitted CRLF warnings for three artifact JSON files.
- observed full baseline pytest: `1 failed, 150 passed`; failure is `ModuleNotFoundError: No module named 'cryptography'` in `tests/test_drm_clearkey.py::test_dash_segment_decrypt`.
- observed reviewer P1/P2 items align with local code: native manifest points at `sys.executable`, controller starts local endpoint by default, Windows named pipe code opens as client, magnet path returns True without plugin queue/completion flags.

## Discovery Limits
- observed GUI, real browser native messaging, real downloads, live extractor-network behavior, and PyInstaller package build were not executed during baseline discovery.
- inferred Linux behavior from files only; current host is Windows.
