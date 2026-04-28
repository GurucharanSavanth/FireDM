# Phase 9 Validation Log

| Command | Exit | Output Summary | Classification |
| --- | ---: | --- | --- |
| `.venv\Scripts\python.exe -m compileall .\firedm .\scripts\release` | 0 | compiled `firedm`, plugins, and release scripts | verified |
| `.venv\Scripts\python.exe -m pytest -q` | 0 | `169 passed in 6.75s` | verified |
| `.venv\Scripts\python.exe -m ruff check firedm\FireDM.py firedm\app_paths.py firedm\extractor_adapter.py firedm\ffmpeg_service.py firedm\tool_discovery.py firedm\setting.py firedm\update.py tests` | 0 | `All checks passed!` | verified |
| `.venv\Scripts\python.exe -m ruff check scripts\release` | 0 | `All checks passed!` | verified |
| `.venv\Scripts\python.exe -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('.github/workflows/draft-release.yml').read_text()); print('yaml ok')"` | 0 | `yaml ok` | verified |
| `cmd /c "set FIREDM_NO_PAUSE=1&& build-release.bat dev"` | 0 | x64 dev installer lane completed; installer validation passed; release ready line printed for dev artifact | verified |
| `.venv\Scripts\python.exe scripts\release\validate_payload.py --arch x64` | 0 | payload validation passed for `dist\payloads\win-x64\FireDM` | verified |
| `.venv\Scripts\python.exe scripts\release\validate_installer.py --artifact dist\installers\FireDM_Setup_2022.2.5_dev_win_x64.exe --test-repair --test-uninstall --test-upgrade --test-downgrade-block` | 0 | install, help, imports, upgrade, repair, downgrade block, uninstall passed | verified |
| `.venv\Scripts\python.exe scripts\release\smoke_installed_app.py --install-root dist\payloads\win-x64\FireDM` | 0 | installed app smoke passed | verified |
| `.venv\Scripts\python.exe scripts\release\smoke_installed_gui.py --install-root dist\payloads\win-x64\FireDM --timeout 20 --headless-safe --no-network` | 0 | `classification=started_timeout_terminated` | verified startup smoke only |
| `.venv\Scripts\python.exe scripts\release\build_windows.py --arch x86 --channel dev` | 1 | unsupported arch `x86`; supported `x64` | verified expected block |
| `.venv\Scripts\python.exe scripts\release\build_windows.py --arch arm64 --channel dev` | 1 | unsupported arch `arm64`; supported `x64` | verified expected block |
| `git diff --check` | 0 | no whitespace or line-ending errors after reverting generated proof JSON drift | verified |

## Build Warnings

- observed: PyInstaller emitted optional collection warnings for `urllib3.contrib.emscripten` and `curl_cffi`; build exit remained 0.
- observed: pip update notice appeared; not release-blocking.

## Generated Dev Artifacts

- observed installer: `dist\installers\FireDM_Setup_2022.2.5_dev_win_x64.exe`
- observed portable ZIP: `dist\portable\FireDM_2022.2.5_win_x64_portable.zip`
- observed manifest channel: `dev`
- observed installer sha256: `b7b3b09f4545f2d44ca930ec05ea04f185e9d8d5d9e7debf00b94a4b89d8f8a0`
- observed portable sha256: `9a1fee8bcfd23549e463d86f5cfb4372377a3da4a446e4e3180c3c792bd63f55`
- observed signing: `unsigned: FIREDM_SIGNTOOL not configured`

