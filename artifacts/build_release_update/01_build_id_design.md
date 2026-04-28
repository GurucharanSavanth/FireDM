# 01 Build ID Design

## Format

- changed format: `YYYYMMDD_V{N}`
- changed tag: `build-YYYYMMDD_V{N}`
- changed release name: `FireDM YYYYMMDD_V{N}`

## Date Source

- changed default date source: local build-machine date via `datetime.now().astimezone()`.
- changed deterministic override: `--date YYYYMMDD`.
- changed explicit rebuild override: `--build-id YYYYMMDD_VN`.

## Enumeration

- changed: `scripts/release/build_id.py` scans local `dist/**` names and release manifests for build IDs.
- changed: local Git tags matching `build-*` are included.
- changed: optional remote tag scan is available with `--include-remote-tags`.
- changed: optional GitHub release scan is available with `--include-github-releases` when `gh` exists and the caller opts in.
- verified before build: `build_id.py --date 20260427 --print-next` returned `20260427_V1`.
- verified after build: same command returned `20260427_V2`.

## Collision Handling

- changed: explicit `--build-id` refuses reuse if local artifacts/tags already contain the ID.
- changed: reuse requires explicit `--allow-overwrite`.
- changed: tag-triggered GitHub Actions passes `--allow-overwrite` because the tag is the release authority in that workflow context.

