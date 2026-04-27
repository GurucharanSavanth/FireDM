# 07 Architecture Lane Status

Evidence labels: observed, verified, blocked.

| Lane | Status | Evidence |
| --- | --- | --- |
| x64 | verified | `build_windows.py --arch x64 --channel dev` and `build-release.bat dev` both completed successfully. |
| x86 | blocked | `.venv\Scripts\python.exe scripts\release\build_windows.py --arch x86 --channel dev` exits with `unsupported arch 'x86'; supported: x64`. Current Python is 64-bit AMD64. |
| ARM64 | blocked | `.venv\Scripts\python.exe scripts\release\build_windows.py --arch arm64 --channel dev` exits with `unsupported arch 'arm64'; supported: x64`. Current host is AMD64, not native ARM64. |
| Intel/AMD x64 | inferred | x64 build uses generic PyInstaller Windows 64-bit Intel bootloader and no vendor-specific CPU tuning. |

## Required Next Steps
- blocked: x86 requires a 32-bit Python/toolchain and 32-bit dependency wheel validation.
- blocked: ARM64 requires native ARM64 Python/toolchain, dependency support verification, and ARM64 runtime validation.
