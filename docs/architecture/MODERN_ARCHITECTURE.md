# Modern Architecture

Status: changed 2026-05-02.

## Local Baseline
- observed: Entry points are `firedm.py`, `firedm/FireDM.py`, and `firedm/__main__.py`.
- observed: GUI lives mainly in `firedm/tkview.py`; orchestration lives in `firedm/controller.py`.
- observed: Internal segmented download behavior lives in `firedm/brain.py`, `firedm/worker.py`, `firedm/downloaditem.py`, and `firedm/utils.py`.
- observed: Media extraction and post-processing live in `firedm/video.py`, `firedm/extractor_adapter.py`, `firedm/ffmpeg_service.py`, and `firedm/ffmpeg_commands.py`.
- changed: `firedm/download_engines/` now defines typed engine contracts, an `EngineConfig` model, a `create_default_registry` factory, a `select_engine` resolver, an `InternalHTTPDownloadEngine` adapter skeleton, and a diagnostic runtime bridge.
- changed: `controller._download` now calls the diagnostic runtime bridge before `Thread(target=brain, args=(d,))`; the `InternalHTTPDownloadEngine.start()` path is intentionally not wired in this patch.

## Current Seam And Next Integration Path
- implemented: A non-runtime seam now exists. Callers can build an `EngineConfig`, get a `DefaultRegistryResult` from `create_default_registry`, and resolve a `DownloadEngine` via `select_engine(registry, config, scheme=..., input_type=...)`.
- changed: `Controller._download()` now performs advisory selection/preflight through `evaluate_engine_for_download_item()` for plain HTTP/HTTPS file-shaped downloads. It records request shape and preflight outcome for tests/logs, then still calls direct legacy `brain(d)`.
- partially implemented: `InternalHTTPDownloadEngine.start()` returns `ENGINE_NOT_CONNECTED` so unwired use cannot silently fake success. The runtime download path is still the legacy `Controller -> brain -> worker` flow.
- planned: Next safe step is a dedicated runtime handoff that can promote the internal engine from advisory preflight to actual execution only after broader parity tests prove queue behavior, cancellation, failed-download state, and live resume/segment behavior.

## Target Shape
- planned: `Controller` remains compatibility facade until engine adapters are tested.
- planned: UI creates a `DownloadRequest`, asks an engine registry for a healthy engine, then hands a `DownloadJob` to the selected adapter.
- planned: Internal pycurl, aria2c, yt-dlp, and FFmpeg work through explicit adapters with capability flags and health checks.
- planned: Platform services own paths, subprocess execution, external tool discovery, updater staging, and release metadata.
- planned: State writes stay atomic and explicit; running jobs are never silently migrated between engines.

## Phase Boundaries
- implemented: Typed model/registry seam, `EngineConfig`, registry factory, selection resolver, `InternalHTTPDownloadEngine` adapter skeleton, and `Controller._download()` advisory preflight bridge.
- partially implemented: Tool discovery, ffmpeg discovery, extractor adapter, playlist models, and redacted pipeline logging already exist.
- planned: Wired internal adapter, aria2c/yt-dlp/ffmpeg adapters, UI dropdown, doctor command, build orchestrator, updater, and legacy lane.
- blocked: Framework swap, pycurl removal, bundled ffmpeg, and legacy Windows support without validation.
