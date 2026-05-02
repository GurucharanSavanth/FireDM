# Phase 1 — Version source audit (observed)

## Canonical sources

| Concept | Source | Reader |
|---------|--------|--------|
| Product version (`2022.2.5`) | `firedm/version.py::__version__` | `firedm/version.py` import; `scripts/release/common.read_version()`; `pyproject.toml` dynamic version; `windows-build.ps1::Get-FireDMVersion` |
| Build code (`YYYYMMDD_VN`) | generated at build time by `scripts/release/build_id.py::select_build_id()` | passed as `--build-id` to all release scripts; written to manifests |
| Tag (`build-YYYYMMDD_VN`) | `build_id.build_tag_name(build_id)` | release script + workflow |
| Release name (`FireDM YYYYMMDD_VN`) | `build_id.build_release_name(build_id)` | release script + workflow |
| Build metadata sidecar | `build-metadata.json` in `dist/FireDM/` | `windows-build.ps1::Write-PackagedBuildMetadata`, payload validators |

## Hits classified (rg `__version__|version|build_id|2022\.2\.5|YYYYMMDD|V\d+|manifest|checksum|artifact`)

| Hit type | Examples | Action |
|----------|----------|--------|
| canonical product version | `firedm/version.py`, `pyproject.toml [tool.setuptools.dynamic]` | keep as canonical |
| runtime display | `firedm/setting.py` (`app_version` static), `firedm/FireDM.py` banner — uses imported `version.__version__` (verified by grep) | unchanged |
| build metadata field name | `build_id` everywhere | retained; `build_code` alias added in versioning.py |
| installer metadata | `build_installer.py`, `build_metadata()` in `common.py` | already build_id aware |
| release artifact name | `installer_name`, `portable_name`, `payload_zip_name`, `release_manifest_name`, `checksum_file_name`, `license_inventory_name`, `release_notes_name`, `dependency_status_name` in `common.py` | extended with Linux helpers |
| manifest field | `version`, `build_id`, `build_date`, `build_index`, `tag_name`, `release_name`, `channel`, `arch`, `artifacts[]` | extended with `platforms[]` after merge |
| docs | `docs/release/*` | new LINUX_BUILD.md added; existing docs updated |
| tests | `tests/release/*` | new test files added |
| stale hardcoded literal | none observed: legacy `scripts/appimage` and `scripts/exe_build` are ruff-excluded but were not modified by this task (unrelated to release pipeline) | left untouched (out of scope) |
| generated outputs | `dist/FireDM/build-metadata.json` | retained; new `firedm/_build_info.py` generation added by versioning.write_build_info during payload build |

## Duplicated literals to watch

- The product version `2022.2.5` only appears in `firedm/version.py` plus regression fixtures (e.g., `tests/release/test_github_release_dry_run.py`). No secondary hardcode found in build/release scripts.
- `build_id` field name is consistent. The mission spec uses `build_code`; we expose it as a synonym in `versioning.py` rather than renaming the wire format.

## Why no rename

The repository, all manifests under `dist/`, every workflow input, and every test relies on `build_id`. Renaming would invalidate published draft-release artifacts and break compatibility tests `test_release_manifest_build_id.py` and `test_workflow_build_id.py`. We add `build_code` as an alias.

## Files to be changed

- new: `scripts/release/versioning.py`
- new: `scripts/release/build_linux.py`, `validate_linux_payload.py`, `validate_linux_portable.py`, `merge_release_manifest.py`
- new: `scripts/linux-build.sh`, `scripts/firedm-linux.spec`
- updated: `scripts/release/common.py` (Linux naming helpers, payload roots)
- updated: `scripts/release/build_payload.py` (write `firedm/_build_info.py` into payload)
- updated: `scripts/release/build_windows.py` (record platform=windows, defer to merge)
- updated: `scripts/release/generate_checksums.py` (cross-platform aware)
- updated: `scripts/release/github_release.py` (consume merged manifest)
- updated: `.github/workflows/draft-release.yml` (build-code job, Linux job, merge job, gated release)
- updated: docs (LINUX_BUILD, LINUX_PORTABLE, BUILD_ID_POLICY, README, RELEASE_CHECKLIST, GITHUB_RELEASES)
- new tests: `test_unified_versioning.py`, `test_build_code_cross_platform.py`, `test_manifest_cross_platform.py`, `test_linux_build_contract.py`, `test_github_actions_cross_platform_release.py`
