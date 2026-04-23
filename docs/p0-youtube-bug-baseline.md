# P0 YouTube Bug — Baseline (Commit 1)

**Status:** reproduced on 2026-04-23 against `master @ 88240da7`.
**Host:** Windows 11, Python 3.10.11, `yt_dlp 2026.03.17`, `youtube_dl 2021.12.17`.

## What the user reported

Entering either a single YouTube video URL or a YouTube playlist URL into
FireDM appears to "do nothing" — no stream menu, no download starts.

## Reproduction harness

`scripts/repro_youtube_bug.py` drives FireDM's extractor pipeline in-process
and captures structured pass/fail per stage. Artifacts:

- `artifacts/repro/single_video_repro.log`
- `artifacts/repro/playlist_repro.log`
- `artifacts/repro/repro_summary.json`

## Reproduction result

| Target | Stage | Pass? | Notes |
| --- | --- | --- | --- |
| single video | `extractor_ready` | yes | `yt_dlp` selected as default |
| single video | `default_is_primary` | yes | matches `PRIMARY_EXTRACTOR` |
| single video | `create_video_playlist` | **NO** | returned 0 items |
| playlist | `extractor_ready` | yes | |
| playlist | `create_video_playlist` | yes | 15 entries populated |
| playlist | `entry_url_normalization` | yes | first 5 entries have valid HTTPS URLs |
| playlist | `process_first_entry` | **NO** | 0 streams after processing |

Both flows fail, but **at different stages**. The common symptom is the same
underlying error masked by a broad `try/except` block.

## Root-cause evidence

### Primary — `Stream.__init__` multiplies `abr=None` by `1024`

From the repro log:

```
>> controller.create_video_playlist: unsupported operand type(s) for *: 'NoneType' and 'int'
>> _process_video()> error: unsupported operand type(s) for *: 'NoneType' and 'int'
```

Source of the crash — `firedm/video.py:558` inside `Stream.__init__`:

```python
self.rawbitrate = stream_info.get('abr', 0) * 1024
```

`yt_dlp` now emits `'abr': None` for certain formats (subtitles pseudo-formats,
audio-only formats without reported bitrate, etc.). `dict.get('abr', 0)`
returns `None` when the key exists with value `None`, so the multiplication
immediately raises `TypeError`. The entire `Video.__init__` aborts and
`create_video_playlist` reports "no video streams detected" to the user.

The same explosion happens for playlist entries because each entry is
processed via `process_video` → `Video.setup()` → `_process_streams()`.

### Secondary — broad `except` masks the failure

`firedm/controller.py:247` and `firedm/video.py:1506`:

```python
except Exception as e:
    playlist = []
    log('controller.create_video_playlist:', e)
```

Error is logged but the user-visible outcome is an empty playlist menu — the
GUI never surfaces a dialog or offers retry. Identical pattern in
`get_stream()` (`firedm/video.py:380`) where a bare `except:` swallows all
stream-selection failures.

### Secondary — `load_user_extractors()` crashes on startup

Repro log also shows:

```
Exception in thread Thread-2 (import_yt_dlp):
  File "firedm/video.py", line 679, in load_user_extractors
    extractors_folder = os.path.join(config.sett_folder, 'extractors')
TypeError: expected str, bytes or os.PathLike object, not NoneType
```

`config.sett_folder` is `None` when `video.load_extractor_engines()` is
driven in a harness / non-GUI path that doesn't run `firedm.setting`'s
import-time side effects. The import thread dies silently. In the GUI this
happens to work only because the Controller runs settings-load first.

### Secondary — async extractor load race

`firedm/video.py:778-779` launches two daemon threads that each re-evaluate
`choose_extractor_name()` when they finish and then call
`set_default_extractor(active)`. Whichever thread finishes last "wins."
Log evidence:

```
>> yt_dlp version: 2026.03.17  load_time= 0 seconds
>> set default extractor engine to: yt_dlp
... (primary caller runs) ...
>> youtube_dl version: 2021.12.17, load_time= 0 seconds
>> set default extractor engine to: yt_dlp
```

The default happened to stick at `yt_dlp` this run. It is not deterministic.

### Secondary — `youtube_dl`-hardcoded HLS helper

`firedm/video.py:840`:

```python
extract_m3u8_formats = youtube_dl.extractor.common.InfoExtractor._parse_m3u8_formats
```

This references `youtube_dl` explicitly regardless of the active extractor.
If `youtube_dl` fails to import, HLS pre-processing breaks. Private-API use
also makes the call fragile across extractor updates.

## Failure classification

| Cause | Layer | Severity | Affects |
| --- | --- | --- | --- |
| `abr=None * 1024` | extractor/stream model | **critical** | all YouTube URLs with a `None`-bitrate format |
| broad `except` in video/controller path | observability | high | hides failures from users and tests |
| `config.sett_folder` None during extractor load | startup ordering | high | non-GUI drivers, tests, scripted harnesses |
| async extractor load race | extractor init | medium | non-deterministic default selection |
| `_parse_m3u8_formats` hardcoded to `youtube_dl` | extractor coupling | medium | HLS flows if `youtube_dl` missing/broken |
| `youtube_dl` remains in mainline path | dependency policy | medium | upstream is abandoned; drift will compound |

## What this blocks downstream

- stream menu never populates → GUI has nothing to render
- download handoff never reached → user reports "doesn't do anything"
- DASH/HLS merge path untouched (cannot be exercised without streams)
- packaged build inherits same bug

## Fix plan (commits 2-10)

1. **commit 2** — remove swallowed exceptions, add structured logging.
2. **commit 3** — make `yt_dlp` the deterministic default; deprecate mainline
   `youtube_dl` usage; isolate the HLS helper behind the adapter.
3. **commit 4** — fix `Stream.__init__` None-arithmetic; harden `Video.setup()`.
4. **commit 5** — playlist entry URL normalization robustness and per-item
   failure containment.
5. **commit 6** — DASH pairing / ffmpeg merge validation.
6. **commit 7** — extract video-pipeline boundaries from controller.
7. **commit 8** — full regression suite and smoke scripts.
8. **commit 9** — packaged-app verification.
9. **commit 10** — final documentation and handover.

## Gate decision (Commit 1)

- single-video bug reproduced to module/function: `firedm/video.py` ::
  `Stream.__init__` @ line 558 → propagated through `Video.__init__` →
  swallowed by `firedm/controller.py :: create_video_playlist` @ line 247.
- playlist bug reproduced to module/function: same arithmetic failure
  surfacing in `firedm/video.py :: process_video` @ line 1506.
- Failure point is identified to module/function/flow level.

**C1 gate: PASS.**
