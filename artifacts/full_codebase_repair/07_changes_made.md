# 07 Changes Made

Evidence labels: changed = modified by this pass; verified = command/test run.

- changed `firedm/native_messaging.py`: new stdlib transport helper for shared secret, settings-folder resolution, `multiprocessing.connection` Listener/Client, message size limit, JSON decoding.
- changed `firedm/native_host.py`: native host now writes only binary native messages to stdout, diagnostics to stderr, forwards through authenticated local transport, rejects oversized/invalid messages.
- changed `firedm/FireDM.py`: added hidden `--native-host` execution path for packaged/source launcher use.
- changed `firedm/plugins/browser_integration.py`: manifest path now points to installed native-host executable or generated launcher; plugin starts/stops endpoint only when controller exists.
- changed `firedm/controller.py`: native endpoint now gated behind enabled browser plugin, uses authenticated Listener, validates JSON action/URL scheme, strips sensitive headers, stops endpoint during quit.
- changed `firedm/plugins/drm_decryption.py`: replaced active DRM decryptor with fail-closed unsupported placeholder.
- changed `firedm/plugins/protocol_expansion.py`: magnet jobs set `_plugin_queued`, pending status, display name, protocol handler, and controller notification on completion/error.
- changed `pyproject.toml`: added `firedm-native-host` console entry point; plugin packages already included by prior local diff.
- changed `scripts/firedm-win.spec`: includes plugin/native messaging modules; removes undeclared `cryptography`/`paramiko` hiddenimports.
- changed tests: browser/native, DRM fail-closed, magnet queue regression.
