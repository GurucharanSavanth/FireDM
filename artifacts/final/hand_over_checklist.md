# Maintainer Handover Checklist

## Quickstart

```powershell
# activate venv
.\.venv\Scripts\activate.ps1

# run all tests
.\.venv\Scripts\python.exe -m pytest -q

# run only the P0 regression suite
.\.venv\Scripts\python.exe .\scripts\run_regression_suite.py

# synthetic network-free smoke
.\.venv\Scripts\python.exe .\scripts\smoke_video_pipeline.py

# real-network repro (requires internet)
.\.venv\Scripts\python.exe .\scripts\repro_youtube_bug.py

# runtime diagnostics snapshot
.\.venv\Scripts\python.exe .\scripts\collect_runtime_diagnostics.py

# packaged-build verification (requires scripts/windows-build.ps1 first)
.\.venv\Scripts\python.exe .\scripts\verify_packaged_video_flow.py
```

## Release-path checklist

- [ ] `git pull --ff-only` on a clean tree
- [ ] `.\.venv\Scripts\python.exe -m pytest -q` — expect 83 passed
- [ ] `.\.venv\Scripts\python.exe .\scripts\run_regression_suite.py` — expect 62 passed
- [ ] `.\scripts\windows-build.ps1` — produces `dist\FireDM\`
- [ ] `.\.venv\Scripts\python.exe .\scripts\verify_packaged_video_flow.py` — exit 0
- [ ] `.\.venv\Scripts\python.exe .\scripts\repro_youtube_bug.py` — single-video AND playlist `overall_passed=true`
- [ ] Visual smoke: paste a YouTube URL into `FireDM-GUI.exe`, confirm stream menu, click Download, confirm progress

## Code-location map

| I want to … | Read / edit |
| --- | --- |
| change extractor selection policy | `firedm/extractor_adapter.py` (`choose_extractor_name`, `ExtractorService`) |
| add a new entry-URL source (e.g. Twitch id rebuild) | `firedm/playlist_entry.py` (`_rebuild_from_id`) + unit test |
| add a new ffmpeg command | `firedm/ffmpeg_commands.py` + `tests/test_ffmpeg_pipeline.py` |
| understand the playlist walk | `firedm/playlist_builder.py :: build_playlist_from_info` |
| add a new pipeline stage event | `firedm/pipeline_logger.py :: PipelineStage` + emit at boundary |
| fix something in `Video` or `Stream` | `firedm/video.py` (see `_coerce_number` for the None-arithmetic rule) |

## Key invariants (do not break)

- `yt_dlp` is the runtime default whenever it is importable. See
  `tests/test_extractor_default_selection.py`.
- `Stream.__init__` must not raise on `None` numeric fields. See
  `tests/test_single_video_flow.py`.
- Playlist walk must survive one bad entry without dropping the rest.
  See `tests/test_playlist_flow.py :: test_playlist_single_bad_entry_does_not_abort_list`.
- ffmpeg argv construction stays in `ffmpeg_commands.py` — do not
  inline f-strings in `video.py`.
- Every pipeline boundary emits a `[pipeline] stage=... status=...`
  event. See `artifacts/diagnostics/observability_matrix.md`.

## Where to look first when a user reports "videos don't download"

1. Ask for `artifacts/diagnostics/runtime_snapshot.json`
   (`scripts/collect_runtime_diagnostics.py`).
2. Check `extractor_service.active`.
3. Check `ffmpeg.found`.
4. Ask for the log filtered on `[pipeline]` lines.
5. The stage with the last `start` and no following `ok/fail` is
   where the pipeline hung.

## Frequently-updated dependencies

- `yt_dlp` — bump monthly. Follow with a full release cadence run.
- `pycurl` — pin to last known-good Windows wheel.
- `Pillow` — updates frequently; `Pillow>=10` is required.
- `awesometkinter`, `pystray`, `plyer` — low churn.

## Pinned decisions (don't re-open without evidence)

See `artifacts/final/technical_decisions.md`.

## Known limitations

See `artifacts/final/remaining_risks.md`.

## Files in the repo that are the source of truth

| Purpose | File |
| --- | --- |
| Project instructions for future agents | `CLAUDE.md` |
| Architecture | `docs/architecture.md`, `docs/video-pipeline-architecture.md` |
| Packaging | `docs/windows-build.md`, `docs/packaged-video-validation.md` |
| Testing | `docs/testing.md`, `docs/regression-strategy.md` |
| Diagnostics | `docs/runtime-diagnostics.md` |
| Extractor policy | `docs/extractor-migration-policy.md` |
| P0 reproduction | `docs/p0-youtube-bug-baseline.md` |
| P0 fix summary | `docs/p0-youtube-bug-fix.md` |
