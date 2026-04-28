# 03 Baseline Validation

Evidence labels: observed = local command output.

## Commands

### `.\.venv\Scripts\python.exe -m compileall .\firedm`
- observed cwd: `G:\Personal Builds\Revive-FireDM\FireDM - Branch`
- observed exit: `0`
- observed output summary: listed `.\firedm`, `.\firedm\plugins`; compiled `firedm\tkview.py`
- classification: baseline pass

### `.\.venv\Scripts\python.exe -c "import firedm; import firedm.FireDM; print('import firedm ok')"`
- observed exit: `0`
- observed output: `import firedm ok`
- classification: baseline pass

### `.\.venv\Scripts\python.exe -m firedm --help`
- observed exit: `0`
- observed output summary: printed CLI help; first line `>> setting.cfg not found`
- classification: baseline pass with expected missing local settings notice

### `.\.venv\Scripts\python.exe firedm.py --imports-only`
- observed exit: `0`
- observed output summary: imported `plyer 2.1.0`, `certifi 2026.04.22`, `yt_dlp 2026.03.17`, `yt_dlp_ejs 0.8.0`, `pycurl 7.45.7`, `PIL 12.2.0`, `pystray`, `awesometkinter 2021.11.8`, `tkinter`, optional `youtube_dl 2021.12.17`
- classification: baseline pass

### `.\.venv\Scripts\python.exe -m pytest --collect-only -q`
- observed exit: `0`
- observed output summary: `151 tests collected in 0.58s`
- classification: baseline pass

### `.\.venv\Scripts\python.exe -m pytest -q`
- observed exit: `1`
- observed output summary: `1 failed, 150 passed in 5.42s`
- observed failing test: `tests/test_drm_clearkey.py::test_dash_segment_decrypt`
- observed failure: `ModuleNotFoundError: No module named 'cryptography'`
- classification: pre-existing local patch failure and prohibited DRM surface; not introduced by this repair pass

## Baseline Limits
- observed not run before patch: Ruff, mypy, wheel/sdist build, PyInstaller package build, GUI smoke, real browser native messaging, real downloads, real extractor-network path, real ffmpeg post-processing.
