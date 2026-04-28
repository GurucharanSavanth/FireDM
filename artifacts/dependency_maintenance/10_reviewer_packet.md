# 10 Reviewer Packet

## Changed Files

- `scripts/release/check_dependencies.py`
- `scripts/release/validate_portable.py`
- `scripts/release/build_windows.py`
- `scripts/release/build_installer.py`
- `scripts/release/build_payload.py`
- `scripts/release/generate_checksums.py`
- `scripts/release/common.py`
- `scripts/release/installer_bootstrap.py`
- `scripts/windows-build.ps1`
- `scripts/verify_extractor_default.py`
- `scripts/smoke_video_pipeline.py`
- `.gitignore`
- `.gitattributes`
- `.github/workflows/draft-release.yml`
- `.github/workflows/windows-smoke.yml`
- `tests/test_packaged_diagnostics.py`
- `tests/release/test_dependency_preflight.py`
- `tests/release/test_validate_portable.py`
- `tests/release/test_workflow_build_id.py`
- `README.md`
- `docs/windows-build.md`
- `docs/release/DEPENDENCY_POLICY.md`
- `docs/release/WINDOWS_PORTABLE.md`
- `docs/release/WINDOWS_INSTALLER.md`
- `docs/release/RELEASE_CHECKLIST.md`
- `docs/release/GITHUB_RELEASES.md`
- `docs/release/FFMPEG_BUNDLING.md`
- `docs/release/THIRD_PARTY_BUNDLED_COMPONENTS.md`
- `artifacts/dependency_maintenance/**`

## Do Not Add

- `dist/**`
- `build/**`
- `__pycache__/**`
- installer EXE/ZIP outputs
- installer validation log directories under `artifacts/dependency_maintenance/`
- pre-existing generated proof JSON timestamp drift unless maintainer wants it

## Notes

- The installer artifact is now a PyInstaller onedir bundle: keep the EXE, `_internal`, and sidecar payload ZIP together.
- `dist\release-manifest.json` is generated output and remains ignored; the source evidence is this reviewer packet and the maintenance reports.
- FFmpeg/ffprobe are still not bundled. Elevated preflight found the WinGet install, but package metadata records `ffmpegBundled: false`.
- Sandbox HKCU registry writes are blocked; elevated installer validation passed.

## Suggested Commands

```powershell
git status --short --branch
git diff --check
git add -- .gitattributes .gitignore .github/workflows/draft-release.yml .github/workflows/windows-smoke.yml README.md docs/windows-build.md docs/release scripts/windows-build.ps1 scripts/release scripts/verify_extractor_default.py scripts/smoke_video_pipeline.py tests/test_packaged_diagnostics.py tests/release artifacts/dependency_maintenance
git commit -m "Harden FireDM dependency preflight and portable validation"
git push origin features
```

Do not run `git tag`, `gh release create`, or `gh release upload` unless intentionally publishing.
