# Extractor Migration Policy

## Decision

`yt_dlp` is the **primary and default** extractor for every mainline code path.
`youtube_dl` is retained only as an **opt-in compatibility fallback** and is
never selected automatically when `yt_dlp` is importable.

## Why now

- `youtube_dl` upstream has been effectively unmaintained since late 2021; its
  YouTube extractor drifts every few months.
- `yt_dlp` is the actively maintained successor family. The repo already
  pinned `yt_dlp>=2024.12.0` in `pyproject.toml` and the baseline environment
  ships `yt_dlp==2026.03.17`.
- The observed P0 defect (`Stream.__init__` exploding on `abr=None`) is a
  direct consequence of extractor drift; keeping `youtube_dl` as an equal
  peer masks the drift.

## Code-level implementation

- `firedm/extractor_adapter.py`
  - `PRIMARY_EXTRACTOR = "yt_dlp"`
  - `FALLBACK_EXTRACTOR = "youtube_dl"`
  - `choose_extractor_name(configured, available)` now returns
    `PRIMARY_EXTRACTOR` whenever it is present, regardless of the user's
    persisted `active_video_extractor`.
  - `ExtractorService` exposes deterministic `wait_until_ready(timeout)` and
    `current()` / `active_name()` / `is_primary_active()` APIs.
- `firedm/video.py`
  - `load_extractor_engines()` registers both engines with `ExtractorService`
    in daemon threads, but the **active** choice is always derived from the
    service's `_reselect_active_locked()` — no "last thread wins" race.
  - `get_media_info()` waits on `ExtractorService.wait_until_ready(45.0)`
    instead of the previous unbounded `while not ytdl: time.sleep(1)`.
  - `set_default_extractor()` respects the primary-first policy; attempts
    to pin the deprecated fallback while the primary is loaded emit a
    `extractor_select status=warn` event but do not actually downgrade.
  - HLS `_parse_m3u8_formats` reference now comes from the active module
    (not hardcoded to `youtube_dl`).
  - `load_user_extractors` guards against unresolved `config.sett_folder`
    (headless / pre-settings callers).

## Deprecation boundary

The fallback extractor:

- Is still loaded best-effort so existing user-installed extractor plugins
  (`<sett>/extractors/*.py` registering `youtube_dl.InfoExtractor` subclasses)
  continue to work.
- Is never made the default when `yt_dlp` is present.
- Must not be referenced by name in new code outside `firedm/video.py`'s
  load helpers. Everywhere else should go through
  `ExtractorService.active_module()` or `video.ytdl` (which is kept mirrored
  from the service purely for backwards compatibility with legacy call
  sites).

## Dependency policy

- `pyproject.toml` keeps `yt_dlp>=2024.12.0` as a hard dependency.
- `youtube_dl>=2021.12.17` is retained in the dependency set for now, with
  the intent to drop it in a future release once telemetry shows no users
  rely on legacy InfoExtractor plugins.
- Packaged Windows build (`scripts/firedm-win.spec`) should continue to
  collect both modules for transition safety.

## Proof

- `scripts/verify_extractor_default.py` exits 0 when the service resolves
  the primary, and writes `artifacts/extractor/default_selection_proof.json`
  (see `artifacts/extractor/default_selection_proof.json` for a real run).
- `tests/test_extractor_adapter.py` encodes the policy as a regression:
  `test_primary_always_wins_even_when_user_configured_fallback`.

## Migration notes for existing users

- `config.active_video_extractor` still accepts `"yt_dlp"` or
  `"youtube_dl"` for compatibility. Writes of `"youtube_dl"` will be
  silently upgraded to `"yt_dlp"` at runtime when the primary is available;
  the user-visible Settings dialog still lets the user pick either value,
  but the service enforces the policy at runtime.
