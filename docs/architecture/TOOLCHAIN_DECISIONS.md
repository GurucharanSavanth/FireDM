# Toolchain Decisions

Status: changed 2026-05-03.

## Official Sources Checked
| Area | Source | Finding | Project impact | Status |
| --- | --- | --- | --- | --- |
| Python Windows support | https://docs.python.org/3/using/windows.html#supported-windows-versions | Python 3.14 supports Windows 10+; Windows 7 needs Python 3.8; Windows 8.1 needs Python 3.12. | Modern lane cannot claim XP/Vista/7 and must not jump past Python 3.10 without retesting dependency support. | verified |
| Python latest stable | https://www.python.org/downloads/latest/python3/ | Python 3.14.4 was released 2026-04-07. | Treat as planning input only; local metadata remains Python 3.10 until tests/builds prove a wider lane. | verified |
| Tkinter | https://docs.python.org/3/library/tkinter.html | `tkinter` is the standard Python interface to Tcl/Tk; official Python binaries bundle threaded Tcl/Tk 8.6. | Keep Tkinter fallback during migration; current problems are local coupling and UI age. | verified |
| Tkinter threading | https://docs.python.org/3/library/tkinter.html#threading-model | Tk event handlers must not run long work; cross-thread calls rely on the Tcl event queue. | Preserve controller/worker background boundaries and UI-thread handoff. | verified |
| PySide6 / Qt for Python | https://doc.qt.io/qtforpython-6/index.html | PySide6 is the official Qt for Python binding and is offered under LGPLv3/GPLv3/commercial licensing. | Primary GUI candidate, but dependency addition is deferred until package/license/build impact is approved. | verified |
| Qt supported platforms | https://doc.qt.io/qtforpython-6/overviews/qtdoc-supported-platforms.html | Qt 6.11 lists supported desktop platform configurations including Windows and Linux distributions. | Modern GUI lane targets Windows 10/11 and Linux x86_64 first; legacy OS claims require proof. | verified |
| PySide package contents | https://doc.qt.io/qtforpython-6/package_details.html | PySide packages include Qt binaries in site-packages. | Packaging size, DLL/data collection, and license inventory must be solved before a Qt build lane ships. | verified |
| PyQt6 | https://riverbankcomputing.com/software/pyqt | PyQt is GPLv3/commercial dual licensed. | Less suitable for this LGPL project unless legal policy accepts GPL/commercial terms. | verified |
| wxPython | https://wxpython.org/pages/overview/ | wxPython is cross-platform and uses native widgets through wxWidgets. | Viable fallback, not selected as primary because Qt model/view/deployment tooling better fits planned architecture. | verified |
| Dear PyGui | https://dearpygui.readthedocs.io/ | GPU-accelerated cross-platform GUI toolkit for Python. | Deferred; less native desktop/download-manager oriented than Qt. | verified |
| Toga | https://beeware.org/docs/toga/ | Python-native, OS-native GUI toolkit. | Deferred; promising but not chosen for this staged desktop migration. | verified |
| Python 3.10 Windows support | https://docs.python.org/3.10/using/windows.html | Python 3.10 supports Windows 8.1+. | Current `pyproject.toml` `>=3.10,<3.11` aligns with a modern Windows 8.1+ candidate, not XP/Vista/7. | verified |
| CPython lifecycle policy | https://peps.python.org/pep-0011/ | CPython Windows support follows Microsoft lifecycle at feature-release start. | Legacy lane must be separate and evidence-gated. | verified |
| PyInstaller | https://pyinstaller.org/en/stable/ | PyInstaller supports Python 3.8+ and is tested on Windows/macOS/Linux; it is not a cross-compiler. | Build Windows on Windows, Linux on Linux. Use one-folder first, one-file only after smoke. | verified |
| PyInstaller data/one-file behavior | https://pyinstaller.org/en/stable/operating-mode.html and https://pyinstaller.org/en/stable/spec-files.html | Output is OS/Python/word-size specific; data files need explicit spec handling. | Release script must control spec, data files, and runtime paths. | verified |
| Nuitka | https://nuitka.net/user-documentation/user-manual.html | Nuitka needs a C compiler; Windows supported compilers include Visual Studio 2022+, Nuitka-managed MinGW64, Zig, and clang-cl. | Treat Nuitka as optional backend until compiler and data-file behavior are validated locally. | verified |
| Nuitka standalone/onefile | https://nuitka.net/user-documentation/use-cases.html | Standalone produces a folder; onefile extracts on target and should follow standalone validation. | Use Nuitka standalone before any onefile lane. | verified |
| aria2 | https://aria2.github.io/ and https://aria2.github.io/manual/en/html/aria2c.html | Supports HTTP/HTTPS, FTP, SFTP, BitTorrent, Metalink, JSON-RPC, and XML-RPC. RPC secret is strongly recommended; loopback is default when `--rpc-listen-all=false`. | Future adapter must use argv subprocess, localhost RPC, random per-session secret, no logged secret. | verified |
| yt-dlp | https://github.com/yt-dlp/yt-dlp/blob/master/README.md | Supports CPython 3.10+; ffmpeg/ffprobe are strongly recommended; release binaries have different licensing. | Keep `yt-dlp[default]` source dependency; do not silently use browser cookies; normalize formats first. | verified |
| FFmpeg | https://www.ffmpeg.org/legal.html | FFmpeg license depends on enabled build options; LGPL/GPL implications apply. | Bundling requires recorded license inventory and artifact-specific decision. | verified |
| GitHub Releases API | https://docs.github.com/rest/releases/releases and https://docs.github.com/rest/releases/assets | Latest release endpoint, asset `browser_download_url`, asset `digest`, public unauthenticated reads, and asset download redirects are documented. | Updater may read public metadata without token, but must verify checksum/digest and handle rate/TLS failures. | verified |
| Inno Setup | https://documentation.help/inno-setup/topic_winvernotes.htm | Docs map Windows version constants through Windows 10. | Installer lane feasible for modern Windows; legacy claims need real installer runtime validation. | verified |
| NSIS | https://nsis.sourceforge.io/Features | NSIS advertises compatibility across major Windows versions through Windows 11. | Candidate for broad installer reach, but runtime app dependencies still decide OS support. | verified |
| WiX | https://documentation.help/WiX-Toolset/index.html | WiX builds MSI/MSP/MSM/MST; older WiX docs require .NET/MSBuild prerequisites. | Candidate only after toolchain bootstrap and target MSI behavior are validated. | verified |
| Sigstore (Cosign) | https://docs.sigstore.dev/ and https://github.com/sigstore/cosign | Open-source supply-chain signing; Python is a listed client language; supports keyless OIDC signing (works with GitHub Actions identity tokens) and self-managed keys/hardware tokens; `cosign sign-blob` can sign arbitrary files (binaries, scripts, archives), not only OCI images. | Candidate for release-asset signing in Layer 13/14 once a signing policy and key/identity decision are recorded. Do not claim signing on stable builds without artifact evidence. | verified |
| CycloneDX | https://cyclonedx.org/specification/overview/ | OWASP-led SBOM format; current spec version 1.7 (2025-10-21); formats are JSON, XML, and Protocol Buffers; conventional filenames `bom.json`, `bom.xml`, `*.cdx.json`, `*.cdx.xml`. | Project SBOM target format is CycloneDX JSON 1.x; emit alongside release manifest in Layer 13. | verified |
| cyclonedx-python (`cyclonedx-bom`) | https://github.com/CycloneDX/cyclonedx-python | Python SBOM generator supporting venv, Poetry, Pipenv, PDM, uv, and `requirements.txt`; requires Python >=3.9; install via pip/pipx/Poetry/uv. | Candidate generator for Layer 13 SBOM emission. Decision deferred until Layer 13 begins; do not install globally; pin per release env. | verified |

## Decisions
- implemented: Keep the current Python 3.10 lane as the only code-validated modern runtime until tests prove another lane.
- changed: First frontend migration slice uses toolkit-neutral `frontend_common` view models and adds no GUI dependency.
- planned: Use PyInstaller one-folder as the first reproducible Windows package lane because local scripts already contain PyInstaller specs.
- planned: Evaluate Nuitka as an alternate backend only after one-folder PyInstaller artifacts are repeatable.
- blocked: XP/Vista/7 are not modern-lane targets. They require a separate runtime/dependency report and real OS validation.
- planned: aria2, yt-dlp, and FFmpeg remain adapters/services behind typed engine and process boundaries.
- planned: Sigstore Cosign blob signing for release assets, gated on a recorded identity/key decision in Layer 13/14.
- planned: CycloneDX JSON 1.x SBOM emission via `cyclonedx-bom` per release, scoped to the project venv; gated on Layer 13.
