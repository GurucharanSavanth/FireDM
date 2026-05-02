# 13 Validation Plan

Evidence labels: planned, blocked, verified.

## Required Local Commands
Planned:

```powershell
.\.venv\Scripts\python.exe -m compileall .\firedm
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\release\build_windows.py --arch x64 --channel dev
.\.venv\Scripts\python.exe scripts\release\validate_payload.py --arch x64
.\.venv\Scripts\python.exe scripts\release\build_installer.py --arch x64 --channel dev
.\.venv\Scripts\python.exe scripts\release\validate_installer.py --artifact dist\installers\FireDM_Setup_<version>_dev_win_x64.exe
.\.venv\Scripts\python.exe scripts\release\smoke_installed_app.py --install-root <temp install root>
```

## Installer Behavior Checks
Planned:
- artifact exists
- `--help` works
- silent install to temp directory works
- installed tree contains `FireDM-GUI.exe`, `firedm.exe`, `_internal`, certifi cert, Tcl/Tk files
- installed `firedm.exe --help` works
- installed `firedm.exe --imports-only` works
- Start Menu shortcut is created when requested
- Desktop shortcut is created only when selected
- repair restores a deleted launcher
- same-version repair allowed
- downgrade blocked unless `--allow-downgrade`
- uninstall removes program files and shortcuts
- uninstall preserves user data by default
- no global PATH mutation

## Blocked Validation
- blocked: x86 validation until a 32-bit Python/toolchain lane exists.
- blocked: ARM64 validation until a native ARM64 runner/toolchain exists.
- blocked: MSI validation until WiX tooling is available.
- blocked: MSIX validation until signing/package tooling is configured.
- blocked: real GUI interaction/download/ffmpeg media flow unless explicitly run manually.

