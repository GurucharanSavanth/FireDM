# 12 Release Readiness

Evidence labels: verified, blocked.

## Verdict
- blocked: not ready for a public stable release.
- verified: ready for maintainer review of the x64 dev installer pipeline.

## Release-Blocking Items
- blocked: artifacts are unsigned.
- blocked: real GUI/manual QA matrix has not been executed.
- blocked: live direct download and video/FFmpeg flows have not been executed.
- blocked: FFmpeg/ffprobe bundling decision is Option B, not bundled.
- blocked: x86, ARM64, universal bootstrapper, MSI, and MSIX are not implemented.
- blocked: GitHub Actions release workflow has not run.

## Safe To Review Now
- verified: x64 installed-tree payload.
- verified: x64 installer bootstrapper with safety hardening.
- verified: shortcut creation/removal.
- verified: synthetic upgrade/downgrade/repair/uninstall validation.
- verified: checksums and release manifest generation.
