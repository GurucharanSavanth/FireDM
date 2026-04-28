# 06 FFmpeg Bundling Decision

Evidence labels: observed, changed, blocked.

## Decision
- blocked: FFmpeg/ffprobe are not bundled in this patch.

## Reason
- observed: current release artifacts do not include FFmpeg or ffprobe binaries.
- observed: current project discovery uses `firedm/ffmpeg_service.py` and `firedm/tool_discovery.py`.
- blocked: no approved redistribution source URL, exact version, architecture matrix, checksums, and license files were provided for bundled FFmpeg builds.

## Changes
- changed: `firedm/tool_discovery.py` now checks app-local tool directories from `FIREDM_TOOLS_DIR` and `FIREDM_INSTALL_DIR\tools` before PATH/Winget discovery.
- changed: added tests for bundled/app-local ffmpeg and ffprobe discovery.
- changed: documented Option B in `docs/release/FFMPEG_BUNDLING.md`.

## Validation
- verified: `tests/test_ffmpeg_service.py` plus release tests pass in the targeted run.
- blocked: actual bundled `ffmpeg -version` and `ffprobe -version` cannot be validated because no binaries were bundled.
