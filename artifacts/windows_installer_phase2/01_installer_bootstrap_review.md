# 01 Installer Bootstrap Review

Evidence labels: observed, changed, verified.

## Scope Reviewed
- observed: reviewed `scripts/release/installer_bootstrap.py`, installer sidecar manifest, payload ZIP extraction, registry use, shortcuts, version comparison, uninstall, repair, and logging.

## Safety Findings
- changed: added strict manifest loading so a missing or malformed installer manifest returns an actionable installer error instead of an unhandled traceback.
- changed: added payload SHA256 and ZIP CRC verification before replacing an install tree.
- changed: added install-root and uninstall-root safety checks. Installer refuses root-like paths and refuses unmanaged non-empty install directories.
- changed: uninstall now requires installer-owned state before removing an install directory.
- changed: log file paths are normalized and must target a file path, not a directory.
- changed: shortcut creation now uses `subprocess.run([...], check=True)` with a temporary PowerShell script and no `shell=True`.

## Registry Behavior
- observed: registry writes are limited to the configured uninstall key under `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\<registry-id>` for per-user validation.
- verified: isolated validation creates and removes the validation registry key.

## PATH And Environment
- observed: installer does not globally mutate `PATH`, `PYTHONPATH`, or `PYTHONHOME`.
- observed: generated launcher sets process-local `FIREDM_INSTALL_DIR`, `FIREDM_RUNTIME_DIR`, `FIREDM_TOOLS_DIR`, `PYTHONUTF8`, and `PYTHONNOUSERSITE`.

## Validation
- verified: `scripts/release/validate_installer.py --test-repair --test-uninstall --test-upgrade --test-downgrade-block` passed against the rebuilt x64 installer.
