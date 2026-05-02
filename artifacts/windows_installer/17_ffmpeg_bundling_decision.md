# 17 FFmpeg Bundling Decision

Evidence labels: observed, changed, blocked.

## Decision
- blocked: do not bundle FFmpeg/ffprobe in the current x64 installer.

## Local Evidence
- observed: `firedm/ffmpeg_service.py` resolves FFmpeg/ffprobe through local discovery helpers.
- observed: `firedm/tool_discovery.py` searches app-local paths, PATH, and Winget package directories.
- observed: `dist/release-manifest.json` and installer sidecar mark FFmpeg bundling as blocked.

## Phase-2 Change
- changed: app-local tool discovery now checks `FIREDM_TOOLS_DIR` and `FIREDM_INSTALL_DIR\tools`, so a later installer can bundle tools without global PATH mutation.
- changed: added regression coverage for bundled ffmpeg/ffprobe discovery.

## Blocker
- blocked: no approved FFmpeg binary source, version, architecture-specific checksums, license file set, and redistribution decision were available in this pass.

## Required Next Action
- blocked: maintainer must approve a redistribution source and license inventory. Then add `tools\ffmpeg.exe`, `tools\ffprobe.exe`, license files, checksums, and version validation to the x64 payload before extending to x86/ARM64.
