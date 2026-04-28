# 14 Review Packet

Evidence labels: changed = modified by this pass; verified = command run; unverified = not executed.

## Files Changed
- changed: `firedm/native_messaging.py`, `firedm/native_host.py`, `firedm/FireDM.py`, `firedm/controller.py`
- changed: `firedm/plugins/browser_integration.py`, `firedm/plugins/drm_decryption.py`, `firedm/plugins/protocol_expansion.py`
- changed: `pyproject.toml`, `scripts/firedm-win.spec`
- changed: `tests/test_browser_integration.py`, `tests/test_drm_clearkey.py`, `tests/test_plugins.py`
- changed: `artifacts/full_codebase_repair/*.md`

## Highest-Risk Changes
- native control endpoint transport and lifecycle in `controller.py` / `native_messaging.py`
- browser manifest launcher behavior in `browser_integration.py`
- DRM plugin behavior intentionally changed to fail closed
- magnet lifecycle now async/plugin-owned

## Behavior Preserved
- plugins remain default disabled.
- source CLI/help/import smoke still works.
- pycurl/yt-dlp/ffmpeg core paths unchanged.
- Windows PyInstaller one-folder packaging remains primary path.

## Behavior Changed
- browser-native controller endpoint no longer starts unless `browser_integration` is enabled.
- local native-control messages require authenticated Listener/Client transport.
- native messages cannot enqueue non-http(s) URLs or sensitive headers.
- DRM decrypt plugin cannot be enabled.
- magnet links stay out of normal worker queue after aria2 accepts them.

## Tests/Validation
- verified `155 passed` full pytest.
- verified scoped Ruff, mypy, build, Twine check.
- verified isolated PyInstaller build and packaged help/import smoke.

## Unverified Claims
- unverified real browser extension capture.
- unverified real magnet transfer.
- unverified GUI visual workflow.
- unverified Linux runtime.

## Suggested Reviewer Focus
- ensure `multiprocessing.connection` auth/pipe behavior meets FireDM threat model.
- decide whether generated `.cmd` launcher is acceptable for browser native messaging or whether a dedicated packaged exe is required.
- review optional plugin policy before exposing plugin manager broadly.
- review whether same-user endpoint secret should use stronger Windows ACLs.

## Rollback Considerations
- native messaging rollback touches `native_messaging.py`, `native_host.py`, `controller.py`, `browser_integration.py`, and `FireDM.py`.
- DRM rollback should not restore decrypt behavior without explicit maintainer/legal/security approval.
- magnet rollback should preserve `_plugin_queued` behavior if aria2 support remains.
