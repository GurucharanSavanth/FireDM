# Phase 4 GitHub Actions Review

## Workflow

- changed: `.github/workflows/draft-release.yml`.
- verified: local PyYAML parse passed: `yaml ok`.
- verified: referenced local script paths exist.
- verified: current workflow action tags exist remotely: `actions/checkout@v6`, `actions/setup-python@v6`, `actions/upload-artifact@v7`.

## Release Gating

- changed: workflow remains tag/manual gated; it does not publish on ordinary push.
- changed: manual dispatch defaults to `dev`.
- changed: tag builds force `stable`.
- changed: stable builds set `FIREDM_REQUIRE_SIGNING=1` before packaging.
- changed: unsigned dev artifacts remain allowed for local/dev validation.

## Artifacts

- observed workflow artifact upload includes installer EXE, portable ZIP, `release-manifest.json`, `SHA256SUMS.txt`, license inventory, installer sidecar manifest, and release body.
- inferred: workflow fails if tests, build, validation, or required signing fail because commands run with strict PowerShell error behavior.

## Remaining Status

- blocked: GitHub Actions was not executed remotely in this pass.
- blocked: no remote release draft was created.

