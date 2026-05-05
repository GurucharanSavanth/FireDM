# Compatibility Matrix

Status: changed 2026-05-03.

Official basis: Python 3.10 docs say Windows 8.1+ for Python 3.10; current Python docs say Python 3.14 is Windows 10+ and recommend Python 3.8 for Windows 7 and Python 3.12 for Windows 8.1. Python 3.14.4 is the latest stable CPython release observed in official docs during the 2026-05-03 run, but it is not the local validated runtime.

| OS | Python candidate | GUI | TLS/network | pycurl/requests/urllib | aria2c | yt-dlp | FFmpeg | PyInstaller | Nuitka | Updater | Feature tier | Validation | Blockers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Windows XP | legacy-only, not modern Python | unverified | blocked | blocked | unverified | blocked | unverified | blocked for modern lane | blocked | blocked | legacy-only minimal if feasible | not verified | runtime, TLS, deps, packaging |
| Windows Vista | legacy-only, not modern Python | unverified | blocked | blocked | unverified | blocked | unverified | blocked for modern lane | blocked | blocked | legacy-only minimal if feasible | not verified | runtime, TLS, deps, packaging |
| Windows 7 | Python 3.8 legacy candidate only | unverified | unverified | unverified | unverified | current yt-dlp source blocked | unverified | legacy-only | unverified | blocked until TLS/update proof | legacy-only | not verified | current project requires Python 3.10 |
| Windows 8 | separate lane needed | unverified | unverified | unverified | unverified | unverified | unverified | unverified | unverified | unverified | limited legacy/transition | not verified | Python/dependency support |
| Windows 8.1 | Python 3.10 current candidate | Tkinter viable by runtime | unverified | unverified | unverified | current source dependency viable by Python floor | unverified | feasible | feasible if compiler works | planned | modern-limited | not verified | needs real OS smoke |
| Windows 10 | Python 3.10 current lane | observed local host uses Tkinter code | observed local OS | observed imports not fully smoked | aria2c missing | dependency declared | ffmpeg/ffprobe detected | feasible | feasible if compiler works | planned | modern | partially verified | GUI/build smoke needed |
| Windows 11 | Python 3.10 current lane | inferred from Windows 10 lane | inferred | inferred | unverified | dependency declared | unverified | feasible | feasible if compiler works | planned | modern | not verified | real host/VM smoke needed |
| Linux x86_64 | Python 3.10 candidate | unverified | unverified | unverified | unverified | dependency declared | unverified | feasible on Linux host | feasible on Linux host | planned | modern | not verified | needs Linux runner/host |

Rules:
- implemented: No code claims XP/Vista/7 support.
- planned: Legacy lane remains separate and may have reduced features.
- blocked: Modern architecture must not be weakened for legacy compatibility.

## GUI Backend Compatibility

| Backend | Default? | Source smoke | Headless construction smoke | Packaged smoke | Live launch | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Tkinter | yes | implicit (existing tests) | n/a | `firedm.exe --imports-only` verified | manual | Active release runtime; alternate preview frontend was removed. |

## Plugin Manifest Coverage (added 2026-05-03)

| Plugin | Status (default) | Notes |
| --- | --- | --- |
| `anti_detection` | blocked | TLS/proxy/header impersonation claims are not release-validated or safely configurable. |
| `browser_integration` | blocked | Native-host origin provisioning and authentication need real connector validation before exposure. |
| `drm_decryption` | blocked | DRM bypass, protected-media circumvention, license-server access, and media-key extraction are prohibited. |
| `native_extractors` | blocked | Site-specific extractor behavior and embedded public API token use need release tests. |
| `post_processing` | blocked | AV/extract/convert substeps need argv-safe execution, path validation, and explicit per-step controls. |
| `protocol_expansion` | blocked | Partial FTP/WebDAV/SFTP/magnet/IPFS/data handlers need capability split or full dependency/RPC safety tests. |
| `queue_scheduler` | disabled | Discovered and selectable; no live activation by build pipeline. |

`release/manifest.json` records the same set under `included_plugins`/`blocked_plugins`/`planned_plugins` after each build.
