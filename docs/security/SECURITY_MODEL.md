# Security Model

Status: changed 2026-05-02.

This document is the modernization-program security model. It cross-references
existing authoritative rule files; it does not duplicate them. The permanent
hard-no list lives in
[`docs/agent/SECURITY_BOUNDARIES.md`](../agent/SECURITY_BOUNDARIES.md).
The updater attack surface lives in
[`docs/security/UPDATER_THREAT_MODEL.md`](./UPDATER_THREAT_MODEL.md).
The engine contract security rules live in
[`docs/architecture/ENGINE_PLUGIN_SYSTEM.md`](../architecture/ENGINE_PLUGIN_SYSTEM.md#security-rules).

## Trust Boundaries
- implemented: GUI, CLI, native browser handoff, and tests are the only callers
  that can construct a `DownloadRequest`. The engine adapter receives a
  validated request and never sees raw user input.
- implemented: `firedm/download_engines/models.Header` rejects CR/LF in
  both name and value (`firedm/download_engines/models.py:69-73`). This
  blocks header-injection attacks at the model boundary before any subprocess
  or HTTP call sees the value.
- implemented: `firedm/download_engines/config.EngineConfig.engine_settings`
  is `field(repr=False)` (`firedm/download_engines/config.py:61`) so default
  `repr()` and `str()` cannot leak future engine secrets (for example an
  aria2c RPC secret) through diagnostics or log lines that print a config.
- implemented: Browser/native handoff via `Controller._coerce_native_headers`
  drops `Authorization`, `Proxy-Authorization`, `Cookie`, and `Set-Cookie`
  before the request reaches any download path (existing behavior, see
  `docs/agent/SECURITY_BOUNDARIES.md`).
- planned: All new engine adapters validate executable paths, output paths,
  working directories, and request schemes before any work starts.

## Subprocess Argv-Only Policy
- implemented: `firedm/download_engines/internal_http.py` uses no subprocess
  at all (`firedm/download_engines/internal_http.py:28-29`). The internal
  engine reaches the legacy `pycurl` transport only after Layer 3 wires the
  handoff; it never spawns a process.
- implemented: `firedm/utils.run_command` forces `shell=False` and splits the
  command via `shlex` even when callers pass a string (existing behavior in
  legacy code).
- implemented: `firedm/ffmpeg_service.py` probes ffmpeg/ffprobe with argv
  lists.
- implemented: `firedm/FireDM.open_config_editor` uses argv lists with
  `shell=False`.
- planned: Layer 4 (Tool discovery + subprocess service) extracts a single
  subprocess service that emits argv-only commands, redacts secrets in
  command logs, captures stderr separately, and surfaces typed failure modes.
  Promotion criterion: an AST grep returns no `shell=True` and no
  `subprocess.run(... str ...)` calls in `firedm/download_engines/`.
- planned: Layer 5 (aria2c) and Layer 6 (yt-dlp) must build argv lists from
  validated `DownloadRequest` fields. They must never interpolate URLs,
  filenames, headers, cookies, metadata, or user input into shell strings.
- observed: Some legacy `video.py` paths still build ffmpeg command strings
  before subprocess handoff. These are gated by `utils.run_command`'s
  `shell=False` behavior but should be argv-only in Layer 7.

## Header Safety
- implemented: `Header` rejects CR/LF and the colon character in `name`. Both
  the legacy native-handoff path (`Controller._coerce_native_headers`) and
  the typed engine boundary (`firedm/download_engines/models.Header`) drop
  injected control characters.
- planned: Layer 8 expands preflight to run before every engine start and to
  return a typed `PreflightResult` listing errors and warnings. The header
  CR/LF rule applies in both layers.

## Path Safety
- implemented: `firedm/utils.safe_extract_zip` and `safe_extract_tar` validate
  archive member targets and reject tar links (existing behavior, see
  `docs/agent/SECURITY_BOUNDARIES.md`).
- implemented: `firedm/download_engines/internal_http.preflight` performs
  local-only validation (no network, no disk write, no spawn) before the
  legacy fallback runs.
- planned: Layer 4 service rejects relative `..` traversal, Windows reserved
  device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1`-`COM9`, `LPT1`-`LPT9`),
  and final paths outside the configured download root.

## Secret Redaction
- implemented: `firedm/pipeline_logger.py` redacts credential-bearing URL
  query and fragment parameters.
- implemented: `EngineConfig.engine_settings` is `field(repr=False)` so
  secrets stored under that key (for example a future aria2c RPC token) are
  never emitted by the default config `repr()` or `str()`.
- implemented: `setting.save_setting` omits remembered web-auth fields when
  the user has disabled remember-credentials (existing behavior).
- planned: The Layer 4 subprocess service captures redacted command logs.
  Tokens, cookies, authorization headers, proxy passwords, and local API
  tokens never appear in `stdout`/`stderr` capture buffers persisted to disk.

## Cookie / Credential Explicit-Consent Rule
- implemented: Browser integration plugin (`firedm/plugins/browser_integration.py`)
  is disabled by default. Native handoff drops `Cookie` and `Set-Cookie`
  before handing off to a download path.
- implemented: Engine capability `COOKIES_EXPLICIT_USER_SUPPLIED` exists so
  any cookie use is opt-in via `EngineConfig` plus a per-job flag.
- planned: Layer 6 (yt-dlp) must not silently use browser cookies.
  Cookie-file usage requires both `EngineConfig.engine_settings.<engine_id>`
  flag and a per-`DownloadRequest` opt-in. Engines without
  `COOKIES_EXPLICIT_USER_SUPPLIED` capability ignore the flag.

## Updater Threat Sketch
- planned: The full updater threat model is in
  [`docs/security/UPDATER_THREAT_MODEL.md`](./UPDATER_THREAT_MODEL.md).
  Headline controls: HTTPS-only GitHub Releases API metadata over the public
  endpoint, SHA256/digest verification of the downloaded asset, temp-folder
  staging, current-install backup, restart/helper-replacement step, rollback
  path, and no auto-run from cache.
- planned: Sigstore Cosign blob signing is a candidate trust upgrade for
  release assets; decision deferred until Layer 13 records a signing identity
  policy. Cosign and CycloneDX rows in
  [`docs/architecture/TOOLCHAIN_DECISIONS.md`](../architecture/TOOLCHAIN_DECISIONS.md)
  are verified.
- blocked: No updater code exists yet. Self-updater is Layer 14; until that
  layer lands the project ships with no in-app update path.

## Engine Isolation
- implemented: `EngineRegistry` filters unavailable engines via
  `health_check()`, catches broken health checks, and returns descriptors so
  the GUI surfaces only engines whose health-check succeeded.
- implemented: `InternalHTTPDownloadEngine.start()` returns a structured
  `DownloadResult(state=FAILED, failure=DownloadFailure(code="ENGINE_NOT_CONNECTED"))`.
  An engine that is not wired cannot silently fake success.
- implemented: AST-level test asserts the `internal_http` adapter contains no
  subprocess imports or calls (`tests/test_internal_http_engine.py`).
- planned: Layer 5 (`Aria2DownloadEngine`) binds RPC to localhost only,
  generates a random per-session secret, never logs the secret, and never
  passes `--rpc-listen-all=true` or `--rpc-allow-origin-all`.

## Plugin Sandbox
- implemented: All plugin modules are off by default. The browser-integration
  plugin requires explicit user enablement.
- planned: A formal plugin-sandbox model is not in scope for the engine
  modernization layers (L0-L14). Plugin behavior remains gated by the
  prohibitions in `docs/agent/SECURITY_BOUNDARIES.md`.

## Permanent Boundaries (cross-reference)
- implemented: DRM bypass, protected-media circumvention, license-server
  bypass, media-key extraction, browser credential theft, silent cookie
  harvesting, arbitrary local file reads, public local API binding by
  default, unsafe shell execution, path traversal, unsafe deserialization,
  saved-state execution, and secret leakage are prohibited at
  `docs/agent/SECURITY_BOUNDARIES.md`.
- planned: Layer 6 (yt-dlp) must surface DRM-protected formats as rejected
  before any download starts. The model-boundary check is the regression
  gate.

## Validation Gates
- implemented: `tests/test_download_engines.py`, `tests/test_internal_http_engine.py`,
  and `tests/test_engine_config_and_factory.py` cover the typed-boundary
  invariants. Full pytest baseline is 287 passed and 1 skipped via
  `.venv/Scripts/python.exe -m pytest -q`.
- planned: Layer 4 promotes a security grep set covering `shell=True`,
  `os.system`, `eval(`, `exec(`, raw cookies in logs, raw authorization
  headers in logs, and unsafe deserialization. See
  [`docs/developer/VALIDATION_PIPELINE.md`](../developer/VALIDATION_PIPELINE.md).

## Update Rules
- Update this file when a security control transitions from planned to
  implemented or when a new boundary is added.
- Do not duplicate the hard-no list from `docs/agent/SECURITY_BOUNDARIES.md`;
  cross-reference instead.
- Do not weaken any control without explicit user instruction and a recorded
  rationale.
