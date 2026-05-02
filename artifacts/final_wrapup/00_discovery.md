# Phase 0 Discovery

Evidence labels: observed = command/file output; changed = local patch; verified = command passed; blocked = not run or unavailable.

## Repository State

- observed path: `G:\Personal Builds\Revive-FireDM\FireDM - Branch`
- observed branch: `features`
- observed last commit: `c6ba615 New Test Features implementation`
- observed remote: `origin https://github.com/GurucharanSavanth/FireDM.git`
- observed shell: PowerShell
- observed Python: `Python 3.10.11`
- observed platform: `Windows-10-10.0.26200-SP0`, `win32`, `AMD64`

## Dirty Tree Summary

- observed modified source/hygiene files: `.gitattributes`, `.gitignore`, `.github/workflows/draft-release.yml`, `README.md`, `build-release.bat`, `docs/windows-build.md`, `firedm/tool_discovery.py`, `tests/test_ffmpeg_service.py`
- observed deleted tracked generated outputs: `artifacts/full_codebase_repair/pyinstaller-build/**`, `artifacts/full_codebase_repair/pyinstaller-dist/**`
- observed untracked source/evidence trees: `artifacts/final_wrapup/`, `artifacts/windows_installer/`, `artifacts/windows_installer_phase2/`, `docs/release/`, `scripts/release/`, `tests/release/`
- observed generated build outputs present and ignored: `dist/**`
- changed generated proof JSON timestamp drift was reverted after the final build command.

## Validation Command Candidates

- `.venv\Scripts\python.exe -m compileall .\firedm .\scripts\release`
- `.venv\Scripts\python.exe -m pytest -q`
- `cmd /c "set FIREDM_NO_PAUSE=1&& build-release.bat dev"`
- `.venv\Scripts\python.exe scripts\release\validate_payload.py --arch x64`
- `.venv\Scripts\python.exe scripts\release\validate_installer.py --artifact dist\installers\FireDM_Setup_2022.2.5_dev_win_x64.exe --test-repair --test-uninstall --test-upgrade --test-downgrade-block`
- `.venv\Scripts\python.exe scripts\release\smoke_installed_app.py --install-root dist\payloads\win-x64\FireDM`
- `.venv\Scripts\python.exe scripts\release\smoke_installed_gui.py --install-root dist\payloads\win-x64\FireDM --timeout 20 --headless-safe --no-network`
- `git diff --check`

