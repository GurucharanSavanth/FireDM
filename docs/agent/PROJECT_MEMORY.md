# Project Memory

## Current Project Identity
- observed: `pyproject.toml` names the project `FireDM`.
- observed: `pyproject.toml` describes a multi-connection download manager with Tkinter GUI, CLI mode, pycurl transport, and ffmpeg post-processing.
- observed: Runtime package is `firedm/`; launcher files are `firedm.py` and `firedm/__main__.py`.
- preserved: Prior `AGENTS.md` recorded Windows 10/11 x64 plus Python `3.10.11` as the known good baseline.

## Current Architecture Summary
- observed: `firedm/FireDM.py` parses CLI args, selects GUI or command mode, loads settings, and exposes import diagnostics.
- observed: `firedm/controller.py` owns app orchestration, queue handoff, view updates, ffmpeg checks, native messaging endpoint, and download lifecycle entry points.
- observed: `firedm/tkview.py` contains the large Tkinter GUI and many widget classes.
- observed: `firedm/brain.py`, `firedm/worker.py`, and `firedm/downloaditem.py` implement segmented download state, worker execution, and merge/progress behavior.
- observed: `firedm/video.py` owns extractor calls, stream selection, HLS/subtitles, ffmpeg execution, metadata writing, and `Video`/`Stream` models.
- observed: Modernized seams include `app_paths.py`, `ffmpeg_service.py`, `tool_discovery.py`, `extractor_adapter.py`, `playlist_builder.py`, `playlist_entry.py`, `ffmpeg_commands.py`, and `pipeline_logger.py`.
- changed: `firedm/download_engines/` now contains inert typed download-engine models, protocol, health descriptors, and registry.

## Current Tooling Summary
- observed: Python version range in `pyproject.toml` is `>=3.10,<3.11`.
- observed: Test runner is `pytest`; config lives in `pyproject.toml`.
- observed: Ruff and mypy are scoped to modernized seams, not the entire legacy tree.
- changed: `pyproject.toml` now includes `firedm/download_engines/base.py`, `models.py`, and `registry.py` in the scoped mypy file list.
- observed: Release scripts live under `scripts/release/`; Windows wrapper is `build-release.bat`; PowerShell wrapper is `scripts/windows-build.ps1`.
- observed: Linux lane files exist: `scripts/linux-build.sh`, `scripts/firedm-linux.spec`, `scripts/release/build_linux.py`, and release docs under `docs/release/`.
- observed: `.gitignore` uses a catch-all ignore pattern; instruction docs must be explicitly allowlisted to become trackable.

## Known Constraints
- observed: README and docs state Python 3.10 is the verified runtime.
- observed: Full GUI, live downloads, live playlist behavior, and live ffmpeg post-processing need manual validation.
- observed: `README.md` and some human-facing docs contain network links; agent docs must not treat those links as authority.
- observed: Worktree may contain user-owned dirty files. Preserve them.

## Known Risks
- observed: `controller.py`, `tkview.py`, `video.py`, `brain.py`, and `utils.py` remain large stateful modules.
- observed: `utils.run_command()` still accepts string commands but forces `shell=False` and splits with `shlex`.
- observed: `video.py` builds some ffmpeg command strings before subprocess handoff.
- observed: Plugin modules exist and default disabled, but future work must not overclaim browser integration, protocol expansion, anti-detection, or DRM behavior.
- observed: Browser/native messaging uses local pipe/socket auth and rejects non-HTTP download URLs; future endpoint work must keep strict local auth.

## Refactor Direction
- inferred: Keep `Controller` as facade while extracting validation, queue scheduling, view events, and completion actions.
- inferred: Split pure stream/HLS parsing from network and file effects before changing live video behavior.
- inferred: Move subprocess creation toward argv-list builders and narrow runners.
- inferred: Keep transport parity tests before any pycurl replacement is considered.
- changed: The first engine-modernization patch adds only a registry/model seam; it does not replace legacy controller, brain, worker, or GUI behavior.

## Modernization Program Baseline
- changed: Added architecture, release, user, security, and developer docs for the phased modernization plan.
- changed: Recorded official-doc-backed toolchain decisions in `docs/architecture/TOOLCHAIN_DECISIONS.md`.
- changed: Recorded OS support claims in `docs/release/COMPATIBILITY_MATRIX.md`; XP/Vista/7 are not modern-lane targets.
- changed: Added `tests/test_download_engines.py` for model and registry invariants.

## Completed Documentation Rebuild Decisions
- changed: Added `AGENT.md`, `AGENTS.md`, `CLAUDE.md`, and `docs/agent/` guidance set.
- changed: `AGENTS.md` is the primary Codex/general-agent instruction file.
- changed: `AGENT.md` is a companion file for tools or humans that look for the singular filename.
- changed: `CLAUDE.md` constrains Claude Code to read-only review unless a file lock grants a bounded write.
- changed: `.claude/agents/` contains read-only Claude reviewer definitions for architecture, security, documentation, and validation.
- preserved: Prior `AGENTS.md` facts about baseline commands, modernized seams, packaging state, and gotchas are carried into primary `AGENTS.md`, companion `AGENT.md`, this file, `ARCHITECTURE_MAP.md`, and `VALIDATION_MATRIX.md`.

## Unverified Items
- blocked: No full line-by-line review of every source file was performed during the documentation rebuild.
- blocked: No live GUI, real download, real playlist, or real ffmpeg post-processing smoke was run for this documentation-only task.
- blocked: Linux build lane was mapped from local scripts/docs but not executed on this Windows host.
- blocked: `markdownlint` and Prettier were not detected as configured repo tools.
- blocked: Repo-local `.claude/agent-memory/` was not created because local Claude help and local plugin references did not verify that as a native project memory layout. Use this file as the auditable repo-local memory source.

## Update Rules
- Update this file after significant architecture, security, packaging, dependency, or validation changes.
- Record only local evidence or clearly marked inference.
- Move stale conclusions to an explicit blocked or superseded note instead of deleting context silently.
- Keep network project pages out of this agent memory.
