# FireDM

Homepage: https://github.com/GurucharanSavanth/FireDM

[![Downloads](https://static.pepy.tech/personalized-badge/pyidm?period=total&units=international_system&left_color=grey&right_color=blue&left_text=PyIDM%20Downloads%20(pypi))](https://pepy.tech/project/pyidm)
[![Downloads](https://static.pepy.tech/personalized-badge/firedm?period=total&units=international_system&left_color=grey&right_color=blue&left_text=FireDM%20Downloads%20(pypi))](https://pepy.tech/project/firedm)
![GitHub All Releases](https://img.shields.io/github/downloads/GurucharanSavanth/FireDM/total?color=blue&label=GitHub%20Releases)
![GitHub issues](https://img.shields.io/github/issues-raw/GurucharanSavanth/FireDM?color=blue)
![GitHub closed issues](https://img.shields.io/github/issues-closed-raw/GurucharanSavanth/FireDM?color=blue)

![logo](icons/48x48.png)

FireDM is a Python open-source Internet Download Manager with a Tkinter GUI, command-line mode, LibCurl/pycurl transport, yt-dlp extraction, and ffmpeg post-processing.

## Project Status

This repository is a Windows-first fork/revival of the original FireDM project. The revival work keeps the original user-facing download-manager behavior where practical, but modernizes dependencies, packaging, GitHub Actions, and Windows runtime discovery.

Current verified baseline:
- Windows 10/11 x64
- Python `3.10.11`
- repo-local `.venv`
- `pycurl 7.45.7`
- `yt-dlp 2026.3.17` with `yt-dlp-ejs 0.8.0`
- external `ffmpeg 8.1`
- Deno `2.7.13` for extractor JavaScript runtime support
- PyInstaller one-folder Windows package

Python 3.11 and 3.12 are not advertised as supported yet. They remain validation targets until install, tests, import smoke, and Windows packaging pass.

## Supported Features

- Multi-connection segmented downloads through pycurl/LibCurl.
- Resume, retry, speed limit, proxy, cookies, authentication, referer, and custom user-agent options.
- Video metadata extraction through yt-dlp as the primary extractor.
- Optional legacy youtube-dl compatibility through the `[legacy]` extra.
- Single video, playlist selection, subtitles, thumbnails, DASH/HLS handling, and ffmpeg merge/conversion paths.
- Tkinter GUI, command-line mode, clipboard monitor, scheduler, checksums, themes, and completion actions.

Real GUI interaction, real network downloads, playlist-network behavior, and real ffmpeg post-processing still require manual validation before a release claim. Unit tests cover deterministic seams, but mocked tests are not treated as proof of those live workflows.

## Quick Links

- Architecture: [docs/architecture.md](docs/architecture.md)
- Dependency strategy: [docs/dependency-strategy.md](docs/dependency-strategy.md)
- Testing: [docs/testing.md](docs/testing.md)
- Windows build: [docs/windows-build.md](docs/windows-build.md)
- Windows installer release: [docs/release/WINDOWS_INSTALLER.md](docs/release/WINDOWS_INSTALLER.md)
- Windows portable package: [docs/release/WINDOWS_PORTABLE.md](docs/release/WINDOWS_PORTABLE.md)
- Known issues: [docs/known-issues.md](docs/known-issues.md)
- Legacy refactor plan: [docs/legacy-refactor-plan.md](docs/legacy-refactor-plan.md)
- Windows bootstrap: [bootstrap/windows-dev-setup.md](bootstrap/windows-dev-setup.md)

## Installation

Windows source setup:

```powershell
git clone https://github.com/GurucharanSavanth/FireDM.git
cd FireDM
powershell -ExecutionPolicy Bypass -File .\bootstrap\bootstrap.ps1
```

Manual editable install:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,build]"
```

Linux remains source-compatible where dependencies are available, but this revival pass validates Windows first.

## Running

Source CLI:

```powershell
.\.venv\Scripts\python.exe -m firedm --help
.\.venv\Scripts\python.exe firedm.py --imports-only
```

Source GUI:

```powershell
.\.venv\Scripts\python.exe -m firedm --gui
```

Packaged Windows build:

```powershell
.\dist\FireDM\firedm.exe --help
.\dist\FireDM\FireDM-GUI.exe
```

## Testing

Maintained validation commands:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check firedm\FireDM.py firedm\app_paths.py firedm\extractor_adapter.py firedm\ffmpeg_service.py firedm\tool_discovery.py firedm\setting.py firedm\update.py tests
.\.venv\Scripts\python.exe -m mypy
```

The full legacy tree is not yet Ruff-gated. Ruff and mypy are intentionally scoped to modernized seams and tests.

## Building And Packaging

Wheel/sdist:

```powershell
.\.venv\Scripts\python.exe -m build --no-isolation
.\.venv\Scripts\python.exe -m twine check dist\*.whl dist\*.tar.gz
```

Windows PyInstaller package:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows-build.ps1
```

One-click local Windows installer build:

```powershell
.\build-release.bat
```

The wrapper defaults to the unsigned `dev` channel. Use
`.\build-release.bat stable` only for a maintainer-controlled build with
signing configured or a clearly documented unsigned test artifact.

This writes the x64 installer, portable zip, release notes, manifest, license
inventory, and SHA256 checksums under `dist\installers\`, `dist\portable\`,
`dist\licenses\`, and `dist\checksums\`.

The preferred Windows distributor is the installed-tree payload generated from
the PyInstaller one-folder build, then installed by
`dist\installers\FireDM_Setup_<version>_<channel>_win_x64.exe`. Historical
AppImage and old executable scripts remain for reference only.

## PyInstaller Notes

PyInstaller may still print a warning that tkinter is broken on this Windows baseline. The project keeps a manual Tcl/Tk collection workaround in [scripts/firedm-win.spec](scripts/firedm-win.spec) and build-time asset checks in [scripts/windows-build.ps1](scripts/windows-build.ps1).

A valid Windows package must include:

```text
dist\FireDM\_internal\tkinter\__init__.py
dist\FireDM\_internal\_tcl_data\init.tcl
dist\FireDM\_internal\_tk_data\tk.tcl
```

Do not remove the manual spec override until PyInstaller detection works without warnings and `dist\FireDM\firedm.exe --imports-only` confirms Tk imports.

## External Tools

`ffmpeg` is external by default. FireDM discovers `ffmpeg.exe` in this order and then verifies it with `ffmpeg -version`:

- saved configured path
- application/current directory
- global settings directory
- `PATH`
- Winget package folders on Windows

`ffprobe` is checked separately for diagnostics and metadata support. FireDM first looks beside the resolved/saved `ffmpeg` path, then uses the same application directory, settings directory, `PATH`, and Winget fallback search. This patch does not make `ffprobe` mandatory for current download enqueue or post-processing behavior.

If ffmpeg is missing, FireDM no longer downloads stale binaries from the historical upstream repository. The GUI opens ffmpeg installation guidance instead.

Deno is also external by default for yt-dlp JavaScript-runtime support. Keep Deno on `PATH` or in the discoverable Windows package location.

## GitHub Actions / CI

Current workflows:

- `windows-smoke.yml`: Windows source install, tests, scoped Ruff, package build, PyInstaller package smoke, artifact upload.
- `draft-release.yml`: tag/manual Windows x64 installer lane using `scripts/release/build_windows.py --arch x64`, then draft GitHub release creation from the installer, portable ZIP, checksums, manifest, and bundled-component inventory. Manual runs default to `dev`; tag builds force `stable` and require signing configuration.
- `pypi-release.yml`: PyPI package build, `twine check`, and trusted-publishing upload path.

CI currently targets Python 3.10 because that is the only verified runtime. Add 3.11/3.12 to CI only when the project is ready to fix and support failures found on those versions.

## Validation Status

| Area | Status |
| --- | --- |
| Source help/import smoke | Verified on Python 3.10.11 |
| Unit tests | Maintained through `pytest` |
| Scoped lint/type checks | Maintained for modernized seams |
| Wheel/sdist build | Verified with `python -m build --no-isolation` |
| Windows PyInstaller build | Verified on the current Windows baseline |
| Packaged CLI import smoke | Verified with `dist\FireDM\firedm.exe --imports-only` |
| Full GUI interaction | Manual/unverified |
| Real file downloads | Manual/unverified |
| Playlist network behavior | Manual/unverified |
| Real ffmpeg post-processing | Manual/unverified |
| Python 3.11 | Unvalidated locally |
| Python 3.12 | Blocked locally by broken Store launcher |

## Manual Release Validation

Before publishing a Windows release, run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m build --no-isolation
.\.venv\Scripts\python.exe -m twine check dist\*.whl dist\*.tar.gz
powershell -ExecutionPolicy Bypass -File .\scripts\windows-build.ps1
.\.venv\Scripts\python.exe scripts\release\build_windows.py --arch x64 --channel dev
.\dist\FireDM\firedm.exe --help
.\dist\FireDM\firedm.exe --imports-only
.\dist\FireDM\FireDM-GUI.exe
```

Manual checks still required:

- Start GUI, paste a normal direct-download URL, validate queue/progress/cancel/resume behavior.
- Download a safe small file and verify final path, checksum option, and resume behavior.
- Test one single-video URL and one playlist URL with yt-dlp metadata extraction.
- Test one ffmpeg-required DASH/HLS item and verify merge/post-processing output.
- Remove or rename ffmpeg temporarily and verify missing-tool error/reporting behavior.

## Troubleshooting

- If `ffmpeg` is installed but not found or not usable, check the actual install path and run `ffmpeg -version`. Agent shells can have stale `PATH`; FireDM also checks Winget package folders where the current process has access. If Winget package folders are access-denied, add ffmpeg to `PATH` or copy `ffmpeg.exe` beside the app. `ffprobe` health is reported separately and can be fixed by placing `ffprobe.exe` beside `ffmpeg.exe` or on `PATH`.
- If PyInstaller reports tkinter as broken, keep the manual Tcl/Tk spec override and verify packaged Tk assets exist.
- If `.venv` dependency installation fails on Windows, verify Python `3.10.11` and the official pycurl wheel path before attempting source builds.
- If `dist\FireDM` cannot be removed during rebuild, close stale packaged FireDM processes.

## Known Limitations

- `controller.py`, `video.py`, and `tkview.py` are still large stateful modules. See [docs/legacy-refactor-plan.md](docs/legacy-refactor-plan.md).
- GUI, live downloads, playlist network behavior, and ffmpeg post-processing need manual release validation.
- Python 3.11/3.12 support is intentionally not advertised yet.
- Packaged Windows builds are release-replace, not in-place self-updating.
- Linux AppImage scripts are historical reference, not the preferred current release path.

## Contributing

Open issues at https://github.com/GurucharanSavanth/FireDM/issues/new.

Developer references:
- [docs/developer_guide.md](docs/developer_guide.md)
- [todo.md](todo.md)
- [contributors.md](contributors.md)

## Credits / Maintainers

Original author:
Mahmoud Elshahat ( 2019-2022 original FireDM );

Gurucharan Savanth ( 2026 fork/revival modernization ) Email: savanthgc@gmail.com
