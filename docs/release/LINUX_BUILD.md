# FireDM Linux Build Lane

The Linux release lane builds a portable PyInstaller payload on
`ubuntu-latest` (GitHub Actions) or any equivalent Linux host. PyInstaller
cannot cross-compile — Linux artifacts cannot be built from Windows.

## Scope (this pass)

| Platform | Format | Status |
|----------|--------|--------|
| Linux x64 | tar.gz portable archive | implemented |
| Linux x86 | — | blocked (no toolchain) |
| Linux ARM64 | — | blocked (no toolchain) |
| AppImage | — | blocked (no AppImage tooling integrated) |
| .deb / .rpm | — | blocked (no packaging integrated) |

FFmpeg/ffprobe stay detect-only; bundling waits on a separate
license/source/checksum review.

## Inputs

The Linux lane consumes the same unified build code (`YYYYMMDD_VN`) as the
Windows lane. See `docs/release/BUILD_ID_POLICY.md`.

## Local build

```bash
# Use repo .venv if available, otherwise python3.10 on PATH.
bash scripts/linux-build.sh --channel dev --arch x64

# Pin a build code:
bash scripts/linux-build.sh --channel dev --arch x64 --build-code 20260428_V1

# Direct invocation (skips the orchestrator’s lint/test guard):
python scripts/release/build_linux.py --arch x64 --channel dev --build-id 20260428_V1
```

The orchestrator (`scripts/linux-build.sh`) refuses to run on non-Linux hosts.
Use WSL or the GitHub Actions ubuntu runner from a Windows workstation.

## What the build does

1. Resolves the build code via `scripts/release/versioning.py select-build-code`.
2. Runs `scripts/release/check_dependencies.py --skip-portable` for tool/runtime preflight.
3. Runs `python -m compileall ./firedm ./scripts` and `pytest -q` (skip with `--skip-tests`).
4. Generates `firedm/_build_info.py` with the cross-platform build identity.
5. Invokes PyInstaller against `scripts/firedm-linux.spec` (one-folder, two entry points: `firedm`, `FireDM-GUI`).
6. Copies the payload into `dist/payloads-linux/linux-x64/FireDM/`, sets the executable bit on the launchers, writes `payload-manifest.json`.
7. Packs `dist/portable-linux/FireDM_<BUILD_CODE>_<CHANNEL>_linux_x64.tar.gz`.
8. Calls `validate_linux_payload.py` and `validate_linux_portable.py` (smoke is skipped on non-Linux hosts).
9. Writes the per-platform manifest to `dist/FireDM_release_manifest_<BUILD_CODE>_linux.json`.
10. Updates `dist/checksums/SHA256SUMS_<BUILD_CODE>.txt` via `generate_checksums.py`.

## GitHub Actions

`.github/workflows/draft-release.yml` exposes a `build-linux` job that runs on
`ubuntu-latest`, installs `python3-tk tk-dev libssl-dev libffi-dev libcurl4-openssl-dev libssl3 libgirepository1.0-dev gir1.2-ayatanaappindicator3-0.1`,
then runs `python scripts/release/build_linux.py`. Inputs:

* `channel` — dev / beta / stable
* `build_id` — optional explicit `YYYYMMDD_VN`
* `include_linux` — set to `false` to skip the Linux job
* `publish_release` — gated; default `false` (dry-run only)

Linux artifacts are uploaded to the `FireDM-Linux-<BUILD_CODE>` artifact
bundle and consumed by the `release` job, which merges Windows + Linux
manifests via `merge_release_manifest.py`.

## Validation contract

`validate_linux_payload.py --arch x64` checks:

* `firedm` and `FireDM-GUI` launchers exist and have the user execute bit;
* `_internal/certifi/cacert.pem` and `_internal/tkinter/__init__.py` exist;
* `payload-manifest.json` exists;
* on Linux only: `firedm --help` and `firedm --imports-only` succeed.

`validate_linux_portable.py --archive <tar.gz>` extracts the archive into a
sandboxed directory, refuses any path that escapes the extraction root, and
runs the same checks against the extracted tree.

## Known blockers

* AppImage / .deb / .rpm / signing remain blocked until a maintainer integrates the tooling.
* GUI smoke is **not** automated — Linux jobs run headless and validate CLI flows only.
* x86 / ARM64 lanes are not implemented.
