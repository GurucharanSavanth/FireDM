# Engine Selection

Status: changed 2026-05-02.

## Planned Options
- planned: `Auto` selects the first healthy engine that supports the request.
- planned: `Internal` uses FireDM's internal HTTP/HTTPS segmented downloader.
- planned: `aria2c` supports normal aria2 protocols when aria2c is installed and healthy.
- planned: `yt-dlp` handles user-authorized accessible media supported by yt-dlp.
- planned: Future plugin engines appear through the registry after health checks.

## Current Status
- implemented: Engine descriptors and health status are modeled in code.
- blocked: UI dropdown and real engine adapters are not implemented.
