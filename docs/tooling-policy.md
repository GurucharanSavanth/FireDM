# Tooling Policy

## Test Runner

`pytest` is the maintained test runner:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Critical video/download regressions can be run faster:

```powershell
.\.venv\Scripts\python.exe scripts\run_regression_suite.py
```

## Linting and Formatting

Ruff is adopted for modernized seams only. Full-repo lint is deferred because legacy GUI/controller/util modules still contain broad historical style debt.

```powershell
.\.venv\Scripts\python.exe -m ruff check firedm\FireDM.py firedm\app_paths.py firedm\extractor_adapter.py firedm\ffmpeg_service.py firedm\tool_discovery.py firedm\setting.py firedm\update.py tests
```

## Type Checking

Mypy is scoped to typed service modules in `pyproject.toml`. Do not enable strict full-repo typing until `controller.py`, `video.py`, and `tkview.py` are split.

## Environment Management

Supported path remains Python 3.10.11 + venv + pip. `uv` was reviewed as a future option but is not adopted because it would add a second dependency workflow before Python 3.11 validation is complete.
