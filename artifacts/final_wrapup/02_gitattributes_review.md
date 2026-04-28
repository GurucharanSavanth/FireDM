# Phase 2 Gitattributes Review

## Result

- changed: `.gitattributes` was expanded from minimal rules to explicit text and binary policy.
- changed: `build-release.bat` working-tree line endings were converted to CRLF to match policy.
- verified: `git diff --check` passed after generated proof JSON drift was reverted.

## Text Policy

- `* text=auto`
- LF for Python, Markdown, YAML, TOML, INI/CFG, JSON, PyInstaller spec, shell, HTML, JavaScript, CSS.
- CRLF for `*.bat`, `*.cmd`, Inno Setup, WiX, Visual Studio project files, and `*.txt`.
- LF for PowerShell scripts. Rationale: existing release PowerShell scripts do not require CRLF and are cleaner under Git normalization.

## Binary Policy

- binary markers for common image files, executables, dynamic libraries, Python extension modules, archives, installers, PyInstaller package files, and compressed assets.

## No Broad Renormalization

- inferred: broad `git add --renormalize .` is not needed for this pass.
- observed: remaining large line-ending noise came from generated tracked proof files; those were reverted, not normalized.

