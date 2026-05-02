# 04 Workflow Review

## Workflow

- changed: `.github/workflows/draft-release.yml`

## Inputs

- changed manual inputs: `channel`, `arch`, `build_id`, `date`, `publish_release`, `draft`, `prerelease`.
- changed channel choices: `dev`, `beta`, `stable`.
- changed arch choices: `x64` only.

## Triggers

- changed tag trigger: `build-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_V*`.
- changed: normal branch push does not publish or build release artifacts.
- changed: tag runs force `stable` and use the tag build ID.
- changed: manual runs dry-run release publishing unless `publish_release=true`.

## Validation

- changed: workflow runs tests before packaging.
- changed: workflow verifies manifest `build_id` and artifact paths contain the build ID.
- changed: workflow uploads only build-ID artifacts.
- changed: workflow calls `github_release.py` for dry-run/publish behavior.
- blocked: remote GitHub Actions execution was not run in this local pass.

