# 03 Version Upgrade Repair Review

Evidence labels: observed, changed, verified.

## Previous Risk
- observed: malformed installed version strings were parsed as `(0)`, which could allow overwrite behavior that looked like an upgrade.

## Changes
- changed: `parse_version()` now rejects malformed first version tokens.
- changed: `version_relation()` returns explicit `upgrade`, `same-version`, or `newer-installed`.
- changed: install blocks downgrade and malformed installed version by default.
- changed: `--allow-downgrade` remains the explicit maintainer override.

## Validation Fixtures
- verified: synthetic older version fixture sets installed version to `0.0.1`, places a stale program file, and preserves temp user config while current installer upgrades.
- verified: same-version `--repair` restores a removed `FireDM-GUI.exe`.
- verified: synthetic newer version fixture sets installed version to `9999.0.0`; current installer exits nonzero and leaves the install root present.
- verified: uninstall removes installer-owned program files, registry metadata, and shortcuts while preserving temp user config.

## Tests
- verified: `tests/release/test_installer_bootstrap_versioning.py` covers upgrade, same version, newer installed version, malformed installed version rejection, and numeric-prefix suffix handling.
