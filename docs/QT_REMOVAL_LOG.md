# Qt Removal Log

## Summary

FireDM was consolidated to a single tkinter-based GUI. All Qt/PyQt code paths, build targets, and GUI framework branches have been removed.

## What Was Removed

- `firedm/frontend_qt/`: Complete PyQt5/PyQt6 frontend implementation
- `firedm-qt.py`: Qt launcher shim (deprecated)
- PyQt imports: removed from all plugin detection and UI config paths
- Qt build targets: removed from pyproject.toml extras and setup.py
- Qt styling system: replaced with ttk theming
- Qt-specific test fixtures: removed from test infrastructure

## Why

- Consolidation reduces maintenance surface area and test complexity
- Tkinter is the only verified GUI baseline
- Single code path improves release predictability
- Removes dependency on PyQt build wheels (platform-specific issues)
- Focuses development on proven delivery mechanism

## When

Initial Qt removal: commit `07497dc` (snapshot before modernization batch)

## Verified: Test Guards Prevent Reintroduction

- Plugin registry rejects PyQt imports: `_uses_forbidden_exec()` static analysis
- No Qt/PyQt strings in application code or build config
- GUI tests explicitly target tkinter via `ttk` widget inspection
- CI workflow tests only tkinter stack (windows-smoke.yml)

## Migration Path

- None: tkinter is the primary GUI framework
- Existing PyQt plugins must be rewritten as tkinter subclasses of `PluginBase`
- GUI state and commands available via CLI; advanced users can script via plugin hooks

## Remaining Tk-Only Artifacts

- `firedm/tkview.py`: Main Tkinter GUI
- `scripts/firedm-win.spec`: PyInstaller spec for tkinter app
- `firedm/frontend_common/`: Toolkit-neutral view models (abstract layer)
- `firedm/setting.py`: Settings UI (ttk-based)
- All icon assets: base64-encoded for tkinter compatibility

## Next Steps

- Keep Tkinter GUI in current state; prioritize stability over new framework migration
- Document any new tkinter widget patterns in `docs/frontend.md`
- Use view models abstraction to allow future UI layer swaps if needed (but not recommended)
