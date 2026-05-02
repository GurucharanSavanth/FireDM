# Multi-Agent Protocol

## Primary Orchestrator Rule
- required: Codex is primary orchestrator for this repo unless the human explicitly assigns that role elsewhere.
- required: Codex owns scope, file locks, diff review, validation, and final reporting.
- required: Reviewer agents inspect and report by default; they do not write.

## Agent Roles
| Role | Default Mode | Scope |
| --- | --- | --- |
| Codex Orchestrator | write with locks | task decomposition, final edits, validation, report |
| Claude Architecture Reviewer | read-only | `.claude/agents/architecture-reviewer.md`; map subsystem coverage and unsupported claims |
| Claude Security Reviewer | read-only | `.claude/agents/security-reviewer.md`; path, subprocess, cookie/header, browser, diagnostics, packaging risks |
| Claude Documentation Reviewer | read-only | `.claude/agents/documentation-reviewer.md`; contradiction, redundancy, missing local-source rules |
| Claude Validation Reviewer | read-only | `.claude/agents/validation-reviewer.md`; command map and validation gaps |

## Parallelism Rules
- Parallel work is read-only unless the lock table grants exactly one write file to exactly one agent.
- Parallel reviewers must inspect different concerns, not rewrite the same text.
- No nested agent spawning.
- No reviewer can run destructive commands, publish, push, install global tools, or delete Markdown.

## Read-Only Parallel Review Pattern
1. Codex prepares a context package.
2. Reviewer inspects assigned files only.
3. Reviewer returns structured findings only.
4. Codex reconciles findings.
5. Codex performs final edits and validation.

## Sequential Write Pattern
1. Codex records a file lock.
2. One agent receives one file set.
3. Agent writes only assigned files.
4. Codex reviews diff.
5. Codex either accepts, adjusts, or reverts only that agent's changes.

## File Ownership Locks
Use this table format in `docs/agent/SESSION_HANDOFF.md`:

| File | Owner | Mode | Status | Reason |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | Codex | write | locked | primary rules |
| `docs/agent/SECURITY_BOUNDARIES.md` | Claude Security Reviewer | read-only | assigned | security review |

## Conflict Prevention
- One write owner per file.
- No overlapping write globs.
- No broad "all docs" edit delegation.
- No file delete delegation.
- Codex must inspect `git diff --name-status` before and after external writes.

## Context Package Format
Provide reviewers:
- objective
- local working tree rule
- network source ban
- allowed files to inspect
- files not to edit
- exact output format
- evidence label requirement
- stop conditions

## Reviewer Output Format
- Scope reviewed
- Files inspected
- Observed facts
- Issues found
- Severity
- Evidence
- Recommended change
- Files affected
- Required or optional
- Unclear or blocked items

## Limit/Interruption Recovery
- Record stop reason in `docs/agent/SESSION_HANDOFF.md`.
- Preserve partial output when available.
- Mark completed and pending sections.
- Continue with remaining sections only.
- If the same reviewer is unavailable, Codex continues and marks that review pass blocked.

## Prohibited Delegation
- "Rewrite all docs."
- "Fix everything."
- App code refactors during documentation tasks.
- Global installs.
- Publish or push operations.
- History rewrite.
- Secret handling.
- Deleting Markdown.
- Running live downloads unless explicitly approved for validation.
- Asking Claude reviewer agents to edit files or run commands.

## Allowed Delegation
- Read-only review of `AGENTS.md` for local-source constraints.
- Read-only review of `SECURITY_BOUNDARIES.md` for unsafe omissions.
- Read-only review of `ARCHITECTURE_MAP.md` against inspected source files.
- Read-only review of `VALIDATION_MATRIX.md` against local config files.
- Non-interactive Claude CLI review with `--print`, `--tools "Read,Grep,Glob"`, and explicit "do not edit" instructions.

## Kill Switch Conditions
- Reviewer attempts broad writes.
- Reviewer requests global install or publish.
- Reviewer reads secrets unnecessarily.
- Reviewer proposes bypassing security boundaries.
- Reviewer edits outside locked files.
- Reviewer output makes unsupported claims.

## Merge/Reconciliation Rules
- Codex preserves useful findings with evidence labels.
- Unsupported reviewer claims are dropped or marked inferred.
- Final docs must use relative local paths only.
- Final validation belongs to Codex.
