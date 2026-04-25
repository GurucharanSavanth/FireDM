# Replacement Matrix

| Old/default | New/policy | Status | Reason |
| --- | --- | --- | --- |
| `youtube_dl` default-capable path | `yt-dlp[default]>=2026.3.17` | Replaced in mainline | Maintained YouTube support, EJS integration |
| No explicit JS runtime path | Deno auto-discovery + `js_runtimes` | Added | yt-dlp now needs JS runtime for YouTube challenges |
| yt-dlp without EJS extra | `yt-dlp[default]` | Upgraded | Includes supported `yt-dlp-ejs` package |
| PATH-only ffmpeg discovery in tools | PATH + app dirs + Winget fallback | Upgraded | Fixes stale shell PATH on Windows |
| PyInstaller collecting `youtube_dl` unconditionally | Safe optional collection | Upgraded | Default env no longer requires legacy extractor |
| setup.py-only packaging | `pyproject.toml` primary | Replaced | Modern editable/build workflow |
| Full-repo lint attempt | Scoped Ruff | Kept scoped | Avoids blocking on untouched legacy style debt |
| Global type checking | Scoped mypy | Kept scoped | Adds value without false failure storm |
