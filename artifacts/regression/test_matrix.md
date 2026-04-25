# Regression Test Matrix (Commit 8)

Every row maps a P0-relevant behavior to the test file + test function
that enforces it. All rows are green as of Commit 8.

| Behavior | Test file | Test function |
| --- | --- | --- |
| `yt_dlp` is always preferred over `youtube_dl` | `tests/test_extractor_default_selection.py` | `test_choose_extractor_name_primary_first` |
| Persisted `active_video_extractor="youtube_dl"` does not downgrade runtime | `tests/test_extractor_default_selection.py` | `test_service_never_returns_fallback_when_primary_ready` |
| Service race: primary promotion sticks no matter thread order | `tests/test_extractor_service.py` | `test_primary_overrides_fallback_regardless_of_load_order` |
| Service wait is bounded | `tests/test_extractor_service.py` | `test_new_service_is_not_ready` |
| Graceful fallback when primary missing | `tests/test_legacy_extractor_fallback.py` | `test_only_fallback_loaded_becomes_active` |
| Explicit failure when no extractor loaded | `tests/test_legacy_extractor_fallback.py` | `test_no_engines_loaded_signals_not_ready` |
| Stream builder tolerates `abr=None` (P0 root cause) | `tests/test_single_video_flow.py` | `test_single_video_builds_streams_even_with_none_bitrate` |
| Stream builder tolerates None in `width`, `height`, `tbr` | `tests/test_single_video_flow.py` | `test_stream_init_tolerates_none_in_numeric_fields` |
| Single-video stream menu populated | `tests/test_single_video_flow.py` | `test_single_video_stream_menu_is_populated` |
| Default stream selected and `eff_url` propagates | `tests/test_single_video_flow.py` | `test_single_video_selects_default_stream` |
| DASH video pairs with compatible audio | `tests/test_single_video_flow.py`, `tests/test_stream_selection.py` | `test_single_video_selecting_dash_video_triggers_audio_pairing`, `test_dash_video_selects_m4a_audio_for_mp4`, `test_dash_video_selects_webm_audio_for_webm` |
| Playlist parsing handles mixed (full / id-only / broken) entries | `tests/test_playlist_flow.py` | `test_playlist_handles_mixed_entries` |
| Playlist title/URL propagated to each Video | `tests/test_playlist_flow.py` | `test_playlist_propagates_title_and_url_to_every_entry` |
| Playlist entry processing succeeds per item | `tests/test_playlist_flow.py` | `test_playlist_per_item_processing_populates_streams` |
| One bad entry does not drop the rest | `tests/test_playlist_flow.py` | `test_playlist_single_bad_entry_does_not_abort_list` |
| Bare YouTube id → full URL | `tests/test_playlist_entry_normalization.py` | `test_rebuilds_from_bare_youtube_id_via_ie_key`, `test_rebuilds_from_bare_youtube_id_even_without_ie_key` |
| Vimeo numeric id → full URL | `tests/test_playlist_entry_normalization.py` | `test_vimeo_numeric_id` |
| Unknown id with no context → rejected (no guessing) | `tests/test_playlist_entry_normalization.py` | `test_non_youtube_bare_id_without_ie_key_returns_none`, `test_returns_none_when_no_identifier` |
| ffmpeg merge command uses `-c copy` fast path | `tests/test_ffmpeg_pipeline.py` | `test_merge_command_has_stream_copy_fast_path` |
| ffmpeg command quotes paths with spaces | `tests/test_ffmpeg_pipeline.py` | `test_merge_command_quotes_paths_with_spaces` |
| HLS protocol whitelist set | `tests/test_ffmpeg_pipeline.py` | `test_hls_process_command_whitelists_protocols` |
| Audio convert uses `-acodec copy` fast path | `tests/test_ffmpeg_pipeline.py` | `test_audio_convert_command_acodec_copy_fast_path` |
| ffmpeg not-found returns a clear `ProbeResult(found=False)` | `tests/test_ffmpeg_pipeline.py` | `test_ffmpeg_service_reports_not_found_when_missing` |
| Download enqueue happy path | `tests/test_download_handoff.py` | `test_download_enqueue_happy_path` |
| Download rejects missing name | `tests/test_download_handoff.py` | `test_download_rejects_missing_name` |
| Download rejects when ffmpeg missing (video) | `tests/test_download_handoff.py` | `test_download_rejects_when_ffmpeg_missing` |
| Builder returns typed result for single video | `tests/test_controller_video_integration.py` | `test_builder_returns_single_video` |
| Builder returns typed result for playlist | `tests/test_controller_video_integration.py` | `test_builder_returns_playlist_entries` |
| Builder records skipped bad entries | `tests/test_controller_video_integration.py` | `test_builder_records_skipped_bad_entries` |
| Controller delegates to builder | `tests/test_controller_video_integration.py` | `test_controller_create_video_playlist_delegates_to_builder` |
| Packaged `firedm --help` works from source | `tests/test_packaged_diagnostics.py` | `test_firedm_help_runs_from_source` |
| Packaged `--imports-only` smoke | `tests/test_packaged_diagnostics.py` | `test_firedm_imports_only_runs_from_source` |
| Extractor default verify script passes | `tests/test_packaged_diagnostics.py` | `test_verify_extractor_default_script_passes` |
| Smoke script passes | `tests/test_packaged_diagnostics.py` | `test_smoke_video_pipeline_script_passes` |

## Counts

- Total P0 regression tests: 30+
- Full test suite: **83 passed / 0 failed** (see
  `artifacts/regression/regression_suite_result.json`).

## How to regenerate

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\run_regression_suite.py
.\.venv\Scripts\python.exe scripts\smoke_video_pipeline.py
.\.venv\Scripts\python.exe scripts\verify_extractor_default.py
.\.venv\Scripts\python.exe scripts\verify_playlist_entry_normalization.py
.\.venv\Scripts\python.exe scripts\verify_ffmpeg_pipeline.py
.\.venv\Scripts\python.exe scripts\collect_runtime_diagnostics.py
```
