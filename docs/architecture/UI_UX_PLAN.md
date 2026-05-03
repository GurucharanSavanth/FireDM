# UI/UX Plan

Status: changed 2026-05-02.

## Current UI
- observed: Tkinter remains the active GUI through `firedm/tkview.py`.
- observed: `Controller` and GUI are tightly coupled through mutable download items and callbacks.
- blocked: No full GUI smoke was run in this phase.

## Planned Incremental UI
- planned: Add an engine selector to job creation with `Auto`, `Internal`, `aria2c`, `yt-dlp`, and future plugin engines.
- planned: Show unavailable engines with health reason where useful.
- planned: Add a preflight action before start.
- planned: Add health panel rows for internal engine, aria2c, yt-dlp, ffmpeg, ffprobe, Python/runtime, portable mode, and updates.
- planned: Add per-job engine labels, progress, speed, ETA, failure reason, retry, open folder, and diagnostics copy.
- planned: Add built-in help pages for engine selection, troubleshooting, updates, compatibility, and stored data.

## Accessibility Rules
- planned: Keep labels readable, keyboard paths intact, critical actions text-visible, and errors specific.
- blocked: GUI framework migration is not approved without proof, migration cost, tests, and packaging impact.
