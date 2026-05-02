# 02 Scripts Changed

## New Scripts

- changed: `scripts/release/build_id.py` implements parsing, validation, discovery, next-ID selection, tag/title generation, and CLI JSON output.
- changed: `scripts/release/github_release.py` implements safe GitHub release dry-run/publish planning and artifact verification.

## Updated Scripts

- changed: `scripts/release/common.py` adds build-ID metadata and build-ID artifact naming helpers.
- changed: `scripts/release/build_windows.py` selects one build ID, passes it through payload/installer/license/checksum steps, writes build-ID manifest/notes, and sets signing required for stable.
- changed: `scripts/release/build_payload.py` forwards the selected build ID into the legacy PowerShell package path and writes build-ID portable ZIPs.
- changed: `scripts/release/build_installer.py` writes build-ID installer EXE and sidecar metadata.
- changed: `scripts/release/collect_licenses.py` writes `license-inventory_<build_id>.json` plus compatibility alias.
- changed: `scripts/release/generate_checksums.py` writes `SHA256SUMS_<build_id>.txt` plus compatibility alias and only checksums current build-ID artifacts.
- changed: `scripts/windows-build.ps1` accepts `-BuildId`, `-BuildDate`, and overwrite/discovery switches; resolves build IDs through `scripts/release/build_id.py`; writes packaged `build-metadata.json`; and names release packages, manifest, checksums, notes, tag, and title with the build ID.
- changed: `build-release.bat` forwards extra args such as `--date` and `--build-id` and avoids fragile `findstr` argument detection.

## Compatibility Aliases

- changed: canonical build-ID files are primary.
- changed: `dist/release-manifest.json`, `dist/release-body.md`, `dist/checksums/SHA256SUMS.txt`, and `dist/licenses/license-inventory.json` remain latest-build aliases.
