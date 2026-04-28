# 00 Discovery

observed path: `G:\Personal Builds\Revive-FireDM\FireDM - Branch`

observed branch: `features`

observed last commit: `182d70c Finalize Windows x64 installer pipeline and release hygiene`

observed dirty files before this pass:
- `artifacts/extractor/default_selection_proof.json`
- `artifacts/smoke/playlist_result.json`
- `artifacts/smoke/single_video_result.json`

observed Python: `3.10.11`, 64-bit, `win32`, `AMD64`, Windows `10.0.26200`.

observed dependency declarations:
- `pyproject.toml`
- `requirements.txt`
- optional extras in `pyproject.toml`

observed build/release scripts:
- `scripts/windows-build.ps1`
- `build-release.bat`
- `scripts/release/build_windows.py`
- `scripts/release/build_payload.py`
- `scripts/release/build_installer.py`
- `scripts/release/generate_checksums.py`
- `scripts/release/collect_licenses.py`
- `scripts/release/github_release.py`
- `scripts/release/validate_payload.py`
- `scripts/release/validate_installer.py`

changed scripts added:
- `scripts/release/check_dependencies.py`
- `scripts/release/validate_portable.py`

observed workflow files:
- `.github/workflows/draft-release.yml`
- `.github/workflows/windows-smoke.yml`
- `.github/workflows/pypi-release.yml`

observed build risks:
- FFmpeg/ffprobe not on PATH in current shell.
- x86/ARM64/MSI/MSIX remain blocked.
- stable public release remains blocked by signing and remote workflow/manual QA.
