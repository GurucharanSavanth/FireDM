# Release Checklist

## Build

```powershell
.\.venv\Scripts\python.exe -m compileall .\firedm .\scripts\release
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\release\build_windows.py --arch x64 --channel dev
```

## Validate

```powershell
.\.venv\Scripts\python.exe scripts\release\validate_payload.py --arch x64
.\.venv\Scripts\python.exe scripts\release\validate_installer.py --artifact dist\installers\FireDM_Setup_<version>_dev_win_x64.exe --test-repair --test-uninstall --test-upgrade --test-downgrade-block
.\.venv\Scripts\python.exe scripts\release\smoke_installed_gui.py --install-root dist\payloads\win-x64\FireDM --timeout 20 --headless-safe --no-network
```

## Manual Checks

- Start installed GUI.
- Validate direct download queue/progress/cancel/resume.
- Validate one safe video URL and one playlist URL.
- Validate ffmpeg-required media only if FFmpeg is available.
- Confirm uninstall preserves user data by default.
- Confirm no global PATH entries were added.

## Release Artifacts

- `dist\installers\FireDM_Setup_<version>_dev_win_x64.exe`
- `dist\portable\FireDM_<version>_win_x64_portable.zip`
- `dist\release-manifest.json`
- `dist\checksums\SHA256SUMS.txt`
- `dist\licenses\license-inventory.json`

Signing:
- dev builds may be unsigned
- public stable builds must be signed with `FIREDM_SIGNTOOL` and certificate environment variables
- do not publish if signing is required but `build_installer.py` reports unsigned output

Blocked until future lanes exist:
- universal bootstrapper
- x86 payload
- ARM64 payload
- MSI packages
- MSIX packages
- signed artifacts
