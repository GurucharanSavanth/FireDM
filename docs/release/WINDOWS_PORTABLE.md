# Windows Portable Package

The portable package is produced by:

```powershell
.\.venv\Scripts\python.exe scripts\release\build_payload.py --arch x64 --channel dev
```

Output:

```text
dist\portable\FireDM_<version>_win_x64_portable.zip
```

Portable behavior:
- no registry writes
- no shortcuts
- no PATH changes
- no admin requirement
- runs `FireDM-GUI.exe` or `firedm.exe` directly

Current limitation:
- blocked: true app-internal portable config-root isolation is not implemented in FireDM itself in this pass. The ZIP includes `README_PORTABLE.txt` and avoids installer side effects, but FireDM runtime settings may still use the normal application config paths unless the app is later patched for a portable-mode marker.

