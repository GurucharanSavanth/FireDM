# 05 Upgrade Downgrade Fixture Results

Evidence labels: changed, verified.

## Script
- changed: extended `scripts/release/validate_installer.py`.

## Options Added
- changed: `--test-upgrade`
- changed: `--test-downgrade-block`
- changed: `--test-repair`
- changed: `--test-uninstall`
- changed: `--keep-temp-on-failure`
- changed: `--log-dir`

## Fixture Isolation
- changed: validation runs with temporary `APPDATA`, `LOCALAPPDATA`, and `USERPROFILE`.
- changed: registry key defaults to `FireDM-InstallerValidation`, not the production app key.
- changed: install root defaults to a generated temp directory.

## Verified Results
- verified: silent install succeeded.
- verified: Start Menu shortcut existed after install.
- verified: Desktop shortcut existed when `--desktop-shortcut` was selected.
- verified: synthetic older version upgraded to current version.
- verified: stale program file created by the fixture was removed on upgrade.
- verified: temp user config survived upgrade and uninstall.
- verified: same-version repair restored a removed launcher.
- verified: synthetic newer version blocked downgrade.
- verified: uninstall removed installer-owned files, shortcuts, and registry metadata.
- verified: parent process `PATH` was unchanged.
