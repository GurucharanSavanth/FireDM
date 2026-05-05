# Windows Build And Packaging

## Decision

Windows distribution targets PyInstaller. Root `.\windows-build.ps1` is the
canonical local Windows build script. `.\scripts\windows-build.ps1` is a
compatibility wrapper only.

## Build Prerequisites

- validated Python environment from `bootstrap/windows-dev-setup.md`
- repo-local `.venv` with build/test tools
- `ffmpeg` and `ffprobe` on `PATH` for runtime diagnostics where available

## Canonical Commands

Dry-run cleanup preview and metadata generation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\windows-build.ps1 -DryRun -Clean -SkipTests -SkipSmoke
```

Validation-only dry run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\windows-build.ps1 -DryRun
```

PyInstaller one-folder build:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\windows-build.ps1 -Clean -Kind OneFolder -Backend PyInstaller -Mode Release
```

The old path still forwards to the canonical script:

```powershell
.\scripts\windows-build.ps1 -Channel dev -Arch x64
```

## Output Contract

Canonical output is root `release\`:

```text
release\build.log
release\manifest.json
release\checksums.sha256
release\CHANGELOG-COMPILED.md
release\FireDM\
```

`dist\FireDM` may be mirrored for old release-script compatibility, but it is
not the final artifact authority after this change.

## Cleanup

Cleanup runs only with `-Clean`. Use `-DryRun -Clean` to preview. The script
removes only explicit generated paths under the repo after containment checks.
It does not remove `.git`, `.venv`, source, tests, docs, scripts, or whole
evidence directories such as `artifacts`.

## Smoke Verification

When a real OneFolder build succeeds and `-SkipSmoke` is not set, the script
runs:

```powershell
.\release\FireDM\firedm.exe --help
.\release\FireDM\firedm.exe --imports-only
```

Full GUI smoke remains manual/headless-gated and is not claimed unless run.

## Blocked Lanes

- PyInstaller OneFile: parameter accepted, real build blocked until a one-file spec is validated.
- Nuitka: blocked until Nuitka and compiler discovery pass.
- Linux: must run on Linux or WSL; PyInstaller is not treated as a cross-compiler.
- Signing/MSI/MSIX/universal Windows artifacts: blocked until separate release lanes are validated.
