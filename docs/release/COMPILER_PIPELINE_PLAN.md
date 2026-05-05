# Compiler Pipeline Plan

Status: changed 2026-05-03.

## Local Build Evidence
- observed: `scripts/windows-build.ps1` runs PyInstaller against `scripts/firedm-win.spec` for Windows x64.
- changed: root `windows-build.ps1` is the canonical Windows build entry point; `scripts/windows-build.ps1` forwards to it.
- observed: Linux build scripts exist but refuse non-Linux hosts for the Linux PyInstaller lane.
- observed: `nuitka` is not available on PATH and no Nuitka build lane exists in scripts.
- observed: current generated `dist/` and `build/` artifacts are stale for this checkout and are not proof of a current build.

## Official Tool Findings
| Tool | Source | Finding | Decision |
| --- | --- | --- | --- |
| PyInstaller | https://pyinstaller.org/en/stable/requirements.html | PyInstaller 6.20.0 runs on Windows 8+ and Linux/macOS with platform prerequisites. | first backend |
| PyInstaller one-folder/one-file | https://pyinstaller.org/en/stable/operating-mode.html | output is OS/Python/word-size specific; one-file extracts to temp and should follow one-folder validation. | one-folder first |
| Nuitka | https://nuitka.net/user-documentation/user-manual.html | needs a C compiler; Windows compiler choices include Visual Studio 2022+. | deferred optional backend |
| Nuitka modes | https://nuitka.net/user-documentation/use-cases.html | standalone and onefile modes exist; onefile extracts on target. | standalone before onefile |

## Planned Orchestrator
- changed: root `windows-build.ps1` drives backend `Auto|PyInstaller|Nuitka`, mode `Debug|Release`, kind `OneFolder|OneFile|PortableZip`, dry-run, logs, manifest, checksums, changelog compilation, and smoke checks.
- blocked: a separate double-click launcher is not restored in this dirty tree; `build-release.bat` is absent and root PowerShell is authoritative.
- blocked: no global installs, no PATH mutation, no destructive cleanup outside repo.

## Backend Order
1. PyInstaller one-folder on Windows x64.
2. PyInstaller portable ZIP from validated one-folder payload.
3. PyInstaller one-file only after one-folder smoke.
4. Nuitka standalone after compiler detection and data-file mapping.
5. Nuitka onefile after standalone smoke.
