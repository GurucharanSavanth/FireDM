# Baseline Environment Summary

Captured at start of P0 modernization sprint.

## Host
- OS: Windows 11 (10.0.26200)
- Python: 3.10.11 (venv at `.\.venv`)
- Shell used for automation: Git Bash on Windows + PowerShell (5.1)

## Binary
- ffmpeg: `C:\Users\SavanthGC\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-essentials_build\bin\ffmpeg.exe`
- ffmpeg version: `ffmpeg version 8.1-essentials_build-www.gyan.dev`
- Not on PATH in automation shells (known issue — ffmpeg_service fallback search must find it)

## Python packages (key)
- `yt_dlp==2026.3.17`
- `youtube_dl==2021.12.17` (unmaintained — scheduled for deprecation)
- `pycurl==7.45.7`
- `certifi==2026.4.22`
- `pyinstaller==6.20.0`
- `pytest==9.0.3`
- `ruff==0.15.11`

## Known-good smokes (CLAUDE.md)
- `python -m firedm --help` passes
- `python firedm.py --imports-only` passes
- `dist\FireDM\firedm.exe --help` passes
- `dist\FireDM\FireDM-GUI.exe` launches

## Repo state at start
- Branch: `master`
- Head: `88240da7f005c9a7a49a4e2d7f6928fd7fddf043`
- Dirty: modernization WIP from prior sprint (app_paths, ffmpeg_service, extractor_adapter seams landed)
