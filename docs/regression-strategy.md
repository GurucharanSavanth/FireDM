# Regression Strategy

## Layers

| Layer | Ownership | Tools | Run before |
| --- | --- | --- | --- |
| 1. Unit tests | per-module invariants | `pytest` | every commit |
| 2. Boundary tests | cross-module seams (playlist builder, ExtractorService) | `pytest tests/test_controller_video_integration.py` | every commit |
| 3. Synthetic smoke | network-free pipeline run | `scripts/smoke_video_pipeline.py` | every PR |
| 4. Real-network repro | in-process against real YouTube | `scripts/repro_youtube_bug.py` | before release |
| 5. Packaged verification | PyInstaller bundle | `scripts/verify_packaged_video_flow.py` | before release |
| 6. Runtime diagnostics | user-facing triage | `scripts/collect_runtime_diagnostics.py` | on-demand (user bug reports) |

## What counts as a P0 regression

Any of:

- Any test in `artifacts/regression/test_matrix.md` flips to red.
- `scripts/verify_extractor_default.py` exits non-zero (deprecated
  extractor became the runtime default).
- `scripts/verify_playlist_entry_normalization.py` exits non-zero
  (entry URL normalization broke).
- `scripts/verify_packaged_video_flow.py` exits non-zero (packaged
  build won't launch or diagnostics fail).
- `scripts/repro_youtube_bug.py` single-video `overall_passed=false`
  AND the failure is not attributable to a YouTube-side change
  (confirm via `yt_dlp --print-json` on the same URL first).

## What counts as acceptable drift

- An individual YouTube format dropped by `yt_dlp` upstream — this is
  by design; the pipeline already logs `stream_build status=fail` and
  skips the format.
- `_parse_m3u8_formats` changing its private signature — guarded by
  try/except at call site; a follow-up slice replaces the private
  call with a public equivalent when one lands.
- User-installed InfoExtractor plugins that register against the
  deprecated `youtube_dl.InfoExtractor` base. The load path still
  works for them; the policy doc (`docs/extractor-migration-policy.md`)
  flags the eventual removal.

## Cadence

- **Every commit:** `pytest -q` (local pre-push).
- **Every PR (CI):** `pytest -q` + `scripts/smoke_video_pipeline.py`
  + `scripts/verify_extractor_default.py`
  + `scripts/verify_ffmpeg_pipeline.py`.
- **Every release:** all of the above plus
  `scripts/run_regression_suite.py`,
  `scripts/verify_packaged_video_flow.py`, and a live
  `scripts/repro_youtube_bug.py` run.
- **Monthly maintenance:** bump `yt_dlp` and re-run the release cadence
  — this is where most real-world extractor drift lands.

## Adding new tests

When a new bug is fixed:

1. Add a unit test that reproduces the bug using synthetic fixtures
   (no network, no ffmpeg binary).
2. Register the behavior in `artifacts/regression/test_matrix.md`.
3. If the bug was visible only in the packaged build, add a check to
   `scripts/verify_packaged_video_flow.py`.
4. Update `docs/p0-youtube-bug-fix.md` or equivalent if the root cause
   overlaps.

## Not covered yet (deferred debt)

- GUI behavioral tests (`tkview.py` exploratory only — manual).
- Real-download progress/resume correctness.
- Subtitle download flow.
- ffmpeg merge success against a real DASH asset (structural argv
  only).
- Clipboard monitor and systray icon — OS surface, manual only.
