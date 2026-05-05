# Changelog Compilation

Status: changed 2026-05-03.

## Output

- changed: `.\windows-build.ps1` writes the compiled changelog to `release\CHANGELOG-COMPILED.md`.
- changed: the compiled file records build ID, version, and validation-status pointer before source content.

## Sources

The script includes local sources when present:

- `ChangeLog.txt`
- `CHANGELOG.md`
- `RELEASE_NOTES.md`
- `docs\release\*.md`
- `docs\agent\SESSION_HANDOFF.md`
- `git log` from the last tag to `HEAD`, or recent `git log` when no tag exists
- dirty working-tree status when Git reports local changes

Missing files are recorded as unavailable, not invented.

## De-Duplication

The compiler removes repeated Markdown heading lines while preserving body text.
This keeps repeated source titles from dominating the final release note file.

## Validation Status

The compiled changelog includes a validation-status pointer. The authoritative
per-command result lives in `release\manifest.json` under `validation_results`.

## Boundaries

- blocked: no release note is invented for a build artifact that was not created.
- blocked: GUI smoke, signing, one-file builds, Nuitka builds, and Linux builds remain unverified until their commands run successfully.
