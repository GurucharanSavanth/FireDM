# User Guide

Status: changed 2026-05-02.

## Current Use
- observed: FireDM remains a Tkinter desktop download manager started through `firedm.py`, `python -m firedm`, or packaged launchers.
- observed: Current download behavior still uses the existing internal path.

## Planned Modernization
- planned: New job panel will offer URL/input, engine selector, destination, file name rules, explicit headers/cookies, preflight, and start.
- planned: Queue rows will show engine, speed, ETA, failure reason, retry, open folder, and diagnostics copy.
- planned: Built-in help will explain engines, updates, compatibility, privacy, and stored data.

## Safety
- implemented: No silent browser cookie harvesting or protected-media bypass is part of this plan.
- blocked: The new engine UI is not implemented yet.
