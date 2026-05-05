# Legacy Modernization Roadmap

## Purpose

This document maps old patterns to modern equivalents and prioritizes migration work across the codebase. Modernization improves readability, safety, and maintenance without breaking user-facing behavior.

## Migration Priority Matrix

### P0: Security + Safety (High Impact, Blocking)

#### print() → logging.getLogger()
- **Status:** In-progress for core modules
- **Scope:** `app_paths.py`, `tool_discovery.py`, `ffmpeg_service.py`, `extractor_adapter.py` (done); `controller.py`, `tkview.py`, `video.py` (blocked until refactored)
- **Risk:** Low; drop-in replacement with backward-compat layer in `utils.log()`
- **Example:**
  ```python
  # Old
  print(f"Download started: {url}")
  
  # New
  import logging
  logger = logging.getLogger(__name__)
  logger.info(f"Download started: {url}")
  ```

#### os.path → pathlib.Path
- **Status:** Partial in modernized seams
- **Scope:** Path construction, resolution, and string concatenation
- **Risk:** Low for well-tested paths; watch for `.resolve()` behavior on symlinks (Windows-specific)
- **Example:**
  ```python
  # Old
  path = os.path.join(folder, subfolder, filename)
  
  # New
  from pathlib import Path
  path = Path(folder) / subfolder / filename
  ```

#### subprocess without shell=True + argv array
- **Status:** Done in `ffmpeg_service.py`, `extractor_adapter.py`
- **Scope:** Review all `subprocess.run()` and `popen()` calls in `controller.py`, `video.py`
- **Risk:** High if args are user-controlled; enforce argparse validation first
- **Example:**
  ```python
  # Old (vulnerable to injection)
  os.system(f"ffmpeg {input_file} -output {output_file}")
  
  # New (safe)
  subprocess.run(
      ["ffmpeg", str(input_file), "-output", str(output_file)],
      check=True,
      capture_output=True
  )
  ```

### P1: Readability + Maintainability

#### .format() → f-strings
- **Status:** New code uses f-strings exclusively
- **Scope:** `controller.py`, `tkview.py`, `video.py`, `utils.py`
- **Risk:** Very low; automated migration via ruff
- **Command:** `ruff check --fix --select RUF001 firedm/`
- **Example:**
  ```python
  # Old
  msg = "Download {} of {} files".format(current, total)
  
  # New
  msg = f"Download {current} of {total} files"
  ```

#### Type hints on function signatures
- **Status:** Partial (modernized seams fully typed)
- **Scope:** All public methods in `PluginBase`, `PluginRegistry`, `PluginMeta`, `ffmpeg_service.py`, `tool_discovery.py`
- **Risk:** Low; use mypy in strict mode for validation
- **Example:**
  ```python
  # Old
  def download(url, output_file):
      ...
  
  # New
  def download(url: str, output_file: Path | str) -> bool:
      ...
  ```

### P2: Data Flow Clarity

#### Hardcoded strings → Named constants
- **Status:** Partial in config seams
- **Scope:** Hook names (`download_start`, `segment_complete`), event types, path defaults
- **Risk:** Low; extract from `registry.py` and `config.py` first
- **Example:**
  ```python
  # Old
  if key == "download_start":
      ...
  
  # New
  from firedm.constants import HOOK_DOWNLOAD_START
  if key == HOOK_DOWNLOAD_START:
      ...
  ```

#### Implicit defaults → Explicit config
- **Status:** In-progress
- **Scope:** Download timeout, retry count, segment size, proxy settings
- **Risk:** Medium; backward compat requires migration code
- **Tool:** Use `firedm/setting.py` and `config.py` as source of truth

### P3: Tk GUI Modernization

#### Old Tk widgets → ttk (themed) widgets
- **Status:** Partial; buttons, labels done in new code; menus, dialogs pending
- **Scope:** `tkview.py` refactor (blocked until business logic extracted)
- **Risk:** Medium; visual/layout changes may affect UX
- **Example:**
  ```python
  # Old
  import tkinter as tk
  btn = tk.Button(root, text="Download", command=on_click)
  
  # New
  import tkinter.ttk as ttk
  btn = ttk.Button(root, text="Download", command=on_click)
  ```

#### Hardcoded colors/fonts → Style tokens
- **Status:** Not started
- **Scope:** Define `firedm/frontend_common/style_tokens.py`
- **Risk:** Low but requires design review
- **Path:** Add CSS-like theme system to `frontend_common/`

#### Event callbacks → Data binding (View Model)
- **Status:** In-progress with `frontend_common/view_models.py`
- **Scope:** Decouple GUI state from business logic via ViewModel layer
- **Risk:** High refactor effort; do incrementally per subsystem
- **Example:**
  ```python
  # Old: GUI directly mutates Download object
  download.status = "downloading"
  
  # New: GUI updates ViewModel; ViewModel syncs to domain
  view_model.set_status("downloading")
  ```

## Phased Execution Plan

### Phase 1: Core Seams (Already Largely Done)
- `app_paths.py` ✓
- `tool_discovery.py` ✓
- `ffmpeg_service.py` ✓
- `extractor_adapter.py` ✓
- `pipeline_logger.py` ✓
- `plugins/registry.py` ✓
- `plugins/policy.py` ✓

**Time estimate:** Maintenance + edge cases only

### Phase 2: Controller + Video Layer (Blocked)
- Requires business logic extraction first (large refactor)
- Cannot modernize logging/subprocess until state machine is clearer
- **Blocker:** `docs/legacy-refactor-plan.md` must guide this work

**Time estimate:** 3-4 weeks per module

### Phase 3: Tkinter Frontend (Blocked)
- Depends on Phase 2 completion
- Refactor into ViewModel + View layers
- Migrate to ttk + style system

**Time estimate:** 2-3 weeks

### Phase 4: Optional Enhancements
- Browser native messaging (if implemented)
- Async download pipeline (if needed for responsiveness)
- Plugin performance monitoring

**Time estimate:** Ongoing, not critical path

## Tool Support

### Automated Migrations
```bash
# f-string conversion
ruff check --fix --select RUF001 firedm/

# Import sorting
isort firedm/

# Type checking (limited scope)
mypy firedm/app_paths.py firedm/plugins/

# Security: check for exec/eval
python -m ast -h  # manual inspection tool
```

### Manual Review Required
- subprocess calls (audit argv construction)
- logging calls (ensure secrets are not logged)
- Path construction on Windows (test with UNC paths)
- Tk GUI changes (visual/UX regression testing)

## Testing Strategy

- **Unit tests:** Cover new modernized functions with fixtures
- **Regression tests:** Existing integration tests must pass before/after migration
- **Smoke tests:** Windows package build and import must succeed
- **Manual validation:** Download, playlist, ffmpeg workflows must work as-is

## Success Metrics

- All modernized seams pass mypy strict mode
- ruff check raises zero security issues on `app_paths.py`, `plugins/`, `frontend_common/`
- 90%+ of new code uses f-strings, type hints, pathlib
- No new `print()` calls in core modules (only via `log()` compat layer)
- GUI remains functional and responsive (UX unchanged)

## See Also

- `docs/legacy-refactor-plan.md` — Business logic extraction roadmap
- `docs/developer/IMPLEMENTATION_LAYERS.md` — Architectural layers
- `docs/testing.md` — Test infrastructure and validation
