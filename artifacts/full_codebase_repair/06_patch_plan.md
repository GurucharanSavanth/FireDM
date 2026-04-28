# 06 Patch Plan

Evidence labels: observed = local files/tests; changed = implemented.

## Group A/G - Native Messaging Startup And Security
- reason: reviewer P1 items; endpoint broken and exposed by default.
- changed files: `firedm/native_messaging.py`, `firedm/native_host.py`, `firedm/controller.py`, `firedm/plugins/browser_integration.py`, `firedm/FireDM.py`, `pyproject.toml`, tests.
- boundaries: did not implement browser extension; did not claim real-browser validation.

## Group F/G - DRM Boundary
- reason: full pytest failure plus hard no-DRM-bypass boundary.
- changed files: `firedm/plugins/drm_decryption.py`, `tests/test_drm_clearkey.py`, `scripts/firedm-win.spec`.
- boundaries: removed active decrypt behavior; did not add `cryptography`.

## Group E - Magnet Queue Ownership
- reason: reviewer P2 item; aria2-owned magnet jobs were falling into normal worker/pycurl path.
- changed files: `firedm/plugins/protocol_expansion.py`, `tests/test_plugins.py`.
- boundaries: real aria2 transfer not executed.

## Group H/I - Packaging And Handover
- reason: package inclusion changed via plugin package and native host path.
- changed files: `pyproject.toml`, `scripts/firedm-win.spec`, `artifacts/full_codebase_repair/*`.
- validation: wheel/sdist build, Twine check, isolated PyInstaller build, packaged CLI/import smoke.
