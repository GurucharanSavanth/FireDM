# Windows Legacy Support

Evidence labels: observed, inferred, blocked.

| Windows Version | Status | Notes |
| --- | --- | --- |
| Windows XP | blocked | Modern Python 3.10, current PyInstaller, TLS/network stack, and downloader dependencies are not validated. A separate frozen legacy branch/toolchain would be required and would carry security risk. |
| Windows Vista | blocked | Not validated; modern dependency support is not assumed. |
| Windows 7 | blocked | Not validated; Python/runtime/package compatibility must be proven separately. |
| Windows 8.1 | blocked | Not validated in this checkout. |
| Windows 10 | supported target for x64 lane | observed host reports Windows `10.0.26200`; installer validation is run on this host only. |
| Windows 11 | supported target by policy | inferred from current Windows 10/11 x64 project baseline; must be validated on a Windows 11 host before a release-specific claim. |
| Future Windows | forward-compatible only | no fake future-version verification. Use documented APIs, per-user install roots, HKCU uninstall metadata, and no global PATH mutation by default. |

XP is not a blocker for the modern installer. If maintainers want XP, create a separate feasibility branch with older Python/tooling, no modern security guarantee, and no shared artifact naming with the modern installer.

