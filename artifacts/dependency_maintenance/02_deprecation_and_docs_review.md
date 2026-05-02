# 02 Deprecation And Docs Review

observed official sources checked on 2026-04-28:

- Python version status: https://devguide.python.org/versions/
  - observed: Python 3.10 is security-only and scheduled EOL in 2026-10.
  - action: keep `>=3.10,<3.11`; document future 3.11/3.12 validation needed.

- PyInstaller spec behavior: https://www.pyinstaller.org/en/stable/usage.html and https://pyinstaller.org/en/v6.12.0/spec-files.html
  - observed: spec files are used for data/binary collection; one-folder builds bundle runtime dependencies.
  - action: keep `scripts/firedm-win.spec`; validate Tcl/Tk/certifi payload files.

- pytest changelog: https://doc.pytest.org/en/latest/changelog.html
  - observed: pytest 9 treats some removals/deprecations more strictly.
  - action: run warning-enabled pytest; do not globally suppress warnings.

- Ruff docs: https://docs.astral.sh/ruff/
  - observed: Ruff supports project config in `pyproject.toml`; repo keeps scoped lint gate.
  - action: extend scoped script lint to `scripts/release`.

- yt-dlp releases/package metadata: https://github.com/yt-dlp/yt-dlp/releases and https://pypi.org/project/yt-dlp/
  - observed: local baseline `2026.3.17` matches current project policy.
  - action: keep `yt-dlp[default]>=2026.3.17`.

- pycurl package metadata: https://pypi.org/project/pycurl/
  - observed: `7.45.7` has Windows wheels including CPython 3.10 x64.
  - action: keep pycurl and validate import/version through preflight.

- FFmpeg legal page: https://ffmpeg.org/legal.html
  - observed: FFmpeg license mode can be LGPL or GPL depending build options.
  - action: do not bundle in this pass; classify external optional warning.

- Deno docs/release page: https://docs.deno.com/runtime/manual/getting_started and https://deno.com/blog/v2.7
  - observed: Deno is a standalone runtime; local elevated shell has `deno 2.7.13`.
  - action: keep Deno external, check it as an optional tool, and do not claim it is bundled.

- GitHub CLI release create manual: https://cli.github.com/manual/gh_release_create
  - observed: `gh release create` can create tags if missing unless guarded.
  - action: local helper remains dry-run by default; `windows-build.ps1` refuses direct publish.

- GitHub setup-python README: https://github.com/actions/setup-python
  - observed: v6 supports Python setup and pip cache.
  - action: workflows keep explicit Python 3.10 and pip cache.
