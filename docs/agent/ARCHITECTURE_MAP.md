# Architecture Map

## Entry Points
| Label | Evidence |
| --- | --- |
| observed | `firedm.py` is a small launcher shim. |
| observed | `firedm/__main__.py` supports `python -m firedm`. |
| observed | `firedm/FireDM.py` contains `main()`, `pars_args()`, `is_gui_mode()`, `import_diagnostics()`, and `open_config_editor()`. |
| observed | `pyproject.toml` exposes console scripts `firedm` and `firedm-native-host`. |

## Package Layout
| Area | Evidence |
| --- | --- |
| observed | Core modules live under `firedm/`. |
| observed | Plugin modules live under `firedm/plugins/`. |
| changed | Engine abstraction models and registry live under `firedm/download_engines/`. |
| observed | Release automation lives under `scripts/release/` plus `build-release.bat`, `scripts/windows-build.ps1`, and `scripts/linux-build.sh`. |
| observed | Tests live under `tests/` and `tests/release/`. |
| observed | Human docs live under `README.md`, `bootstrap/`, `docs/`, and `docs/release/`. |
| changed | Agent docs live under `docs/agent/`. |

## GUI/View Layer
| Label | Evidence |
| --- | --- |
| observed | `firedm/tkview.py` imports Tkinter and defines many GUI classes including `MainWindow`, `DItem`, playlist windows, subtitle/audio/batch windows, and custom widgets. |
| observed | `firedm/view.py` defines abstract `IView`; `firedm/cmdview.py` defines command-line view. |
| inferred | GUI construction is side-effectful because `MainWindow` builds the full UI during init. |

## Controller/Application Orchestration
| Label | Evidence |
| --- | --- |
| observed | `firedm/controller.py` defines `Controller`, `check_ffmpeg()`, `create_video_playlist()`, `url_to_playlist()`, and `download_thumbnail()`. |
| observed | `Controller.__init__` starts observer, download queue, scheduled download, and completion watchdog threads. |
| observed | `Controller.download()` and playlist methods hand items to `download_q`; `brain()` performs actual download work. |
| observed | Native browser messages enter through `_native_control_loop()` and `_handle_native_message()`. |
| inferred | Controller remains the compatibility facade for future service extraction. |

## Download Engine
| Label | Evidence |
| --- | --- |
| observed | `firedm/downloaditem.py` defines `Segment` and `DownloadItem`. |
| observed | `firedm/brain.py` defines `brain()`, `file_manager()`, `thread_manager()`, `fpr()`, and `spr()`. |
| observed | `firedm/worker.py` defines `Worker` with pycurl setup, resume range handling, progress callbacks, protocol handlers, and per-segment writes. |
| observed | `firedm/utils.py` provides `download()`, `get_headers()`, `set_curl_options()`, `get_range_list()`, and file helpers. |
| changed | `firedm/download_engines/base.py`, `models.py`, and `registry.py` define an inert future engine seam; no runtime download behavior is replaced yet. |

## Worker/Thread/Async Model
| Label | Evidence |
| --- | --- |
| observed | `brain()` starts reporter, file manager, and thread manager daemon threads per download. |
| observed | `Controller.__init__` starts daemon threads for observer, queue, scheduler, and completion actions. |
| observed | `utils.threaded()`, `thread_after()`, and `run_thread()` create daemon threads. |
| inferred | Shared mutable `DownloadItem` state crosses controller, worker, file-manager, observer, and GUI layers. |

## Queue/Session/State Persistence
| Label | Evidence |
| --- | --- |
| observed | `setting.py` reads/writes `setting.cfg`, `downloads.dat`, and `thumbnails.dat` as JSON under `config.sett_folder`. |
| observed | `setting.load_setting()` filters persisted settings to `config.settings_keys`. |
| observed | `setting.load_d_map()` drops unsafe persisted download keys before restoring `ObservableDownloadItem`. |
| observed | `app_paths.py` selects local or global settings directory based on writability. |

