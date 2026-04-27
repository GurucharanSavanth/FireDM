# 00 Discovery

Evidence labels: observed = local command/file output; changed = modified in this patch; verified = command passed; blocked = not run.

## Repository

- observed path: `G:\Personal Builds\Revive-FireDM\FireDM - Branch`
- observed branch: `features`
- observed last commit: `5abaa2f Finalize Windows x64 installer pipeline and release hygiene`
- observed remote: `origin https://github.com/GurucharanSavanth/FireDM.git`
- observed tags: none from `git tag --list`
- observed initial git diff: clean before this build-ID patch
- observed Python: `3.10.11`
- observed platform: `Windows-10-10.0.26200-SP0`, `win32`, `AMD64`
- observed local time during discovery: `2026-04-27T21:41:29.948423+05:30`

## Files Inspected

- `build-release.bat`
- `scripts/release/common.py`
- `scripts/release/build_windows.py`
- `scripts/release/build_payload.py`
- `scripts/release/build_installer.py`
- `scripts/release/generate_checksums.py`
- `scripts/release/collect_licenses.py`
- `scripts/release/validate_payload.py`
- `scripts/release/validate_installer.py`
- `.github/workflows/draft-release.yml`
- `README.md`
- `docs/windows-build.md`
- `docs/release/*.md`
- `pyproject.toml`
- `tests/`
- `tests/release/`
- `dist/release-manifest.json`
- `dist/checksums/SHA256SUMS.txt`

## Current Behavior Before Patch

- observed artifact naming used application version: `FireDM_Setup_2022.2.5_dev_win_x64.exe`, `FireDM_2022.2.5_win_x64_portable.zip`.
- observed manifest path was stable alias only: `dist/release-manifest.json`.
- observed checksum path was stable alias only: `dist/checksums/SHA256SUMS.txt`.
- observed workflow tag trigger was `v*`; manual workflow created a GitHub release directly.
- observed local `build-release.bat` passed only `--arch x64 --channel <channel>` to `build_windows.py`.

