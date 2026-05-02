# FireDM Agent Instructions

## Primary Authority
- This file is the primary instruction file for Codex and other agents that load `AGENTS.md`.
- The local working directory is the only source of truth.
- Do not use any online repository as project authority.
- Read `AGENTS.md` before `AGENT.md` or any `docs/agent` file.
- If `AGENT.md` conflicts with `AGENTS.md`, `AGENTS.md` wins.
- If `CLAUDE.md` conflicts with `AGENTS.md` during Codex execution, `AGENTS.md` wins unless the user explicitly invokes a Claude-specific workflow.
- Treat dirty working-tree changes as user-owned unless you made them in the current session.

## Local Discovery First
Run and record local evidence before broad changes:

```powershell
pwd
git status --short --branch
git branch --show-current
git log -1 --oneline
python --version
python -c "import sys, platform; print(sys.version); print(platform.platform()); print(sys.platform)"
rg --files
rg --files -g "*.md"
```

## No Online Project Authority
- Network pages, remotes, package indexes, and old prompts are not source of truth for this checkout.
- Local files decide architecture, commands, branch state, tests, packaging, and behavior.
- External official tool docs may be used only to verify tool syntax, not to define this project.

## Markdown Safety
- Read existing Markdown before replacing it.
- Preserve useful project-specific facts before redirecting or replacing stale docs.
- Do not delete Markdown in this repo unless preservation, rationale, and diff review are complete.
- Keep agent docs free of project-authority network links.
- Keep human docs and artifact docs unchanged unless a task requires targeted updates.

## Protected Scope
- This documentation/instruction layer may change: `AGENTS.md`, `AGENT.md`, `CLAUDE.md`, `docs/agent/`, `.claude/agents/`, and `.gitignore` allowlist entries needed to track those files.
- Do not modify application source code during documentation hardening tasks.
- Do not run publish, push, release upload, history rewrite, global install, system PATH edit, broad delete, or user-data delete commands.
- Never revert user-owned changes without explicit instruction.

## Local References
- Project memory: `docs/agent/PROJECT_MEMORY.md`.
- Continuation state and file locks: `docs/agent/SESSION_HANDOFF.md`.
- Architecture map: `docs/agent/ARCHITECTURE_MAP.md`.
- Multi-agent protocol: `docs/agent/MULTI_AGENT_PROTOCOL.md`.
- Security boundaries: `docs/agent/SECURITY_BOUNDARIES.md`.
- Validation command map: `docs/agent/VALIDATION_MATRIX.md`.
- Full Markdown inventory: `docs/agent/DOCUMENTATION_INDEX.md`.

## Architecture Map
- observed: Runtime package is `firedm/`.
- observed: Startup is `firedm/FireDM.py`, CLI module is `firedm/__main__.py`, launcher shim is `firedm.py`.
- observed: Large legacy hot spots include `firedm/controller.py`, `firedm/tkview.py`, `firedm/video.py`, `firedm/brain.py`, and `firedm/utils.py`.
- observed: Modernized seams include `app_paths.py`, `tool_discovery.py`, `ffmpeg_service.py`, `extractor_adapter.py`, `playlist_builder.py`, `playlist_entry.py`, `ffmpeg_commands.py`, and `pipeline_logger.py`.
- Use `docs/agent/ARCHITECTURE_MAP.md` before refactors. Update it when subsystem ownership changes.

## Refactor Policy
- Modernization means measurable simplification, behavior preservation, explicit data flow, safer subprocess/path handling, clearer diagnostics, reproducible packaging, and documented platform differences.
- Modernization does not mean whole-app rewrites, GUI-framework swaps, dependency churn, deleting legacy behavior without migration, or claiming support without validation.
- Keep `Controller` as compatibility facade until extracted services are covered by tests.

## Dependency And Platform Policy
- observed: `pyproject.toml` limits verified Python to `>=3.10,<3.11`.
- observed: Windows x64 is the best validated lane; Linux scripts/docs exist but need Linux or WSL validation.
- observed: `yt-dlp[default]` is primary extractor; `youtube_dl` is optional legacy.
- observed: `pycurl` remains runtime transport; do not remove without transport parity proof.
- observed: ffmpeg, ffprobe, and Deno are external by default unless release docs prove bundling.

## Multi-Agent Rules
- Codex is primary orchestrator unless the human explicitly assigns another orchestrator.
- Other models and Claude subagents are read-only reviewers by default.
- No nested agent spawning.
- No broad rewrite delegation.
- No parallel writes to overlapping files.
- Use file locks in `docs/agent/SESSION_HANDOFF.md` before any delegated write.
- Codex reviews and validates final diffs.
- See `docs/agent/MULTI_AGENT_PROTOCOL.md`.

## Claude Rules
- `CLAUDE.md` applies when Claude Code is explicitly used.
- `.claude/agents/*.md` reviewer agents are findings-only and read-only by default.
- Claude project memory must not contain secrets.
- If Claude reaches a limit, it must return a continuation packet or update `docs/agent/SESSION_HANDOFF.md` when granted write ownership.

## Security Boundaries
- Follow `docs/agent/SECURITY_BOUNDARIES.md`.
- Prohibited: DRM bypass, protected-media circumvention, license-server bypass, media-key extraction, browser credential theft, silent cookie harvesting, arbitrary local file reads, public local API bind by default, shell execution by default, path traversal, unsafe deserialization, saved-state execution, and secret leakage.
- Do not weaken browser/native handoff, cookie/header, diagnostic redaction, subprocess, path, or packaging-secret rules.

## Validation
After documentation changes, run at minimum:

```powershell
git diff --check
rg <forbidden-project-authority-pattern> AGENTS.md AGENT.md CLAUDE.md docs/agent .claude/agents
rg <placeholder-pattern> AGENTS.md AGENT.md CLAUDE.md docs/agent .claude/agents
```

Also verify required docs exist, `docs/agent/DOCUMENTATION_INDEX.md` lists every Markdown file, authority terms do not contradict, and `git diff --name-only` shows no application-code edits for documentation-only tasks. For the full validation command map, see `docs/agent/VALIDATION_MATRIX.md`.

## Evidence Labels
- observed: seen in local files or command output.
- preserved: old local content retained or migrated.
- changed: modified in the current task.
- verified: validation command ran and output was observed.
- inferred: reasoned from inspected local evidence.
- assumed: not verified; must be explicit.
- blocked: could not inspect or validate.
- reverted: change removed because unnecessary or unsafe.

## Stop Conditions
- Stop before destructive commands, broad deletion, push/publish, history rewrite, global install, system PATH edit, or writes outside repo.
- Stop if credentials appear in Markdown.
- Stop if required writes are blocked or user-owned changes cannot be merged safely.
- Stop if a claim would require full line-by-line review that was not performed.

## Final Report
Report repo state, prior output audit, discovery, authority model, Claude/multi-agent implementation, Markdown alignment, `.gitignore` audit, files changed, validation, remaining risks, next safe command, and commit message.
