# 15 Release Handover

Evidence labels: changed, verified, blocked.

## Ready For Local Use
- verified: run `build-release.bat dev` for the validated local dev-channel x64 installer lane.
- changed: run `build-release.bat` with no argument for the unsigned dev-channel x64 installer lane; use `build-release.bat stable` only with signing configured or as a documented unsigned test artifact.
- changed: generated artifacts are under `dist/installers`, `dist/portable`, `dist/checksums`, `dist/licenses`, and `dist/release-manifest.json`.

## GitHub Release
- changed: `.github/workflows/draft-release.yml` builds the x64 stable installer lane and uploads installer/release assets.
- blocked: workflow was not executed on GitHub in this session.
- required future action: run workflow_dispatch and inspect the uploaded draft release before publishing.

## Signing
- blocked: no signing certificate is configured.
- required future action: sign installer EXE and verify signature before public release.

## Architecture Expansion
- blocked: x86 requires a 32-bit Python/toolchain and dependency validation.
- blocked: ARM64 requires a native ARM64 Python/toolchain and dependency validation.
- blocked: MSI requires WiX installation and a product/upgrade code plan.
