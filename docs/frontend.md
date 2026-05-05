# Tkinter Frontend Architecture

## Overview

FireDM uses Tkinter (tk/ttk) as the sole GUI framework. The frontend layer is split into three concerns:

1. **tkview.py** — Tk widget tree and event callbacks (GUI implementation)
2. **setting.py** — Settings UI and persistence (ttk-based form)
3. **frontend_common/view_models.py** — Toolkit-neutral state (testable, reusable)

## Architecture

```
┌─────────────────────────────────────────────┐
│ firedm/tkview.py (Tk Widgets)               │
│ - Canvas, Frame, Menu, Menubutton           │
│ - Button, Entry, Listbox, Scrollbar         │
│ - Event callbacks: on_download_click, ...   │
└────────────────┬────────────────────────────┘
                 │ calls
                 ↓
┌─────────────────────────────────────────────┐
│ firedm/frontend_common/view_models.py       │
│ - DownloadViewModel                         │
│ - SettingsViewModel                         │
│ - PlaylistViewModel                         │
│ - Observable state + methods (no Tk)        │
└────────────────┬────────────────────────────┘
                 │ reads/writes
                 ↓
┌─────────────────────────────────────────────┐
│ firedm/ (Core Domain)                       │
│ - controller.py (download orchestration)    │
│ - video.py (metadata + codec logic)         │
│ - ffmpeg_service.py (post-processing)       │
│ - extractor_adapter.py (yt-dlp bridge)      │
│ - plugins/registry.py (hook dispatch)       │
└─────────────────────────────────────────────┘
```

## Modern Tkinter Patterns

### 1. Themed Widgets (ttk)
Use `tkinter.ttk` for modern, platform-native appearance:

```python
import tkinter as tk
import tkinter.ttk as ttk

root = tk.Tk()
style = ttk.Style()
style.theme_use("clam")  # or "alt", "default"

# Modern buttons
btn = ttk.Button(root, text="Download", command=on_click)
btn.pack()

# Old (avoid)
btn = tk.Button(root, text="Download", bg="gray", fg="black")
```

### 2. Layout with Grid + Sticky
Use grid for complex layouts; avoid pack mixing:

```python
# Good: predictable column/row alignment
label = ttk.Label(root, text="URL:")
label.grid(row=0, column=0, sticky="W", padx=5, pady=5)

entry = ttk.Entry(root, width=40)
entry.grid(row=0, column=1, sticky="EW", padx=5, pady=5)

# Configure column weight for responsive resizing
root.columnconfigure(1, weight=1)
```

### 3. Event Loop Responsiveness

#### Problem: Blocking Download on Main Thread
```python
# Bad: GUI freezes during download
def on_download_click():
    download_file(url)  # 30 seconds, blocks all UI events
    update_status("Done")
```

#### Solution: Non-Blocking with Threading
```python
import threading

def on_download_click():
    # Offload to background thread
    thread = threading.Thread(target=_download_background, daemon=True)
    thread.start()

def _download_background():
    download_file(url)
    # Queue UI update back to main thread
    root.after(0, lambda: update_status("Done"))
```

#### Better: Use Callback Pattern
```python
# GUI registers callback; business logic calls it
class DownloadController:
    def __init__(self, on_progress, on_done):
        self.on_progress = on_progress
        self.on_done = on_done
    
    def start(self, url):
        # Background work...
        self.on_progress(50)  # 50% done
        # ... more work...
        self.on_done()  # GUI updates safely

# In GUI layer
controller = DownloadController(
    on_progress=lambda p: progress_var.set(p),
    on_done=lambda: update_status("Done")
)
controller.start(url)
```

### 4. State Management via ViewModel

```python
# firedm/frontend_common/view_models.py
from dataclasses import dataclass

@dataclass
class DownloadViewModel:
    url: str = ""
    status: str = "idle"  # idle, downloading, paused, error, done
    progress: int = 0
    speed: str = "0 B/s"
    eta: str = "unknown"
    
    def set_downloading(self, speed: str):
        self.status = "downloading"
        self.speed = speed
        # Observable change triggers UI callback
    
    def set_progress(self, percent: int):
        self.progress = min(100, max(0, percent))

# In tkview.py
view_model = DownloadViewModel()

def on_download_start():
    view_model.set_downloading("1.5 MB/s")
    progress_var.set(view_model.progress)  # TkVar syncs to Entry/Label
```

## Event Loop + Responsiveness

### Tk Main Loop Fundamentals
```python
root = tk.Tk()
root.title("FireDM")
root.geometry("800x600")

# Bind events
root.bind("<Escape>", on_escape)
root.bind("<Control-q>", on_quit)

# Start main loop (blocks until window closed)
root.mainloop()  # Event pump: processes events, calls callbacks
```