## Video/Extractor Layer
| Label | Evidence |
| --- | --- |
| observed | `video.py` defines `Video`, `Stream`, `MediaPlaylist`, `Key`, extractor loading, HLS processing, subtitle download, metadata write, and media info functions. |
| observed | `extractor_adapter.py` defines `ExtractorService`, `ExtractorModule`, and extractor selection helpers. |
| observed | `playlist_builder.py` and `playlist_entry.py` normalize extractor results into playlist entries. |
| observed | `pyproject.toml` makes `yt-dlp[default]` the default extractor dependency and keeps `youtube_dl` under optional legacy extra. |

## FFmpeg/Ffprobe/External Tool Discovery
| Label | Evidence |
| --- | --- |
| observed | `ffmpeg_service.py` discovers ffmpeg/ffprobe paths and parses version output. |
| observed | `tool_discovery.py` resolves executable names, PATH directories, and Windows package-store locations. |
| observed | `controller.check_ffmpeg()` updates `config.ffmpeg_actual_path` and `config.ffmpeg_version`. |
| observed | `ffmpeg_commands.py` builds merge, HLS, and audio conversion command pairs. |

## Settings/Config Flow
| Label | Evidence |
| --- | --- |
| observed | `config.py` holds legacy global settings, status constants, popup definitions, and runtime flags. |
| observed | `setting.load_setting()` updates `config.__dict__` only from allowed settings keys. |
| observed | `setting.save_setting()` omits remembered web auth when disabled. |
| inferred | Future work should avoid adding new mutable globals and prefer explicit models. |

## Logging/Error Handling
| Label | Evidence |
| --- | --- |
| observed | `utils.log()` is the central log helper. |
| observed | `pipeline_logger.py` emits structured pipeline events and redacts credential-bearing URL parts. |
| observed | Many legacy paths log exceptions and continue; test-mode branches sometimes re-raise. |

## Tests/Fixtures
| Label | Evidence |
| --- | --- |
| observed | `tests/` includes security, CLI, extractor, ffmpeg, HLS parser, pipeline logger, browser integration, plugin, and download handoff tests. |
| observed | `tests/release/` covers build ID, installer bootstrap, dependency preflight, manifests, Linux build contracts, and workflow checks. |
| observed | `scripts/run_regression_suite.py` lists focused regression tests. |
| changed | `tests/test_download_engines.py` covers typed engine model and registry invariants. |

## Packaging/Build Path
| Label | Evidence |
| --- | --- |
| observed | `pyproject.toml` uses setuptools build backend and dynamic version from `firedm.version.__version__`. |
| observed | Windows PyInstaller spec is `scripts/firedm-win.spec`. |
| observed | Linux PyInstaller spec is `scripts/firedm-linux.spec`. |
| observed | Windows release wrapper `build-release.bat` calls `scripts/release/build_windows.py --arch x64`. |
| observed | `.github/workflows/draft-release.yml` contains Windows and Linux build jobs plus dry-run/publish gating. |

## Platform-Specific Code
| Label | Evidence |
| --- | --- |
| observed | Windows paths appear in `app_paths.py`, `tool_discovery.py`, `scripts/windows-build.ps1`, `installer_bootstrap.py`, and release validation scripts. |
| observed | Linux path/build support appears in `scripts/linux-build.sh`, `scripts/release/build_linux.py`, `docs/release/LINUX_BUILD.md`, and `docs/release/LINUX_PORTABLE.md`. |
| observed | `tkview.py` includes Linux process handling around `ibus`. |

## Dependency Surface
| Label | Evidence |
| --- | --- |
| observed | Runtime deps: `plyer`, `certifi`, `yt-dlp[default]`, `pycurl`, `Pillow`, `pystray`, `awesometkinter`, `packaging`, and Linux-only `distro`. |
| observed | Optional legacy dep: `youtube_dl`. |
| observed | Dev/build deps: `pytest`, `pytest-cov`, `ruff`, `mypy`, `twine`, `build`, and `pyinstaller`. |
| observed | External tools: ffmpeg, ffprobe, Deno, PyInstaller, and optional signing tools. |

## Unknown/Unclear Areas
| Label | Evidence |
| --- | --- |
| blocked | No full line-by-line review of `tkview.py`, `controller.py`, `video.py`, `brain.py`, or `utils.py` was performed in this documentation rebuild. |
| blocked | Live GUI, network download, playlist, and ffmpeg post-processing behavior were not executed. |
| blocked | Linux build lane was not executed on this Windows host. |
