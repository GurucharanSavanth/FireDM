# Windows Bootstrap Guide

## Goal
Revive FireDM on native Windows 10/11 with a reproducible Python 3.10 baseline, isolated venv, verified dependencies, verified `pycurl`, verified `ffmpeg`, and a first successful local run.

## Known-Good Baseline
- Host OS: Windows 11 64-bit, build `26200`
- Repo snapshot: `88240da7f005c9a7a49a4e2d7f6928fd7fddf043`
- Python target: `3.10.11`
- Virtualenv: `FireDM-win-bootstrap\\.venv`
- FFmpeg: `8.1` essentials build from `Gyan.FFmpeg.Essentials`
- `pycurl`: `7.45.7` official `cp310-win_amd64` wheel from PyPI

## Repo Runtime Facts
- Entrypoints: root `firedm.py`, `python -m firedm`, and console script `firedm`
- Modes: GUI by default, CLI when args are passed, `--interactive` for terminal mode
- Video extractors: both `youtube_dl` and `yt_dlp`; default is `yt_dlp`
- `ffmpeg` lookup order: saved path, app folder, global settings folder, then `PATH`
- Frozen-update logic in `firedm/update.py` still assumes legacy cx_Freeze/AppImage behavior

## Install Base Tools
Run in PowerShell:

```powershell
winget install --id Python.Python.3.10 --exact --accept-source-agreements --accept-package-agreements --override "InstallAllUsers=0 PrependPath=0 Include_test=0 Include_launcher=1"
winget install --id Microsoft.VisualStudio.2022.BuildTools --exact --accept-source-agreements --accept-package-agreements --override "--quiet --wait --norestart --nocache --installPath C:\Users\<you>\AppData\Local\Programs\VSBuildTools2022 --add Microsoft.VisualStudio.Workload.VCTools"
winget install --id Gyan.FFmpeg.Essentials --exact --accept-source-agreements --accept-package-agreements
```

Open a new shell after installer-managed `PATH` updates.

## Clone And Prepare Venv

```powershell
git clone --depth 1 https://github.com/GurucharanSavanth/FireDM.git FireDM-win-bootstrap
C:\Users\<you>\AppData\Local\Programs\Python\Python310\python.exe -m venv .\FireDM-win-bootstrap\.venv
.\FireDM-win-bootstrap\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
```

## Install Dependencies
Install in safe order:

```powershell
.\.venv\Scripts\python.exe -m pip install certifi youtube_dl yt_dlp
.\.venv\Scripts\python.exe -m pip install Pillow pystray awesometkinter plyer
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: pycurl
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
```

## Verification

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m firedm --help
.\.venv\Scripts\python.exe firedm.py --imports-only
.\.venv\Scripts\firedm.exe --help
ffmpeg -version
```

Observed good result:
- all major imports succeeded
- `--imports-only` imported `pycurl`, `tkinter`, `yt_dlp`, `youtube_dl`, `awesometkinter`, `pystray`
- GUI smoke run launched and exited cleanly
- `ffmpeg` was detected on `PATH`

## Important Windows Quirks
- Source runs do **not** default to `%APPDATA%\\.FireDM` when repo is writable. `firedm/setting.py` chooses local `firedm\\setting.cfg` first.
- In this bootstrap, settings were written to `FireDM-win-bootstrap\\firedm\\setting.cfg`.
- `PYTHONUTF8=1` was set at User scope for consistent UTF-8 behavior.

## Remaining Blocker
Visual Studio Build Tools installed, and `MSBuild.exe` is present, but `vswhere -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64` returned no matching instance and no `cl.exe` was found. This did **not** block FireDM because `pycurl` now has an official Windows wheel for Python 3.10. If future native builds are required, revisit Build Tools with explicit elevated component install.

## Upgrade Path
Stabilize on Python 3.10 first. After codebase smoke tests and download-path tests pass, trial Python 3.11+ one version at a time and re-verify:
- `pycurl` wheel availability
- Tkinter GUI launch
- extractor imports
- actual download + ffmpeg post-processing
