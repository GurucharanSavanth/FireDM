# Implementation Layers

Status: changed 2026-05-02.

This is the developer-facing one-paragraph-per-layer view of the modernization
program. The status table and dependency graph live in
[`docs/architecture/MODERNIZATION_MASTER_PLAN.md`](../architecture/MODERNIZATION_MASTER_PLAN.md).

## L0 — Safety baseline + decision records
- implemented (this run): All later layers depend on a recorded baseline. Layer 0 produces the agent rules (`AGENTS.md`, `AGENT.md`, `CLAUDE.md`), the security model, the toolchain decisions, the compatibility matrix, the modernization master plan, this file, the validation pipeline, and the multi-agent protocol. No application code changes. Validation gate: docs diff plus pytest baseline of 287 passed and 1 skipped using `.venv/Scripts/python.exe -m pytest -q`.
- depends on: nothing.

## L1 — Core data models + error/warning system
- implemented (uncommitted in working tree): Adds typed dataclasses for `DownloadRequest`, `DownloadJob`, `DownloadProgress`, `DownloadResult`, `DownloadFailure`, and the engine-side `EngineCapability`, `EngineDescriptor`, `EngineHealth`, `EngineHealthStatus`, `EngineInputType`, `Header`, `PreflightResult`, plus the `DownloadEngine` Protocol. Header model rejects CR/LF. Validation gate: `tests/test_download_engines.py`, mypy on `firedm/download_engines/{base,models,registry}.py`, and ruff on the same files.
- depends on: L0.

## L2 — Engine interface + registry
- partially implemented (uncommitted): Adds `EngineRegistry`, `EngineConfig` (`schema_version`, `default_engine_id`, `auto_select_enabled`, `disabled_engine_ids`, `per_scheme_preference`, `per_input_type_preference`, `engine_settings`), `create_default_registry`, `select_engine`, and the inert `InternalHTTPDownloadEngine` adapter skeleton whose `start()` returns `ENGINE_NOT_CONNECTED`. `EngineConfig.engine_settings` is `repr=False` so secrets cannot leak through default `repr()`/`str()`. Validation gate: `tests/test_engine_config_and_factory.py`, `tests/test_internal_http_engine.py`, full pytest, ruff, mypy. The legacy `Controller -> brain -> worker` path is still authoritative; nothing in this layer is wired into runtime.
- depends on: L1.

## L3 — Internal engine wired into controller with parity tests
- planned (next safe step): Land a thin handoff inside `Controller._download` that asks the registry for an engine via `select_engine(...)`, calls `engine.preflight(request)`, and falls back to direct `brain(d)` if the engine returns `ENGINE_NOT_CONNECTED`. Block the wire-up behind parity regression tests for resume, segmentation, HLS, fragmented, FTP/SFTP, and proxy paths. Do not delete the legacy path; keep `brain(d)` as the compatibility fallback until adapters cover the parity surface. Validation gate: parity regression tests pass plus existing 287/1 baseline.
- depends on: L1, L2, L8 (preflight) at minimum.

## L4 — Tool discovery + subprocess service
- partially implemented (existing seam): `firedm/tool_discovery.py` resolves PATH and Windows package-store locations; `firedm/ffmpeg_service.py` discovers ffmpeg/ffprobe; `firedm/utils.run_command` forces `shell=False` and splits with `shlex`. Modernization adds an explicit subprocess service that emits argv-only commands, redacts secrets, captures stderr separately, and surfaces typed failure modes. Validation gate: tool-discovery unit tests, redaction regression, and a no-`shell=True` AST grep across new code.
- depends on: L0.

## L5 — aria2c engine
- planned: `Aria2DownloadEngine` performs aria2c executable discovery, version/capabilities probe, localhost-only RPC startup with a random per-session secret, no `--rpc-listen-all`, no `--rpc-allow-origin-all`, no logged secret, and path/scheme validation before queuing each job. The adapter is registered as disabled by default and only becomes selectable after a successful `health_check()`. Validation gate: missing/bad path/version/RPC/redaction/path tests plus parity regression on covered schemes (HTTP, HTTPS, FTP).
- depends on: L1, L2, L3, L4, L8.

## L6 — yt-dlp engine (accessible media only; no DRM)
- planned: `YtDlpDownloadEngine` calls yt-dlp as a Python library to enumerate accessible formats, normalizes them into `Stream`/`MediaPlaylist` shapes via `extractor_adapter`/`playlist_builder`, and refuses DRM-protected media at the model boundary. The engine does not silently use browser cookies; cookie file usage requires an explicit `EngineConfig` flag plus a per-job opt-in. Validation gate: missing fields/no formats/audio/video/merge/redaction tests plus a regression that DRM-marked formats are rejected before download. DRM bypass remains explicitly prohibited in `docs/agent/SECURITY_BOUNDARIES.md`.
- depends on: L1, L2, L3, L4, L7, L8.

## L7 — FFmpeg/ffprobe service
- partially implemented (existing seam): `firedm/ffmpeg_service.py`, `firedm/ffmpeg_commands.py`, and `firedm/extractor_adapter.py` already exist. Modernization moves remaining string-based ffmpeg paths in `video.py` behind argv-list builders, captures both fast and slow-merge command pairs, surfaces typed failure modes back to the engine, and never accepts URLs/filenames/headers as shell-interpolated tokens. Validation gate: extractor fixtures, HLS parser tests, ffmpeg fast/slow fallback tests, plus manual single-video and playlist smoke.
- depends on: L0, L4.

## L8 — URL/header preflight
- partially implemented: `InternalHTTPDownloadEngine.preflight` performs local-only validation (scheme allowlist, header CR/LF rejection via `Header`, output path safety). `Controller._coerce_native_headers()` already drops authorization, proxy-authorization, cookie, and set-cookie. Modernization expands preflight to run before every engine start and to return a typed `PreflightResult` with errors and warnings. Validation gate: preflight unit tests plus header-injection regression.
- depends on: L1.

