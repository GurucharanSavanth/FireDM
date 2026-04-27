# 05 Validation Log

| Command | Exit | Summary |
| --- | ---: | --- |
| `.venv\Scripts\python.exe scripts\release\build_id.py --date 20260427 --print-next` before build | 0 | `20260427_V1` |
| `.venv\Scripts\python.exe scripts\release\build_id.py --build-id 20260427_V1 --validate` | 0 | `valid` |
| `.venv\Scripts\python.exe scripts\release\build_id.py --date 20260427 --print-next --json` | 0 | JSON contained build ID, tag, release name, discovered IDs, collision status |
| `cmd /c "set FIREDM_NO_PAUSE=1&& build-release.bat dev"` | 0 | built dev x64 artifact `20260427_V1`; payload and installer validation passed |
| `cmd /c "set FIREDM_NO_PAUSE=1&& build-release.bat --help"` | 0 | wrapper forwarded help without build |
| `cmd /c "set FIREDM_NO_PAUSE=1&& build-release.bat dev --help"` | 0 | wrapper channel/extra-arg forwarding worked |
| `.venv\Scripts\python.exe -m ruff check scripts\release tests\release` | 0 | `All checks passed!` |
| `.venv\Scripts\python.exe -m pytest -q tests\release\test_build_id.py tests\release\test_release_manifest_build_id.py tests\release\test_github_release_dry_run.py tests\release\test_workflow_build_id.py` | 0 | `24 passed in 1.02s` |
| `.venv\Scripts\python.exe -m compileall .\firedm .\scripts\release` | 0 | compile passed |
| `.venv\Scripts\python.exe -m pytest -q` | 0 | `193 passed in 7.72s` |
| `.venv\Scripts\python.exe scripts\release\build_id.py --date 20260427 --print-next` after build | 0 | `20260427_V2` |
| `.venv\Scripts\python.exe scripts\release\validate_payload.py --arch x64` | 0 | payload validation passed |
| `.venv\Scripts\python.exe scripts\release\validate_installer.py --artifact dist\installers\FireDM_Setup_20260427_V1_dev_win_x64.exe --test-repair --test-uninstall --test-upgrade --test-downgrade-block` | 0 | installer validation passed |
| `.venv\Scripts\python.exe scripts\release\github_release.py --manifest dist\release-manifest.json --dry-run` | 0 | dry-run printed build-ID release plan; no publish |
| PowerShell parser check for `scripts\windows-build.ps1` | 0 | `powershell parse ok` |
| `.venv\Scripts\python.exe -m pytest -q tests\release\test_workflow_build_id.py tests\release\test_release_manifest_build_id.py tests\release\test_build_id.py` | 0 | `19 passed in 0.74s` after adding PowerShell build-ID assertions |
| `.venv\Scripts\python.exe -m ruff check scripts\release tests\release` after PowerShell path update | 0 | `All checks passed!` |
| `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows-build.ps1 -SkipTests -SkipLint -SkipPythonPackage -SkipTwineCheck -BuildId 20260427_V9` | 0 | PyInstaller package built; packaged smoke checks passed; `dist\FireDM\build-metadata.json` recorded build ID `20260427_V9`, tag `build-20260427_V9`, and release name `FireDM 20260427_V9` |
| `.venv\Scripts\python.exe -m compileall .\scripts\release` after PowerShell path update | 0 | compile passed |
| `git diff --check` | 0 | clean after generated proof JSON drift was reverted |

## Generated Artifact Evidence

- verified installer: `dist\installers\FireDM_Setup_20260427_V1_dev_win_x64.exe`
- verified portable ZIP: `dist\portable\FireDM_20260427_V1_dev_win_x64_portable.zip`
- verified manifest: `dist\FireDM_release_manifest_20260427_V1.json`
- verified checksums: `dist\checksums\SHA256SUMS_20260427_V1.txt`
- verified license inventory: `dist\licenses\license-inventory_20260427_V1.json`
- verified signing state: unsigned dev artifact; stable release still requires signing.
