# Modernization Master Plan

Status: changed 2026-05-02.

This document is the authoritative status table and dependency graph for the
FireDM modernization program. Per-layer narrative lives in
[`docs/developer/IMPLEMENTATION_LAYERS.md`](../developer/IMPLEMENTATION_LAYERS.md).
Per-tool decision records live in
[`docs/architecture/TOOLCHAIN_DECISIONS.md`](./TOOLCHAIN_DECISIONS.md).

## Purpose
- planned: Modernize the legacy `Controller -> brain -> worker` engine path while preserving user-visible behavior.
- planned: Land changes one layer at a time with parity tests before any byte-moving code path is replaced.
- implemented: Keep `Controller`, `tkview`, `brain`, `worker`, and `video` as the working facade until adapters are tested.

## Layer Status Table
| Layer | Title | Status | Authoritative artifacts | Validation gate |
| --- | --- | --- | --- | --- |
| L0 | Safety baseline + decision records | implemented (this run) | `AGENTS.md`, `AGENT.md`, `CLAUDE.md`, `docs/agent/`, `docs/architecture/MODERNIZATION_MASTER_PLAN.md`, `docs/architecture/TOOLCHAIN_DECISIONS.md`, `docs/developer/IMPLEMENTATION_LAYERS.md`, `docs/developer/VALIDATION_PIPELINE.md`, `docs/security/SECURITY_MODEL.md`, `docs/release/COMPATIBILITY_MATRIX.md` | docs diff + grep + pytest baseline 287 passed, 1 skipped |
| L1 | Core data models + error/warning system | implemented (uncommitted in working tree) | `firedm/download_engines/models.py`, `firedm/download_engines/base.py`, `firedm/download_engines/__init__.py`, `tests/test_download_engines.py` | targeted pytest, ruff, mypy on `firedm/download_engines/` |
| L2 | Engine interface + registry | partially implemented (uncommitted) | `firedm/download_engines/registry.py`, `firedm/download_engines/config.py`, `firedm/download_engines/factory.py`, `firedm/download_engines/internal_http.py`, `tests/test_engine_config_and_factory.py`, `tests/test_internal_http_engine.py` | full pytest, mypy, ruff scoped to engine package |
| L3 | Internal engine wired into controller with parity tests | planned (next safe step) | future: `firedm/controller.py` thin handoff, parity regression tests | parity tests for resume, segmentation, HLS, fragmented, FTP/SFTP, proxy paths before any wire-up |
| L4 | Tool discovery + subprocess service | partially implemented (existing seam) | `firedm/tool_discovery.py`, `firedm/ffmpeg_service.py`, `firedm/utils.run_command` | tool-discovery unit tests + redaction tests |
| L5 | aria2c engine | planned | future: `firedm/download_engines/aria2.py`, aria2c discovery, RPC client | aria2c missing/bad path/version/RPC/redaction/path tests |
| L6 | yt-dlp engine (accessible media only; no DRM) | planned | future: `firedm/download_engines/ytdlp.py`, normalization adapter | yt-dlp missing fields/no formats/audio/video/merge/redaction tests |
| L7 | FFmpeg/ffprobe service | partially implemented (existing seam) | `firedm/ffmpeg_service.py`, `firedm/ffmpeg_commands.py`, `firedm/extractor_adapter.py` | extractor fixtures, HLS parser tests, ffmpeg fast/slow fallback tests |
| L8 | URL/header preflight | partially implemented | `firedm/download_engines/internal_http.preflight`, `firedm/controller._coerce_native_headers`, header CR/LF rejection in `models.Header` | preflight unit tests, header injection regression |
| L9 | Queue profiles + scheduler | planned | future: queue admission service extracted from `controller` | queue admission/scheduling tests |
| L10 | UI/UX modernization | planned | `docs/architecture/UI_UX_PLAN.md` (design-only) | manual GUI smoke + extracted view-event tests |
| L11 | Persistence + crash-safe state | planned | future: typed persistence service replacing direct `setting.py` writes | atomic-write tests, restore-after-crash tests |
| L12 | Build orchestrator (`scripts/release/release_build.ps1`, `.cmd`) | planned | `docs/release/BUILD_SYSTEM.md` | dry-run build script smoke + artifact layout tests |
| L13 | Release manifest + supply-chain metadata | planned | `docs/architecture/TOOLCHAIN_DECISIONS.md` (CycloneDX, Cosign rows) | manifest schema test, SBOM presence test |
| L14 | Self-updater (verified, staged, rollback-capable) | planned (design-only) | `docs/architecture/UPDATE_SYSTEM.md`, `docs/security/UPDATER_THREAT_MODEL.md`, `docs/release/SELF_UPDATER.md` | updater no-update / available / wrong-asset / checksum-mismatch / interrupt / rate-limit / TLS-failure / rollback / cancel tests |
| L15 | Documentation + built-in help | partially implemented (docs scaffolded) | `docs/user/USER_GUIDE.md`, `docs/user/BUILT_IN_HELP.md`, `docs/user/TROUBLESHOOTING.md`, `docs/user/ENGINE_SELECTION.md` | docs-diff + index completeness |
| L16 | Multi-agent review pipeline | implemented (process layer) | `docs/agent/MULTI_AGENT_PROTOCOL.md`, `.claude/agents/*.md` | doc presence + reviewer-output format check |
| L17 | CI/release pipeline | partially implemented (existing workflow) | `.github/workflows/draft-release.yml`, `scripts/release/` | release tests + workflow review |
| L18 | Legacy compat lane (XP/Vista/7 feasibility) | blocked | `docs/release/COMPATIBILITY_MATRIX.md`, `docs/release/WINDOWS_LEGACY_SUPPORT.md` | requires real OS validation; not gated on modern lane |

