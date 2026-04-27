# FFmpeg Bundling

Evidence labels: observed, changed, blocked.

## Decision

blocked: FireDM does not bundle FFmpeg or ffprobe in the current Windows installer lane.

Reason:
- redistribution source, license text, architecture-specific checksums, and maintainer approval are not recorded yet
- x86 and ARM64 payload lanes are not available yet
- the existing runtime already reports missing FFmpeg with an install-help path instead of silently downloading binaries

## Runtime Discovery

changed: FireDM now honors `FIREDM_TOOLS_DIR` and `FIREDM_INSTALL_DIR\tools` during binary discovery before falling back to `PATH` and Winget package folders.

Observed search behavior for FFmpeg/ffprobe:
- saved custom path, if configured
- explicit search directories from caller
- app-local tools directory from launcher environment
- system `PATH`
- Winget package folder fallback on Windows

## Future Bundling Requirements

Before bundling FFmpeg/ffprobe:
- choose the exact build source
- record license and redistribution terms
- record version and architecture
- record SHA256 for every binary and license file
- include license files under the installed tree
- validate `ffmpeg -version` and `ffprobe -version`
- verify paths with spaces
- update `dist/licenses/license-inventory.json`
- update this document and `THIRD_PARTY_BUNDLED_COMPONENTS.md`

## User-Facing Status

Users still need FFmpeg externally if they use workflows requiring media merge, conversion, metadata writing, or HLS post-processing.

