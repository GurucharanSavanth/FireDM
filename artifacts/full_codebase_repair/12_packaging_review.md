# 12 Packaging Review

Evidence labels: observed = local files; changed = modified by this pass; verified = command run.

## Source Package
- changed `pyproject.toml`: `firedm-native-host = "firedm.native_host:main"`.
- observed `pyproject.toml` includes `firedm.*`, so plugin/native modules are packaged.
- verified wheel/sdist build succeeds.
- verified Twine metadata check passes.

## PyInstaller
- changed `scripts/firedm-win.spec`: includes `firedm.plugins`, `firedm.native_host`, `firedm.native_messaging`.
- changed: removed undeclared `cryptography` and `paramiko` hiddenimports.
- verified isolated PyInstaller build succeeds under `artifacts/full_codebase_repair\pyinstaller-dist`.
- verified packaged `firedm.exe --help` and `--imports-only` succeed.
- verified required Tk assets exist.

## Blocked/Not Run
- blocked `scripts/windows-build.ps1`: script performs `Remove-Item ... -Recurse -Force` and can stop packaged processes; not run under destructive-command policy.
- not verified: `FireDM-GUI.exe` visual launch in this pass.
