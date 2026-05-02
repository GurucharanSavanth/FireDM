# Phase 5 Release Scripts Review

## Files Reviewed

- `scripts/release/common.py`
- `scripts/release/build_windows.py`
- `scripts/release/build_payload.py`
- `scripts/release/build_installer.py`
- `scripts/release/installer_bootstrap.py`
- `scripts/release/validate_payload.py`
- `scripts/release/validate_installer.py`
- `scripts/release/smoke_installed_app.py`
- `scripts/release/smoke_installed_gui.py`
- `scripts/release/generate_checksums.py`
- `scripts/release/collect_licenses.py`
- `build-release.bat`

## Fixes

- changed: build wrapper defaults to unsigned `dev`, supports `FIREDM_NO_PAUSE=1`, and fails cleanly if no usable Python exists.
- changed: release manifests and installer sidecar metadata use relative dist paths instead of user-specific absolute paths.
- changed: checksum generation now covers publishable release assets only.
- changed: license inventory no longer records local Python executable paths.
- changed: validation temp cleanup refuses unsafe roots and only removes expected installer-validation temp roots.
- changed: script style/import issues were fixed and release scripts pass scoped Ruff.
- changed: unsupported `x86` and `arm64` build requests fail explicitly.

## Validation

- verified: `cmd /c "set FIREDM_NO_PAUSE=1&& build-release.bat dev"` exited 0.
- verified: `.venv\Scripts\python.exe -m ruff check scripts\release` exited 0.

