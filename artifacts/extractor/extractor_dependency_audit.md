# Extractor Dependency Audit

Generated after Commit 3.

## Current extractors in the environment

| Package | Version | Role | Maintenance status |
| --- | --- | --- | --- |
| `yt_dlp` | `2026.03.17` | **Primary**, default runtime extractor | Actively maintained (monthly releases) |
| `youtube_dl` | `2021.12.17` | Fallback only; retained for user InfoExtractor plugins | Effectively unmaintained since 2022 |

## Packaging metadata

- `pyproject.toml`
  - `yt_dlp>=2024.12.0` (hard requirement)
  - `youtube_dl>=2021.12.17` (kept for compatibility, scheduled for future removal)
- `setup.py` — shim, mirrors pyproject.
- `scripts/firedm-win.spec` — both modules collected as hidden imports.

## Extractor API surface used inside the repo

| Symbol | Callers | Replacement after Commit 3 |
| --- | --- | --- |
| `ytdl.YoutubeDL(options)` | `firedm/video.py :: get_media_info`, `Video.__init__`, `Video.get_title` | unchanged (public API, works on both extractors) |
| `ytdl.utils.std_headers` | `firedm/video.py :: get_ytdl_options` (Referer) | unchanged (public utility in both extractors), guarded against `None` extractor |
| `youtube_dl.extractor.common.InfoExtractor._parse_m3u8_formats` | `firedm/video.py :: pre_process_hls / refresh_urls` | **removed hardcode** — now `active.extractor.common.InfoExtractor._parse_m3u8_formats` via `ExtractorService.active_module()` |
| `youtube_dl.utils.random_user_agent` | `firedm/video.py :: load_extractor_engines` | unchanged, still used when fallback loads (primary path uses yt_dlp UA rotation built in) |
| `youtube_dl.InfoExtractor` subclass registration | user `<sett>/extractors/*.py` plugins | unchanged; `load_user_extractors(engine=…)` now works for both primary and fallback |

## Risk snapshot

- **Private-API reliance on `_parse_m3u8_formats`**: still a private method
  on `InfoExtractor`; both extractor families currently expose it. Flagged
  as a follow-up in Commit 6 ffmpeg / HLS work.
- **`std_headers` mutation**: still module-global in both extractors.
  Controlled risk. Commit 2 added try/except + structured logging.
- **User-extractor compatibility**: plugins that subclass
  `youtube_dl.InfoExtractor` still register against `youtube_dl` only. A
  future slice should teach `load_user_extractors` to register against
  whichever engine a plugin declares.

## Policy enforcement

- `choose_extractor_name(...)` places `PRIMARY_EXTRACTOR` first.
- `ExtractorService._reselect_active_locked` re-runs selection on every
  engine load — no "last thread wins" race.
- `set_default_extractor(preferred)` with `preferred=FALLBACK_EXTRACTOR`
  emits a `extractor_select status=warn` event and keeps the primary.

## Evidence

- Proof of default selection: `artifacts/extractor/default_selection_proof.json`
- Observability matrix: `artifacts/diagnostics/observability_matrix.md`
- Policy doc: `docs/extractor-migration-policy.md`
