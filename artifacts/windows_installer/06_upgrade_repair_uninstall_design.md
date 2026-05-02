# 06 Upgrade Repair Uninstall Design

Evidence labels: changed, verified, blocked.

## Installed Metadata
- changed: installer writes HKCU uninstall metadata under `Software\Microsoft\Windows\CurrentVersion\Uninstall\<registry id>`.
- changed: metadata includes display name, display version, publisher, install location, display icon, uninstall strings, channel, and architecture.

## Upgrade
- changed: installer reads the existing uninstall key, compares versions with `packaging.version.Version`, and blocks downgrade by default.
- changed: newer installers remove stale program files safely by replacing the installed program tree while preserving user data roots.
- blocked: live upgrade from a separately installed older FireDM release was not validated because no older installed fixture was present.

## Repair
- verified: validation deletes the installed GUI executable, runs the same installer with `--repair`, and confirms restoration.
- changed: same-version install is treated as repair/reinstall.

## Uninstall
- verified: validation runs `--silent --uninstall` and confirms program files and registry metadata are removed.
- changed: user settings/cache roots are preserved by default.
- changed: `--remove-user-data` is explicit and guarded to FireDM-specific appdata/localappdata roots only.

