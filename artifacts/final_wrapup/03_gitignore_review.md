# Phase 3 Gitignore Review

## Result

- changed: `.gitignore` now uses an allowlist source policy with explicit generated-output ignores.
- changed: generated release/build outputs, caches, virtual environments, logs, screenshots, temp directories, installers, and archives are ignored.
- changed: source scripts/docs/tests/workflows/icons and selected Markdown evidence artifacts are explicitly allowed.

## Check-ignore Results

- verified: `dist\installers\FireDM_Setup_2022.2.5_dev_win_x64.exe` is ignored by `dist/`.
- verified: `dist\portable\FireDM_2022.2.5_win_x64_portable.zip` is ignored by `dist/`.
- verified: `scripts\release\build_windows.py` is not ignored because of `!scripts/release/*.py`.
- verified: `docs\release\WINDOWS_INSTALLER.md` is not ignored because of `!docs/release/*.md`.
- verified: `tests\release\test_installer_bootstrap_paths.py` is not ignored because of `!tests/release/*.py`.
- verified: `artifacts\windows_installer\00_repo_packaging_discovery.md` is not ignored because of `!artifacts/windows_installer/*.md`.
- verified: `artifacts\final_wrapup\00_discovery.md` is not ignored because of `!artifacts/final_wrapup/*.md`.

## Artifact Policy

- source-controlled evidence is Markdown only under `artifacts/windows_installer*/` and `artifacts/final_wrapup/`.
- binary installer/portable outputs under `dist/` stay ignored.

