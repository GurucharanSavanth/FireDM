# 16 Review Packet

Evidence labels: changed, verified, blocked.

## Files Changed
- changed: `.github/workflows/draft-release.yml`
- changed: `.gitignore`
- changed: `README.md`
- changed: `build-release.bat`
- changed: `docs/windows-build.md`
- changed: `docs/release/*.md`
- changed: `scripts/release/*.py`
- changed: `artifacts/windows_installer/*.md`

## Highest-Risk Changes
- changed: `scripts/release/installer_bootstrap.py` owns install, repair, uninstall, shortcut creation, registry metadata, version comparison, and path extraction.
- changed: `.github/workflows/draft-release.yml` now builds release assets from the new installer lane.
- changed: `build-release.bat` now drives installer release artifacts instead of the previous release ZIP path.

## Behavior Preserved
- changed: source and PyInstaller payload still use existing `scripts/windows-build.ps1` and `scripts/firedm-win.spec`.
- changed: FFmpeg and Deno remain external by default.
- changed: no global PATH mutation is introduced.

## Behavior Changed
- changed: x64 release output now includes an installer EXE, portable ZIP, release manifest, checksum file, and license inventory under `dist`.
- changed: installer supports silent install, optional Desktop shortcut, Start Menu shortcut, repair, uninstall, and downgrade blocking.

## Tests And Validation
- verified: `155 passed` under pytest.
- verified: x64 payload validation passed.
- verified: x64 installer validation passed.
- verified: one-click batch wrapper passed with `FIREDM_NO_PAUSE=1`.

## Known Limitations
- blocked: x86, ARM64, universal bootstrapper, MSI, MSIX, signing, GUI interaction, real downloads, and ffmpeg post-processing remain unverified.
- blocked: GitHub release workflow was not executed in GitHub Actions during this local session.

## Suggested Reviewer Focus
- review `installer_bootstrap.py` path containment, uninstall guards, registry writes, version comparison, and shortcut creation first.
- review workflow asset names and stable-channel release behavior.
- review license inventory before approving bundled third-party binaries.

## Rollback Considerations
- revert `build-release.bat`, `.github/workflows/draft-release.yml`, `scripts/release/*`, and release docs to return to the old ZIP-only release path.
- generated `dist` artifacts can be rebuilt; do not treat them as source of truth.

