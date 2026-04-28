# 03 Import Warning Sweep

observed import/dependency issue:
- command: `.venv\Scripts\python.exe -c "import ... pystray; print(pystray.__version__)"`
- result: `AttributeError: module 'pystray' has no attribute '__version__'`
- fix: `scripts/release/check_dependencies.py` uses `importlib.metadata.version()` instead of module `__version__`.
- validation: dependency preflight JSON reports `pystray 0.19.5`.

verified:
- `.venv\Scripts\python.exe -m compileall .\scripts\release` passed after new scripts.
- `.venv\Scripts\python.exe scripts\release\check_dependencies.py --arch x64 --channel dev --skip-portable --json` passed with no required missing dependencies.
- optional warnings: `ffmpeg`, `ffprobe`.
- source smoke scripts now support `--output-dir`; tests write extractor/video proof artifacts to temp directories instead of tracked `artifacts/**`.

final sweep:
- full `.venv\Scripts\python.exe -m pytest -q` passed with `201 passed`.
- scoped Ruff passed after removing one unused import from `scripts/smoke_video_pipeline.py`.
