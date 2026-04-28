# 04 Dependency Declaration Cleanup

observed canonical declaration: `pyproject.toml`.

observed mirror declaration: `requirements.txt`.

changed package declarations: none.

reason:
- required runtime imports are already represented in `pyproject.toml`.
- dev/build/test dependencies already live in optional dependency groups.
- `youtube_dl` remains optional legacy and is not restored to default runtime.
- FFmpeg/ffprobe are external tools, not Python packages.

changed maintenance behavior:
- new preflight verifies declared required packages are installed before build.
- docs now describe required vs optional dependencies in `docs/release/DEPENDENCY_POLICY.md`.

deferred:
- constraints/lock file not introduced in this patch because repo currently uses `pyproject.toml` optional groups and CI pip cache. Add constraints only after maintainer chooses reproducibility policy.
