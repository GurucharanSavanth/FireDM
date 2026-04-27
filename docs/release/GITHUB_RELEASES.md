# GitHub Releases

Local release publishing is safe by default. The GitHub release helper dry-runs
unless `--publish` is passed.

Dry-run current manifest:

```powershell
.\.venv\Scripts\python.exe scripts\release\github_release.py --manifest dist\release-manifest.json
```

Dry-run canonical build manifest:

```powershell
.\.venv\Scripts\python.exe scripts\release\github_release.py --manifest dist\FireDM_release_manifest_<build_id>.json
```

Publish a draft prerelease after maintainer review:

```powershell
.\.venv\Scripts\python.exe scripts\release\github_release.py --manifest dist\FireDM_release_manifest_<build_id>.json --publish --draft --prerelease
```

The script uses:

```text
tag: build-YYYYMMDD_V{N}
title: FireDM YYYYMMDD_V{N}
```

Before creating a release, the script verifies:
- manifest has a valid `build_id`
- every manifest artifact exists
- every artifact filename contains the build ID
- artifact SHA256 values match the manifest
- checksum file exists and matches the listed files
- dev/beta releases default to prerelease
- stable releases require a clean tree, passed payload/installer validation,
  and signed installer artifacts

The script never prints GitHub tokens. It requires GitHub CLI only when
`--publish` is provided.

GitHub Actions uses the same helper. Manual workflow runs dry-run by default;
set `publish_release=true` only when the maintainer intends to create/upload a
GitHub draft release. Tag builds use `build-YYYYMMDD_VN` tags and force the
stable channel, so signing must be configured.

