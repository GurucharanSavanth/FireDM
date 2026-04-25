# Dependency Strategy

## Matrix

| Dependency/tool | Role | Decision | Risk | Windows impact |
| --- | --- | --- | --- | --- |
| `yt-dlp[default]>=2026.3.17` | primary extractor + EJS extras | keep as default | high | requires JS runtime; bundled data collected by PyInstaller |
| Deno | JavaScript runtime for YouTube challenges | external, auto-discovered | medium | Winget package dir supported |
| `youtube_dl` | legacy extractor | optional `[legacy]` only | high | no longer default dependency |
| `pycurl` | segmented download transport | keep | high | official wheel required |
| ffmpeg | merge/post-processing | external, auto-discovered | high | app path, PATH, Winget fallback |
| `certifi` | CA bundle | keep | low | collected by PyInstaller |
| `Pillow` | thumbnails/tray images | keep modern lower bound | low | wheel available |
| `pystray` | tray icon | keep | medium | GUI manual validation |
| `awesometkinter` | Tk widgets/theme | keep | medium | replacing would be UI rewrite |
| `plyer` | notifications | keep | low | manual GUI validation |
| `packaging` | version parsing | keep | low | unit-testable |
| `distro` | Linux platform detection | Linux-only marker | low | skipped on Windows |

## Policy

- Do not remove `pycurl` until a tested transport abstraction proves parity.
- Treat `yt_dlp` as the only mainline extractor. `youtube_dl` is fallback debt.
- Keep Deno and ffmpeg external for now, but keep robust discovery.
- Use `pip install -e .[dev,build]` for maintainers. `dependency.py` is legacy
  emergency auto-install only.

## Version Policy

- Python: verified 3.10.11; metadata is constrained to `>=3.10,<3.11`
  until Python 3.11/3.12 pass local or CI validation.
- Extractor: lower-bound on verified stable family, currently
  `yt-dlp[default]>=2026.3.17`.
- Monthly extractor bumps require full pytest, P0 regression suite, live repro,
  and packaged diagnostics.
