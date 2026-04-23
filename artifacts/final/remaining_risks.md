# Remaining Risks

## High

### R-H1: Private HLS helper

`firedm/video.py` still reaches the active extractor's
`InfoExtractor._parse_m3u8_formats`. The hardcoded `youtube_dl` path is gone,
but the method remains private upstream API.

Mitigation: the call is centralized behind the active extractor boundary and
covered by ffmpeg/HLS command tests. Future work should replace this with a
public yt-dlp helper or local minimal parser.

### R-H2: Legacy GUI exception swallowing

`tkview.py` still contains broad legacy exception handling outside the P0 path.

Mitigation: pipeline events now expose extractor/playlist/download boundaries
even when GUI reporting is weak. Future work should audit GUI exception paths.

## Medium

### R-M1: yt-dlp upstream drift

YouTube changes often. The verified family is `yt-dlp[default]>=2026.3.17`, but
future releases can change info-dict shape or format availability.

Mitigation: run `scripts/run_regression_suite.py` and
`scripts/repro_youtube_bug.py` before accepting extractor bumps.

### R-M2: External Deno and ffmpeg

Deno and ffmpeg are not bundled by default. FireDM now discovers app-local
paths, `PATH`, and Winget package directories, but a user without either tool
still needs installation guidance.

Future decision: bundle one or both in Windows releases, after license and size
review.

### R-M3: Legacy user extractor plugins

User plugins that subclass `youtube_dl.InfoExtractor` remain fallback-only debt.

Mitigation: `[legacy]` extra remains available. Future work should support
`yt_dlp.InfoExtractor` plugin registration or formally remove the feature.

## Deferred

- Split `controller.py` download/video orchestration further.
- Add real-download resume/progress tests with a local HTTP server.
- Validate Python 3.11 end-to-end.
- Decide bundled ffmpeg/Deno release policy.
