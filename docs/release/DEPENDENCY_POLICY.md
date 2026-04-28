# Dependency Policy

Evidence labels: observed, changed, blocked.

## Canonical declarations

observed: `pyproject.toml` is the canonical Python package declaration. `requirements.txt` mirrors runtime dependencies for older tooling only.

observed runtime dependencies:
- `plyer`, `certifi`, `yt-dlp[default]`, `pycurl`, `Pillow`, `pystray`, `awesometkinter`, `packaging`
- Linux-only: `distro`
- optional legacy extractor: `youtube_dl` through `[legacy]`

observed dev/build dependencies:
- tests: `pytest`, `pytest-cov`
- lint/type/build/release: `ruff`, `mypy`, `build`, `twine`, `pyinstaller`, `wheel`, `setuptools`

## Preflight

changed: run this before build or release work:

```powershell
.\.venv\Scripts\python.exe scripts\release\check_dependencies.py --arch x64 --channel dev
```

Use JSON for CI or handoff evidence:

```powershell
.\.venv\Scripts\python.exe scripts\release\check_dependencies.py --arch x64 --channel dev --skip-portable --json
```

Required failures return non-zero. Optional external tools return warnings.

## Native and external tools

observed required local tools for the Windows lane:
- Python `3.10.x`, 64-bit
- PowerShell
- Git
- PyInstaller
- Tcl/Tk from the Python runtime
- certifi CA bundle

observed optional tools:
- GitHub CLI, required only for explicit release publishing
- FFmpeg/ffprobe, required only for media post-processing flows that use them
- Deno, optional for yt-dlp JavaScript runtime support when extractors need it

blocked: FFmpeg/ffprobe and Deno are not bundled. Do not claim bundled post-processing or bundled JavaScript-runtime readiness until redistribution source, license text, checksums, and validation are recorded.

## Portable runtime rule

changed: portable packages must launch without end-user Python or pip. The frozen PyInstaller runtime, Python packages, certifi bundle, Tcl/Tk assets, metadata, and README must be inside the ZIP.

Validate with:

```powershell
.\.venv\Scripts\python.exe scripts\release\validate_portable.py --archive dist\portable\<portable>.zip
```
