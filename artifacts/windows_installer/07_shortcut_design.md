# 07 Shortcut Design

Evidence labels: changed, verified.

## Start Menu
- changed: default Start Menu shortcut is created under `%APPDATA%\Microsoft\Windows\Start Menu\Programs\FireDM`.
- changed: shortcut target is `FireDM-Launcher.cmd`.
- changed: shortcut working directory is the install directory.
- changed: shortcut icon points to `FireDM-GUI.exe`.
- verified: installer validation checks shortcut creation and uninstall cleanup with a validation shortcut name.

## Desktop
- changed: Desktop shortcut is opt-in via `--desktop-shortcut`.
- verified: installer validation installs with `--desktop-shortcut`, checks desktop shortcut creation, then uninstalls.
- changed: uninstall removes only the expected FireDM shortcut path/name.

## Implementation
- changed: shortcuts are created through Windows Script Host COM from PowerShell using argument binding rather than string interpolation.
- changed: shortcut failures are logged and raise installer failure instead of being silently ignored.

