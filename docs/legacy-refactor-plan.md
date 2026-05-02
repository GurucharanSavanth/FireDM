# Legacy Refactor Plan

This document records the current state of the remaining large stateful modules
and gives staged extraction boundaries. It is intentionally a refactor plan, not
a claim that these areas are fully modernized.

## Scope Reviewed

`firedm/controller.py`, `firedm/video.py`, and `firedm/tkview.py` were inspected
for entry points, classes/functions, mutable state, concurrency, external tool
handoffs, and test boundaries. Together they still carry most of the runtime
behavior: URL intake, playlist extraction, download queueing, GUI state, and
ffmpeg post-processing.

## controller.py

Responsibility:
- Owns MVC orchestration, app settings loading, URL processing, playlist
  preparation, download queueing, observer fanout, ffmpeg availability checks,
  update checks, and completion actions.

Key state:
- `self.d_map`, `self.download_q`, `self.observer_q`, `self.playlist`,
  `self.last_active_playlist`, `_playlist_menu`, `_stream_menu`, and global
  `config` mutation through `set_option`.

Risk:
- Multiple daemon threads are started in `Controller.__init__`, which makes
  construction side-effectful and hard to test.
- Download state is mutated on shared `ObservableDownloadItem` objects across
  worker, observer, scheduled-download, and completion threads.
- View updates are string-command dictionaries instead of typed events.
- GUI prompts are mixed into pre-download validation, including ffmpeg handling.

Safe next extraction:
- Move pre-download validation into `download_validation.py`.
- Move queue scheduling and active-download admission into `download_queue.py`.
- Move view event construction into `view_events.py`.
- Keep `Controller` as the compatibility facade until tests cover the extracted
  services.

Validation required:
- Unit tests for direct file, video, missing ffmpeg, duplicate filename,
  scheduled item, cancel, retry, and completion-command paths.
- Mocked integration test for URL to playlist to queue handoff.
- Manual GUI download smoke before each behavior-changing extraction.

## video.py

Responsibility:
- Owns video object construction, stream selection, extractor loading, yt-dlp
  options, HLS preprocessing, subtitle handling, ffmpeg merge/conversion, and
  metadata writing.

Key state:
- Module globals `youtube_dl`, `yt_dlp`, `ytdl`, `EXTRACTOR_SERVICE`, and many
  reads/writes against global `config`.

Risk:
- Extractor loading is asynchronous but legacy callers still read module-level
  globals.
- `Video` combines metadata parsing, stream selection, thumbnail download, and
  output-name logic.
- HLS preprocessing performs network downloads, manifest parsing, temp-file
  writes, segment creation, and unsupported-protocol decisions in one function.
- ffmpeg command creation is partly separated, but ffmpeg process execution and
  status mutation remain in this module.

Safe next extraction:
- Keep `extractor_adapter.py` as the loading/selection boundary and move more
  direct `ytdl` reads behind it.
- Split stream selection into `stream_selection.py`.
- Split HLS manifest parsing into pure functions before moving network/file
  effects.
- Keep ffmpeg command builders in `ffmpeg_commands.py`; move process execution
  behind a testable runner after command tests are complete.

Validation required:
- Mocked yt-dlp single-video and playlist fixtures.
- HLS manifest parser tests for encrypted, unsupported, media, and master
  playlists.
- ffmpeg runner tests for fast-path, slow fallback, cancellation, and failure
  reporting.
- Manual real video, playlist, subtitle, DASH, and HLS validation.

## tkview.py

Responsibility:
- Owns the Tkinter GUI, custom widgets, dialogs, playlist window, downloads tab,
  settings tab, systray integration, cross-thread method dispatch, and user
  prompts.

Key state:
- `MainWindow` owns `root`, `d_items`, playlist/subtitle/batch windows,
  command/response/update queues, post-processors, theme globals, config-bound
  Tk variables, and controller callbacks.

Risk:
- Importing the module loads Tk-related globals and many widget classes.
- `MainWindow.__init__` builds the full GUI immediately, so construction is a
  real GUI action.
- Controller-to-view events are untyped dictionaries and string commands.
- Blocking popup response queues couple worker threads to GUI event handling.
- Linux-specific `ibus` subprocess handling lives inside the main window class.

Safe next extraction:
- Keep lazy GUI import in `FireDM.py` so CLI and packaging diagnostics do not
  need a Tk window.
- Move popup/request-response protocol into `gui_prompts.py`.
- Move downloads-tab list behavior into a smaller view model after event shapes
  are typed.
- Move Linux-only ibus workaround out of `MainWindow`.

Validation required:
- Non-GUI unit tests for event-shape handlers where callbacks can be isolated.
- Manual source GUI startup and packaged GUI startup.
- Manual playlist dialog, download queue, settings write, systray, and close
  behavior.

## Rebuild Decision

No full rebuild is justified yet. The modules are risky because of size and
mutable state, but targeted extraction is safer than replacing working legacy
behavior. Rebuild only a bounded service when tests can exercise the old and new
paths side by side.
