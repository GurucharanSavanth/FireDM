# 02 Architecture Matrix

Evidence labels: observed, inferred, blocked.

| Lane | Status | Evidence | Required Next Step |
| --- | --- | --- | --- |
| win-x64 | verified | verified: `build_windows.py --arch x64 --channel dev`, `build-release.bat dev`, payload validation, installer validation, CLI smoke, and GUI smoke all ran locally | Run manual QA and signing before stable release. |
| win-x86 | blocked | verified: `build_windows.py --arch x86 --channel dev` exits with `unsupported arch 'x86'; supported: x64`; current Python is 64-bit AMD64 | Add a 32-bit Python 3.10 lane, install 32-bit wheels, build payload, validate on 32-bit or WOW64. |
| win-arm64 | blocked | verified: `build_windows.py --arch arm64 --channel dev` exits with `unsupported arch 'arm64'; supported: x64`; host is AMD64 | Add ARM64 runner/toolchain, verify pycurl/Pillow/PyInstaller bootloader support, validate natively. |
| win-universal bootstrapper | blocked | inferred: a universal bootstrapper must contain or fetch per-arch payloads; only x64 exists | Produce x86 and ARM64 payloads first, then implement arch-selecting bundle. |
| MSI x64 | blocked | observed: WiX tooling is not on PATH | Install/use WiX in CI or repo-local tool cache, author component-safe MSI. |
| MSI x86 | blocked | blocked by missing x86 payload and WiX tooling | Build x86 payload and MSI lane. |
| MSI ARM64 | blocked | blocked by missing ARM64 payload and WiX tooling | Build ARM64 payload and MSI lane. |
| MSIX | blocked | observed: no manifest/signing workflow exists | Add signing and MSIX packaging validation if maintainers choose Store/sideload model. |

## CPU Vendor Policy
- inferred: x64 payload targets generic AMD64/x64 and is not Intel- or AMD-specific.
- inferred: no AVX2/AVX512-only binaries are introduced.
- inferred: CPU-specific optimization is deferred until benchmark evidence exists.

## Windows Policy
- observed: current validation host reports Windows `10.0.26200`.
- inferred: modern mainline installer targets Windows 10/11 x64 first.
- blocked: Windows XP/Vista/7/8.1 are not validated with modern Python 3.10/PyInstaller/dependency stack.
- inferred: future Windows compatibility should be forward-compatible API usage, not fake verification claims.
