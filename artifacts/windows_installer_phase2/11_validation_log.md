# 11 Validation Log

Evidence labels: verified, blocked.

| Command | Exit | Result |
| --- | ---: | --- |
| `pwd` | 0 | `G:\Personal Builds\Revive-FireDM\FireDM - Branch` |
| `git status --short --branch` | 0 | branch `features`, dirty working tree with first-pass and phase-2 changes |
| `git log -1 --oneline` | 0 | `c6ba615 New Test Features implementation` |
| `python --version` | 0 | `Python 3.10.11` |
| `python -c "import sys, platform; ..."` | 0 | Windows `10.0.26200`, `win32`, `AMD64` |
| `.venv\Scripts\python.exe -m compileall .\firedm .\scripts\release` | 0 | compileall succeeded |
| `.venv\Scripts\python.exe -m pytest -q tests\release tests\test_ffmpeg_service.py` | 0 | `34 passed` |
| `.venv\Scripts\python.exe scripts\release\build_windows.py --arch x64 --channel dev` | 0 | x64 lane built installer, validated installer, generated checksums |
| `cmd /c "set FIREDM_NO_PAUSE=1&& build-release.bat dev"` | 0 | one-click wrapper completed |
| `.venv\Scripts\python.exe scripts\release\validate_payload.py --arch x64` | 0 | payload validation passed |
| `.venv\Scripts\python.exe scripts\release\validate_installer.py --artifact .\dist\installers\FireDM_Setup_2022.2.5_dev_win_x64.exe --test-repair --test-uninstall --test-upgrade --test-downgrade-block` | 0 | installer validation passed |
| `.venv\Scripts\python.exe scripts\release\smoke_installed_app.py --install-root .\dist\payloads\win-x64\FireDM` | 0 | installed app smoke passed |
| `.venv\Scripts\python.exe scripts\release\smoke_installed_gui.py --install-root .\dist\payloads\win-x64\FireDM --timeout 20 --headless-safe --no-network` | 0 | `classification=started_timeout_terminated` |
| `.venv\Scripts\python.exe -m pytest -q` | 0 | `169 passed` |
| `.venv\Scripts\python.exe scripts\release\build_windows.py --arch x86 --channel dev` | 1 | blocked: unsupported arch, supported: x64 |
| `.venv\Scripts\python.exe scripts\release\build_windows.py --arch arm64 --channel dev` | 1 | blocked: unsupported arch, supported: x64 |
| `git diff --check` | 0 | no whitespace errors; line-ending warnings only |

## Remaining Validation Gaps
- blocked: GitHub Actions not run.
- blocked: live HTTP download, video download, and FFmpeg post-processing not run.
- blocked: real old-installer upgrade not run.
