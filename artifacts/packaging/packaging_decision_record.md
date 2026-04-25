# Packaging Decision Record

## Decision

Use `pyproject.toml` + setuptools for Python package metadata and PyInstaller for Windows app distribution.

## Evidence

- Editable install already passes under Python 3.10.11.
- `python -m build` supports sdist/wheel from `pyproject.toml`.
- PyInstaller supports explicit spec files, data files, binaries, and multi-executable bundles.

## Changes

- `setup.py` stays as a compatibility shim.
- `scripts/firedm-win.spec` now safely collects optional modules and includes `yt_dlp_ejs` data files.
- Default dependencies no longer require `youtube_dl`.

## Deferred

- Bundling ffmpeg and Deno is deferred. They remain external dependencies discovered by app-local path, `PATH`, or Winget packages.
