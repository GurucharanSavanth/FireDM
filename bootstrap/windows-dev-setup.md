# Windows Development Setup

## Supported baseline
- Verified host: Windows 10/11 x64
- Verified Python: `3.10.11`
- Supported package range: `>=3.10,<3.13`
- Required external binary: `ffmpeg`

## Prerequisites
Install these before bootstrapping:

```powershell
winget install --id Git.Git --exact
winget install --id Python.Python.3.10 --exact --accept-source-agreements --accept-package-agreements
winget install --id Gyan.FFmpeg.Essentials --exact --accept-source-agreements --accept-package-agreements
```

`pycurl` now has an official Windows wheel for the validated baseline, so local native compilation is not required for normal development.

## Bootstrap
From the repo root:

```powershell
.\bootstrap\bootstrap.ps1
```

Override the interpreter if needed:

```powershell
.\bootstrap\bootstrap.ps1 -PythonExe "C:\Users\<you>\AppData\Local\Programs\Python\Python310\python.exe"
```

The script will:
- create `.venv` if missing
- upgrade bootstrap tooling
- install FireDM with `.[dev,build]`
- run `pytest`
- run CLI/import smoke checks
- write `bootstrap/environment-manifest.json`

## Manual verification

```powershell
.\.venv\Scripts\python.exe -m firedm --help
.\.venv\Scripts\python.exe firedm.py --imports-only
ffmpeg -version
```

## Environment notes
- `PYTHONUTF8=1` is recommended on Windows for consistent UTF-8 console/config behavior.
- FireDM prefers a local writable settings folder when running from source. On a normal checkout, `firedm\setting.cfg` is expected.
- Global fallback remains `%APPDATA%\.FireDM`.

## Packaging
Build the Windows distribution with:

```powershell
.\scripts\windows-build.ps1
```

See [docs/windows-build.md](../docs/windows-build.md) for release details.
