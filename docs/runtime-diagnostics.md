# Runtime Diagnostics Guide

## Generating a snapshot

```powershell
.\.venv\Scripts\python.exe .\scripts\collect_runtime_diagnostics.py
```

Writes `artifacts/diagnostics/runtime_snapshot.json`.

The snapshot reports `ffmpeg` and `ffprobe` as separate health blocks:
`found`, `path`, `version`, `usable`, `failure`, and `returncode`.
`ffmpeg.usable` means the executable was found and `-version` exited 0.
`ffprobe` is diagnostic/metadata support in this patch; it is not a hard
requirement for current download enqueue or post-processing behavior.

## Reading the structured pipeline log

Every relevant boundary emits a line of the form:

```
[pipeline] stage=<stage> status=<start|ok|fail|warn|skip> key=value ...
```

These are grep-friendly — from a user's log file:

```powershell
Select-String -Path .\log.txt -Pattern '\[pipeline\]'
```

## Stage reference

| Stage | Where it fires | What `ok` means |
| --- | --- | --- |
| `extractor_load` | one per engine, from `video.load_extractor_engines` | the engine imported and reported a version |
| `extractor_ready` | `get_media_info` waiting on the service | an extractor is active within the timeout |
| `extractor_select` | `set_default_extractor` / `_sync_module_globals` | active module mirrored onto `video.ytdl` |
| `metadata_fetch` | `get_media_info` + `process_video` | extractor returned a usable info dict |
| `playlist_parse` | `controller.create_video_playlist` / `playlist_builder` | playlist or single entry built |
| `playlist_entry_normalize` | `playlist_builder._build_playlist_entries` | entry has a full URL we can extract against |
| `stream_build` | `Video._process_streams` | all formats constructed into Stream objects |
| `stream_select` | reserved for future use by controller | |
| `download_enqueue` | `Controller.download` | pre-checks passed; item on `download_q` |
| `download_start` | reserved for brain/worker | |
| `ffmpeg_discover` | `controller.check_ffmpeg` | `ffmpeg.exe` located and `ffmpeg -version` returned rc=0 |
| `ffmpeg_merge` | `merge_video_audio`, `post_process_hls` | ffmpeg returned rc=0 |

## Common triage paths

**User says "nothing happens when I paste a YouTube URL"**

1. Ask for `artifacts/diagnostics/runtime_snapshot.json`
   (`scripts/collect_runtime_diagnostics.py` produces it).
2. Confirm `extractor_service.active == "yt_dlp"`.
3. If `active` is null or `"youtube_dl"`, the primary failed to load.
   Check the user's `yt_dlp` version and ask them to upgrade.
4. Look at the log for `[pipeline] stage=stream_build status=fail` —
   any format_id consistently failing points at yt_dlp drift.

**User says "playlist only downloads the first video"**

1. Request their log filtered on `playlist_entry_normalize`.
2. `fail detail="no identifier or url"` means yt_dlp returned entries
   in an unexpected shape; add a case in `playlist_entry.py` and a
   unit test.

**User says "merge fails on 1080p YouTube"**

1. Confirm `ffmpeg_discover status=ok` in their log.
2. Confirm `ffmpeg_merge status=warn detail=fast stream-copy failed…`
   followed by `ok attempted=['fast', 'slow']`. If slow also fails,
   the container pairing rule (`dash_audio_extension_for`) may need
   extension for their source extension.

## Diagnostic scripts

| Script | What it proves |
| --- | --- |
| `scripts/collect_runtime_diagnostics.py` | python, platform, extractor state, Deno/yt-dlp-ejs, ffmpeg/ffprobe health, active config |
| `scripts/verify_extractor_default.py` | yt_dlp is the runtime default even when the persisted config says otherwise |
| `scripts/verify_playlist_entry_normalization.py` | 7 entry-shape cases all normalize correctly |
| `scripts/verify_ffmpeg_pipeline.py` | ffmpeg usable + every command builder produces the expected shape; ffprobe health is reported but not exit-code mandatory |
| `scripts/verify_packaged_video_flow.py` | packaged binary launches, diagnostics green |
| `scripts/smoke_video_pipeline.py` | synthetic network-free single + playlist smoke |
| `scripts/repro_youtube_bug.py` | live single + playlist repro against real YouTube |
| `scripts/run_regression_suite.py` | P0 regression tests only (fast) |

## Structured event → log-file cheat sheet

```
[pipeline] stage=extractor_load   status=start engine=yt_dlp
[pipeline] stage=extractor_load   status=ok engine=yt_dlp version=2026.03.17 load_seconds=0.35
[pipeline] stage=extractor_select status=ok active=yt_dlp module=yt_dlp
[pipeline] stage=ffmpeg_discover  status=ok path="C:\\ffmpeg\\bin\\ffmpeg.exe" version=8.1
[pipeline] stage=playlist_parse   status=start url=https://youtube.com/watch?v=...
[pipeline] stage=stream_build     status=start url=... formats=19
[pipeline] stage=playlist_parse   status=ok url=... kind=single entries=1
[pipeline] stage=download_enqueue status=ok uid=uid_xxx name="title.mp4" type=video
```
