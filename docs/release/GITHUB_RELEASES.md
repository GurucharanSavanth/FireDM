# GitHub Releases

Local release publishing is safe by default. The GitHub release helper
dry-runs unless `--publish` is passed.

## Cross-platform release flow

`.github/workflows/draft-release.yml` runs four jobs in series:

1. **`resolve-build-code`** (`ubuntu-latest`) — resolves the unified
   `YYYYMMDD_VN` build code via `scripts/release/versioning.py select-build-code`
   and exposes `build_code`, `tag`, `release_name`, and `channel` as outputs.
2. **`build-windows`** (`windows-latest`) — builds the Windows installer +
   portable lane with `scripts/release/build_windows.py`. Skip with
   `include_windows=false` (manual dispatch only).
3. **`build-linux`** (`ubuntu-latest`) — builds the Linux portable archive
   with `scripts/release/build_linux.py`. Skip with `include_linux=false`
   (manual dispatch only).
4. **`release`** (`ubuntu-latest`) — downloads both lanes' uploaded artifact
   bundles, runs `scripts/release/merge_release_manifest.py` to produce
   `dist/FireDM_release_manifest_<BUILD_CODE>.json`, regenerates
   `dist/checksums/SHA256SUMS_<BUILD_CODE>.txt`, then dry-runs (or, when
   explicitly authorized, publishes) the GitHub release.

Both build jobs consume the same
`needs.resolve-build-code.outputs.build_code` so the Windows and Linux
artifacts are guaranteed to share one identifier.

## Manual publish gating

The `release` job adds `--publish` only when **either**:

* `inputs.publish_release == true` (workflow_dispatch), **or**
* the workflow was triggered by a `build-YYYYMMDD_V*` tag push.

Normal pushes and pull-request runs never publish.

## Local dry-run

```powershell
# Windows
.\.venv\Scripts\python.exe scripts\release\github_release.py --manifest dist\release-manifest.json
.\.venv\Scripts\python.exe scripts\release\github_release.py --manifest dist\FireDM_release_manifest_<build_id>.json
```

```bash
# Linux / WSL
python scripts/release/github_release.py --manifest dist/FireDM_release_manifest_<build_id>.json
```

## Local publish (after maintainer review)

```bash
python scripts/release/github_release.py \
    --manifest dist/FireDM_release_manifest_<build_id>.json \
    --publish --draft --prerelease
```

The script uses:

```text
tag:   build-YYYYMMDD_V{N}
title: FireDM YYYYMMDD_V{N}
```

## Verification before publish

Before creating a release, the helper verifies that:

* the manifest has a valid `build_id` (== `build_code`);
* every manifest artifact exists on disk;
* every artifact filename contains the build code (stale Windows or Linux
  artifacts from previous runs are rejected);
* artifact SHA256 values match the manifest;
* the checksum file exists, every line resolves, every target is listed in
  the manifest, and `# build_id: <code>` is present;
* dev/beta releases default to `--prerelease`;
* stable releases require a clean tree, passed Windows
  payload/installer validation, and signed installer artifacts when the
  Windows lane is present.

The script never prints GitHub tokens and only invokes `gh` when `--publish`
is set.

## Workflow artifact bundles

| Bundle | Contents |
|--------|----------|
| `FireDM-Windows-<BUILD_CODE>` | installer EXE, installer sidecar manifest, payload sidecar zip, portable ZIP, dependency status JSON, Windows per-platform manifest, merged manifest, release notes, license inventory, build-code-scoped checksums |
| `FireDM-Linux-<BUILD_CODE>` | Linux portable tar.gz, payload manifest JSON, Linux per-platform manifest, release notes, dependency status JSON, license inventory |

The `release` job downloads both bundles, merges the manifests, regenerates
the checksum file, then runs the dry-run / publish step.
