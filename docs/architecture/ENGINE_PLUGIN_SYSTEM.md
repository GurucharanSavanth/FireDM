# Engine Plugin System

Status: changed 2026-05-02.

## Implemented
- implemented: `DownloadEngine` protocol defines `id`, `display_name`, supported schemes/input types, capabilities, `health_check()`, `preflight()`, lifecycle methods, status, and shutdown.
- implemented: `EngineCapability` includes segmented HTTP, resume, rate limit, proxy, custom headers, explicit user cookies, checksum, BitTorrent, Metalink, FTP, SFTP, media extraction, post-processing, subtitles, thumbnails, and metadata embedding.
- implemented: `EngineRegistry` registers adapters, returns descriptors, catches broken health checks, filters unavailable engines, and selects by preferred id, scheme, and input type.
- implemented: `Null/TestEngine` behavior is covered by the fake engine in `tests/test_download_engines.py`.
- implemented: `EngineConfig` typed model holds `default_engine_id`, `auto_select_enabled`, `disabled_engine_ids`, `per_scheme_preference`, `per_input_type_preference`, `engine_settings`, and `schema_version`. Validation rejects invalid/duplicate engine ids, mismatched input types, non-mapping settings, and conflicting default+disabled. `to_dict`/`from_dict` round-trips for later persistence; `engine_settings` is excluded from `repr()`/`str()` to avoid leaking secret values.
- implemented: `create_default_registry(config=None)` returns `DefaultRegistryResult` with the registry, the effective default engine id (downgraded to `None` with a structured warning if the configured default is not registered), and any other warnings emitted while assembling. The factory does not register aria2c, yt-dlp, or any test/null engine in production.
- implemented: `select_engine(registry, config, scheme=..., input_type=...)` resolves preferences in order: per-scheme -> per-input-type -> default -> auto-select (when enabled).
- partially implemented: `InternalHTTPDownloadEngine` adapter skeleton lives in `firedm/download_engines/internal_http.py`. It advertises only `http`/`https`, only `EngineInputType.URL`, and only the capabilities the legacy worker is known to support (segmented HTTP, resume, rate limit, proxy, custom headers, explicit user cookies). `health_check()` only inspects whether `pycurl` is importable; it never opens a connection. `preflight()` performs local-only validation. `start()`/`pause()`/`resume()`/`cancel()` return `DownloadResult(state=FAILED, failure=DownloadFailure(code="ENGINE_NOT_CONNECTED", detail="not_implemented_for_runtime"))` because the legacy `Controller -> brain -> worker` path is still authoritative.
- changed: `Controller._download()` now calls the Layer 3 advisory bridge before each legacy `brain(d)` attempt. The bridge builds a `DownloadRequest`, selects an engine, and calls `preflight()` for plain HTTP/HTTPS file-shaped downloads only. It always falls through to the legacy `brain(d)` runtime and never calls `engine.start()`.
- changed: `firedm/download_engines/runtime_bridge.py` preserves non-secret parity metadata in `DownloadRequest.options`: resumable flag, segment count, total parts, and proxy presence booleans. Raw proxy strings are intentionally not copied because they can contain credentials.

## Planned Adapters
- planned: Wire `InternalHTTPDownloadEngine.start` to the existing `Controller -> brain -> worker` path through a dedicated runtime handoff only after parity tests prove resume, segmentation, proxy, HLS/fragmented skip behavior, FTP/SFTP fallback, queue behavior, cancellation, and failed-download state.
- planned: `Aria2DownloadEngine` owns aria2c discovery, version check, localhost JSON-RPC startup, random RPC secret, and path validation.
- planned: `YtDlpDownloadEngine` normalizes accessible media formats into internal models before UI/controller use.
- planned: `FfmpegPostProcessEngine` or service adapter owns merge/probe/post-processing through argv-list subprocess calls.
- planned: UI engine dropdown surfacing `EngineRegistry.descriptors()`.

## Security Rules
- implemented: Header model rejects CR/LF injection.
- implemented: `EngineConfig.engine_settings` is `field(repr=False)` so default `repr()`/`str()` cannot leak secret-looking values that future engines (for example aria2c RPC secret) might store there.
- implemented: `InternalHTTPDownloadEngine` uses no subprocess, no shell, no arbitrary local file reads, and never logs secret material in failure messages. AST-level tests pin the no-subprocess invariant.
- changed: Controller advisory bridge logs only engine ids, skip reasons, failure codes, and dropped-header counts. It does not log URLs, raw headers, cookies, or raw proxy strings.
- planned: Engine configs use typed models, validated paths, no raw shell strings, and redacted diagnostics.
- blocked: No real aria2c/yt-dlp/FFmpeg engine adapter exists yet.
