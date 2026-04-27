# 03 GitHub Release Dry Run

## Behavior

- changed: `scripts/release/github_release.py` is dry-run by default.
- changed: real release creation requires `--publish`.
- changed: draft is default; dev/beta are prerelease by default.
- changed: tag is `build-YYYYMMDD_VN`.
- changed: title is `FireDM YYYYMMDD_VN`.

## Verification

- verified command: `.venv\Scripts\python.exe scripts\release\github_release.py --manifest dist\release-manifest.json --dry-run`
- verified exit: 0
- verified output build ID: `20260427_V1`
- verified output tag: `build-20260427_V1`
- verified output title: `FireDM 20260427_V1`
- verified artifacts listed:
  - `dist\installers\FireDM_Setup_20260427_V1_dev_win_x64.exe`
  - `dist\installers\FireDM_Setup_20260427_V1_dev_win_x64.manifest.json`
  - `dist\portable\FireDM_20260427_V1_dev_win_x64_portable.zip`
  - `dist\licenses\license-inventory_20260427_V1.json`
  - `dist\FireDM_release_notes_20260427_V1.md`
  - `dist\checksums\SHA256SUMS_20260427_V1.txt`
  - `dist\FireDM_release_manifest_20260427_V1.json`

## Safety

- changed: manifest absolute paths are refused.
- changed: artifacts without the build ID in the filename are refused.
- changed: missing artifacts and checksum mismatches fail before publish.
- changed: stable release planning requires signed installer artifacts, passed validation, and clean tree unless explicitly allowed.

