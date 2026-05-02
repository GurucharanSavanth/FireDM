# Phase 0 — Repository discovery (observed)

Date: 2026-04-28
Branch: `features`
Last commit: `d60194e Harden FireDM dependency preflight and portable validation`
Working tree: clean (env reminder of pending modifications was stale; `git status` reports no changes).
Remote: `origin git@.../GurucharanSavanth/FireDM.git` — fetch/push only.
Tags: none locally.
Python: 3.10.11 (CPython, MSC v.1929 64-bit AMD64).
Host: Windows 11 26200, MINGW64 bash.

## Existing canonical artefacts

- Product version source: `firedm/version.py` exposes `__version__ = '2022.2.5'`.
  - `pyproject.toml` reads it via `[tool.setuptools.dynamic] version = { attr = "firedm.version.__version__" }`.
  - `scripts/release/common.py::read_version()` execs the file. (observed)
- Build identifier: `scripts/release/build_id.py` already implements the `YYYYMMDD_VN` format with parse/validate/select/discover/tag/release-name helpers and CLI (`--print-next`, `--validate`, `--build-id`, `--date`, `--allow-overwrite`). (observed)
- Tag prefix: `build-` (constant `TAG_PREFIX`). Release-name format: `FireDM YYYYMMDD_VN`.
- Windows release scripts (all consume one build_id passed end-to-end):
  - `scripts/release/build_windows.py` — orchestrator
  - `scripts/release/build_payload.py` — invokes `windows-build.ps1 -PayloadOnly` then zips portable
  - `scripts/release/build_installer.py` — PyInstaller bootstrapper installer
  - `scripts/release/validate_payload.py`, `validate_portable.py`, `validate_installer.py`
  - `scripts/release/check_dependencies.py`, `collect_licenses.py`, `generate_checksums.py`, `github_release.py`
  - `scripts/release/installer_bootstrap.py`, `smoke_installed_*.py`
  - `scripts/release/common.py` — naming + metadata helpers
- Windows shell wrappers: `scripts/windows-build.ps1`, `build-release.bat`.
- PyInstaller spec: `scripts/firedm-win.spec` (Windows-only Tcl/Tk + tkinter handling).
- Existing legacy Linux helpers (NOT integrated, ruff-excluded): `scripts/appimage/`, `scripts/exe_build/`.
- GitHub Actions workflows:
  - `.github/workflows/draft-release.yml` (windows-latest only, manual + tag triggers)
  - `.github/workflows/windows-smoke.yml` (push/PR validation, windows-latest)
  - `.github/workflows/pypi-release.yml` (unrelated)
- Tests under `tests/release/`: build_id, dependency preflight, github release dry-run, installer bootstrap, manifest build_id, validate_portable, workflow_build_id.
- Docs under `docs/release/`: BUILD_ID_POLICY (referenced indirectly), DEPENDENCY_POLICY, FFMPEG_BUNDLING, GITHUB_RELEASES, RELEASE_CHECKLIST, THIRD_PARTY_BUNDLED_COMPONENTS, WINDOWS_INSTALLER, WINDOWS_PORTABLE.

## Gaps vs. mission

| Required | Status |
|----------|--------|
| One canonical product version source | observed: `firedm/version.py` |
| Unified build code `YYYYMMDD_VN` | observed (named `build_id`); needs facade renaming exposure as `build_code` |
| Generated build info module for packaged runtime | partially observed (`build-metadata.json` written into `dist/FireDM/`); no `firedm/_build_info.py` Python module |
| Windows pipeline using build code | observed and wired |
| Linux build pipeline | **MISSING** — must add scripts + spec + validators |
| Cross-platform manifest merge | **MISSING** — Windows manifest is single-platform |
| Cross-platform checksums | partially: `generate_checksums.py` is build_id-scoped but not Linux-aware |
| GitHub Actions Linux job | **MISSING** |
| Build-code generation job feeding both OS jobs | **MISSING** — current workflow generates build_id inside the windows job |
| `gh release` dry-run with both platforms | partially observed; refuses stale artifacts; needs Linux upload path |
| Tests for cross-platform build code, manifest merge, Linux contract, workflow | **MISSING** |
| Docs: LINUX_BUILD, LINUX_PORTABLE, BUILD_ID_POLICY (reaffirmed) | **MISSING** |

## Working assumptions

- Keep the field name `build_id` for back-compat across all existing scripts/tests/manifests/workflows (it already matches `YYYYMMDD_VN`).
- Introduce `versioning.py` as a thin façade that exposes `build_code` aliases, the `write_build_info` API, and a Linux-friendly product-version reader.
- Linux artifacts cannot be built on Windows host; local validation produces unit-level coverage and dry-run only. CI Ubuntu runner produces the actual binary.
- FFmpeg/ffprobe stays detect-only on Linux too.
- AppImage NOT implemented in this pass — only `tar.gz` portable. Mark blocked.
- x86, ARM64, MSI, MSIX remain blocked honestly.