### Scheduling Tasks on Main Thread
```python
# Update GUI from background thread (safe)
def _background_work():
    result = expensive_computation()
    root.after(0, lambda: display_result(result))

threading.Thread(target=_background_work, daemon=True).start()

# Periodic polling (e.g., check download progress every 100ms)
def check_progress():
    if download_in_progress:
        progress_var.set(download.percent_done)
    root.after(100, check_progress)

check_progress()  # Start the loop
```

## System Tray Integration

### Windows Tray Icon
```python
import win32gui
import win32con

# Hide window to system tray
def hide_to_tray():
    root.withdraw()
    # Add minimize button that calls hide_to_tray()
    # Create tray icon with right-click menu: Show/Hide/Exit

# Restore from tray
def show_from_tray():
    root.deiconify()
    root.lift()
    root.focus()
```

### Cross-Platform Fallback
For Linux/macOS, use pystray (external dependency):
```python
try:
    import pystray
    # Implement tray icon
except ImportError:
    # Fallback: minimize to taskbar only
    pass
```

## Accessibility Features

### Keyboard Navigation
```python
# Tab order must be logical
root.bind("<Tab>", on_tab)

# Use Alt+Key for menu shortcuts
menu.add_command(label="Download (Ctrl+D)", command=on_download)
root.bind("<Control-d>", on_download)

# Focus visible indicators
ttk.Style().configure("TButton", relief="solid")
```

### Screen Reader Hints
```python
# Use descriptive labels, not just icons
label = ttk.Label(root, text="Speed Limit (KB/s):")

# Tooltips for icons (no alt text in Tk; use status bar instead)
status_var = tk.StringVar(value="Hover for details")
status_bar = ttk.Label(root, textvariable=status_var, relief="sunken")
```

## Styling System

### Theme Variables
```python
import tkinter.ttk as ttk

style = ttk.Style()

# Query current theme colors
bg_color = style.lookup("TFrame", "background")

# Set custom colors for a specific widget style
style.configure("Accent.TButton", foreground="green")
btn = ttk.Button(root, text="Go", style="Accent.TButton")
```

### Custom Fonts
```python
import tkinter.font as tkFont

title_font = tkFont.Font(family="Helvetica", size=14, weight="bold")
label = ttk.Label(root, text="FireDM", font=title_font)

# Use tk.Label if ttk doesn't support font customization needed
label = tk.Label(root, text="FireDM", font=("Courier", 10, "bold"))
```

## Debugging Tk Applications

### Print Widget Tree
```python
def debug_widget_tree(widget, indent=0):
    name = widget.winfo_class()
    geometry = widget.winfo_geometry()
    print(" " * indent + f"{name} {geometry}")
    for child in widget.winfo_children():
        debug_widget_tree(child, indent + 2)

debug_widget_tree(root)
```

### Monitor Variable Changes
```python
var = tk.StringVar(value="initial")
var.trace("w", lambda *args: print(f"Variable changed to: {var.get()}"))
var.set("new value")  # Prints: "Variable changed to: new value"
```

### Event Log
```python
def log_event(event):
    print(f"Event: {event.type} on {event.widget.winfo_class()}")

root.bind("<Button-1>", log_event)
root.bind("<Motion>", log_event)
```

## Common Pitfalls

### Memory Leaks
```python
# Bad: lambda captures loop variable, not value
for i in range(10):
    btn = ttk.Button(root, command=lambda: print(i))  # Always prints 9

# Good: default argument captures value
for i in range(10):
    btn = ttk.Button(root, command=lambda i=i: print(i))
```

### Thread Safety
```python
# Bad: directly modify Tk variable from background thread
def background_task():
    var.set("result")  # Can crash or freeze GUI

# Good: schedule update on main thread
def background_task():
    result = compute()
    root.after(0, lambda: var.set(result))
```

### Circular References
```python
# Bad: ViewModel holds reference to Tk widget; widget holds ViewModel
class GuiController:
    def __init__(self, root):
        self.root = root
        self.view_model = DownloadViewModel()
        self.root.bind("<Close>", lambda: cleanup(self.view_model))

# Good: Separate lifecycle; use weak references or explicit cleanup
root.protocol("WM_DELETE_WINDOW", on_closing)
```

## See Also

- `firedm/tkview.py` — Main GUI implementation
- `firedm/frontend_common/view_models.py` — ViewModel layer (toolkit-neutral)
- `docs/architecture.md` — System architecture overview
- `docs/legacy-refactor-plan.md` — Tkview refactoring roadmap
