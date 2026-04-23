# Validation Summary

## Automated

| Test / script | Result |
| --- | --- |
| Full pytest suite | `85 passed in 7.19s` |
| Scoped Ruff gate | `All checks passed!` |
| Scoped mypy gate | `Success: no issues found in 8 source files` |
| P0 regression suite | `63 passed in 0.86s` |
| `smoke_video_pipeline.py` | single-video and playlist passed |
| `verify_extractor_default.py` | `passed=true`, active `yt_dlp` |
| `verify_playlist_entry_normalization.py` | `7/7`, `overall_passed=true` |
| `verify_ffmpeg_pipeline.py` | exit 0, ffmpeg found |
| `verify_packaged_video_flow.py` | `overall_passed=true` |
| `python -m build` | sdist + wheel built |
| `pip check` | no broken requirements |

## Real-Network Repro

`scripts/repro_youtube_bug.py` exit 0.

| Target | Evidence |
| --- | --- |
| Single video | 1 item, title `Me at the zoo`, 20 streams, selected stream has URL |
| Playlist | 15 items, 0 malformed inspected entries, first entry processed with 49 streams |
| Extractor | `yt_dlp==2026.03.17`, primary active |
| JS runtime | yt-dlp log shows `[jsc:deno] Solving JS challenges using deno` |

## Runtime Diagnostics

`artifacts/diagnostics/runtime_snapshot.json` shows:

- active extractor: `yt_dlp`
- Deno path: Winget package dir
- Deno version: `2.7.13`
- `yt_dlp_ejs`: `0.8.0`
- ffmpeg path: Winget package dir
- ffmpeg version: `8.1-essentials_build-www.gyan.dev`

## Packaged Build

`scripts/windows-build.ps1 -SkipTests` built `dist\FireDM` using PyInstaller
6.20.0. The script now stops stale packaged processes from the same dist path
before replacing the bundle.

Packaged checks passed:

- `dist\FireDM\firedm.exe --help`
- `dist\FireDM\firedm.exe --show-settings`
- `dist\FireDM\firedm.exe --imports-only`
- `dist\FireDM\FireDM-GUI.exe` stays alive for 4 seconds

## P0 Acceptance

All required P0 gates pass: maintained extractor default, single-video path,
playlist path, stream generation, controlled download handoff, ffmpeg
diagnostics, regression tests, source build, packaged build, and docs/artifacts.
