# 08 GitHub Actions Review

changed `.github/workflows/draft-release.yml`:
- dependency preflight added.
- compileall added before tests.
- build-ID dependency status JSON uploaded.
- onedir installer bundle, nested installer EXE, sidecar payload ZIP, portable ZIP, manifest, checksums, license inventory, and dependency status are uploaded.
- release helper remains dry-run unless tag build or `publish_release=true`.

changed `.github/workflows/windows-smoke.yml`:
- `scripts/release/**` added to path triggers.
- dependency preflight added.
- compileall added.
- Windows build now calls `scripts/windows-build.ps1 -Channel dev -Arch x64`.
- portable ZIP validation added after build.

observed publish safety:
- normal push does not publish.
- manual draft-release defaults to dry-run.
- stable tag/manual release still requires signing policy gates.
- local `github_release.py --dry-run` verified the build tag, release title, artifact list, and checksum validation without publishing.

blocked:
- remote GitHub Actions not run in this local pass.
