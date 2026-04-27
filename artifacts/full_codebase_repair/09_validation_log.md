# 09 Validation Log

Evidence labels: observed = command output; verified = successful command.

| Command | Exit | Output Summary | Classification |
| --- | --- | --- | --- |
| `.\.venv\Scripts\python.exe -m compileall .\firedm` | 0 | listed `firedm` and `firedm\plugins` | verified |
| `.\.venv\Scripts\python.exe -m pytest tests\test_browser_integration.py tests\test_drm_clearkey.py tests\test_plugins.py -q` | 0 | `31 passed in 0.61s` | verified |
| `.\.venv\Scripts\python.exe -m pytest tests\test_browser_integration.py tests\test_drm_clearkey.py tests\test_plugins.py tests\test_download_handoff.py tests\test_cli.py tests\test_security.py -q` | 0 | `49 passed in 1.71s` | verified |
| `.\.venv\Scripts\python.exe -m pytest -q` | 0 | `155 passed in 5.62s` | verified |
| `.\.venv\Scripts\python.exe -m firedm --help` | 0 | CLI help printed | verified |
| `.\.venv\Scripts\python.exe firedm.py --imports-only` | 0 | imports succeeded; yt-dlp 2026.03.17, pycurl 7.45.7, tkinter, optional youtube_dl | verified |
| `.\.venv\Scripts\python.exe firedm.py --native-host` | 0 | no stdin, clean exit with no stdout corruption | verified |
| `.\.venv\Scripts\python.exe -m ruff check firedm\FireDM.py firedm\app_paths.py firedm\extractor_adapter.py firedm\ffmpeg_service.py firedm\tool_discovery.py firedm\setting.py firedm\update.py tests` | 0 | `All checks passed!` | verified |
| `.\.venv\Scripts\python.exe -m mypy` | 0 | `Success: no issues found in 8 source files` | verified |
| `.\.venv\Scripts\python.exe -m build --no-isolation` | 0 | built `firedm-2022.2.5.tar.gz` and wheel | verified |
| `.\.venv\Scripts\python.exe -m twine check dist\*.whl dist\*.tar.gz` | 0 | wheel and sdist `PASSED` | verified |
| `.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --distpath artifacts\full_codebase_repair\pyinstaller-dist --workpath artifacts\full_codebase_repair\pyinstaller-build .\scripts\firedm-win.spec` | 0 | built isolated `artifacts\full_codebase_repair\pyinstaller-dist\FireDM` | verified |
| `artifacts\full_codebase_repair\pyinstaller-dist\FireDM\firedm.exe --help` | 0 | packaged CLI help printed | verified |
| `artifacts\full_codebase_repair\pyinstaller-dist\FireDM\firedm.exe --imports-only` | 0 | packaged imports succeeded | verified |
| `Test-Path ...\_internal\tkinter\__init__.py`, `_tcl_data\init.tcl`, `_tk_data\tk.tcl` | 0 | all `True` | verified |
| `git diff --check` | 0 | no whitespace errors; CRLF warnings on existing artifacts | verified with warnings |

## Not Run
- blocked: `scripts/windows-build.ps1` not run because it performs recursive deletion of `build`/`dist\FireDM` and can stop packaged processes. Isolated PyInstaller validation was run instead.
- not verified: real GUI interaction, real browser extension/native messaging from Chrome/Firefox/Edge, real downloads, real aria2 magnet transfer, live extractor-network behavior, real ffmpeg post-processing.
