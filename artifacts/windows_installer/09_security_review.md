# 09 Security Review

Evidence labels: changed, verified, blocked.

## Installer Safety
- changed: installer extraction validates ZIP member paths stay inside the install root.
- changed: installer subprocess calls use argv lists; no shell command interpolation is used for payload extraction or validation.
- changed: shortcuts are created with a fixed PowerShell script and bound arguments.
- changed: global `PATH` and Python environment are not modified.
- changed: uninstall removes the program tree and known shortcut/registry entries only.

## User Data
- changed: uninstall preserves user data by default.
- changed: optional user-data removal is explicit and limited to FireDM appdata/localappdata directories.
- blocked: real user-data migration was not exercised against historical installs.

## Bundled Components
- changed: release artifacts include `dist/licenses/license-inventory.json`.
- blocked: FFmpeg/ffprobe are not bundled until redistribution/source/checksum decisions are documented.
- blocked: artifacts are unsigned because no code-signing certificate is configured.

## Residual Risks
- blocked: SmartScreen reputation/code-signing behavior not validated.
- blocked: full GUI, live downloads, and media post-processing security behavior not revalidated by this packaging pass.

