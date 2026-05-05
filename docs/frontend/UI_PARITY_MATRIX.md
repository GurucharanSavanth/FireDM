# UI Parity Matrix

Status: changed 2026-05-04.

| Existing feature | Current evidence | Modernized surface | Test target | Status |
| --- | --- | --- | --- | --- |
| GUI mode entry | `firedm/FireDM.py` imports `MainWindow` and builds `Controller(view_class=MainWindow)` | Tk route with smaller view contract | CLI route test with fake view, import smoke | observed |
| View contract | `firedm/view.py` `IView` | controller adapter plus common event DTOs | adapter unit tests | planned |
| URL input | `tkview.py` `process_url` calls controller | `DownloadFormViewModel` wired back into Tk | validation and adapter tests | changed |
| Destination picker | `tkview.py` `Browse` / `FileDialog` | common destination DTO, Tk file dialog wrapper | path validation tests | planned |
| Engine dropdown | no active GUI selector; engine registry exists | `EngineSelectorViewModel` plus descriptor adapter | `tests/test_frontend_common_view_models.py`, `tests/test_frontend_common_adapters.py` | changed |
| Queue row | `tkview.py` `DItem` and `DItem.update` | `QueueItemViewModel` plus legacy item adapter | adapter tests | changed |
| Queue stats | `tkview.py` `update_stat_lbl` and `total_speed` | `QueueStatsViewModel` | aggregation tests | changed |
| Progress/segments | `tkview.py` `Segmentbar` | segment/progress DTO | range/fragment tests | planned |
| Failure display | popup/update-view command flow | `FailureViewModel` | view-model tests | changed |
| Health dashboard | no active panel | `HealthItemViewModel` | view-model tests | changed |
| Update status | legacy update module and docs | `UpdateStatusViewModel` | view-model tests | changed |
| Settings | `tkview.py` `create_settings_tab`, option widgets write config | `SettingsSummaryViewModel` adapter | config side-effect-free adapter tests | changed |
| Plugin manager | `tkview.py` settings tab toggles safe `PluginRegistry` entries and disables policy-blocked rows | policy-backed plugin manifest/status | `tests/test_plugin_manifest.py`, `tests/test_plugins.py` | changed |
| Playlist selection | `SimplePlaylist` with `ttk.Treeview` | playlist selection view model | pure selection tests | planned |
| Media presets | `MediaPresets` | media option DTOs | stream option tests | planned |
| Subtitle dialog | `SubtitleWindow` | subtitle selection DTO | selection tests | planned |
| Batch URLs | `BatchWindow` | batch form view model | URL validation/redaction tests | planned |
| Tray/menu | `pystray` and Tk bindings | platform service adapter | import/smoke tests | planned |
| Diagnostics/help | docs and scripts only | `DiagnosticsActionViewModel` and `HelpTopicViewModel` adapters | import/safety adapter tests | changed |

Rules:
- changed: Common view models are data-only and do not import Tkinter.
- changed: Parallel preview GUI code is removed; current modernization happens inside the active FireDM path.
- blocked: Any future GUI framework switch needs full parity status and packaged launch evidence first.
