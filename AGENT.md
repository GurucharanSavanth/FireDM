# FireDM Agent Companion

## Authority
- `AGENTS.md` is the primary Codex-facing instruction file.
- Read `AGENTS.md` first.
- If this file conflicts with `AGENTS.md`, `AGENTS.md` wins.
- This file exists for tools or humans that look for singular `AGENT.md`; it is a companion, not the primary authority.

## Essential Rules
- The local working directory is the only source of truth.
- Do not use any online repository as project authority.
- Inspect local files before editing or claiming behavior.
- Preserve user-owned dirty-tree changes.
- Do not modify application source code during documentation/instruction hardening tasks.
- Do not delete or replace Markdown before reading it and preserving useful local content.
- Do not run destructive commands, push, publish, rewrite history, globally install tools, change system PATH, or delete user data.
- Use evidence labels: observed, preserved, changed, verified, inferred, assumed, blocked, reverted.

## Local References
- Primary rules: `AGENTS.md`
- Claude rules: `CLAUDE.md`
- Project memory: `docs/agent/PROJECT_MEMORY.md`
- Architecture map: `docs/agent/ARCHITECTURE_MAP.md`
- Multi-agent protocol: `docs/agent/MULTI_AGENT_PROTOCOL.md`
- Security boundaries: `docs/agent/SECURITY_BOUNDARIES.md`
- Validation matrix: `docs/agent/VALIDATION_MATRIX.md`
- Documentation inventory: `docs/agent/DOCUMENTATION_INDEX.md`

## Continuation
- Resume from `AGENTS.md`, then `docs/agent/SESSION_HANDOFF.md`.
- If a prior agent stopped due to limits, continue only from recorded completed/pending state.