## Dependency Graph
- L0 must precede every later layer. Decision records are the gate.
- L1 is precondition for L2, L3, L5, L6, L7 (they all depend on the typed model and error/warning system).
- L2 is precondition for L3, L5, L6 (registry + config + factory).
- L3 is the integration gate. L5 and L6 must not wire byte-moving paths into runtime before L3 lands a thin handoff with parity regression tests.
- L4 underpins L5, L6, L7 (any external-tool engine needs the discovery and subprocess service).
- L7 underpins L6 (yt-dlp engine surfaces post-process needs back through ffmpeg service).
- L8 underpins L3, L5, L6 (preflight runs before any engine start).
- L9 depends on stable L1 model (`DownloadJob`/`DownloadRequest`) plus L3 wired engine.
- L10 depends on L9 and L8 because it surfaces queue profiles, engine selection dropdown, and preflight diagnostics.
- L11 depends on stable L1 typed models and L9 queue model.
- L12 depends on a stable engine surface (L3 minimum). Manifest layout requires the model surface from L1 + L13.
- L13 depends on L12 (manifest emission inside the orchestrator).
- L14 depends on L12 + L13 (signed/checked release artifacts before staged self-update).
- L15 depends on L10 + L14 (built-in help references stable UI and updater behavior).
- L16 is process-only and gates every layer. Already implemented.
- L17 depends on L12 + L13 + L14 stability before publish gating tightens.
- L18 is intentionally out-of-band. It must not regress modern lane.

## Status Labels
- implemented: code or docs land in working tree and tests pass.
- partially implemented: seam exists or design recorded; runtime not wired yet.
- planned: scope agreed; not in working tree.
- blocked: cannot proceed without external evidence (e.g., real legacy-OS host, SBOM tooling install policy, signing identity decision).

## Cross-References
- Per-layer narrative: [`docs/developer/IMPLEMENTATION_LAYERS.md`](../developer/IMPLEMENTATION_LAYERS.md).
- Validation pipeline: [`docs/developer/VALIDATION_PIPELINE.md`](../developer/VALIDATION_PIPELINE.md).
- Security model: [`docs/security/SECURITY_MODEL.md`](../security/SECURITY_MODEL.md).
- Updater threat model: [`docs/security/UPDATER_THREAT_MODEL.md`](../security/UPDATER_THREAT_MODEL.md).
- Engine plugin contract: [`docs/architecture/ENGINE_PLUGIN_SYSTEM.md`](./ENGINE_PLUGIN_SYSTEM.md).
- Modern architecture target: [`docs/architecture/MODERN_ARCHITECTURE.md`](./MODERN_ARCHITECTURE.md).
- Compatibility matrix: [`docs/release/COMPATIBILITY_MATRIX.md`](../release/COMPATIBILITY_MATRIX.md).
- Build system plan: [`docs/release/BUILD_SYSTEM.md`](../release/BUILD_SYSTEM.md).
- Refactor roadmap (process): [`docs/agent/REFACTOR_ROADMAP.md`](../agent/REFACTOR_ROADMAP.md).

## Update Rules
- Update the status column when a layer transitions states.
- Do not promote `release_build.ps1`, the self-updater, aria2c, or yt-dlp adapters past `planned` before their files exist and tests pass.
- Keep the dependency graph monotonic — if a precondition regresses, downstream layer status downgrades.
