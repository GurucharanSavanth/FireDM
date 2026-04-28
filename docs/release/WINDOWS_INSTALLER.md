# Windows Installer

Evidence labels in this document use observed/changed/blocked language.

## Supported Installer Lane

- changed: the implemented installer lane is `win-x64`.
- blocked: `win-universal`, `win-x86`, `win-arm64`, MSI, and MSIX require additional payload/tooling validation before release claims.

Build the x64 installer:

```powershell
.\.venv\Scripts\python.exe scripts\release\build_windows.py --arch x64 --channel dev
```

Preflight only:

```powershell
.\.venv\Scripts\python.exe scripts\release\check_dependencies.py --arch x64 --channel dev --skip-portable
```

One-click wrapper:

```powershell
.\build-release.bat
```

The wrapper defaults to unsigned `dev`. Pass a channel name to override it, for
example `.\build-release.bat stable`. Set `FIREDM_NO_PAUSE=1` for
non-interactive automation. Public stable builds require signing configuration.
Every build receives a deterministic `YYYYMMDD_V{N}` build ID. Use
`--date YYYYMMDD` for deterministic tests or `--build-id YYYYMMDD_VN` for an
explicit maintainer rebuild.

Primary output:

```text
dist\installers\FireDM_Setup_<build_id>_dev_win_x64\FireDM_Setup_<build_id>_dev_win_x64.exe
dist\installers\FireDM_Setup_<build_id>_dev_win_x64\FireDM_<build_id>_dev_win_x64_payload.zip
dist\portable\FireDM_<build_id>_dev_win_x64_portable.zip
dist\dependency-status_<build_id>.json
```

The installer is a PyInstaller one-dir bundle. Keep the EXE, `_internal`
runtime folder, and payload ZIP sidecar together when validating or
distributing the installer lane. The bootstrapper verifies the sidecar SHA256
before extraction.

## Install Behavior

Default install scope is per-user:

```text
%LocalAppData%\Programs\FireDM
```

This avoids admin/UAC for the first validated lane. Program Files/all-users can be added later with explicit elevation handling.

The installer:
- detects Windows architecture
- blocks wrong architecture
- extracts the bundled PyInstaller one-dir payload
- creates `FireDM-Launcher.cmd` with process-local FireDM environment variables
- creates Start Menu shortcut by default
- creates Desktop shortcut only when requested
- writes HKCU uninstall metadata
- blocks downgrade by default
- treats same-version install as repair/reinstall
- preserves `%AppData%\FireDM` and `%LocalAppData%\FireDM` by default

## Silent Flags

```powershell
FireDM_Setup_<build_id>_dev_win_x64.exe --silent
FireDM_Setup_<build_id>_dev_win_x64.exe --silent --install-dir C:\Users\me\AppData\Local\Programs\FireDM
FireDM_Setup_<build_id>_dev_win_x64.exe --silent --desktop-shortcut
FireDM_Setup_<build_id>_dev_win_x64.exe --silent --repair
FireDM_Setup_<build_id>_dev_win_x64.exe --silent --uninstall
FireDM_Setup_<build_id>_dev_win_x64.exe --silent --uninstall --remove-user-data
FireDM_Setup_<build_id>_dev_win_x64.exe --silent --log install.log
```

`--allow-downgrade` exists for maintainer-approved rollback only.

## Shortcuts

- Start Menu: `FireDM`
- Desktop: optional via `--desktop-shortcut`
- Shortcut target: `FireDM-Launcher.cmd`
- Shortcut icon: `FireDM-GUI.exe`

The command launcher sets app-local environment variables and starts `FireDM-GUI.exe`.

## Validation

```powershell
.\.venv\Scripts\python.exe scripts\release\validate_installer.py --artifact dist\installers\FireDM_Setup_<build_id>_dev_win_x64.exe
```

Validation installs into a temp directory using a validation registry id, runs packaged smoke checks, verifies repair, and uninstalls.

Full validation:

```powershell
.\.venv\Scripts\python.exe scripts\release\validate_installer.py --artifact dist\installers\FireDM_Setup_<build_id>_dev_win_x64.exe --test-repair --test-uninstall --test-upgrade --test-downgrade-block
.\.venv\Scripts\python.exe scripts\release\smoke_installed_gui.py --install-root dist\payloads\win-x64\FireDM --timeout 20 --headless-safe --no-network
```

The installer validates payload SHA256 before extraction and refuses to replace
or uninstall unmanaged non-empty directories. Custom install directories must be
dedicated FireDM install roots.
