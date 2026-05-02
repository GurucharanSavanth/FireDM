# Packaged Video-Flow Validation

## Scope

The Windows PyInstaller distribution at `dist\FireDM\` is **release-replace**,
not self-updating in place (see `docs/windows-build.md`). This doc captures
what we validate against the packaged binary before signing off a build.

## Build

```powershell
.\scripts\windows-build.ps1
```

Or, if the venv is already set up:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm .\scripts\firedm-win.spec
```

Artifacts produced:

- `dist\FireDM\firedm.exe` — CLI entry point.
- `dist\FireDM\FireDM-GUI.exe` — GUI entry point (windowed, no console).
- `dist\FireDM\_internal\` — PyInstaller dependency bundle.

## Automated verification

`scripts\verify_packaged_video_flow.py` runs four checks against the
packaged bundle:

| # | Check | Asserts |
| --- | --- | --- |
| 1 | `firedm.exe --help` exits 0 | argparse wiring intact |
| 2 | `firedm.exe --show-settings` exits 0 and prints the resolved settings folder | `app_paths.py` + `setting.py` + `config.py` all survive the freeze |
| 3 | `firedm.exe --imports-only` exits 0 | runtime deps (`pycurl`, `yt_dlp`, `yt_dlp_ejs`, Pillow, awesometkinter, pystray, plyer, packaging) are importable from the frozen bundle; optional `youtube_dl` imports only if installed |
| 4 | `FireDM-GUI.exe` launched for 4 seconds stays alive | Tk root initializes and stays running before we terminate the process |

Results:

- `artifacts/packaged/packaged_startup.log`
- `artifacts/packaged/packaged_video_flow_result.json`

Running locally:

```powershell
.\.venv\Scripts\python.exe .\scripts\verify_packaged_video_flow.py
```

Exit code 0 = all checks pass. Non-zero = packaged build regressed.

## What is deliberately not exercised against the packaged binary

- **Live YouTube extraction.** The primary pipeline is already covered
  by `scripts/repro_youtube_bug.py` from source (which uses the same
  `yt_dlp` wheel PyInstaller bundled). Repeating the same live call from
  the packaged binary would prove no new behavior.
- **Real segmented downloads.** The download engine (`brain.py` +
  `worker.py`) is identical bytes in source and in the bundle; the
  relevant regressions are caught earlier by
  `tests/test_download_handoff.py`.
- **ffmpeg post-processing against a real DASH stream.** The merge/HLS
  commands are pure string construction (`ffmpeg_commands.py`) and are
  tested structurally in `tests/test_ffmpeg_pipeline.py`.

## Known packaged-build limitations

- `ffmpeg` and Deno are external. The bundle checks app-local paths,
  `PATH`, and Windows Winget package directories.
- The packaged updater does not rewrite bundled Python packages in place
  (see `firedm/update.py` changes). It opens the release page.
- GUI clipboard monitor, systray icon, and plyer notifications require
  user-level privileges; they are not asserted by the automated script.

## Release checklist (suggested)

1. `git pull --ff-only` on a clean working tree.
2. `.\scripts\windows-build.ps1` — produces `dist\FireDM\`.
3. `.\.venv\Scripts\python.exe .\scripts\verify_packaged_video_flow.py`.
4. Visually confirm `FireDM-GUI.exe` — paste a YouTube URL, see stream
   menu, click Download, confirm progress starts.
5. Zip `dist\FireDM\` and attach to the GitHub release.
