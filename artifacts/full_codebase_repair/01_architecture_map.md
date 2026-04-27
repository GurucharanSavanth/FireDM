# 01 Architecture Map

Evidence labels: observed = local file/command output; inferred = local-code reasoning.

## Entry Points
- observed files: `firedm.py`, `firedm/__main__.py`, `firedm/FireDM.py`
- observed functions: `firedm.FireDM.main`, `pars_args`, `is_gui_mode`, `import_diagnostics`
- observed deps: `argparse`, `subprocess`, `setting`, `Controller`, `CmdView`
- failure points: import diagnostics, settings load, GUI import, updater/edit-config subprocess
- coverage: `tests/test_cli.py`, `tests/test_packaged_diagnostics.py`

## GUI/View Layer
- observed files: `firedm/tkview.py`, `firedm/cmdview.py`, `firedm/view.py`, `firedm/systray.py`
- observed classes: `MainWindow`, many Tk widget subclasses, `CmdView`, `IView`
- state owned: GUI widgets, callbacks, user settings controls, plugin toggles
- failure points: large legacy Tk surface, GUI-thread coupling, plugin toggle errors swallowed to log
- coverage: limited CLI routing tests; real GUI interaction unverified

## Controller/Application Orchestration
- observed file: `firedm/controller.py`
- observed class: `Controller`
- state owned: `d_map`, queues, playlist/stream menu state, `download_q`, plugin lifecycle, native-control endpoint
- entry/exit: user URL updates, `download`, queue worker loop, `_pre_download_checks`, `_post_download`, plugin hooks
- failure points: new native endpoint starts regardless of plugin, raw JSON accepted, Windows pipe server not real
- coverage: `tests/test_download_handoff.py`, `tests/test_controller_video_integration.py`, plugin tests partial

## Download Model/Items
- observed files: `firedm/downloaditem.py`, `firedm/model.py`, `firedm/video.py`
- observed classes: `Segment`, `DownloadItem`, `Observable`, `ObservableDownloadItem`, `ObservableVideo`, `Video`, `Stream`, `Key`, `MediaPlaylist`
- state owned: URL, headers, status, segments, temp/target paths, media fields, observer callbacks
- failure points: broad legacy exceptions, thread mutation, saved `http_headers`, `Key.__init__` uses suspicious `super().__init__(self)`
- coverage: stream/video/model observer tests

## Download Engine / Worker / Queue
- observed files: `firedm/brain.py`, `firedm/worker.py`, `firedm/controller.py`
- observed functions/classes: `brain`, `file_manager`, `thread_manager`, `Worker`
- model: controller enqueues `DownloadItem`; brain starts worker/file-manager threads; workers fetch segments; file manager merges and post-processes
- failure points: plugin queue path can misroute magnet links into pycurl worker; protocol handlers add optional dependency paths; broad exceptions remain
- coverage: `tests/test_download_handoff.py`, `tests/test_plugins.py`, mocked subsystem tests

## Video/Media Layer
- observed files: `firedm/video.py`, `firedm/extractor_adapter.py`, `firedm/playlist_builder.py`, `firedm/playlist_entry.py`
- observed functions/classes: `ExtractorService`, `Video`, `Stream`, playlist normalization, HLS pre/post processing
- deps: `yt_dlp` primary, optional `youtube_dl`, ffmpeg/ffprobe
- failure points: real network and ffmpeg merge manual-only; DRM decryption plugin introduces prohibited ClearKey/AES behavior
- coverage: video/playlist/HLS/extractor unit and smoke tests

## Settings/State/Config
- observed files: `firedm/config.py`, `firedm/setting.py`, `firedm/app_paths.py`
- state owned: global config module, `setting.cfg`, `downloads.dat`, `thumbnails.dat`
- persistence: JSON with key allow-list; unsafe completion keys stripped from download map
- failure points: plugin state persisted and plugin load deferred to controller; native-host secret path previously diverges from settings path
- coverage: `tests/test_security.py`, `tests/test_app_paths.py`, plugin config tests

## FFmpeg/Tool Discovery
- observed files: `firedm/ffmpeg_service.py`, `firedm/ffmpeg_commands.py`, `firedm/tool_discovery.py`, `firedm/update.py`
- deps: external ffmpeg/ffprobe, PATH/app dir/Winget discovery
- failure points: stale PATH false negatives, package mode external-tool drift
- coverage: `tests/test_ffmpeg_service.py`, `tests/test_ffmpeg_pipeline.py`

## Logging/Error Handling
- observed files: `firedm/utils.py`, `firedm/pipeline_logger.py`, callers in brain/video/model
- behavior: structured pipeline logger redacts credential-like URL fields and freeform detail text
- failure points: legacy broad `except/pass`; native host used `utils.log` on stdio path, which can corrupt native messaging stdout
- coverage: `tests/test_pipeline_logger_redaction.py`, observer isolation tests

## Packaging/Build
- observed files: `pyproject.toml`, `setup.py`, `scripts/firedm-win.spec`, `scripts/windows-build.ps1`, `.github/workflows/*.yml`
- behavior: setuptools source package; PyInstaller one-folder Windows package; historical AppImage/exe scripts remain
- failure points: new plugin hiddenimports included undeclared optional deps (`cryptography`, `paramiko`); native host lacks dedicated executable path in manifest/package
- coverage: package smoke tests and spec reviewed; package build not run in baseline

## Platform-Specific Code
- observed Windows: app paths, Winget discovery, PyInstaller spec, native pipe path, `os.startfile`
- observed Linux: AppImage historical scripts, `xdg-open`, distro dep, Unix socket path
- verified status: Windows source compile/import/test baseline verified; Linux inferred only
