# 10 GitHub Actions Status

Evidence labels: observed, changed, blocked.

## Workflow
- observed: `.github/workflows/draft-release.yml` exists.
- changed: workflow is gated to `workflow_dispatch` and `v*` tags instead of path-based pushes.
- changed: workflow builds x64 payload and installer, validates payload and installer, generates checksums, and uploads artifacts.
- changed: signing environment is populated only when signing secrets/vars are present.

## Blocked
- blocked: GitHub Actions was not run from this local session.
- blocked: x86 and ARM64 lanes are not enabled in workflow because local release scripts support only x64.
- blocked: signing in CI is unverified without configured secrets.

## Local Equivalent
- verified: `cmd /c "set FIREDM_NO_PAUSE=1&& build-release.bat dev"` completed locally.
