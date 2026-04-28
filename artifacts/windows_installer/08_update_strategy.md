# 08 Update Strategy

Evidence labels: changed, observed, blocked.

## Installer-Run Upgrade
- changed: the implemented update path is installer-run upgrade.
- changed: upgrade uses local installed version metadata and blocks downgrade by default.
- changed: user settings/download state are preserved by default because installer program-file replacement is separate from user data roots.

## In-App Update
- observed: packaged FireDM already treats in-place packaged self-update cautiously.
- blocked: this pass does not add in-app auto-download or auto-execution.
- required future rule: any in-app update check must use trusted metadata, checksum/signature verification, explicit user consent, and no automatic elevation.

## Release Metadata
- changed: `dist/release-manifest.json` records version, channel, installer path, installer checksum, portable ZIP path, portable checksum, and blocked artifact lanes.
- changed: `dist/checksums/SHA256SUMS.txt` is generated after `release-manifest.json` exists.

