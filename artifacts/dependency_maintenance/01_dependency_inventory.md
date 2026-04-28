# 01 Dependency Inventory

## Runtime Python

observed/kept:
- `plyer`: runtime desktop notification/platform helper.
- `certifi`: runtime CA bundle; portable validator requires `_internal/certifi/cacert.pem`.
- `yt-dlp[default]`: primary extractor.
- `yt-dlp-ejs`: observed installed through extractor defaults; checked as optional support.
- `pycurl`: required transport.
- `Pillow`: GUI/image runtime.
- `pystray`: tray runtime.
- `awesometkinter`: Tk widgets/themes.
- `packaging`: version comparison.
- `distro`: Linux-only runtime.
- `youtube_dl`: optional legacy extra only.

## Dev/Test/Build

observed/kept:
- `pytest`, `pytest-cov`
- `ruff`
- `mypy`
- `build`, `twine`, `wheel`, `setuptools`
- `PyInstaller`

## External/native tools

observed required:
- Python `3.10.x`, 64-bit
- PowerShell
- Git
- Tcl/Tk from Python runtime
- certifi CA bundle

observed optional:
- GitHub CLI: installed; used only for explicit publish.
- FFmpeg/ffprobe: warning; not found in current shell.
- Deno: optional external yt-dlp JavaScript runtime; not bundled; checked by preflight.

## Portable contents policy

changed required in portable ZIP:
- `firedm.exe`
- `FireDM-GUI.exe`
- `_internal/tkinter/__init__.py`
- `_internal/_tcl_data/init.tcl`
- `_internal/_tk_data/tk.tcl`
- `_internal/certifi/cacert.pem`
- `README_PORTABLE.txt`
- `build-metadata.json`
- `payload-manifest.json`

blocked:
- FFmpeg/ffprobe not bundled.
- Deno not bundled.
- true portable-only config root remains blocked in app runtime.
