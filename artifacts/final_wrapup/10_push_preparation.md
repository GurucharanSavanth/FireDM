# Phase 10 Push Preparation

Do not execute these commands until after maintainer review. This pass did not run `git add`, `git commit`, `git push`, `git tag`, or release publication commands.

## Final Dirty Tree Summary

- modified tracked source/docs/hygiene files remain unstaged.
- untracked source/docs/tests/evidence files remain unstaged.
- generated `dist/**` artifacts remain ignored.
- 1187 tracked generated PyInstaller/build files under `artifacts/full_codebase_repair/pyinstaller-build/**` and `artifacts/full_codebase_repair/pyinstaller-dist/**` are deleted in the working tree for de-tracking.

## Suggested Status Checks

```powershell
git status --short --branch
git diff --check
git diff --stat
```

## Suggested Add

```powershell
git add -A -- .gitattributes .gitignore .github/workflows/draft-release.yml README.md build-release.bat docs/windows-build.md docs/release artifacts/windows_installer artifacts/windows_installer_phase2 artifacts/final_wrapup scripts/release tests/release firedm/tool_discovery.py tests/test_ffmpeg_service.py artifacts/full_codebase_repair/pyinstaller-build artifacts/full_codebase_repair/pyinstaller-dist
```

## Suggested Commit

```powershell
git commit -m "Finalize Windows x64 installer pipeline and release hygiene" -m "Completes final wrap-up for the x64 Windows installer pipeline, hardens release scripts, updates GitHub Actions, adds .gitattributes/.gitignore hygiene, refreshes release docs, validates tests/build/installer flows, and documents blocked x86/ARM64/MSI/MSIX/signing/FFmpeg gates."
```

## Suggested Push

```powershell
git push origin features
```

## Files Not To Add

- `dist/**`
- `build/**`
- generated installer/portable binaries except through release upload.
- local caches/logs/screenshots/temp directories.

## Recovery

- to abandon only the de-tracking decision before staging: `git restore --worktree -- artifacts/full_codebase_repair/pyinstaller-build artifacts/full_codebase_repair/pyinstaller-dist`
- to abandon all final-wrapup local edits before staging, review `git status --short` first and restore paths explicitly; do not use `git reset --hard`.

