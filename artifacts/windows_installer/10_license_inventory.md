# 10 License Inventory

Evidence labels: observed, changed, blocked.

## Generated Inventory
- changed: `scripts/release/collect_licenses.py` generates `dist/licenses/license-inventory.json`.
- observed: generated inventory includes FireDM, pycurl, yt-dlp, yt-dlp-ejs, Pillow, certifi, pystray, awesometkinter, plyer, packaging, and Python runtime.
- observed: generated inventory records component version, license metadata when discoverable, summary, home page, and status.

## Bundled Binary Policy
- blocked: FFmpeg/ffprobe are not bundled in this pass.
- blocked: Deno is not bundled in this pass.
- required future action: record source URL, license, architecture, checksum, included files, and license-file path before bundling any external binary tools.

## Docs
- changed: `docs/release/THIRD_PARTY_BUNDLED_COMPONENTS.md` documents the generated inventory and blocked FFmpeg/ffprobe status.

