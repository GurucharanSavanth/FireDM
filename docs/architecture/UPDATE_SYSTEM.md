# Update System Architecture

Status: changed 2026-05-02.

## Current State
- observed: Release docs and scripts exist under `docs/release/`, `scripts/release/`, and `build-release.bat`.
- observed: No validated in-app self-updater was added in this phase.

## Planned Flow
- planned: UI exposes a visible `Check for updates` action and current/latest version display.
- planned: Update client calls GitHub Releases latest metadata only for the configured release source.
- planned: Asset selection matches platform, architecture, package kind, and stable/prerelease preference.
- planned: Verification accepts GitHub asset `digest` or a signed/checksummed release manifest; checksum mismatch stops install.
- planned: Download goes to a temp staging directory, then install is user-confirmed.
- planned: Running executables are not overwritten. Replacement uses next-launch swap or a helper process with backup and rollback.

## Boundaries
- planned: No silent updates, no forced updates, no token requirement for public checks, no execution from download cache.
- blocked: Rollback helper, signature format, UI, and tests are not implemented.
