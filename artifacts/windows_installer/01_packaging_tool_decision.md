# 01 Packaging Tool Decision

Evidence labels: observed, inferred, blocked, changed.

## Official Docs Checked
- observed: PyInstaller docs state that one-file mode extracts support files into `_MEI...` temp folders, can be slower, can leave temp folders after crashes, and advise distributing privileged programs in one-folder mode. Source: https://www.pyinstaller.org/en/v4.10/operating-mode.html
- observed: PyInstaller usage docs cover one-file extraction-location behavior. Source: https://www.pyinstaller.org/en/stable/usage.html
- observed: Inno Setup docs show `/SILENT`, `/VERYSILENT`, `/DIR`, `/TASKS`, `/MERGETASKS`, `/LOG`, `/NORESTART`, and user/all-users command-line flags. Source: https://jrsoftware.org/ishelp/topic_setupcmdline.htm
- observed: Inno Setup docs state x64 install mode must only be enabled for 64-bit binaries and should use `ArchitecturesAllowed=x64compatible` for x64-only installers. Source: https://jrsoftware.org/ishelp/topic_setup_architecturesinstallin64bitmode.htm
- observed: Inno Setup compiler docs state scripts are compiled with `ISCC.exe`. Source: https://jrsoftware.org/ishelp/topic_compilercmdline.htm
- observed: WiX `MajorUpgrade` docs include downgrade blocking behavior through `DowngradeErrorMessage` when downgrades are not allowed by default. Source: https://docs.firegiant.com/wix3/xsd/wix/majorupgrade/
- observed: Microsoft MSIX docs require package creation/signing workflow and describe separate app packages/bundles for x86/x64/ARM architectures. Source: https://learn.microsoft.com/en-us/windows/msix/

## Freeze Tool Selected
- selected: PyInstaller one-dir for installed application payloads.
- reason: observed repo already has a maintained PyInstaller spec, validated Tk workaround, hidden imports, packaged CLI smoke, and Python-free runtime.
- reason: PyInstaller one-file is rejected for the installed app runtime because official docs describe repeated temp extraction and crash leftovers.

## Installer Tool Selected For This Pass
- selected: repo-owned Python bootstrapper built to an EXE with PyInstaller.
- reason: Inno Setup and WiX are not locally available, and global installer-tool installation is out of scope for this pass.
- reason: a Python bootstrapper can validate architecture, extract an app-local one-dir payload, create Start Menu/Desktop shortcuts, write uninstall metadata, support silent mode, uninstall, repair, and downgrade blocking without requiring internet or system Python for end users once frozen.
- scope: x64 lane only for this implementation pass.

## Alternatives Rejected Or Deferred
- deferred: Inno Setup. It is a good production candidate for native shortcuts, uninstall support, silent flags, and x64 install mode, but `ISCC.exe` is not available locally.
- deferred: WiX/MSI. Strong for enterprise MSI/major-upgrade semantics, but WiX is not available locally and requires strict component authoring.
- deferred: MSIX. Signing/certificate and packaging constraints are not configured locally.
- rejected for app runtime: PyInstaller one-file application mode, due temp extraction/performance/supportability concerns.
- deferred: Nuitka/cx_Freeze. No local evidence they improve this app enough to replace the existing PyInstaller seam.

## Architecture Implications
- observed: This host and `.venv` are AMD64; the validated PyInstaller payload is x64.
- inferred: x86 requires a 32-bit Python/toolchain/dependency wheel set.
- inferred: ARM64 requires a native ARM64 Python/toolchain/dependency lane or explicit emulation-only labeling.
- blocked: universal installer cannot be honestly produced until x86 and ARM64 payloads exist.

