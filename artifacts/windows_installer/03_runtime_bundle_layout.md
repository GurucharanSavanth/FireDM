# 03 Runtime Bundle Layout

Evidence labels: observed, inferred, planned.

## x64 Installed Tree
Planned installed root:

```text
%LocalAppData%\Programs\FireDM\
  FireDM-GUI.exe
  firedm.exe
  _internal\
  installer\
    install-state.json
  licenses\
  release-manifest.json
```

Reason:
- inferred: per-user LocalAppData install avoids mandatory admin/UAC and avoids writable all-users Program Files complexity for this x64 slice.
- inferred: future all-users Program Files mode can be added after elevation and HKLM validation.

## Payload Tree
Planned build output:

```text
dist\payloads\win-x64\FireDM\
```

Content source:
- observed: copied from validated PyInstaller one-dir `dist\FireDM\`.

## Installer Output
Planned output:

```text
dist\installers\FireDM_Setup_<version>_<channel>_win_x64.exe
```

## Portable Output
Planned output:

```text
dist\portable\FireDM_<version>_win_x64_portable.zip
```

Portable mode:
- inferred: portable ZIP must not write registry, shortcuts, or PATH.
- planned: include `README_PORTABLE.txt`.

## Config, Cache, Logs, User Data
- planned installed config root: `%AppData%\FireDM`.
- planned logs/cache root: `%LocalAppData%\FireDM`.
- inferred: user data must not live inside the install directory.
- inferred: uninstall preserves user data by default.

## Tools Directory
- planned: `tools\win-x64\` under installed root when tools are bundled.
- blocked: FFmpeg/ffprobe bundling is not enabled until license/source/checksum inventory is complete.

## App-Local Environment Variables
Process-local only:
- `FIREDM_INSTALL_DIR`
- `FIREDM_RUNTIME_DIR`
- `FIREDM_TOOLS_DIR`
- `FIREDM_CONFIG_DIR`
- `FIREDM_CACHE_DIR`
- `FIREDM_LOG_DIR`
- `PYTHONUTF8=1`

Global policy:
- inferred: no global PATH mutation by default.
- inferred: no global Python, PYTHONPATH, or PYTHONHOME changes.

