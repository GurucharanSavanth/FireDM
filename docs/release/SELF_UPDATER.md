# Self-Updater

Status: changed 2026-05-02.

## Implemented
- blocked: No in-app updater implementation exists in this phase.

## Planned UI
- planned: `Check for updates` button, current version, latest version, release notes preview, download progress, verify progress, install/restart prompt, and clear failure text.

## Planned Metadata
- planned: Configured release owner/repo/source, defaulting only when local settings/docs explicitly choose it.
- planned: `GET /repos/{owner}/{repo}/releases/latest` for stable checks; prereleases ignored by default.
- planned: Use release asset `digest` when present or a release manifest checksum.

## Planned Install
- planned: Stage to temp, verify, backup current folder, replace on restart/helper, preserve user config, never delete downloads.
- planned: Roll back on helper failure.
- blocked: No helper, manifest signature, or UI tests yet.
