# Windows Build And Packaging

## Decision
Windows distribution now targets **PyInstaller**. The legacy cx_Freeze scripts remain in the repo for historical reference, but they are no longer the preferred release path.

Reasons:
- PyInstaller is easier to reproduce on current Windows Python versions
- it supports a manual Tcl/Tk collection workaround when PyInstaller's Tk hook
  mis-detects this Windows Python layout
- it supports explicit hidden-import collection for dynamic extractor imports
- it avoids the old frozen-layout assumptions baked into the cx_Freeze updater flow

## Build prerequisites
- validated Python environment from [bootstrap/windows-dev-setup.md](../bootstrap/windows-dev-setup.md)
- `ffmpeg` available on `PATH` for runtime verification

## Build command

```powershell
.\scripts\windows-build.ps1 -Channel dev -Arch x64
```

The script uses the already-bootstrapped repo environment by default. It does
not install packages unless `-InstallLocalDeps` is passed, and that install is
limited to the repo-local Python environment selected by `-PythonExe` or
`.venv\Scripts\python.exe`.

Validation-only preflight:

```powershell
.\scripts\windows-build.ps1 -Channel dev -Arch x64 -ValidateOnly
```

Explicit local dependency refresh:

```powershell
.\scripts\windows-build.ps1 -Channel dev -Arch x64 -InstallLocalDeps
```

Optional GUI smoke in the same script:

```powershell
.\scripts\windows-build.ps1 -SmokeGui
```

One-click local release build:

```powershell
.\build-release.bat
```

The one-click wrapper runs:

```powershell
.\.venv\Scripts\python.exe scripts\release\build_windows.py --arch x64 --channel dev
```

That installer release path generates the next `YYYYMMDD_V{N}` build ID, builds
the PyInstaller one-dir payload, validates
the payload and portable ZIP, creates the x64 installer bootstrapper, validates
silent install, repair, uninstall, upgrade, and downgrade blocking, collects
bundled-component license metadata, writes a dependency status report, writes a
release manifest, and generates SHA256 checksums.

## Output
PyInstaller writes a one-folder distribution to:

```text
dist\FireDM\
```

Expected executables:
- `dist\FireDM\firedm.exe`
- `dist\FireDM\FireDM-GUI.exe`

The new installer lane writes GitHub-ready assets under:

```text
dist\installers\
dist\portable\
dist\checksums\
dist\licenses\
```

Expected release files:
- `FireDM_Setup_<build_id>_<channel>_win_x64\FireDM_Setup_<build_id>_<channel>_win_x64.exe`
- `FireDM_Setup_<build_id>_<channel>_win_x64\FireDM_<build_id>_<channel>_win_x64_payload.zip`
- `FireDM_Setup_<build_id>_<channel>_win_x64.manifest.json`
- `FireDM_<build_id>_<channel>_win_x64_portable.zip`
- `SHA256SUMS_<build_id>.txt`
- `FireDM_release_notes_<build_id>.md`
- `FireDM_release_manifest_<build_id>.json`
- `dependency-status_<build_id>.json`
- `license-inventory_<build_id>.json`

The installer is a PyInstaller one-dir bundle. Keep the EXE, `_internal`
runtime folder, and payload ZIP sidecar together; the installer verifies the
payload SHA256 before extraction.

Stable compatibility aliases are also written: `release-manifest.json`,
`release-body.md`, `checksums\SHA256SUMS.txt`, and
`licenses\license-inventory.json`.

## Smoke verification

```powershell
.\dist\FireDM\firedm.exe --help
.\dist\FireDM\firedm.exe --imports-only
.\.venv\Scripts\python.exe scripts\release\validate_portable.py --archive dist\portable\<portable>.zip
Start-Process .\dist\FireDM\FireDM-GUI.exe
```

The build script also verifies these packaged Tk assets:

```text
dist\FireDM\_internal\tkinter\__init__.py
dist\FireDM\_internal\_tcl_data\init.tcl
dist\FireDM\_internal\_tk_data\tk.tcl
```

PyInstaller can still log a tkinter/Tcl warning in this environment. That
warning is not ignored blindly: keep `scripts/firedm-win.spec` collecting the
stdlib tkinter package, Tcl/Tk data folders, `_tkinter.pyd`, `tcl86t.dll`, and
`tk86t.dll`; remove the workaround only after the warning disappears and the
packaged import smoke still passes.

Packaged Windows builds are **release-replace**, not self-patching. The in-app updater opens the release page instead of rewriting packaged Python files in place.

## CI release path

- `.github/workflows/windows-smoke.yml` runs tests, scoped Ruff, `python -m build`, PyInstaller, source smoke, packaged CLI smoke, and uploads the `dist\FireDM` artifact.
- `.github/workflows/draft-release.yml` runs the x64 installer lane, uploads the generated build-ID artifacts, and dry-runs the GitHub release helper unless manual `publish_release=true` or a `build-YYYYMMDD_VN` tag run is used. Manual runs default to `dev`; tag builds force `stable` and require signing.
- `.github/workflows/pypi-release.yml` builds wheel/sdist from `pyproject.toml`, checks metadata with Twine, and publishes through PyPI trusted publishing when the PyPI project is configured for this repository.

To create a draft GitHub release from a local machine with GitHub CLI installed:

```powershell
.\.venv\Scripts\python.exe scripts\release\github_release.py --manifest dist\release-manifest.json
```

Add `--publish --draft --prerelease` only when the maintainer intends to write
to GitHub.
