# 04 Environment Variable Policy

Evidence labels: observed, changed, verified, blocked.

## Process-Local Runtime Variables
- changed: `scripts/release/installer_bootstrap.py` creates `FireDM-Launcher.cmd` in the installed root.
- changed: the launcher sets only process-local variables before starting `FireDM-GUI.exe`.
- changed: variables set by the launcher are `FIREDM_INSTALL_DIR`, `FIREDM_RUNTIME_DIR`, `FIREDM_TOOLS_DIR`, `FIREDM_CONFIG_DIR`, `FIREDM_CACHE_DIR`, `FIREDM_LOG_DIR`, and `PYTHONUTF8=1`.

## Global Environment Policy
- changed: the installer does not mutate global `PATH`.
- changed: the installer does not set global `PYTHONPATH`, `PYTHONHOME`, `TCL_LIBRARY`, or `TK_LIBRARY`.
- verified: `validate_installer.py` runs silent install and uninstall without any PATH mutation step.

## Tool Policy
- observed: the payload contains PyInstaller-bundled Python, Tcl/Tk, certifi, pycurl, yt-dlp, and GUI/runtime dependencies.
- blocked: FFmpeg, ffprobe, and Deno are not bundled in this pass because redistribution/source/checksum policy remains a maintainer decision.

