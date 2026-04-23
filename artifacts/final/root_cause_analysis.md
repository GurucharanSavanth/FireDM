# Root Cause Analysis

## Symptom

Pasting a YouTube single-video URL or playlist URL into FireDM resulted in
no stream menu, no download, and no user-visible error.

## Single dominant root cause

`firedm/video.py :: Stream.__init__` (before Commit 4):

```python
self.rawbitrate = stream_info.get('abr', 0) * 1024
```

`yt_dlp` (actively maintained, 2026.03.17 at baseline) emits `abr: None`
for several formats that FireDM surfaces, notably the legacy format id
`18`. `dict.get('abr', 0)` returns `None` when the key is present with a
`None` value, so the multiplication raises `TypeError`. The exception
aborts `Video.__init__` before the stream menu is built.

## Why it was invisible

- `firedm/controller.py :: create_video_playlist` wrapped the entire
  construction in `except Exception as e: playlist=[]; log(...)`. The
  user saw an empty playlist menu and no diagnostic.
- `firedm/video.py :: process_video` did the same for playlist entries:
  `except Exception as e: log(...)` with nothing surfaced to the GUI.
- `firedm/video.py :: Stream.get_stream` swallowed selection misses in
  a bare `except:`.

## Why it manifested now but not earlier

- `youtube_dl` (2021.12.17) still shipped numeric defaults for `abr`
  (mostly 0). The old extractor rarely emitted `None`.
- `yt_dlp` normalized its info dict contracts more aggressively, and
  new YouTube formats (AV1-in-WebM pseudo-formats, storyboard/preview
  pseudo-formats, legacy format_id=18 after the 2023 refactor) started
  carrying explicit `None` bitrates.
- FireDM's extractor selection was a daemon-thread race that leaned
  toward `youtube_dl` on slow-import machines — so some users silently
  stayed on the legacy extractor and never hit the bug. Newer machines
  finished `yt_dlp` first and failed.

## Contributing defects

| ID | Defect | Severity |
| --- | --- | --- |
| R1 | `Stream.__init__` None-arithmetic | critical — primary crash |
| R2 | `create_video_playlist` broad except | high — masks R1 and any future similar failure |
| R3 | `process_video` broad except | high — masks R1 on the playlist path |
| R4 | `Stream.get_stream` bare except | medium — stream selection silently returns None |
| R5 | `load_user_extractors` on `config.sett_folder=None` | high — kills extractor daemon thread silently in non-GUI callers |
| R6 | Async extractor load race | medium — non-deterministic default selection |
| R7 | Unbounded `while not ytdl: time.sleep(1)` in `get_media_info` | medium — hangs forever if both extractors fail to import |
| R8 | `_parse_m3u8_formats` hardcoded to `youtube_dl` | medium — HLS flows break if fallback import fails |
| R9 | `create_video_playlist` playlist entry URL pick: `webpage_url or url or id` | high — id-only entries produced invalid Video URLs |

All nine are addressed by commits 2 through 7.

## Why the regression suite missed this before

- Automated coverage was focused on the startup seams (cli, app_paths,
  ffmpeg_service, extractor_adapter). There were no tests for the
  `Video / Stream` model pathway, so `abr=None` never ran under pytest.
- The existing `test_extractor_adapter.py` enforced the *wrong*
  policy — it asserted the user-configured extractor wins (which let
  `youtube_dl` be the default). That policy is reversed in Commit 3
  and the test rewritten.

## Confidence level

High. The fix is proven by:

- `scripts/repro_youtube_bug.py` against real YouTube: all five stages
  for single-video pass end-to-end.
- `tests/test_single_video_flow.py :: test_single_video_builds_streams_even_with_none_bitrate`:
  explicit regression on the `abr=None` format.
- `artifacts/repro/repro_summary.json`: structured pass/fail per stage.
- `artifacts/packaged/packaged_video_flow_result.json`: packaged
  diagnostics all green.

## Probability of recurrence

Low for the exact `abr=None` shape (coerced at the source in
`_coerce_number`). Medium for similar drift in other numeric fields
(`filesize`, `vbr`, `height` on exotic formats) — mitigated by the
`stream_build` try/except containment in `_process_streams`. High for
downstream drift in private extractor APIs like `_parse_m3u8_formats` —
tracked in `artifacts/final/remaining_risks.md`.
