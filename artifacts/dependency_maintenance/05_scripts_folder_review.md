# 05 Scripts Folder Review

changed:
- `scripts/release/check_dependencies.py`: new dependency/toolchain/portable preflight.
- `scripts/release/validate_portable.py`: new portable ZIP/root validator.
- `scripts/release/build_windows.py`: runs dependency preflight, records dependency status artifact, validates portable ZIP, records FFmpeg policy in manifest.
- `scripts/release/build_installer.py`: builds the installer as a PyInstaller onedir bundle, keeps the payload ZIP as a sidecar, and records the sidecar in the installer manifest.
- `scripts/release/build_payload.py`: calls `scripts/windows-build.ps1 -PayloadOnly`, embeds `payload-manifest.json` in portable payload.
- `scripts/release/generate_checksums.py`: includes build-ID dependency status JSON.
- `scripts/release/installer_bootstrap.py`: resolves onedir payload sidecars and copies the onedir `_internal` runtime for the installed uninstaller.
- `scripts/windows-build.ps1`: full lane by default; payload-only mode for internal PyInstaller build; validate-only mode; local dependency install only with explicit `-InstallLocalDeps`; direct GitHub publish disabled.
- `scripts/verify_extractor_default.py`: supports `--output-dir` so tests can write proof artifacts to temp directories.
- `scripts/smoke_video_pipeline.py`: supports `--output-dir` so tests can write smoke artifacts to temp directories.

observed unchanged but reviewed:
- `scripts/release/github_release.py`: dry-run default, verifies artifacts/checksums before publish.
- `scripts/release/validate_installer.py`: temp-root install, repair, uninstall, upgrade, downgrade checks; no global PATH mutation.

resolved:
- Normal payload builds no longer delete the whole `build` tree, so stale locked PyInstaller runtime temp directories do not block package rebuilds.
- The installer bootstrapper no longer uses onefile mode; local onefile extraction failed with WinError 5 on this host, while the onedir bundle passed installer validation.
- Full pytest no longer rewrites tracked extractor/video smoke artifacts.

blocked:
- legacy `scripts/exe_build/**` and `scripts/appimage/**` remain historical reference, not current release lane.
