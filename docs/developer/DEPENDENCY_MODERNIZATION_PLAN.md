# Dependency Modernization Plan

Status: changed 2026-05-03.

## Local Inventory
| Family | Local declarations | Used by | Risk | Decision |
| --- | --- | --- | --- | --- |
| Runtime Python | `pyproject.toml` `>=3.10,<3.11`; workflows use Python 3.10 | whole app, release scripts | high | keep current lane until widened by tests |
| Transport | `pycurl>=7.45.2` | `worker.py`, `utils.py`, `download_engines/internal_http.py` | high | keep; no replacement without parity |
| Extractor | `yt-dlp[default]>=2026.3.17`; `youtube_dl` legacy extra | `video.py`, tests, packaging | high | update only in media slice |
| GUI | `awesometkinter`, `Pillow`, `pystray`, `plyer`, stdlib Tk | `tkview.py`, `systray.py`, themes | high | do not mix with backend upgrades |
| Tooling | `pytest`, `ruff`, `mypy`, `build`, `twine`, `pyinstaller` extras | tests/release/CI | medium | upgrade tooling family separately |
| Linux-only | `distro` with platform marker | release/runtime diagnostics | low | keep marker |

## Official-Doc Decisions
- verified: Python 3.14.4 is the latest stable CPython release as of this run, but current Python docs state Python 3.14 supports Windows 10 and newer only.
- verified: Python docs state Windows 8.1 needs Python 3.12, and Windows 7 needs Python 3.8.
- verified: yt-dlp documents CPython 3.10+ support and FFmpeg use for several media operations.
- changed: The prior alternate GUI-framework dependency lane was removed from this checkout.
- verified: uv can manage project dependencies and a lockfile, but this checkout does not yet use a uv lockfile.

## Policy
1. Do not widen Python or add GUI-framework dependencies in the same patch as runtime/download changes.
2. Upgrade one dependency family per patch.
3. Run target tests plus full suite after each family.
4. Keep `requirements.txt` and `pyproject.toml` coherent.
5. Add a rollback note for every dependency change.
6. Do not globally install packages; use `.venv` or documented release environments.

## Current Deferred Items
- blocked: `yt-dlp-ejs` requirement status is inconsistent between release preflight and declarations; resolve in extractor dependency slice.
- blocked: System Python is missing some dev/build tools; `.venv` is the authoritative validation environment.
- blocked: No lockfile strategy has been selected.
