# Dependency Modernization Review

Review date: 2026-04-23. Baseline: Windows, Python 3.10.11, editable install.

## Decision Matrix

| Current package/tool | Role | Current problem | Decision | Docs reviewed | Complexity | Risk | Windows impact | Test impact |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `yt_dlp` | Video extraction | Prior install missed current YouTube EJS/runtime requirements | Upgrade policy to `yt-dlp[default]>=2026.3.17`; keep as primary | yt-dlp README, EJS wiki, releases | Medium | High | Needs Deno or JS runtime | Single/playlist regressions |
| `youtube_dl` | Legacy extractor | Stale YouTube support, old API assumptions | Move out of default install; optional `[legacy]` only | yt-dlp "changes from youtube-dl", existing FireDM usage | Medium | High | Reduces packaged drift | Fallback tests only |
| Deno | JS runtime for yt-dlp EJS | Not previously detected from Winget if PATH stale | Require/recommend; auto-discover Winget binary | Deno install docs, yt-dlp EJS wiki | Low | Medium | Windows x64 supported | Runtime diagnostics |
| `yt-dlp-ejs` | YouTube JS challenge solvers | Missing before `yt-dlp[default]` install | Bring via `yt-dlp[default]` | yt-dlp EJS wiki | Low | High | Bundle data in PyInstaller | Repro logs |
| `pycurl` | Transport | Windows native dep | Keep, isolate later | PycURL docs/PyPI | High | High | Wheel required | Import smoke |
| `ffmpeg` | Media merge | PATH can be stale in agent shells | Keep external; add Winget discovery; pass to yt-dlp | yt-dlp deps docs, FFmpeg docs | Low | High | Finds Winget package | FFmpeg tests |
| `Pillow` | Images/icons | Old lower bound | Raise lower bound to modern wheels | Pillow docs/PyPI | Low | Low | Wheels available | Import smoke |
| `plyer` | Notifications | Lightly maintained | Keep; isolate later | Plyer docs | Low | Medium | Works on Windows | Manual GUI |
| `pystray` | Tray icon | Last release older but stable | Keep | pystray docs/PyPI | Low | Medium | GUI only | Manual GUI |
| `awesometkinter` | Tk widgets | Older project | Keep for UI stability | PyPI/project docs | High to replace | Medium | No change | Manual GUI |
| `certifi` | CA bundle | Required by network libs | Keep, modern lower bound | certifi PyPI | Low | Low | Helpful in frozen app | Import smoke |
| `packaging` | Version parsing | Foundational, maintained | Keep | PyPA packaging docs | Low | Low | No issue | Unit tests |
| `distro` | Linux platform data | Not needed on Windows | Keep Linux-only marker | distro docs | Low | Low | None | Import smoke |
| setuptools/build | Packaging | `setup.py`-only legacy | Keep setuptools backend under `pyproject.toml`; `setup.py` shim only | PyPA + setuptools docs | Medium | Medium | Editable install works | Build smoke |
| PyInstaller | Windows packaging | Spec needed hidden data | Keep; collect `yt_dlp_ejs` data safely | PyInstaller spec docs | Medium | High | Primary distributor | Packaged smoke |
| pytest | Tests | Existing legacy gap | Keep primary runner | pytest docs | Low | Low | Works on Windows | Full suite |
| Ruff | Lint/format | Full repo too noisy | Keep scoped to modern seams | Ruff docs | Low | Medium | Fast local check | Lint gate |
| mypy | Types | Legacy too dynamic | Keep scoped only | mypy docs | Medium | Medium | No runtime impact | Type gate |
| uv | Env/deps | Attractive but new workflow | Defer; do not replace pip/venv now | uv docs | Low | Medium | Avoids churn | None |

## Replacement Decisions

The only mainline package replacement is extractor policy: `youtube_dl` is no longer a default dependency or default runtime path. The maintained stack is `yt-dlp[default]` plus Deno plus ffmpeg discovery. Other dependencies are kept because replacing them would be higher risk than value during P0 recovery.
