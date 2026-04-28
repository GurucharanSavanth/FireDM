# 09 Signing Status

Evidence labels: changed, verified, blocked.

## Status
- blocked: artifacts are unsigned because no signing tool/certificate was configured.

## Changes
- changed: `scripts/release/build_installer.py` now supports optional signing through environment variables.
- changed: supported variables include `FIREDM_SIGNTOOL`, `FIREDM_SIGN_CERT_SHA1`, `FIREDM_SIGN_PFX`, `FIREDM_SIGN_PFX_PASSWORD`, `FIREDM_SIGN_TIMESTAMP_URL`, and `FIREDM_REQUIRE_SIGNING`.
- changed: signing command uses argv-list subprocess calls and redacts PFX password from printed command text.
- changed: release builds can fail if `FIREDM_REQUIRE_SIGNING=1` is set and signing configuration is absent.
- changed: signature verification runs after signing when signing is configured.

## Evidence
- verified: installer sidecar records `signed: false` and `signatureStatus: unsigned: FIREDM_SIGNTOOL not configured`.
- verified: `dist/release-manifest.json` records the installer as unsigned.

## Docs
- changed: `docs/release/CODE_SIGNING.md` documents signing requirements and unsigned artifact implications.
