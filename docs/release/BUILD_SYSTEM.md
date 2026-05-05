# Build System

Status: changed 2026-05-03.

## Canonical Windows Entry Point

- changed: root `.\windows-build.ps1` is the canonical local Windows build script.
- changed: `.\scripts\windows-build.ps1` is a thin compatibility wrapper that forwards arguments to root `.\windows-build.ps1`.
- observed: `build-release.bat` is deleted in the current dirty tree and was not restored by this patch.
- planned: CI and older release docs can continue using `scripts\windows-build.ps1` during transition because the wrapper forwards to the root script.

## Supported Parameters

`.\windows-build.ps1` accepts:

```powershell
.\windows-build.ps1 `
  -Mode Debug|Release `
  -Kind OneFolder|OneFile|PortableZip `
  -Backend Auto|PyInstaller|Nuitka `
  -Clean|-NoClean `
  -DryRun `
  -SkipTests `
  -SkipSmoke `
  -OutputDir .\release `
  -Version <version>
```

Compatibility arguments from the older script are also accepted: `-PythonExe`,
`-Channel`, `-Arch`, `-BuildId`, `-BuildDate`, `-AllowOverwrite`,
`-SkipLint`, `-PayloadOnly`, `-ValidateOnly`, `-InstallLocalDeps`,
`-SmokeGui`, `-Release`, `-ReleaseDir`, `-PublishDraftRelease`, `-GithubRepo`,
and `-GithubTag`. `-SkipPythonPackage` skips the wheel/sdist stage, and
`-SkipTwineCheck` keeps those artifacts but skips metadata validation.
Compatibility does not make deprecated behavior authoritative.

## Build Stages

1. Bootstrap: resolve repo root, release root, Python, PowerShell, OS, Git, PyInstaller, Nuitka, ffmpeg, and ffprobe.
2. Repo snapshot: record branch, commit, dirty status, and blocked Git state when Git is unavailable.
3. Cleanup crew: remove only explicitly allowlisted generated paths when `-Clean` is used; preview with `-DryRun`.
4. Dependency/runtime checks: validate Python, `pyproject.toml`, entry point, backend, and spec file.
5. QA: compileall, targeted modern tests including frontend-common view-model and adapter tests, full pytest, mypy, and scoped Ruff unless skipped.
6. Python distribution build: writes `.\release\*.whl` and `.\release\*.tar.gz`, then runs `twine check` unless skipped.
7. Package build: Auto selects PyInstaller; Nuitka is blocked unless explicitly selected and installed.
8. Release assembly: root `.\release` is the final artifact directory.
9. Changelog compilation: writes `.\release\CHANGELOG-COMPILED.md`.
10. Plugin artifact compilation: writes `.\release\plugins-manifest.json` and `.\release\plugins-manifest.txt`.
11. Manifest generation: writes `.\release\manifest.json`.
12. Checksums: writes `.\release\checksums.sha256`.
13. Smoke: packaged CLI help/import smoke when artifacts exist and `-SkipSmoke` is not set.

## Cleanup Policy

- changed: cleanup is allowlist-based and uses `Remove-Item -LiteralPath` only after repo containment checks.
- changed: `-DryRun -Clean` logs what would be removed without deleting.
- safe: `build`, `build\windows-build`, `dist`, cache folders, bytecode caches, coverage outputs, legacy release staging folders, root `release\FireDM`, root `release\FireDM.zip`, and exact generated Windows release artifacts matching `FireDM-*-windows-*` under root `release`.
- forbidden: `.git`, `.venv`, source packages, tests, docs, scripts, and mixed evidence directories such as whole `artifacts`.
- unknown: source-like folders such as `browser_extension` and local metadata such as `package-lock.json` are skipped.

## Artifact Layout

See `docs/release/RELEASE_ARTIFACT_LAYOUT.md`. The required root files are:

- `release\build.log`
- `release\manifest.json`
- `release\checksums.sha256`
- `release\CHANGELOG-COMPILED.md`
- `release\plugins-manifest.json`
- `release\plugins-manifest.txt`
- `release\*.whl`
- `release\*.tar.gz`

## Backend Status

| Backend | Status | Notes |
| --- | --- | --- |
| Auto | implemented | Selects PyInstaller in this Windows lane. |
| PyInstaller OneFolder | verified on Windows host | `.\windows-build.ps1 -Clean -Kind OneFolder -Backend PyInstaller -Mode Release` produces `release\FireDM` with Tk CLI/GUI executables and runs packaged CLI help/import smoke. |
| PyInstaller PortableZip | implemented in script | Builds OneFolder, then zips the release app folder. |
| PyInstaller OneFile | blocked | Parameter is accepted; real build fails until a one-file spec is validated. |
| Nuitka | blocked | Requires installed Nuitka and compiler validation before real claims. |

## GUI Backends

| Backend | Status | Entry Point | Notes |
| --- | --- | --- | --- |
| Tkinter | default | `firedm.exe`, `FireDM-GUI.exe`, `firedm.py` | Active release runtime. Modernization continues inside the current FireDM GUI/core path; the prior alternate preview lane has been removed. |

## Plugin Manifest Section

`.\windows-build.ps1` runs `firedm.plugins.manifest.discover_plugin_manifest()` after QA. The result is folded into `release/manifest.json` under `included_plugins`, `blocked_plugins`, `planned_plugins`, and `plugin_discovery_warnings`, and written as standalone `plugins-manifest.json` plus `plugins-manifest.txt` artifacts. Plugins are never enabled by the build script; the manifest only records discovery state. `firedm/plugins/policy.py` is the local policy source for shipped plugins that must be blocked in the registry, Tk Plugin Manager, and release manifest.

## Validation Behavior

- changed: tests were added for PowerShell parse, dry-run contract, cleanup dry-run safety, wrapper behavior, manifest fields, checksums, and changelog output.
- changed: the canonical QA target list now includes `tests\test_frontend_common_adapters.py` because connector adapters are part of the GUI migration contract.
- observed: full-project Ruff still has legacy debt; the canonical script runs scoped Ruff on modernized code.
- verified: PyInstaller OneFolder Release build, full pytest, compileall, mypy, scoped Ruff, packaged `--help`, and packaged `--imports-only` passed on the Windows host.
- blocked: GUI smoke, installer smoke, signing, Nuitka compilation, Linux build, and one-file PyInstaller are not proven by this script until those commands run successfully.

## Future-Agent Rule

Every future patch that changes runtime files, dependencies, entry points,
bundled docs/assets, tests, versioning, external tools, packaging assumptions,
artifact layout, or release-note sources must inspect `.\windows-build.ps1`.
If the patch changes build behavior, update this file and the script in the
same patch. Reviewers must block build-affecting patches that skip this check.
