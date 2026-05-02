# Windows Portable Package

The portable package is produced by:

```powershell
.\.venv\Scripts\python.exe scripts\release\build_payload.py --arch x64 --channel dev --build-id 20260427_V1
```

Output:

```text
dist\portable\FireDM_<build_id>_<channel>_win_x64_portable.zip
```

Portable behavior:
- no registry writes
- no shortcuts
- no PATH changes
- no admin requirement
- runs `FireDM-GUI.exe` or `firedm.exe` directly
- no end-user Python installation
- no end-user `pip` install during portable launch
- contains PyInstaller `_internal` runtime, Tcl/Tk assets, certifi CA bundle, `build-metadata.json`, and `payload-manifest.json`

Validation:

```powershell
.\.venv\Scripts\python.exe scripts\release\validate_portable.py --archive dist\portable\FireDM_<build_id>_<channel>_win_x64_portable.zip
```

The validator extracts into a temp directory, rejects zip path traversal,
checks required files, runs CLI help/import smoke on Windows, and reports
FFmpeg/ffprobe as optional warnings when they are not bundled.

Current limitation:
- blocked: true app-internal portable config-root isolation is not implemented in FireDM itself in this pass. The ZIP includes `README_PORTABLE.txt` and avoids installer side effects, but FireDM runtime settings may still use the normal application config paths unless the app is later patched for a portable-mode marker.
- blocked: FFmpeg/ffprobe are not bundled; media merge/post-processing still
  needs external tools or future approved bundling.
