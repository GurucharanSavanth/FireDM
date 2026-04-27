# 14 Validation Log

Evidence labels: verified, blocked.

## Repository/Source Validation
- verified: `.venv\Scripts\python.exe -m compileall .\firedm` exit 0.
- verified: `.venv\Scripts\python.exe -m pytest -q` exit 0, `155 passed in 7.27s`.
- verified: `.venv\Scripts\python.exe -m compileall .\scripts\release` exit 0.
- verified: `git diff --check -- .\scripts\release .\docs\release .\artifacts\windows_installer .\.github\workflows\draft-release.yml .\.gitignore` exit 0.

## Release Build Validation
- verified: `.venv\Scripts\python.exe scripts\release\build_windows.py --arch x64 --channel dev` exit 0.
- verified: `cmd /c "set FIREDM_NO_PAUSE=1&& build-release.bat dev"` exit 0.
- verified: `.venv\Scripts\python.exe scripts\release\validate_payload.py --arch x64` exit 0.
- verified: `.venv\Scripts\python.exe scripts\release\validate_installer.py --artifact .\dist\installers\FireDM_Setup_2022.2.5_dev_win_x64.exe` exit 0.
- verified: `.venv\Scripts\python.exe scripts\release\smoke_installed_app.py --install-root .\dist\payloads\win-x64\FireDM` exit 0.

## Installer Validation Coverage
- verified: installer `--help` works.
- verified: silent temp install works.
- verified: installed `firedm.exe --help` works.
- verified: installed `firedm.exe --imports-only` works.
- verified: repair restores a removed `FireDM-GUI.exe`.
- verified: uninstall removes installed program files and validation registry metadata.

## Blocked/Not Verified
- blocked: x86 build command exits cleanly with `unsupported arch 'x86'; supported: x64`.
- blocked: ARM64 build command exits cleanly with `unsupported arch 'arm64'; supported: x64`.
- blocked: GitHub Actions workflow was edited but not run on GitHub in this session.
- blocked: code signing, MSI, MSIX, GUI interaction, live downloads, and ffmpeg post-processing were not validated.
