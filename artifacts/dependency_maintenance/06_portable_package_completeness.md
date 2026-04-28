# 06 Portable Package Completeness

changed validator: `scripts/release/validate_portable.py`.

required portable files:
- `firedm.exe`
- `FireDM-GUI.exe`
- `_internal/tkinter/__init__.py`
- `_internal/_tcl_data/init.tcl`
- `_internal/_tk_data/tk.tcl`
- `_internal/certifi/cacert.pem`
- `README_PORTABLE.txt`
- `build-metadata.json`
- `payload-manifest.json`

changed build behavior:
- `scripts/release/build_payload.py` now writes `payload-manifest.json` into the portable payload before zipping.
- `scripts/release/build_windows.py` runs portable validation during release lane validation.

optional warnings:
- FFmpeg/ffprobe absent is a warning, not a package failure.

verified:
- `.venv\Scripts\python.exe scripts\release\validate_portable.py --archive .\dist\portable\FireDM_20260428_V2_dev_win_x64_portable.zip` passed.
- Required executable, `_internal`, Tcl/Tk, certifi, metadata, and smoke checks passed.

blocked:
- true portable-only settings/cache/log root is not implemented in app runtime.
- FFmpeg/ffprobe are not bundled.
