# Release Checklist

## Build

```powershell
.\.venv\Scripts\python.exe -m compileall .\firedm .\scripts\release
.\.venv\Scripts\python.exe scripts\release\check_dependencies.py --arch x64 --channel dev --skip-portable
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\release\build_windows.py --arch x64 --channel dev
```

## Validate

```powershell
.\.venv\Scripts\python.exe scripts\release\validate_payload.py --arch x64
.\.venv\Scripts\python.exe scripts\release\validate_portable.py --archive dist\portable\FireDM_<build_id>_dev_win_x64_portable.zip
.\.venv\Scripts\python.exe scripts\release\validate_installer.py --artifact dist\installers\FireDM_Setup_<build_id>_dev_win_x64.exe --test-repair --test-uninstall --test-upgrade --test-downgrade-block
.\.venv\Scripts\python.exe scripts\release\smoke_installed_gui.py --install-root dist\payloads\win-x64\FireDM --timeout 20 --headless-safe --no-network
```

## Manual Checks

- Start installed GUI.
- Validate direct download queue/progress/cancel/resume.
- Validate one safe video URL and one playlist URL.
- Validate ffmpeg-required media only if FFmpeg is available.
- Confirm uninstall preserves user data by default.
- Confirm no global PATH entries were added.

## Linux Build (Linux host or WSL only)

```bash
bash scripts/linux-build.sh --channel dev --arch x64
python scripts/release/build_linux.py --arch x64 --channel dev --build-id <build_code>
python scripts/release/validate_linux_payload.py --arch x64
python scripts/release/validate_linux_portable.py --archive dist/portable-linux/FireDM_<build_code>_dev_linux_x64.tar.gz
```

`scripts/linux-build.sh` refuses to run on non-Linux hosts (PyInstaller cannot
cross-compile). Use the GitHub Actions `build-linux` job from a Windows
workstation.

## Cross-platform manifest merge

Once both Windows and Linux per-platform manifests exist:

```bash
python scripts/release/merge_release_manifest.py \
    --build-id <build_code> \
    --windows-manifest dist/FireDM_release_manifest_<build_code>_windows.json \
    --linux-manifest dist/FireDM_release_manifest_<build_code>_linux.json \
    --output dist/FireDM_release_manifest_<build_code>.json
python scripts/release/generate_checksums.py --build-id <build_code>
```

The cross-platform release pipeline in `.github/workflows/draft-release.yml`
runs both build jobs followed by a `release` job that performs the merge,
checksum regeneration, and the dry-run/publish step automatically.

## Release Artifacts

Windows lane:

- `dist\installers\FireDM_Setup_<build_code>_dev_win_x64\FireDM_Setup_<build_code>_dev_win_x64.exe`
- `dist\installers\FireDM_Setup_<build_code>_dev_win_x64\FireDM_<build_code>_dev_win_x64_payload.zip`
- `dist\portable\FireDM_<build_code>_dev_win_x64_portable.zip`
- `dist\FireDM_release_manifest_<build_code>_windows.json`

Linux lane:

- `dist/portable-linux/FireDM_<build_code>_dev_linux_x64.tar.gz`
- `dist/payloads-linux/linux-x64/payload-manifest.json`
- `dist/FireDM_release_manifest_<build_code>_linux.json`

Cross-platform:

- `dist\FireDM_release_manifest_<build_code>.json` (merged)
- `dist\dependency-status_<build_code>.json`
- `dist\checksums\SHA256SUMS_<build_code>.txt`
- `dist\licenses\license-inventory_<build_code>.json`
- `dist\FireDM_release_notes_<build_code>.md`

Dry-run GitHub release before publishing:

```powershell
.\.venv\Scripts\python.exe scripts\release\github_release.py --manifest dist\release-manifest.json
```

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
- AppImage / .deb / .rpm
- signed artifacts
