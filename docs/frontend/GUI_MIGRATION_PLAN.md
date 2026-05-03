# GUI Migration Plan

Status: changed 2026-05-03.

## Evidence
- observed: GUI entry is `firedm/FireDM.py`, which lazily imports `firedm.tkview.MainWindow` for GUI mode and passes it to `Controller(view_class=MainWindow)`.
- observed: `firedm/tkview.py` is the active Tkinter UI and creates `tk.Tk()` in `MainWindow.__init__`.
- observed: `firedm/view.py` defines the small `IView` contract: `run`, `quit`, `update_view`, and `get_user_response`.
- observed: `Controller` calls `self.view.update_view(**kwargs)` and the Tk view queues updates back to the Tk event loop.
- changed: `firedm/frontend_common/` now holds toolkit-neutral view models for engine selection, queue rows, failures, health rows, and update status.

## Official Documentation Checked
| Area | Source | Finding | Impact |
| --- | --- | --- | --- |
| Tkinter | https://docs.python.org/3/library/tkinter.html | `tkinter` is the standard Python interface to Tcl/Tk and Python binaries bundle threaded Tcl/Tk 8.6. | Tkinter remains a valid fallback; current problems are coupling and age of UX, not absence from Python. |
| Tkinter threading | https://docs.python.org/3/library/tkinter.html#threading-model | Tk event handlers must stay quick; long work must not block the event loop. | Preserve controller/worker background boundaries and main-thread UI handoff. |
| Qt for Python | https://doc.qt.io/qtforpython-6/index.html | PySide6 is the official Qt for Python binding and is available under LGPLv3/GPLv3/commercial licensing. | Candidate primary GUI, gated on dependency, license, packaging, and smoke tests. |
| Qt supported platforms | https://doc.qt.io/qtforpython-6/overviews/qtdoc-supported-platforms.html | Qt 6.11 documents supported desktop platforms including Windows and Linux distributions. | Use modern Windows/Linux lane only; legacy OS claims need separate proof. |
| PySide package layout | https://doc.qt.io/qtforpython-6/package_details.html | PySide packages include Qt binaries in site-packages. | Packaging size/data/DLL handling must be planned before adding dependency. |
| PyQt6 | https://riverbankcomputing.com/software/pyqt | PyQt is GPLv3/commercial dual licensed. | Less suitable for this LGPL project unless legal policy accepts GPL/commercial terms. |
| wxPython | https://wxpython.org/pages/overview/ | wxPython is cross-platform and wraps wxWidgets native widgets. | Viable fallback, but migration would not reuse Qt model/view tooling. |
| Dear PyGui | https://dearpygui.readthedocs.io/ | GPU-accelerated cross-platform Python GUI toolkit. | Better for tools than native desktop download-manager parity; not preferred. |
| Toga | https://beeware.org/docs/toga/ | Python-native, OS-native GUI toolkit. | Interesting future candidate but not mature enough locally to displace Qt plan. |

## Target Architecture
- planned: `frontend_common` contains view models and formatting DTOs with no GUI imports.
- planned: `frontend_qt` will contain PySide6 widgets only after dependency policy and packaging impact are approved.
- planned: Tkinter remains the default UI until Qt parity, source smoke, packaged smoke, and rollback are proven.
- planned: Widgets call controller adapters; long-running work stays outside the GUI event loop.

## Migration Order
1. changed: Add toolkit-neutral view models and tests.
2. planned: Add controller adapter functions that translate legacy `DownloadItem`/engine descriptors into view models.
3. planned: Add a feature-gated Qt shell with URL input, engine selector, queue placeholder, health panel, diagnostics/help placeholders.
4. planned: Migrate settings, queue, progress, playlist, video, failure, and completion dialogs one surface at a time.
5. blocked: Retire Tkinter only after parity tests, Windows GUI smoke, packaged smoke, and rollback docs exist.

## Current Blockers
- blocked: No PySide6 dependency is declared.
- blocked: No Qt package/build smoke has run.
- blocked: Existing GUI tests avoid constructing a real Tk root.
- blocked: `tkview.py` imports controller helpers and writes global config directly, so extraction must be staged.
