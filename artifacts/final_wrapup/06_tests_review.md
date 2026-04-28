# Phase 6 Tests Review

## Tests Reviewed

- `tests/`
- `tests/release/`
- `tests/test_ffmpeg_service.py`

## Test Safety

- observed: release tests use temporary directories and fixtures.
- observed: tests do not run the real installer against the user machine.
- observed: installer validation command uses a validation temp root and validation app id.
- observed: FFmpeg discovery tests cover app-local tool lookup behavior.

## Commands

- verified: `.venv\Scripts\python.exe -m compileall .\firedm .\scripts\release` exited 0.
- verified: `.venv\Scripts\python.exe -m pytest -q` exited 0 with `169 passed in 6.75s`.
- verified: scoped modern seam Ruff exited 0 with `All checks passed!`.
- verified: release-script Ruff exited 0 with `All checks passed!`.

## Remaining Test Gaps

- blocked: live HTTP download QA not run.
- blocked: live video download QA not run.
- blocked: FFmpeg post-processing QA not run.
- blocked: real old-installer upgrade not run with a historical installer artifact.

