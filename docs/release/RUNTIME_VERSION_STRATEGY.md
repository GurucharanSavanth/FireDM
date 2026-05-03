# Runtime Version Strategy

Status: changed 2026-05-03.

## Current Local Lane
- observed: `pyproject.toml` requires Python `>=3.10,<3.11`.
- observed: local runtime is Python 3.10.11 on Windows `win32` AMD64.
- observed: release workflows and dependency preflight are aligned to Python 3.10.
- changed: No runtime range was widened in this slice.

## Official Python Findings
| Target | Official basis | Project decision |
| --- | --- | --- |
| Latest stable | https://www.python.org/downloads/latest/python3/ reports Python 3.14.4, released 2026-04-07 | planning input only; not adopted locally |
| Windows 10/11 | https://docs.python.org/3/using/windows.html says Python 3.14 supports Windows 10 and newer | future modern lane candidate after dependency/build proof |
| Windows 8.1 | same docs say use Python 3.12 for Windows 8.1 | separate compatibility lane |
| Windows 7 | same docs say use Python 3.8 for Windows 7 | legacy-only lane, incompatible with current metadata |
| XP/Vista | no modern CPython lane | blocked unless separate legacy proof exists |

## Strategy
1. Keep Python 3.10.11 as the only validated source/build lane for now.
2. Create a Python 3.12/3.14 matrix only after dependency import smoke and full tests pass.
3. Do not weaken the modern lane for XP/Vista/7.
4. Record every packaging smoke per OS/runtime before compatibility claims.

## Validation Gates For Widening
- targeted pytest for engines, controller bridge, extractor, ffmpeg, release scripts
- full pytest
- import smoke: source and packaged
- PyInstaller one-folder build and smoke on target OS
- GUI smoke on target OS
- dependency preflight for every declared platform
