# 06 Reviewer Packet

## Review First

- `scripts/release/build_id.py`
- `scripts/release/build_windows.py`
- `scripts/windows-build.ps1`
- `scripts/release/github_release.py`
- `.github/workflows/draft-release.yml`
- `tests/release/test_github_release_dry_run.py`
- `docs/release/BUILD_ID_POLICY.md`
- `docs/release/GITHUB_RELEASES.md`

## Commit Candidates

- source scripts under `scripts/release/`
- tests under `tests/release/`
- workflow `.github/workflows/draft-release.yml`
- docs under `README.md`, `docs/windows-build.md`, `docs/release/`
- evidence under `artifacts/build_release_update/`

## Do Not Add

- `dist/**`
- `build/**`
- installer EXE/ZIP outputs
- generated logs/screenshots/temp directories
- regenerated proof JSON timestamp drift

## Suggested Commands

```powershell
git status --short --branch
git diff --check
git add -- .github/workflows/draft-release.yml .gitignore README.md build-release.bat scripts/windows-build.ps1 docs/windows-build.md docs/release scripts/release tests/release artifacts/build_release_update
git commit -m "Add deterministic build IDs to FireDM release automation"
git push origin features
```

Do not run `git tag`, `gh release create`, or `gh release upload` unless the maintainer explicitly intends to publish.

## Remaining Blocks

- blocked: remote GitHub Actions not run.
- blocked: no GitHub release was created.
- blocked: stable release signing not configured.
- blocked: x86, ARM64, universal bootstrapper, MSI, MSIX, and FFmpeg/ffprobe bundling remain separate future work.
