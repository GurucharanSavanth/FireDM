# 05 Warning Audit

Evidence labels: observed = command output; changed = modified by this pass.

## Captured Warnings
- observed `git diff --stat` and `git diff --check`: CRLF-to-LF warnings for existing artifact JSON/log files under `artifacts/smoke` and `artifacts/extractor`.
- observed PyInstaller warning: failed submodule collection for `urllib3.contrib.emscripten` due missing `js`; external packaging noise from dependency hook.
- observed PyInstaller warning: `collect_data_files` skipped `curl_cffi` because it is not a package; external optional dependency hook noise.

## Fixed Warnings/Failures
- changed `tests/test_browser_integration.py` to satisfy scoped Ruff: sorted imports, context-managed file read, no unnecessary `open(..., "r")`.
- changed DRM test path so full pytest no longer fails on undeclared `cryptography`.

## Remaining Warnings
- deferred CRLF warnings: pre-existing artifact line-ending state; not functionally tied to repaired code.
- deferred PyInstaller dependency-hook warnings: packaging completed and packaged CLI/import smoke passed; no project source warning to fix.

## Validation
- verified `ruff check ... tests`: `All checks passed!`
- verified `pytest -q`: `155 passed`
