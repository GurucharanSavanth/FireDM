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
.\scripts\windows-build.ps1
```

The script installs the build extra with `pip install --no-build-isolation -e ".[build]"` and uses `python -m build --no-isolation` for the local package build, so the Windows package path uses the already-bootstrapped repo environment instead of creating temporary build environments that may need network access.

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
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows-build.ps1 -Release
```

That complete release path runs tests, scoped Ruff, wheel/sdist build, Twine
metadata check, PyInstaller, packaged CLI smoke checks, release zip creation,
release notes, a JSON manifest, and SHA256 checksums.

## Output
PyInstaller writes a one-folder distribution to:

```text
dist\FireDM\
```

Expected executables:
- `dist\FireDM\firedm.exe`
- `dist\FireDM\FireDM-GUI.exe`

When `-Release` is used, GitHub-ready assets are written under:

```text
release\FireDM-<version>-windows-x64\
```

Expected release files:
- `FireDM-<version>-windows-x64.zip`
- `firedm-<version>-py3-none-any.whl`
- `firedm-<version>.tar.gz`
- `SHA256SUMS.txt`
- `release-body.md`
- `release-manifest.json`

## Smoke verification

```powershell
.\dist\FireDM\firedm.exe --help
.\dist\FireDM\firedm.exe --imports-only
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
- `.github/workflows/draft-release.yml` runs `scripts/windows-build.ps1 -Release`, uploads the generated release folder, and creates a draft GitHub release from the script-generated zip, checksums, manifest, and notes.
- `.github/workflows/pypi-release.yml` builds wheel/sdist from `pyproject.toml`, checks metadata with Twine, and publishes through PyPI trusted publishing when the PyPI project is configured for this repository.

To create a draft GitHub release from a local machine with GitHub CLI installed:

```powershell
.\scripts\windows-build.ps1 -Release -PublishDraftRelease -GithubRepo GurucharanSavanth/FireDM
```

Do not use `-PublishDraftRelease` unless you intend to write to GitHub.
