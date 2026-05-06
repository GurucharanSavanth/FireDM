# FireDM Build Modes: Release vs Debug

## Overview

The Windows build script (`windows-build.ps1`) supports two distinct modes to separate test-phase gates from release-phase work:

- **Release mode** (default): Focuses on artifact generation with minimal testing overhead
- **Debug mode**: Runs full test suite for development and validation

## Mode Selection

```powershell
# Release build (default)
.\windows-build.ps1

# Explicit Release build
.\windows-build.ps1 -Mode Release

# Debug build with full testing
.\windows-build.ps1 -Mode Debug

# Debug build with custom parameters
.\windows-build.ps1 -Mode Debug -Clean -SkipSmoke
```

## Stage Execution by Mode

### Stages That Run In Both Modes

| Stage | Purpose | Release | Debug |
|-------|---------|---------|-------|
| 1 | Repo state snapshot | ✓ | ✓ |
| 2 | Cleanup crew | ✓ | ✓ |
| 3 | Dependency checks | ✓ | ✓ |
| 4 | Build info stamp | ✓ | ✓ |
| 5b | Python distribution | ✓ | ✓ |
| 6 | Plugin manifest discovery | ✓ | ✓ |
| 6a | Plugin manifest artifacts | ✓ | ✓ |
| 7 | Package build (PyInstaller) | ✓ | ✓ |
| 8 | Artifact integrity check | ✓ | ✓ |
| 9 | Smoke check (CLI/imports) | ✓ | ✓ |
| 10 | Changelog compilation | ✓ | ✓ |
| 11 | Manifest generation | ✓ | ✓ |
| 12 | Checksum generation | ✓ | ✓ |

### Stage 5: QA (Unit Tests, Linting, Type Checking)

| Aspect | Release | Debug |
|--------|---------|-------|
| Python compilation check | ✗ | ✓ |
| pytest (all tests) | ✗ | ✓ |
| mypy (type checking) | ✗ | ✓ |
| ruff (linting) | ✗ | ✓ |

**Release mode**: Skipped entirely unless `-SkipTests $false` is explicitly passed.

**Debug mode**: Full suite runs by default; use `-SkipTests` to skip.

## Build Artifacts

Both modes produce these core artifacts:

- `FireDM/` (one-folder executable bundle)
- `FireDM.zip` (portable archive, if `-Kind PortableZip`)
- `plugins-manifest.json` (plugin metadata with user-sovereignty policy)
- `requirements-advanced.txt` (optional feature dependencies)
- `CHANGELOG-COMPILED.md` (consolidated release notes)
- `manifest.json` (release metadata)
- `checksums.sha256` (file integrity hashes)
- Python distribution artifacts (`.whl`, `.tar.gz`)

### Release Build (Default)

Release artifacts exclude:
- `tests/` directory (excluded via PyInstaller spec)
- `pytest`, `_pytest` modules (excluded via PyInstaller spec)
- `docs/agent/` development notes (not included in changelog)
- Session handoff files (development-only context)

**Result**: Minimal, clean release bundle suitable for end users. No test infrastructure, no debug notes.

### Debug Build

Debug artifacts may include:
- Session handoff documentation in CHANGELOG-COMPILED.md (if present)
- Full git log history (all commits, not just tags)
- Build diagnostic information

**Result**: Full transparency build with development context for validation and troubleshooting.

## Build Metadata

The build mode is encoded in the generated `firedm/_build_info.py`:

```python
BUILD_MODE = "Release"  # or "Debug"
```

This can be inspected at runtime via:

```python
from firedm._build_info import BUILD_MODE
```

## Interaction with Config Defaults

The application's default settings are **release-oriented**:

- `config.test_mode = False` (test debugging disabled by default)
- `config.keep_temp = False` (temporary files cleaned up after download)
- User can override via Settings → Advanced

The build script itself does **not** modify these defaults; it applies Mode gating only to the build process, not the installed application behavior.

## Recommended Workflows

### Local Development
```powershell
# Fast dev builds with incremental testing
.\windows-build.ps1 -Mode Debug -NoClean -SkipSmoke
```

### Pre-Release Validation
```powershell
# Full test suite before release
.\windows-build.ps1 -Mode Debug -Clean
```

### CI/CD Release Pipeline
```powershell
# Fast release artifact generation
.\windows-build.ps1 -Mode Release
```

### Dry-Run Planning
```powershell
# Preview what will happen without running anything
.\windows-build.ps1 -Mode Release -DryRun
```

## Forcing QA in Release Builds

If you must run QA in Release mode (rare):

```powershell
# Override Release mode QA skip
.\windows-build.ps1 -Mode Release -SkipTests $false
```

This will run all QA checks before artifact generation.

## Exit Codes and Logging

Both modes produce:

- Detailed build log at `build-<timestamp>.log`
- Exit code 0 on success, 1 on failure
- Identical validation results and manifest structure
- Same error reporting for blocker items

The only difference is whether the QA stage is invoked.

## See Also

- `RELEASE_ARTIFACT_LAYOUT.md` — artifact structure and conventions
- `BUILD_SYSTEM.md` — detailed stage documentation
- `windows-build.ps1` — annotated script implementation
