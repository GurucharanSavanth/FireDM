# 09 Validation Log

| Command | Exit | Summary |
| --- | ---: | --- |
| `.venv\Scripts\python.exe -m compileall .\scripts\release` | 0 | new/changed release scripts compile |
| `.venv\Scripts\python.exe scripts\release\check_dependencies.py --arch x64 --channel dev --skip-portable --json` | 0 | no required missing dependencies; sandbox warnings: FFmpeg/ffprobe/Deno |
| `.venv\Scripts\python.exe -m pytest -q tests\release\test_dependency_preflight.py tests\release\test_validate_portable.py tests\release\test_workflow_build_id.py` | 0 | `8 passed` |
| `.venv\Scripts\python.exe -m compileall .\firedm .\scripts` | 0 | source and scripts compile |
| `.venv\Scripts\python.exe -m pytest -q tests\test_packaged_diagnostics.py tests\release` | 0 | `48 passed`; smoke proof artifacts written to temp dirs |
| `.venv\Scripts\python.exe -m pytest -q` | 0 | `202 passed` |
| `.venv\Scripts\python.exe -m pip check` | 0 | no broken requirements |
| `.venv\Scripts\python.exe -m ruff check firedm\FireDM.py firedm\app_paths.py firedm\extractor_adapter.py firedm\ffmpeg_service.py firedm\tool_discovery.py firedm\setting.py firedm\update.py scripts\release scripts\verify_extractor_default.py scripts\smoke_video_pipeline.py tests` | 0 | lint passed |
| `powershell -ExecutionPolicy Bypass -File .\scripts\windows-build.ps1 -Channel dev -Arch x64 -ValidateOnly` | 0 | preflight, compileall, pytest, and Ruff passed |
| `powershell -ExecutionPolicy Bypass -File .\scripts\windows-build.ps1 -Channel dev -Arch x64 -BuildId 20260428_V2 -AllowOverwrite -SkipTests -SkipLint` | 0 | x64 build, payload, portable ZIP, installer, installer validation, Deno/FFmpeg preflight, checksums, and manifest passed in elevated maintainer-equivalent shell |
| `.venv\Scripts\python.exe scripts\release\validate_payload.py --arch x64` | 0 | payload validation passed |
| `.venv\Scripts\python.exe scripts\release\validate_portable.py --archive .\dist\portable\FireDM_20260428_V2_dev_win_x64_portable.zip` | 0 | portable validation passed with optional FFmpeg/ffprobe warnings |
| `.venv\Scripts\python.exe scripts\release\validate_installer.py --artifact .\dist\installers\FireDM_Setup_20260428_V2_dev_win_x64\FireDM_Setup_20260428_V2_dev_win_x64.exe --test-repair --test-uninstall --test-upgrade --test-downgrade-block` | 0 | installer validation passed in elevated maintainer-equivalent shell |
| `.venv\Scripts\python.exe scripts\release\github_release.py --manifest .\dist\release-manifest.json --dry-run` | 0 | dry-run only; no release created |
| `git diff --check` | 0 | no whitespace or line-ending errors |

blocked/local-only:
- Installer registry validation fails in the sandbox with `PermissionError: [WinError 5] Access is denied` on HKCU uninstall key creation. The same validation passed outside sandbox.
- Remote GitHub Actions were not run.
- Live HTTP/video/FFmpeg post-processing QA was not run.
