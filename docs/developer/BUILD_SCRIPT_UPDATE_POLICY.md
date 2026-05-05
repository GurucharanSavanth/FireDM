# Build Script Update Policy

Status: changed 2026-05-03.

## Rule

Every future patch must check whether it affects the canonical Windows build
script, root `.\windows-build.ps1`.

Ask these questions before reviewer PASS:

1. Did runtime files change?
2. Did dependencies change?
3. Did entry points change?
4. Did UI assets or bundled help/docs change?
5. Did tests or QA commands change?
6. Did versioning change?
7. Did external tool assumptions change?
8. Did packaging assumptions change?
9. Did artifact layout change?
10. Did changelog or release-note sources change?

## Required Action

If the answer to any question is yes:

- inspect `.\windows-build.ps1`;
- update it when the build behavior changes;
- update `docs/release/BUILD_SYSTEM.md`;
- update `docs/release/RELEASE_ARTIFACT_LAYOUT.md` when paths change;
- update `docs/release/CHANGELOG_COMPILATION.md` when release-note sources change;
- update build-script tests when script behavior changes;
- run at least the PowerShell parser and dry-run validation.

If the script does not need changes, record the reason in the handoff or final
report.

## Reviewer Block Conditions

Reviewers must block a patch when build-affecting behavior changes but the patch
does not inspect and either update `.\windows-build.ps1` or explicitly mark it
unchanged with evidence.
