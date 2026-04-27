# 13 Reviewer Packet

Evidence labels: changed, verified, blocked.

## Highest-Risk Files To Review First
- changed: `scripts/release/installer_bootstrap.py`
- changed: `scripts/release/validate_installer.py`
- changed: `scripts/release/build_installer.py`
- changed: `scripts/release/build_windows.py`
- changed: `.github/workflows/draft-release.yml`

## Behavior Changed
- changed: installer refuses unsafe install/uninstall roots.
- changed: installer verifies payload checksum/CRC before extraction.
- changed: installer blocks malformed installed version by default.
- changed: shortcuts are created through a checked temporary PowerShell script instead of inline `-Command` text.
- changed: release manifest records artifact size, SHA256, and signing status.
- changed: app-local `FIREDM_TOOLS_DIR` and `FIREDM_INSTALL_DIR\tools` are searched before PATH/Winget for tool discovery.

## Behavior Preserved
- observed: default installer scope remains per-user.
- observed: no global PATH mutation by default.
- observed: user data is preserved during validation uninstall.
- observed: FFmpeg remains external unless explicitly bundled later.

## Tests And Validation
- verified: `169 passed` full pytest.
- verified: x64 build script and one-click batch wrapper completed.
- verified: payload, installer, CLI/import smoke, GUI smoke, upgrade, downgrade block, repair, uninstall, shortcuts, checksums all ran locally.

## Artifacts
- verified: installer `dist/installers/FireDM_Setup_2022.2.5_dev_win_x64.exe`, SHA256 `3f6a8cb90acaa84384536c372cc7b33c8adf9189f5bb82dd2d99bd4c2c8b0662`.
- verified: portable ZIP `dist/portable/FireDM_2022.2.5_win_x64_portable.zip`, SHA256 `19108d0e099e0c6789bcb7fa6ea9d0e1a43f61f8cf8537311579e8411580b096`.
- verified: `dist/release-manifest.json` and `dist/checksums/SHA256SUMS.txt`.

## Remaining Risks
- blocked: unsigned artifacts.
- blocked: manual GUI/download/video/FFmpeg QA not executed.
- blocked: x86/ARM64/universal/MSI/MSIX lanes not implemented.
- blocked: GitHub workflow not run.

## Rollback Considerations
- changed: rollback by reverting `scripts/release/*`, release docs, workflow, tests, and `firedm/tool_discovery.py`.
- observed: generated `dist` output is ignored release output and should be regenerated, not committed, unless maintainer policy changes.
