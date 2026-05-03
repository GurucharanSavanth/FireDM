# UI Parity Matrix

Status: changed 2026-05-03.

| Existing feature | Current evidence | Future common/Qt surface | Test target | Status |
| --- | --- | --- | --- | --- |
| GUI mode entry | `firedm/FireDM.py` imports `MainWindow` and builds `Controller(view_class=MainWindow)` | feature-gated Qt entry point after dependency approval | CLI route test with fake view, import smoke | observed |
| View contract | `firedm/view.py` `IView` | controller adapter plus common event DTOs | adapter unit tests | planned |
| URL input | `tkview.py` `process_url` calls controller | `DownloadFormViewModel` next slice, then Qt URL form | validation and signal tests | planned |
| Destination picker | `tkview.py` `Browse` / `FileDialog` | common destination DTO, Qt file dialog wrapper | path validation tests | planned |
| Engine dropdown | no active GUI selector; engine registry exists | `EngineSelectorViewModel` | changed in `tests/test_frontend_common_view_models.py` | changed |
| Queue row | `tkview.py` `DItem` and `DItem.update` | `QueueItemViewModel` | changed in `tests/test_frontend_common_view_models.py` | changed |
| Queue stats | `tkview.py` `update_stat_lbl` and `total_speed` | `DownloadListStatsViewModel` | aggregation tests | planned |
| Progress/segments | `tkview.py` `Segmentbar` | segment/progress DTO | range/fragment tests | planned |
| Failure display | popup/update-view command flow | `FailureViewModel` | changed in `tests/test_frontend_common_view_models.py` | changed |
| Health dashboard | no active panel | `HealthItemViewModel` | changed in `tests/test_frontend_common_view_models.py` | changed |
| Update status | legacy update module and docs | `UpdateStatusViewModel` | changed in `tests/test_frontend_common_view_models.py` | changed |
| Settings | `tkview.py` `create_settings_tab`, option widgets write config | settings DTOs plus explicit controller adapter | config side-effect tests | planned |
| Plugin manager | `tkview.py` settings tab toggles `PluginRegistry` | plugin settings adapter | disabled/default tests | planned |
| Playlist selection | `SimplePlaylist` with `ttk.Treeview` | playlist selection view model | pure selection tests | planned |
| Media presets | `MediaPresets` | media option DTOs | stream option tests | planned |
| Subtitle dialog | `SubtitleWindow` | subtitle selection DTO | selection tests | planned |
| Batch URLs | `BatchWindow` | batch form view model | URL validation/redaction tests | planned |
| Tray/menu | `pystray` and Tk bindings | platform service adapter | import/smoke tests | planned |
| Diagnostics/help | docs and scripts only | diagnostics/help panel | export safety tests | planned |

Rules:
- changed: Common view models are data-only and do not import Tkinter or Qt.
- blocked: Qt widgets cannot be added until dependency and packaging gates pass.
- blocked: Tk fallback stays until every row has parity status and smoke evidence.
