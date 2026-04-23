# Windows Bootstrap Log

## Phase 0: Recon
- Read `README.md`, `requirements.txt`, `setup.py`, `firedm/FireDM.py`, `firedm/config.py`, `firedm/setting.py`, `firedm/dependency.py`, `firedm/video.py`, `firedm/update.py`, and `docs/developer_guide.md`.
- Confirmed entrypoints: `firedm.py`, `python -m firedm`, `console_scripts: firedm = firedm.FireDM:main`.
- Confirmed runtime modes: GUI default, CLI with args, interactive terminal mode with `--interactive`.
- Confirmed dependency model: manual `requirements.txt` + `dependency.py` auto-installer fallback.
- Confirmed extractor handling: both `youtube_dl` and `yt_dlp`, default `yt_dlp`.
- Confirmed ffmpeg handling: app folder -> global settings folder -> system `PATH`.
- Confirmed frozen assumptions: `update.py` still has cx_Freeze/AppImage update logic.

## Phase 1: Base Software

### Commands
```powershell
python --version
py -0p
git --version
winget --version
winget install --id Python.Python.3.10 --exact --accept-source-agreements --accept-package-agreements --override "InstallAllUsers=0 PrependPath=0 Include_test=0 Include_launcher=1"
winget install --id Microsoft.VisualStudio.2022.BuildTools --exact --accept-source-agreements --accept-package-agreements --override "--quiet --wait --norestart --nocache --installPath C:\Users\SavanthGC\AppData\Local\Programs\VSBuildTools2022 --add Microsoft.VisualStudio.Workload.VCTools"
winget install --id Gyan.FFmpeg.Essentials --exact --accept-source-agreements --accept-package-agreements
```

### Verified Outputs
- Python before install: `Python 3.12.10` via Store shim
- Python after install: `Python 3.10.11`
- Git: `git version 2.53.0.windows.2`
- FFmpeg after install: `ffmpeg version 8.1-essentials_build-www.gyan.dev`
- Build Tools instance: `Visual Studio Build Tools 2022 17.14.31`
- MSBuild present: `17.14.40.60911`
- `cl.exe` not found; VC compiler component still unresolved

## Phase 2: Environment Variables

### Explicit Change
```powershell
[Environment]::SetEnvironmentVariable('PYTHONUTF8','1','User')
```

### Verified
- Old User value: empty
- New User value: `1`
- Reason: force UTF-8 behavior for legacy Windows console/config handling

### Installer-Managed PATH Additions
- `C:\Users\SavanthGC\AppData\Local\Programs\Python\Python310\Scripts\`
- `C:\Users\SavanthGC\AppData\Local\Programs\Python\Python310\`
- `C:\Users\SavanthGC\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-essentials_build\bin`

## Phase 3: Fresh Checkout And Venv

### Commands
```powershell
git clone --depth 1 https://github.com/GurucharanSavanth/FireDM.git G:\Personal Builds\Revive-FireDM\FireDM-win-bootstrap
C:\Users\SavanthGC\AppData\Local\Programs\Python\Python310\python.exe -m venv G:\Personal Builds\Revive-FireDM\FireDM-win-bootstrap\.venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
```

### Verified
- Repo commit: `88240da7f005c9a7a49a4e2d7f6928fd7fddf043`
- Venv Python: `3.10.11`
- Venv pip: `26.0.1`

## Phase 4: Dependency Resolution

### Commands
```powershell
.\.venv\Scripts\python.exe -m pip install certifi youtube_dl yt_dlp
.\.venv\Scripts\python.exe -m pip install Pillow pystray awesometkinter plyer
.\.venv\Scripts\python.exe -m pip index versions pycurl
.\.venv\Scripts\python.exe -m pip download --only-binary=:all: --no-deps pycurl -d .\wheelhouse
.\.venv\Scripts\python.exe -m pip install --no-deps --only-binary=:all: pycurl -v
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
```

### Result
- `pycurl` wheel available from PyPI: `pycurl-7.45.7-cp310-cp310-win_amd64.whl`
- No source build required
- `requirements.txt` resolved cleanly on Windows; Linux-only `distro` marker skipped

## Phase 5: Import And Entrypoint Smoke

### Commands
```powershell
.\.venv\Scripts\python.exe -m firedm --help
.\.venv\Scripts\python.exe firedm.py --imports-only
.\.venv\Scripts\firedm.exe --help
```

### Result
- Major module imports: all passed
- `--help`: passed
- `--imports-only`: passed
- Editable console entrypoint: passed

## Phase 6: First GUI Run

### Result
- GUI launched
- GUI mainloop ran for ~5 seconds
- Graceful quit succeeded
- `ffmpeg` detection succeeded
- `setting.cfg` created
- Actual source-run settings folder was local repo path:
  `G:\Personal Builds\Revive-FireDM\FireDM-win-bootstrap\firedm`
- Global fallback folder remained:
  `C:\Users\SavanthGC\AppData\Roaming\.FireDM`

## Raw Logs
Full raw command outputs were captured in:

```text
G:\Personal Builds\Revive-FireDM\FireDM-win-bootstrap\bootstrap-logs
```

Files include:
- `01-upgrade-bootstrap.txt`
- `02-install-pure.txt`
- `03-install-gui.txt`
- `04a-pycurl-index.txt`
- `04b-pycurl-download-binary.txt`
- `04c-pycurl-install.txt`
- `04d-pycurl-verify.txt`
- `05-install-requirements.txt`
- `06a-import-sweep.txt`
- `06b-module-help.txt`
- `06c-imports-only.txt`
- `07-gui-smoke.txt`
- `08-editable-install.txt`
- `09-entrypoint-help.txt`

## Remaining Blocker
- Build Tools instance installed, but native MSVC compiler payload is not verifiable:
  - `vswhere -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64` returned `[]`
  - `cl.exe` not found under install path
- Current repo bootstrap is still successful because official `pycurl` wheel removed need for local native build.
