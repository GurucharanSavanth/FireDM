# Refactor Roadmap

## Current State Summary
- observed: The app runs through legacy global config plus large controller, GUI, video, download, and utility modules.
- observed: Several safer seams already exist for app paths, tool discovery, ffmpeg discovery, extractor selection, playlist building, command construction, and pipeline logging.
- inferred: Future refactor should expand existing seams instead of replacing the app wholesale.

## Refactor Principles
- Preserve user-visible behavior first.
- Extract one boundary at a time.
- Add regression tests before or with behavior changes.
- Prefer explicit data models for new state.
- Replace stringly events with typed structures only behind compatibility adapters.
- Keep Windows and Linux differences explicit.
- Keep packaging reproducible.

## Non-Goals
- No whole-app rewrite.
- No GUI framework replacement without proof and migration plan.
- No pycurl removal without transport parity evidence.
- No dependency churn for trend reasons.
- No deletion of legacy behavior without compatibility path.
- No platform support claims without validation.
- No security boundary weakening.

## Phase 0: Documentation And Guard Rails
- changed: Create `AGENTS.md`, companion `AGENT.md`, `CLAUDE.md`, `docs/agent/`, and `.claude/agents/` reviewer definitions.
- required: Maintain `PROJECT_MEMORY.md`, `ARCHITECTURE_MAP.md`, and `SESSION_HANDOFF.md`.
- validation: doc diff check, forbidden-reference grep, placeholder grep, required-file checks.

## Phase 1: Architecture Isolation
- changed: Added inert `firedm/download_engines/` typed engine models, health descriptors, and local registry.
- changed: Added `tests/test_download_engines.py` for model/registry invariants.
- target: Extract pre-download validation from `controller.py`.
- target: Extract queue admission/scheduling behind a small service.
- target: Extract GUI event construction behind a view-event boundary.
- validation: direct file, video, missing ffmpeg, duplicate filename, scheduled item, cancel/retry, and completion-action tests.

## Phase 2: Dependency And Packaging Modernization
- target: Keep Python 3.10 support stable while probing later Python versions separately.
- target: Keep `yt-dlp[default]` as primary extractor and `youtube_dl` as optional legacy.
- target: Keep ffmpeg/ffprobe/Deno external unless bundling evidence is recorded.
- validation: dependency preflight, wheel/sdist, Windows payload, installer/portable checks.

## Phase 3: Diagnostics/Doctor/Preflight Foundation
- target: Extend `collect_runtime_diagnostics.py` into a clear doctor/preflight path.
- target: Keep redaction in `pipeline_logger.py`.
- target: Report ffmpeg, ffprobe, Deno, extractor, settings path, and package health separately.
- validation: diagnostics unit tests and redaction regression tests.

## Phase 4: Download Engine Reliability
- target: Keep `brain.py` and `worker.py` behavior stable while isolating worker runner and segment merge state.
- target: Make resume/range behavior testable without live network.
- target: Keep pycurl protocol restrictions.
- validation: mocked pycurl/segment tests, direct download handoff tests, manual cancel/resume smoke.

## Phase 5: Video Workflow Modernization
- target: Split stream selection into pure helpers.
- target: Split HLS parser logic from network/file effects.
- target: Move ffmpeg process execution behind a runner that accepts argv lists.
- validation: extractor fixtures, HLS parser tests, ffmpeg fast/slow fallback tests, manual single-video and playlist smoke.

## Phase 6: Safe Browser Handoff
- target: Keep browser integration disabled by default.
- target: Keep local-only authenticated handoff.
- target: Reuse controller/queue path.
- target: Reject unsafe schemes and sensitive headers.
- validation: browser integration tests, local auth tests, manual browser extension smoke only after explicit enablement.

## Phase 7: Release Automation
- target: Keep build-code naming consistent across Windows and Linux lanes.
- target: Keep release publishing dry-run by default.
- target: Keep signing and bundling claims evidence-backed.
- validation: release tests, payload validation, installer validation, manifest/checksum verification.

## Phase 8: Regression Hardening
- target: Expand tests around controller lifecycle, download state, playlist normalization, HLS, ffmpeg, settings, and packaging.
- target: Keep manual validation checklist for GUI and live workflows.
- validation: full pytest, scoped ruff, mypy, manual smoke checklist.

## Validation Per Phase
| Phase | Minimum Validation |
| --- | --- |
| 0 | docs validation only |
| 1 | controller/download handoff tests |
| 2 | dependency preflight plus package build checks |
| 3 | diagnostics and redaction tests |
| 4 | segment/resume tests plus manual smoke |
| 5 | extractor/HLS/ffmpeg tests plus manual video smoke |
| 6 | browser/native tests plus manual enabled-path smoke |
| 7 | release tests plus artifact validation |
| 8 | full suite plus manual release checklist |

## Rollback Strategy
- Keep changes narrow enough to revert by file or feature slice.
- Preserve old path behind compatibility facade until tests cover replacement path.
- Do not remove legacy flags or settings without migration.
- For packaging, keep previous validated artifact lane until new lane passes validation.

## Stop Conditions
- Stop if a change requires broad rewrite.
- Stop if validation cannot prove behavior preservation.
- Stop if a security boundary would be weakened.
- Stop if a platform claim cannot be tested.
- Stop if user-owned dirty changes block safe merge.
