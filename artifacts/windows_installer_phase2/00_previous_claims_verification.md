# 00 Previous Claims Verification

Evidence labels: observed, changed, verified, blocked.

## Repository
- observed: cwd is `G:\Personal Builds\Revive-FireDM\FireDM - Branch`.
- observed: branch is `features`; last commit is `c6ba615 New Test Features implementation`.
- observed: Python is `3.10.11` on `Windows-10-10.0.26200-SP0`, `win32`, `AMD64`.

## Verified Claims
- verified: x64 installed-tree payload exists and validates at `dist/payloads/win-x64/FireDM`.
- verified: repo-owned Python bootstrapper installer builds as `dist/installers/FireDM_Setup_2022.2.5_dev_win_x64.exe`.
- verified: silent install, Start Menu shortcut, Desktop shortcut, repair, uninstall, synthetic older-version upgrade, and synthetic newer-version downgrade block pass through `scripts/release/validate_installer.py`.
- verified: portable ZIP exists at `dist/portable/FireDM_2022.2.5_win_x64_portable.zip`.
- verified: release manifest and checksum file are generated at `dist/release-manifest.json` and `dist/checksums/SHA256SUMS.txt`.
- verified: full pytest now reports `169 passed`.

## Disproven Or Corrected Claims
- changed: first-pass shortcut creation was not reliable. Inline PowerShell argument passing failed and did not create `.lnk` files. It now uses a temporary `.ps1` with typed parameters.
- changed: first-pass uninstall/replace safety was too broad. Installer now requires safe roots and installer-owned state before replacing/removing non-empty install trees.
- changed: malformed installed versions previously degraded to `0`; malformed versions now block install unless `--allow-downgrade` is explicitly used.

## Still Unverified
- blocked: GitHub Actions has not been run on GitHub in this session.
- blocked: live GUI workflow, real HTTP download, real video download, and FFmpeg post-processing were not manually QA-tested.
- blocked: real old-installer upgrade remains unverified; synthetic isolated upgrade fixture passes.

## Blocked Claims
- blocked: x86 and ARM64 release lanes are blocked; current release scripts support only `x64`.
- blocked: universal bootstrapper is blocked until at least two architecture payloads exist.
- blocked: MSI/MSIX are blocked by missing tooling/signing workflow.
- blocked: FFmpeg/ffprobe are not bundled; bundling needs license/source/checksum approval.
- blocked: signing is not configured; artifacts are unsigned.
