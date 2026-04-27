# Build ID Policy

FireDM release automation uses deterministic build IDs:

```text
YYYYMMDD_V{N}
```

Examples:

```text
20260427_V1
20260427_V2
20260427_V3
```

`YYYYMMDD` comes from the local build machine date by default. Use `--date
YYYYMMDD` only for deterministic test/rebuild workflows. `N` starts at `1` and
increments when matching local `dist/**` artifacts, local `build-YYYYMMDD_VN`
Git tags, optional remote tags, or optional GitHub releases are discovered.

Canonical tag format:

```text
build-YYYYMMDD_V{N}
```

Canonical release title:

```text
FireDM YYYYMMDD_V{N}
```

Local dev build:

```powershell
.\build-release.bat dev
```

Explicit date:

```powershell
.\.venv\Scripts\python.exe scripts\release\build_windows.py --arch x64 --channel dev --date 20260427
```

Explicit build ID:

```powershell
.\build-release.bat dev --build-id 20260427_V7
```

Explicit reuse is blocked unless `--allow-overwrite` is also provided. Do not
use overwrite for normal release creation.

Canonical artifacts include the build ID:

```text
dist\installers\FireDM_Setup_<build_id>_<channel>_win_x64.exe
dist\portable\FireDM_<build_id>_<channel>_win_x64_portable.zip
dist\FireDM_release_manifest_<build_id>.json
dist\checksums\SHA256SUMS_<build_id>.txt
dist\licenses\license-inventory_<build_id>.json
```

Compatibility aliases remain for tooling that expects stable paths:

```text
dist\release-manifest.json
dist\release-body.md
dist\checksums\SHA256SUMS.txt
dist\licenses\license-inventory.json
```

Commit source scripts, tests, workflows, docs, and text evidence. Do not commit
`dist/**`, installer EXEs, portable ZIPs, logs, screenshots, or temp validation
directories.

Blocked lanes remain blocked until implemented and validated: x86, ARM64,
universal bootstrapper, MSI, MSIX, and FFmpeg/ffprobe bundling.

