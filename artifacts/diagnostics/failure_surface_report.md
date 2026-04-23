# Failure Surface Report (Commit 2)

## Purpose

Inventory every swallowed or vague failure path in the YouTube / download
pipeline, categorize each, and decide what Commit 2 does about it. Business
fixes live in Commits 3-6.

## Before-state inventory

| Location | Shape | Blast radius | Commit 2 disposition |
| --- | --- | --- | --- |
| `firedm/controller.py :: create_video_playlist` line 247 | `except Exception as e: playlist=[]; log(...)` | **user sees empty playlist** for any downstream error | narrowed: emits structured `playlist_parse status=fail` event; still returns `[]` to preserve GUI contract |
| `firedm/video.py :: get_media_info` line 1482 | single wide `except Exception` around `extract_info` + `process_ie_result` | **user sees nothing** — `get_media_info` returns whatever fell through | split into two narrower `try` blocks around `ydl.extract_info` and `process_ie_result`; both emit `metadata_fetch fail` |
| `firedm/video.py :: process_video` line 1506 | `except Exception as e: log(...)` | **playlist item silently stays un-processed** | narrowed: emits `metadata_fetch fail` + keeps test-mode re-raise |
| `firedm/video.py :: Stream.get_stream` line 380 | `except:` (bare) | stream-selection miss silently returns `None` | kept (selection logic iterates multiple times; raising here would cascade into GUI) — observability added at caller |
| `firedm/video.py :: Stream.quality` line 604 | `except:` (bare) | quality falls back to `0` | kept (type coercion helper) |
| `firedm/video.py :: set_interrupt_switch` line 812 | `except Exception` | swallowed URL-open hook install | instrumented via future Commit 3 work |
| `firedm/video.py :: Video.get_thumbnail` line 417 | `except Exception` | thumbnail quietly missing | kept; low-severity UX-only |
| `firedm/video.py :: load_user_extractors` line 706 | `except Exception as e: log(...); raise` | re-raises from daemon thread → thread dies silently | **fixed by wrapping at call-site with `_load_user_extractors_safely`** — emits `extractor_load fail phase=user_extractors` |
| `firedm/video.py :: Video._process_streams` no try | single malformed format aborted entire menu | **menu built with 0 streams** | **wrapped per-format**: `extract_build status=fail format_id=…` event, skip bad format, keep menu |
| `firedm/controller.py :: check_ffmpeg` | silent negative | user sees `FFMPEG is missing` but no machine-readable signal | `ffmpeg_discover` event with both `ok` and `fail` statuses |
| `firedm/controller.py :: Controller.download` | failure returns `False` without trace | download fails to enqueue with no telemetry | `download_enqueue` event on both branches |
| `firedm/controller.py :: auto_refresh_url` line 377 | bare `except:` inside audio match | silent audio drop on refresh | out of P0 scope (url-refresh is a secondary flow); flagged for future |

## After-state invariants

1. **Extractor initialization failure is observable**: both daemon threads
   emit `extractor_load start` and terminate with `ok` or `fail`. `fail` also
   fires for `load_user_extractors` so a broken user-extractor folder no
   longer masquerades as "extractor didn't load."
2. **Extractor readiness timeout is bounded**: `get_media_info` waits at
   most 45 seconds (was `while not ytdl: time.sleep(1)` infinite).
   Timeout emits `extractor_ready fail` and returns `None`.
3. **Metadata fetch failure is attributed**: two `metadata_fetch fail`
   events with `phase=initial` vs `phase=process_ie` distinguish between
   network / extractor drift vs post-processing errors.
4. **Stream build failure is per-format**: a single unhappy format in the
   upstream payload no longer aborts the menu build. Each skipped format
   emits a `stream_build fail` event with `format_id`.
5. **Playlist parse failure is attributed**: `kind=single` vs `kind=playlist`
   lets automated tests and GUI know which branch failed.
6. **ffmpeg discovery has machine-readable signals**: `ffmpeg_discover ok
   path=... version=...` vs `fail detail=... searched=[...]`.
7. **Download enqueue has telemetry on both branches**.

## Residual risks

- `brain.brain`, `worker.thread_manager`, per-segment workers, HLS pre/post
  processing still use ad-hoc logging. Commits 6-7 extend pipeline events
  into these modules.
- `tkview.py` (GUI) still has 29 bare `except:` blocks. They are not part of
  the P0 video pipeline and are deferred.
- `utils.py` has 14 bare `except:` blocks — most in helpers that Commit 3's
  extractor work will touch only partially. Full sweep deferred.

## Commit 2 gate decision

- all extractor / metadata / playlist / stream / ffmpeg / enqueue failure
  paths now emit a structured, actionable event;
- no critical failure in the YouTube single-video or playlist flow remains
  silently swallowed (the `Stream.__init__` crash is still there as a
  defect, but it is now **visible**, which is exactly what Commit 2 owes).

**C2 gate: PASS.**
