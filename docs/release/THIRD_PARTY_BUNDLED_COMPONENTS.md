# Third-Party Bundled Components

Generated metadata:

```text
dist\licenses\license-inventory.json
```

See [FFMPEG_BUNDLING.md](FFMPEG_BUNDLING.md) for the current FFmpeg/ffprobe
decision.

Bundled through the current PyInstaller payload:
- Python runtime `3.10.11`
- pycurl/libcurl native stack
- yt-dlp and yt-dlp-ejs
- certifi CA bundle
- Pillow
- pystray
- awesometkinter
- Tcl/Tk runtime files
- dependent DLLs collected by PyInstaller
- `build-metadata.json`, `payload-manifest.json`, and dependency status JSON

Blocked from bundling in this pass:
- FFmpeg
- ffprobe
- Deno

Reason: redistribution source, license mode, checksum, architecture, and included-file inventory must be finalized before bundling these tools into the installer.

Code signing:
- blocked: no signing certificate or signing workflow is configured locally.
