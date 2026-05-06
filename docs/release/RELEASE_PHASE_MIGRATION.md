# Release Phase Migration

## Overview

The FireDM codebase has been migrated from test-phase orientation to release-phase orientation. This document describes the separation of test and production code, ensuring Release builds are clean and production-ready.

## Configuration Defaults (Release-Oriented)

| Setting | Default | Purpose |
|---------|---------|---------|
| `config.test_mode` | `False` | Disables test-specific code paths (error re-raising, debug logging) |
| `config.keep_temp` | `False` | Cleans up temporary files after download |
| `config.log_level` | `2` (verbose) | Standard logging; users can increase to debug level if needed |
| `config.advanced_features_enabled` | `False` | Disables experimental plugins until user explicitly enables |

**Why**: Default configuration reflects production use case. Users can opt into testing/debugging via Settings → Advanced.

## Code Organization

### Test-Only Code Paths

Code guarded by `if config.test_mode:` that is NOT active in production:

| Location | Behavior | Purpose |
|----------|----------|---------|
| `brain.py:63, 214` | Re-raise exceptions on HLS processing errors | Makes failures visible during test runs |
| `cmdview.py:174` | Re-raise exceptions on download errors | Captures test failures |
| `controller.py` (multiple) | Re-raise exceptions on various operations | Test visibility |
| `downloaditem.py:839` | Re-raise exceptions on segment operations | Test visibility |
| `systray.py:51` | Special test mode UI behavior | Testing UI in isolation |
| `video.py:303, 1832` | Re-raise exceptions on video processing | Test visibility |

**Philosophy**: In production, the app logs errors and continues gracefully. In test mode, errors propagate so tests fail loudly.

### Production Code (Always Active)

These features work regardless of mode:

- Exception logging and error handling
- User-facing error dialogs
- Network retry logic
- Config persistence
- Plugin system
- Download engine selection
- Post-processing pipeline
- Advanced feature gates (with user consent)

## Build Phase Separation

### Release Build (`-Mode Release`, default)

```
Build Phases Executed:
✓ Stage 1: Repo state snapshot
✓ Stage 2: Cleanup
✓ Stage 3: Dependency checks
✓ Stage 4: Build info stamp (embeds BUILD_MODE="Release")
✗ Stage 5: QA (skipped)
  - No pytest
  - No mypy
  - No ruff lint
✓ Stage 5b: Python distribution
✓ Stage 6: Plugin manifest discovery
✓ Stage 7: Package build (PyInstaller)
✓ Stage 8: Artifact integrity
✓ Stage 9: Smoke check
✓ Stage 10: Changelog (excludes dev notes)
✓ Stage 11: Manifest generation
✓ Stage 12: Checksum generation
```

### Debug Build (`-Mode Debug`)

```
Build Phases Executed:
✓ Stage 1: Repo state snapshot
✓ Stage 2: Cleanup
✓ Stage 3: Dependency checks
✓ Stage 4: Build info stamp (embeds BUILD_MODE="Debug")
✓ Stage 5: QA (full suite)
  - pytest all tests
  - mypy type checking
  - ruff linting
✓ Stage 5b: Python distribution
✓ Stage 6: Plugin manifest discovery
✓ Stage 7: Package build (PyInstaller)
✓ Stage 8: Artifact integrity
✓ Stage 9: Smoke check
✓ Stage 10: Changelog (includes dev notes)
✓ Stage 11: Manifest generation
✓ Stage 12: Checksum generation
```

## PyInstaller Exclusions

Both Windows and Linux spec files explicitly exclude:

```python
excludes=["pytest", "tests", "test", "_pytest"]
```

This ensures test infrastructure never gets packaged, even if accidentally imported.

## Codebase Layout

```
FireDM/
├── firedm/              # Production code (always shipped)
│   ├── config.py        # test_mode=False by default
│   ├── plugins/         # Plugin system (production)
│   ├── download_engines/
│   └── [application modules]
├── tests/               # NOT included in Release artifacts
│   ├── test_*.py
│   └── [test fixtures]
├── scripts/             # Build scripts (not shipped)
├── docs/
│   ├── release/         # Shipped with Release builds
│   │   ├── BUILD_MODES.md
│   │   └── [release docs]
│   └── agent/           # Debug/development notes (Debug builds only)
└── windows-build.ps1    # Build script (not shipped)
```

## Migration Checklist

- [x] Config defaults are release-oriented (test_mode=False)
- [x] PyInstaller excludes test modules
- [x] Release builds skip QA phases
- [x] Build script gates dev-only artifacts by Mode
- [x] Application gracefully handles errors in Release mode
- [x] Test mode can be enabled by users for debugging
- [x] Plugin system is user-controlled (advanced gate)
- [x] No test files are packaged in Release artifacts
- [x] BUILD_MODE is embedded in executable for inspection

## Runtime Inspection

The build mode is available at runtime:

```python
from firedm._build_info import BUILD_MODE
print(BUILD_MODE)  # "Release" or "Debug"
```

Applications can use this to adjust behavior if needed (though typically unnecessary).

## Testing Production Code

To test production code paths:

1. **Default**: Run pytest with `config.test_mode = False` (default)
   ```bash
   pytest tests/
   ```

2. **Explicit test_mode**: Set `config.test_mode = True` to enable test-only paths
   ```bash
   # In test code:
   config.test_mode = True
   # Then errors re-raise instead of being silently logged
   ```

## User Sovereign Features

The advanced feature system allows users to enable experimental plugins:

1. **Master Gate**: `advanced_features_enabled` (Default: False)
2. **Per-Plugin Override**: `enable_plugin_<id>` (Default: False)
3. **Permanent Blocks**: DRM-related features (Never overridable per DMCA §1201)

Users who enable advanced features assume responsibility for risks. See `USER_SOVEREIGNTY_POLICY.md`.

## See Also

- `BUILD_MODES.md` — Build mode selection and workflows
- `BUILD_SYSTEM.md` — Detailed stage documentation
- `USER_SOVEREIGNTY_POLICY.md` — Advanced feature policy
- `windows-build.ps1` — Build script implementation
