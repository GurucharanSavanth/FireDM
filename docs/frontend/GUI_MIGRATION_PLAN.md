# GUI Modernization Plan

Status: changed 2026-05-04.

## Evidence
- observed: GUI entry is `firedm/FireDM.py`; GUI mode imports `firedm.tkview.MainWindow` and passes it to `Controller(view_class=MainWindow)`.
- observed: `firedm/tkview.py` is the active Tkinter UI and creates `tk.Tk()` in `MainWindow.__init__`.
- observed: `firedm/view.py` defines the small `IView` contract: `run`, `quit`, `update_view`, and `get_user_response`.
- observed: `Controller` calls `self.view.update_view(**kwargs)` and the Tk view queues updates back to the Tk event loop.
- changed: `firedm/frontend_common/` holds toolkit-neutral view models for engine selection, download forms, queue rows/stats, failures, health rows, update status, settings summaries, diagnostics actions, help topics, and connector warnings.
- changed: `firedm/frontend_common/adapters.py` maps legacy controller/backend objects into common view models without importing Tkinter, controller, or config modules.
- changed: The experimental alternate frontend lane was removed; modernization now targets the active FireDM GUI/core path instead of a parallel preview app.

## Target Architecture
- Keep `Controller` as the compatibility facade while moving GUI-facing state into typed DTOs and side-effect-free adapters.
- Keep Tkinter as the shipped runtime until a replacement has full feature parity, real packaged launch smoke, and a rollback plan.
- Extract high-risk Tk code in small surfaces: URL form, queue table, stream menu, settings, playlist, dialogs, tray, diagnostics, and updater notices.
- Keep network/download work outside the GUI event loop; UI updates must flow through the `IView.update_view` contract.
- Do not introduce another GUI framework until the current UI behavior is mapped, tested, and decoupled from controller/config globals.

## Migration Order
1. changed: Add toolkit-neutral view models and tests.
2. changed: Add pure adapter functions for legacy `DownloadItem` objects, engine descriptors, engine health, structured failures, update mappings, settings/config mappings, diagnostics actions, and help paths.
3. current: Remove the parallel preview frontend and keep release builds focused on `firedm.py`, `firedm/FireDM.py`, and `firedm/tkview.py`.
4. next: Refactor `tkview.py` one surface at a time behind view-model adapters.
5. next: Add GUI smoke hooks that can launch and exit the packaged Tk app without relying on manual clicks.
6. blocked: Full GUI replacement is not credible until the extracted surfaces have parity tests and packaged smoke evidence.

## Current Blockers
- blocked: `tkview.py` is still a large legacy module with direct controller/config coupling.
- blocked: Full packaged GUI interaction remains manual.
- blocked: No alternate framework is approved until the active GUI contract is stabilized.
