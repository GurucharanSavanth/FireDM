# Windows Build And Packaging

## Decision
Windows distribution now targets **PyInstaller**. The legacy cx_Freeze scripts remain in the repo for historical reference, but they are no longer the preferred release path.

Reasons:
- PyInstaller is easier to reproduce on current Windows Python versions
- it handles Tkinter well
- it supports explicit hidden-import collection for dynamic extractor imports
- it avoids the old frozen-layout assumptions baked into the cx_Freeze updater flow

## Build prerequisites
- validated Python environment from [bootstrap/windows-dev-setup.md](../bootstrap/windows-dev-setup.md)
- `ffmpeg` available on `PATH` for runtime verification

## Build command

```powershell
.\scripts\windows-build.ps1
```

Optional GUI smoke in the same script:

```powershell
.\scripts\windows-build.ps1 -SmokeGui
```

## Output
PyInstaller writes a one-folder distribution to:

```text
dist\FireDM\
```

Expected executables:
- `dist\FireDM\firedm.exe`
- `dist\FireDM\FireDM-GUI.exe`

## Smoke verification

```powershell
.\dist\FireDM\firedm.exe --help
Start-Process .\dist\FireDM\FireDM-GUI.exe
```

Packaged Windows builds are **release-replace**, not self-patching. The in-app updater opens the release page instead of rewriting packaged Python files in place.
