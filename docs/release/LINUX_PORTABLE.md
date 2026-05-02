# FireDM Linux Portable Archive

## Layout

```
FireDM_<BUILD_CODE>_<CHANNEL>_linux_x64.tar.gz
└── FireDM/
    ├── firedm                  (CLI launcher, +x)
    ├── FireDM-GUI              (GUI launcher, +x)
    ├── _internal/              (PyInstaller bootstrap, Python stdlib, deps, tcl/tk)
    ├── README_PORTABLE.txt
    └── payload-manifest.json
```

The archive is extracted with `tar -xzf FireDM_<...>.tar.gz`. Run the GUI with
`./FireDM/FireDM-GUI`, the CLI with `./FireDM/firedm --help`.

The portable package does **not** install desktop entries, icons, or PATH
modifications. Configuration follows FireDM runtime settings unless explicit
portable-mode support is added in the application.

## Naming

| Concept | Pattern |
|---------|---------|
| Portable archive | `FireDM_<BUILD_CODE>_<CHANNEL>_linux_x64.tar.gz` |
| Per-platform manifest | `FireDM_release_manifest_<BUILD_CODE>_linux.json` |
| Payload manifest (inside archive) | `FireDM/payload-manifest.json` |

`<BUILD_CODE>` follows `YYYYMMDD_VN` and is identical to the Windows lane in
the same release run. See `docs/release/BUILD_ID_POLICY.md`.

## Validation

```bash
python scripts/release/validate_linux_payload.py --arch x64
python scripts/release/validate_linux_portable.py --archive dist/portable-linux/FireDM_<BUILD_CODE>_dev_linux_x64.tar.gz
```

`validate_linux_portable.py`:

* refuses to extract any tar member whose resolved path escapes the
  extraction root;
* requires the `firedm` and `FireDM-GUI` launchers to have the user execute
  bit set;
* runs `firedm --help` and `firedm --imports-only` on Linux hosts and skips
  smoke on other operating systems.

## Bundled tools

| Tool | Bundled? | Notes |
|------|----------|-------|
| Python 3.10 | yes | via PyInstaller `_internal` |
| Tcl/Tk | yes | via PyInstaller `_internal/tkinter` |
| certifi CA bundle | yes | `_internal/certifi/cacert.pem` |
| FFmpeg / ffprobe | no | detect-only; install externally for media post-processing |
| Deno | no | optional yt-dlp JS runtime; install externally if required |

The portable lane does not ship a system-tray helper or `.desktop` integration.
Both are out of scope for this pass.

## Blocked

* AppImage, .deb, .rpm — no tooling integrated.
* Signing — no GPG/notary policy in place yet.
* GUI smoke — Linux jobs are headless; the GUI binary is exercised only by
  start-up imports.
