# 00 Repo Packaging Discovery

Evidence labels: observed, inferred, blocked.

## Local State
- observed: Path is `G:\Personal Builds\Revive-FireDM\FireDM - Branch`.
- observed: Branch is `main`; last commit is `836a54d _`; remote is `origin https://github.com/GurucharanSavanth/FireDM.git`.
- observed: Working tree was already dirty before this installer pass. Existing modified/untracked files include FireDM source, plugin/native-host files, tests, `scripts/windows-build.ps1`, `.github/workflows/draft-release.yml`, `build-release.bat`, and prior artifacts.
- observed: Python is repo-local `.venv` Python `3.10.11`, 64-bit AMD64.
- observed: OS is Windows `10.0.26200`, PowerShell `5.1.26100.8115`, host architecture `X64`.

## Files Inspected
- observed: `AGENTS.md`, `README.md`, `pyproject.toml`, `setup.py`, `requirements.txt`.
- observed: `docs/windows-build.md`, `docs/packaging-modernization.md`, `docs/dependency-strategy.md`, `docs/testing.md`, `docs/known-issues.md`, release-adjacent docs.
- observed: `scripts/windows-build.ps1`, `scripts/firedm-win.spec`, legacy `scripts/exe_build/*`, legacy `scripts/appimage/*`, verification scripts.
- observed: `.github/workflows/windows-smoke.yml`, `.github/workflows/draft-release.yml`, `.github/workflows/pypi-release.yml`.
- observed: `tests/*`, `firedm/*`, `firedm/plugins/*`, `firedm/native_host.py`, `firedm/native_messaging.py`.

## Current Build System
- observed: Python packaging is driven by `pyproject.toml`; `setup.py` is a shim.
- observed: `scripts/firedm-win.spec` builds a PyInstaller one-dir `dist\FireDM` containing `firedm.exe` and `FireDM-GUI.exe`.
- observed: `scripts/windows-build.ps1 -Release` currently runs pytest, scoped Ruff, wheel/sdist build, Twine check, PyInstaller, packaged CLI smoke, ZIP, manifest, and checksums.
- observed: Existing release output is a portable ZIP under `release\FireDM-2022.2.5-windows-x64\`.

## Installer State
- observed: No `installer/` directory, `.iss`, `.wxs`, `.wixproj`, or MSIX manifest was found in `rg --files`.
- observed: `iscc.exe`, `candle.exe`, and `wix.exe` are not available on PATH in this shell.
- inferred: The repo currently has a portable/release ZIP pipeline, not a real installer with uninstall registry entries, shortcuts, repair, or downgrade blocking.

## Entry Points
- observed: `pyproject.toml` declares `firedm = firedm.FireDM:main` and `firedm-native-host = firedm.native_host:main`.
- observed: Source launcher is `firedm.py`.
- observed: Packaged launchers are `dist\FireDM\firedm.exe` and `dist\FireDM\FireDM-GUI.exe`.

## Dependency And Runtime Model
- observed: Runtime dependencies include `pycurl`, `yt-dlp[default]`, `Pillow`, `certifi`, `pystray`, `awesometkinter`, and Tkinter from Python stdlib.
- observed: PyInstaller spec explicitly collects Tcl/Tk assets, certifi, yt-dlp-ejs, pystray/yt-dlp/youtube_dl hidden imports, and Windows runtime binaries.
- observed: FFmpeg/Deno are currently external by policy; current PyInstaller payload does not bundle FFmpeg/ffprobe.
- inferred: End-user install can be Python-free because PyInstaller bundles Python runtime/DLLs, stdlib, native extensions, and Tcl/Tk.

## Current Packaging Risks
- observed: No local production installer tool is installed.
- observed: No real installer validation scripts exist under `scripts/release/`.
- inferred: Universal x86/x64/ARM64 bootstrapper cannot be honestly produced from this x64-only host without per-arch payloads.
- inferred: FFmpeg bundling is blocked until licensing/source/checksum decisions are documented.
- inferred: MSI/MSIX are blocked until WiX/MSIX tooling and signing are available.

