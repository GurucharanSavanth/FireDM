# 11 Legacy Windows Feasibility

Evidence labels: observed, blocked, inferred.

## Mainline
- verified by local host only: Windows 10/11 x64 class host with Python 3.10.11 and PyInstaller x64 payload.
- inferred: the current x64 installer is appropriate for modern x64 Windows systems where the PyInstaller-built payload can run.

## Legacy
- blocked: Windows XP is not a mainline target. Modern Python, TLS, yt-dlp, pycurl/libcurl, and PyInstaller support do not justify an XP release claim.
- blocked: Vista, Windows 7, and Windows 8.1 are not validated by this pass.
- required future action: create a separate legacy branch/toolchain feasibility study before any legacy artifact claim.

## ARM64
- blocked: no native ARM64 Python/toolchain payload was built.
- inferred: x64-on-ARM emulation may run on some Windows ARM64 systems, but this is not native ARM64 support and was not validated.

## Future Windows
- inferred: installer avoids hardcoded future-version gates and global system mutation.
- blocked: no future Windows version is verified or claimed.

