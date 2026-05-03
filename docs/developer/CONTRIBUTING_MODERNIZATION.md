# Contributing Modernization

Status: changed 2026-05-02.

## Ground Rules
- implemented: `AGENTS.md` is primary authority for agents.
- implemented: Use local files as source of truth; online docs only verify external tool syntax/support.
- implemented: Treat dirty changes as user-owned unless made in the current session.
- planned: Extract one boundary at a time and keep legacy behavior until replacement tests pass.

## First Seams
- implemented: Typed engine models and registry live in `firedm/download_engines/`.
- planned: Next patch wraps current internal pycurl path with an adapter without changing controller behavior.
- blocked: Do not add new dependencies or build lanes without updating toolchain docs.
