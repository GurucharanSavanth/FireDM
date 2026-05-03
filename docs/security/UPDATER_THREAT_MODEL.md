# Updater Threat Model

Status: changed 2026-05-02.

## Assets
- planned: Release metadata, release asset, checksum/digest, local staged download, current install folder, user config, and user downloads.

## Threats
- planned: Wrong asset selection, downgrade, prerelease surprise, checksum mismatch, interrupted download, TLS failure, rate limit, malicious mirror/cache, partial replacement, and rollback failure.

## Controls
- planned: HTTPS-only GitHub API, public unauthenticated metadata by default, newer-version check, platform/architecture match, SHA256/digest validation, temp staging, backup, restart/helper replacement, rollback, and no auto-run from cache.
- blocked: No updater code exists yet.
