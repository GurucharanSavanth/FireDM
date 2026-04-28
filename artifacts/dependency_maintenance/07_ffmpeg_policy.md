# 07 FFmpeg Policy

decision: Option B, do not bundle yet.

observed sandbox shell:
- `ffmpeg`: not found
- `ffprobe`: not found

observed elevated maintainer-equivalent shell:
- `ffmpeg`: found through WinGet package directory, version `8.1-essentials_build-www.gyan.dev`
- `ffprobe`: found through WinGet package directory, version `8.1-essentials_build-www.gyan.dev`

changed:
- dependency preflight reports FFmpeg/ffprobe as optional warnings.
- portable validation reports FFmpeg/ffprobe as optional warnings.
- release manifest records `ffmpegBundled: false`.
- docs state FFmpeg/ffprobe are not bundled.

blocked before bundling:
- approved binary source
- license mode and redistribution text
- architecture-specific SHA256 checksums
- included license files
- app-local `tools\` validation
- manual FFmpeg post-processing QA
