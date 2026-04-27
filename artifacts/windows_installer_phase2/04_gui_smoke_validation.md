# 04 GUI Smoke Validation

Evidence labels: changed, verified, blocked.

## Script
- changed: added `scripts/release/smoke_installed_gui.py`.
- changed: script accepts `--install-root`, `--timeout`, `--headless-safe`, `--no-network`, and `--expect-launcher`.

## Checks
- changed: confirms GUI launcher exists.
- changed: confirms `_internal` runtime exists.
- changed: classifies missing Tcl/Tk runtime when the bundled runtime lacks Tk data.
- changed: starts the GUI process, waits for immediate crash or timeout, captures stdout/stderr snippets, and terminates cleanly after timeout.

## Result
- verified: `.venv\Scripts\python.exe scripts\release\smoke_installed_gui.py --install-root .\dist\payloads\win-x64\FireDM --timeout 20 --headless-safe --no-network` exited `0`.
- verified: classification was `started_timeout_terminated`, meaning the packaged GUI launcher started and did not immediately crash before the timeout.

## Limitations
- blocked: this is not full GUI QA. It does not verify button flows, real downloads, tray behavior, or visual correctness.
