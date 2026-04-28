# 08 Tests Added Or Updated

Evidence labels: changed = modified by this pass; verified = test result.

## `tests/test_browser_integration.py`
- changed: asserts manifest path is not raw `sys.executable`.
- changed: asserts generated Windows launcher references `native_host.py` or `--native-host`.
- changed: asserts controller does not start native endpoint when plugin is disabled.
- changed: asserts native message handler rejects non-http URLs and strips `Authorization`/`Cookie`.
- verified in targeted run and full suite.

## `tests/test_drm_clearkey.py`
- changed: replaces crypto/decryption tests with fail-closed DRM placeholder tests.
- verified no `cryptography` import is needed.

## `tests/test_plugins.py`
- changed: adds magnet regression asserting `_plugin_queued`, pending status, protocol ownership, and magnet display name.
- verified in targeted run and full suite.

## Mock Vs Real
- mocked: browser registry write, controller threads, aria2 JSON-RPC, magnet monitor thread.
- real: pytest full suite, source import/help/native-host smoke, wheel/sdist build, Twine check, isolated PyInstaller build, packaged help/import smoke.
