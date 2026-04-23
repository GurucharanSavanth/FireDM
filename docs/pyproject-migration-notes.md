# pyproject Migration Notes

## Summary

FireDM now uses modern PEP 517/518/621 packaging through `pyproject.toml` with setuptools as the backend. `setup.py` stays as a thin compatibility entrypoint for old tooling.

## Important Metadata

- Python support: `>=3.10,<3.13`
- Runtime extractor: `yt-dlp[default]>=2026.3.17`
- Legacy extractor: optional extra `[legacy]`
- Dev/test/build extras: `[dev]`, `[test]`, `[build]`, `[type]`
- Console entrypoint: `firedm = firedm.FireDM:main`

## Rationale

The Python Packaging User Guide defines `[build-system]`, `[project]`, and `[tool]` as standard `pyproject.toml` sections. Setuptools supports project metadata plus package discovery through `[tool.setuptools]`. This lets FireDM keep its flat legacy package layout while supporting editable installs, wheel builds, and tool configuration in one file.
