# Release Artifact Layout

Status: changed 2026-05-03.

## Canonical Root

- changed: root `.\release` is the canonical Windows build output directory for `.\windows-build.ps1`.
- changed: `dist` remains a legacy compatibility mirror for old release scripts, not the final artifact authority.
- blocked: old generated files already under `release` or `dist` are not proof of a current build.

## Required Files

Every successful canonical script run writes or refreshes:

| Path | Purpose |
| --- | --- |
| `release\build.log` | Timestamped build log. |
| `release\manifest.json` | Build metadata, repo state, validation results, cleanup actions, warnings, blocked items, release file list, and selected hashes. |
| `release\checksums.sha256` | SHA256 hashes for files under `release`, excluding `checksums.sha256` itself. |
| `release\CHANGELOG-COMPILED.md` | Compiled changelog and release notes from local sources. |
| `release\plugins-manifest.json` | Machine-readable plugin discovery output; no plugin is enabled by the build script. |
| `release\plugins-manifest.txt` | Human-readable plugin discovery summary for release review. |

## App Artifacts

| Kind | Expected Output | Status |
| --- | --- | --- |
| OneFolder | `release\FireDM\` containing `firedm.exe` (CLI/Tk) and `FireDM-GUI.exe` (Tk no-console launcher) | verified on this Windows host by the canonical PyInstaller run. |
| PortableZip | `release\FireDM.zip` | implemented in script; requires real PyInstaller run for proof. |
| OneFile | single executable under `release` | blocked until a one-file spec is validated. |

## GUI Entry Points

| Executable | Backend | Status | Notes |
| --- | --- | --- | --- |
| `firedm.exe` | CLI / Tk | default | `--gui` opens Tkinter MainWindow. |
| `FireDM-GUI.exe` | Tkinter (no console) | default | Same Tk codepath as `firedm.exe --gui`. |

## Legacy Compatibility

- changed: `scripts\windows-build.ps1` forwards to root `windows-build.ps1`.
- planned: older callers that expect `dist\FireDM` may continue during transition because real OneFolder builds mirror the payload there for compatibility.
- blocked: `build-release.bat` is absent in the current dirty tree, so docs should prefer root `.\windows-build.ps1`.

## Verification Rule

Do not claim release readiness from file presence alone. Release-ready requires a
real package build, manifest/checksum generation, and smoke checks that were run
and observed for the selected artifact.
