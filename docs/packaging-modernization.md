# Packaging Modernization

## Current Policy

Packaging metadata lives in `pyproject.toml`. `setup.py` is retained only as a compatibility shim.

Build source distributions and wheels:

```powershell
.\.venv\Scripts\python.exe -m build
```

Build Windows app:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows-build.ps1
```

## Why PyInstaller Stays

PyInstaller is still the Windows release tool because the app is a Tkinter desktop program with data files, hidden imports, and two launch modes. The spec file is intentionally explicit and now collects:

- `certifi` data
- `yt_dlp` modules
- `yt_dlp_ejs` modules and data
- optional `youtube_dl` modules only when installed

## External Binaries

FFmpeg and Deno are not bundled by default. Packaged builds locate them from app-local paths, `PATH`, or Winget package directories. Bundling remains a future release decision because it affects licensing, build size, and update cadence.
