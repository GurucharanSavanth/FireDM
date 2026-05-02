# Build System

Status: changed 2026-05-02.

## Current Local Build Surface
- observed: `build-release.bat`, `scripts/windows-build.ps1`, `scripts/firedm-win.spec`, `scripts/firedm-linux.spec`, and `scripts/release/` exist.
- observed: `pyproject.toml` defines build extra `pyinstaller>=6.10`.
- blocked: This phase did not create or run `scripts/release/release_build.ps1`.

## Planned Orchestrator
- planned: `scripts/release/release_build.ps1` becomes authoritative for clean/debug/release, one-folder, optional one-file, backend `pyinstaller|nuitka|auto`, logs, manifest, checksums, metadata, and safe smoke checks.
- planned: `release_build.cmd` becomes the double-click launcher that invokes PowerShell, writes a log, pauses on failure, and points to artifacts.
- planned: No global Python mutation, no global installs, no destructive delete outside repo, no hidden network restore.

## Artifact Layout
- planned: `artifacts/release/<version>/<platform>/<build_kind>/`
- planned: Include executable/folder, dependencies, `manifest.json`, `checksums.sha256`, `build.log`, build diagnostics, and SBOM if tooling exists.

## Backend Matrix
| Backend | Pros | Cons | Current decision |
| --- | --- | --- | --- |
| PyInstaller one-folder | Existing specs; easier data/path debugging; good first smoke target. | Platform-specific build; data files need explicit handling. | planned first |
| PyInstaller one-file | Single artifact; user-friendly. | Extracts to temp; harder updater replacement; AV false positives more likely. | planned after one-folder |
| Nuitka standalone | Potential performance/startup gains; compiler reports. | Requires C compiler; data/DLL handling needs proof. | evaluate later |
| Nuitka onefile | Single binary option after standalone. | Extraction/path behavior and compiler setup add risk. | blocked until standalone passes |