## L9 — Queue profiles + scheduler
- planned: Extract queue admission and scheduler from `Controller` into a typed service. Profiles control max-concurrent downloads, per-host throttle, retry policy, and engine preference. The service receives `DownloadRequest`, resolves an engine via `select_engine`, and hands a `DownloadJob` to the chosen adapter. Validation gate: queue admission/scheduling tests plus controller lifecycle regression.
- depends on: L1, L3.

## L10 — UI/UX modernization
- planned: Incremental UI work surfaces the engine registry, queue profiles, and preflight diagnostics. Engine dropdown shows `EngineRegistry.descriptors()`. No GUI framework swap. The plan is recorded design-only in `docs/architecture/UI_UX_PLAN.md`. Validation gate: manual GUI smoke plus extracted view-event tests.
- depends on: L8, L9.

## L11 — Persistence + crash-safe state
- planned: Replace direct writes in `setting.py` with a typed persistence service that performs atomic file replace (write-temp-then-rename) for `setting.cfg`, `downloads.dat`, and `thumbnails.dat`. Restored downloads still drop unsafe completion-action keys per existing `setting.load_d_map()` rule. Validation gate: atomic-write tests, restore-after-crash tests, and a no-execute-from-saved-state regression.
- depends on: L1, L9.

## L12 — Build orchestrator (`scripts/release/release_build.ps1`, `.cmd`)
- planned (not implemented): `release_build.ps1` becomes the authoritative entry point for clean/debug/release builds, one-folder/one-file selection, backend `pyinstaller|nuitka|auto`, log capture, manifest emission, checksum generation, and safe smoke checks. `release_build.cmd` is the double-click wrapper. No global Python install, no destructive delete outside repo, no hidden network restore. Validation gate: dry-run script smoke plus artifact layout test.
- depends on: L3 (stable engine surface for smoke), L4 (tool discovery for build-time tools).

## L13 — Release manifest + supply-chain metadata
- planned: Per-release manifest schema captures version, build kind, backend, arch, OS, source commit, dependency snapshot, and asset checksums. CycloneDX JSON 1.x SBOM is emitted alongside the manifest using `cyclonedx-bom` scoped to the release venv. Manifest schema test validates required fields and SBOM presence. Validation gate: manifest schema test plus SBOM presence test.
- depends on: L12.

## L14 — Self-updater (verified, staged, rollback-capable)
- planned (design-only): `docs/architecture/UPDATE_SYSTEM.md`, `docs/security/UPDATER_THREAT_MODEL.md`, and `docs/release/SELF_UPDATER.md` record the intended behavior. The updater fetches public GitHub release metadata over HTTPS, verifies SHA256/digest, stages to a temp folder, backs up current install, replaces via helper, supports rollback, and never auto-runs from cache. Sigstore Cosign blob signing is candidate for a stronger trust gate (decision deferred). Validation gate: no-update / update-available / prerelease-ignored / wrong-asset / checksum-mismatch / interruption / rate-limit / TLS-failure / rollback / cancel tests.
- depends on: L12, L13.

## L15 — Documentation + built-in help
- partially implemented (docs scaffolded): User-facing modernization docs exist as scaffolded plans (`docs/user/USER_GUIDE.md`, `docs/user/BUILT_IN_HELP.md`, `docs/user/TROUBLESHOOTING.md`, `docs/user/ENGINE_SELECTION.md`). Built-in help that surfaces preflight messages, engine selection rationale, and updater status is planned. Validation gate: docs-diff plus `docs/agent/DOCUMENTATION_INDEX.md` completeness check.
- depends on: L10, L14.

## L16 — Multi-agent review pipeline
- implemented (process layer): `docs/agent/MULTI_AGENT_PROTOCOL.md`, `.claude/agents/*.md`, file-lock convention in `docs/agent/SESSION_HANDOFF.md`, and reviewer output format are in place. Reviewers are read-only by default; writes are gated on file locks and orchestrator approval. Validation gate: doc presence plus reviewer-output format check.
- depends on: L0.

## L17 — CI/release pipeline
- partially implemented (existing workflow): `.github/workflows/draft-release.yml` already runs build jobs and gates publish behind a manual step. Modernization tightens the publish gate to require a passing manifest schema test and SBOM presence, and to block on missing release notes. Validation gate: release tests plus workflow review.
- depends on: L12, L13, L14.

## L18 — Legacy compat lane (XP/Vista/7 feasibility)
- blocked: Modern Python on the project floor (`>=3.10,<3.11`) does not target XP/Vista/7. Any legacy lane requires a separate Python version (3.8 for Win 7), separate dependency feasibility report, and real OS validation. Cannot regress the modern lane. Decision deferred until a real test host or VM with each target OS is available. Validation gate: requires real OS smoke; no current modern-lane validation covers it.
- depends on: independent of modern lane; must not weaken modern lane.

## Cross-References
- Master plan + dependency graph: [`docs/architecture/MODERNIZATION_MASTER_PLAN.md`](../architecture/MODERNIZATION_MASTER_PLAN.md).
- Validation commands: [`docs/developer/VALIDATION_PIPELINE.md`](./VALIDATION_PIPELINE.md).
- Security model: [`docs/security/SECURITY_MODEL.md`](../security/SECURITY_MODEL.md).
- Engine contract: [`docs/architecture/ENGINE_PLUGIN_SYSTEM.md`](../architecture/ENGINE_PLUGIN_SYSTEM.md).
- Refactor process: [`docs/agent/REFACTOR_ROADMAP.md`](../agent/REFACTOR_ROADMAP.md).
