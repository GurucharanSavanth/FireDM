# 05 Installer Feature Matrix

Evidence labels: changed, verified, blocked.

| Feature | Status | Evidence |
| --- | --- | --- |
| x64 installer EXE | verified | `build-release.bat dev` exit 0 created `dist/installers/FireDM_Setup_2022.2.5_dev_win_x64.exe` |
| silent install | verified | `validate_installer.py` ran installer with `--silent --install-dir <temp>` |
| Start Menu shortcut | verified | validation used a validation shortcut name and checked `.lnk` creation |
| optional Desktop shortcut | verified | validation installed with `--desktop-shortcut` and checked `.lnk` creation |
| launcher wrapper | verified | validation checked `FireDM-Launcher.cmd` and ran installed `firedm.exe` |
| repair | verified | validation deleted `FireDM-GUI.exe`, ran `--repair`, and confirmed restoration |
| uninstall | verified | validation ran `--silent --uninstall` and checked install tree removal |
| downgrade block | changed, not dynamically verified | installer compares installed version and blocks lower installer version unless `--allow-downgrade` |
| same-version repair | verified | validation re-ran same-version installer in repair path |
| user data preservation | changed, not destructively verified | uninstall preserves `%APPDATA%\FireDM` and `%LOCALAPPDATA%\FireDM` unless `--remove-user-data` |
| x86 payload/installer | blocked | script exits cleanly: `unsupported arch 'x86'; supported: x64` |
| ARM64 payload/installer | blocked | script exits cleanly: `unsupported arch 'arm64'; supported: x64` |
| MSI/MSIX | blocked | WiX/MSIX signing/tooling not available locally |

