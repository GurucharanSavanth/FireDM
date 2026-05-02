# Claude Code Instructions

## Local Project Context
- observed: This is a local FireDM checkout with Python/Tkinter GUI, CLI mode, pycurl transport, yt-dlp extraction, ffmpeg post-processing, plugin modules, and release scripts.
- observed: `AGENTS.md` is the primary Codex-facing authority. `AGENT.md` is a companion file.
- observed: Deeper repo-local memory and maps live in `docs/agent/`.
- observed: If this file conflicts with `AGENTS.md` during Codex execution, `AGENTS.md` wins unless the user explicitly invokes Claude-specific workflow.

## Claude-Specific Operating Rules
- Claude is reviewer-first unless explicitly assigned implementation.
- Read local files before giving architecture or code-change advice.
- Treat network project pages as non-authoritative for this checkout.
- Do not delete, rewrite, or replace Markdown without preserving useful local content.
- Do not alter application code during documentation-only tasks.
- Do not push, publish, rewrite history, globally install tools, or edit outside the repo.
- Do not edit files unless a file lock grants write ownership.
- Claude project memory must not contain secrets.

## Subagent Use Rules
- Default subagent mode is read-only review.
- Subagents must not spawn nested subagents.
- Subagents must not edit files unless Codex or the human assigns one locked file set.
- Subagents must return findings, evidence, and recommended changes; Codex reconciles diffs.
- Orchestration must happen from the main Codex or Claude session, not from nested subagents.
- Follow `docs/agent/MULTI_AGENT_PROTOCOL.md`.

## Read-Only Review First
- Architecture review inspects `firedm/`, `scripts/`, `tests/`, `docs/`, and `pyproject.toml`; it flags unsupported claims.
- Security review inspects path, subprocess, cookie/header, browser, diagnostics, persistence, and packaging surfaces; it flags unsafe omissions.
- Documentation review inspects `AGENT.md`, `AGENTS.md`, `CLAUDE.md`, and `docs/agent/`; it flags duplicate or conflicting rules.

## No Autonomous Broad Writes
- Do not accept prompts such as "rewrite all docs" or "fix everything" without a file lock plan.
- Do not edit overlapping file groups in parallel.
- Do not delete Markdown files as a reviewer.

## When To Use Opus/Sonnet/Haiku If Available
- Use Opus for high-risk architecture, security, or release-gate review.
- Use Sonnet for normal documentation consistency and bounded refactor review.
- Use Haiku for narrow grep summaries, table cleanup, or formatting review.
- If model selection is unavailable, continue with current model and record the limitation.

## How To Continue After Limit/Interruption
- Write partial state to `docs/agent/SESSION_HANDOFF.md`.
- Record completed steps, files read, files changed, validation run, pending steps, stop reason, and next safe command.
- Resume from recorded state. Do not restart from scratch unless the handoff is stale and local discovery proves it.
- If write access is not granted, return a continuation packet with the same fields instead of editing `SESSION_HANDOFF.md`.

## Evidence Reporting
- Use labels: observed, preserved, changed, verified, inferred, assumed, blocked, reverted.
- Do not claim commands ran unless executed in this session or pasted as evidence by the orchestrator.
- Mark unverified architecture areas explicitly.

## Final Output Format
- Findings first for reviews, ordered by severity with file/line evidence.
- For implementation tasks, report changed files, validation commands, failures, remaining risk, and next safe step.
- Keep output concise; link local files by relative path in Markdown docs and by absolute clickable paths in chat when useful.

## Reference
- Multi-agent process: `docs/agent/MULTI_AGENT_PROTOCOL.md`.
