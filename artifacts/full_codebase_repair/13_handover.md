# 13 Handover

Evidence labels: changed = modified by this pass; verified = command run; unverified = not executed.

## What Changed
- native browser integration is no longer exposed by default and uses an authenticated local Listener/Client transport.
- manifest generation points to a launcher/executable path, not raw `sys.executable`.
- native host stdout is reserved for browser protocol bytes.
- DRM decrypt plugin fails closed.
- magnet links are owned by the plugin queue path instead of normal pycurl worker path.

## Review First
- `firedm/controller.py`: endpoint lifecycle, native message validation, plugin hook interaction.
- `firedm/native_messaging.py`: settings-folder/secret/Listener semantics.
- `firedm/plugins/browser_integration.py`: launcher generation and registry writes.
- `firedm/plugins/protocol_expansion.py`: magnet ownership and controller notification.

## Verified
- full pytest: `155 passed`.
- scoped Ruff: passed.
- mypy: passed on configured files.
- wheel/sdist + Twine: passed.
- isolated PyInstaller + packaged CLI/import smoke: passed.

## Unverified
- real Chrome/Firefox/Edge native messaging launch.
- real aria2 magnet download.
- real GUI interaction.
- real network download/extractor/ffmpeg merge.
- Linux runtime.

## Next Patch Group
- add integration harness for native host <-> controller roundtrip without browser.
- review optional plugins (`anti_detection`, `native_extractors`, `post_processing`) for release policy, subprocess argv handling, and dependency declaration.
- focused HLS key/class review for `video.py::Key`.
