# Validation Summary

## Automated

| Test / script | Count | Result |
| --- | --- | --- |
| Full pytest suite | 83 | **83 passed, 0 failed** |
| P0 regression suite (`run_regression_suite.py`) | 62 | **62 passed** |
| `smoke_video_pipeline.py` | 2 targets (single, playlist) | both **passed=True** |
| `verify_extractor_default.py` | yt_dlp as default | **passed=true** |
| `verify_playlist_entry_normalization.py` | 7 cases | **overall_passed=true** |
| `verify_ffmpeg_pipeline.py` | 3 command builders + discovery | exit 0 |
| `verify_packaged_video_flow.py` | 4 checks | **overall_passed=true** |

## Real-network repro (`scripts/repro_youtube_bug.py`)

| Target | Stage | Result |
| --- | --- | --- |
| single video | extractor_ready | PASS |
| single video | default_is_primary | PASS |
| single video | create_video_playlist | PASS (1 item) |
| single video | stream_menu | PASS (17 streams) |
| single video | selected_stream_url | PASS (eff_url present) |
| playlist | extractor_ready | PASS |
| playlist | create_video_playlist | PASS (15 entries) |
| playlist | entry_url_normalization | PASS (0 malformed) |
| playlist | process_first_entry | PASS (12 streams) |

## Packaged build (`dist\FireDM\`)

| Check | Result |
| --- | --- |
| `firedm.exe --help` | exit 0 |
| `firedm.exe --show-settings` | exit 0 |
| `firedm.exe --imports-only` | exit 0 |
| `FireDM-GUI.exe` launch | alive_after_4s=true |

## Extractor modernization acceptance

| Criterion | Evidence |
| --- | --- |
| `yt_dlp` is the runtime default | `artifacts/extractor/default_selection_proof.json` (`active: yt_dlp`) |
| `youtube_dl` is not the default | `tests/test_extractor_default_selection.py :: test_service_never_returns_fallback_when_primary_ready` |
| Deprecated APIs isolated | `artifacts/extractor/deprecated_api_inventory.md` (3 private/legacy refs, all behind the adapter) |
| Dependency metadata reflects policy | `pyproject.toml` (`yt_dlp>=2024.12.0`), `docs/extractor-migration-policy.md` |
| Single-video flow passes on maintained extractor | `artifacts/repro/single_video_repro.log` |
| Playlist flow passes on maintained extractor | `artifacts/repro/playlist_repro.log` |

## P0 acceptance matrix

| Acceptance criterion | Status | Evidence |
| --- | --- | --- |
| A.1 user enters valid YouTube URL | PASS | repro single-video |
| A.2 metadata extracted | PASS | repro stage `create_video_playlist` |
| A.3 stream menu built | PASS | repro stage `stream_menu` |
| A.4 stream selected | PASS | repro stage `selected_stream_url` |
| A.5 download starts | PASS | `tests/test_download_handoff.py :: test_download_enqueue_happy_path` |
| A.6 no silent failure | PASS | every stage emits structured events |
| B.1 valid playlist URL | PASS | repro playlist |
| B.2 playlist extracted | PASS | repro stage `create_video_playlist` |
| B.3 entries populated | PASS | repro stage `entry_url_normalization` |
| B.4 items processed | PASS | repro stage `process_first_entry` |
| B.5 downloads start | PASS | `tests/test_download_handoff.py` |
| B.6 no silent failure | PASS | per-entry structured events |
| C.1 active extractor visible | PASS | `artifacts/diagnostics/runtime_snapshot.json :: extractor_service.active` |
| C.2 extractor version visible | PASS | same |
| C.3 ffmpeg path/version visible | PASS | same |
| C.4 primary failure points actionable | PASS | pipeline events at every boundary |
| D.1 single-video regression test | PASS | `tests/test_single_video_flow.py` |
| D.2 playlist regression test | PASS | `tests/test_playlist_flow.py` |
| E.1 packaged app launches | PASS | `verify_packaged_video_flow.py` |
| E.2 packaged diagnostics execute | PASS | same |
| F.1 maintained extractor is default | PASS | test_extractor_default_selection |
| F.2 deprecated extractor is not default | PASS | same |
| F.3 deprecated APIs isolated | PASS | deprecated_api_inventory.md |
| F.4 dependencies reflect policy | PASS | pyproject.toml + policy doc |
| F.5 single-video passes on maintained path | PASS | repro + tests |
| F.6 playlist passes on maintained path | PASS | repro + tests |

**All acceptance criteria PASS.**
