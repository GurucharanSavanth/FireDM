# Validation Matrix

## Discovery Commands
| Purpose | Command | Status |
| --- | --- | --- |
| repo path | `pwd` | verified in rebuild |
| branch/status | `git status --short --branch` | verified in rebuild |
| branch name | `git branch --show-current` | verified in rebuild |
| last commit | `git log -1 --oneline` | verified in rebuild |
| remotes as non-authority metadata | `git remote -v` | verified in rebuild |
| Python version | `python --version` | verified in rebuild |
| Python/platform | `python -c "import sys, platform; print(sys.version); print(platform.platform()); print(sys.platform)"` | verified in rebuild |
| file inventory | `rg --files` | verified in rebuild |
| Markdown inventory | `rg --files -g "*.md"` | verified in rebuild |

## Markdown Validation
| Check | Command | Status |
| --- | --- | --- |
| whitespace diff | `git diff --check` | required after docs edit |
| required docs exist | `Test-Path AGENTS.md, AGENT.md, CLAUDE.md` plus `docs/agent/*` checks | required after docs edit |
| non-empty docs | `Get-Item AGENTS.md, AGENT.md, CLAUDE.md, docs\agent\*.md` | required after docs edit |
| forbidden network/source refs | `rg <forbidden-reference-pattern> AGENTS.md AGENT.md CLAUDE.md docs/agent` | required after docs edit |
| unresolved marker scan | `rg <placeholder-pattern> AGENTS.md AGENT.md CLAUDE.md docs/agent` | required after docs edit |
| Claude reviewer docs scan | `rg <pattern> .claude/agents` | required if reviewer agents exist |
| Markdown linter | `markdownlint` | not detected locally |
| Prettier docs | `prettier` | not detected locally |

## Python Syntax Validation
| Check | Command | Status |
| --- | --- | --- |
| compile source and release scripts | `.\.venv\Scripts\python.exe -m compileall .\firedm .\scripts\release` | available, not needed for docs-only edits |
| import smoke | `.\.venv\Scripts\python.exe firedm.py --imports-only` | available, not needed for docs-only edits |

## Unit Test Validation
| Check | Command | Status |
| --- | --- | --- |
| full suite | `.\.venv\Scripts\python.exe -m pytest -q` | available |
| focused regression | `.\.venv\Scripts\python.exe scripts\run_regression_suite.py` | available |
| security tests | `.\.venv\Scripts\python.exe -m pytest -q tests/test_security.py` | available |
| browser integration tests | `.\.venv\Scripts\python.exe -m pytest -q tests/test_browser_integration.py` | available |
| frontend common adapter tests | `.\.venv\Scripts\python.exe -m pytest -q tests/test_frontend_common_view_models.py tests/test_frontend_common_adapters.py` | available |

## Integration/Smoke Validation
| Check | Command | Status |
| --- | --- | --- |
| source help | `.\.venv\Scripts\python.exe -m firedm --help` | available |
| extractor default | `.\.venv\Scripts\python.exe scripts\verify_extractor_default.py` | available |
| synthetic video pipeline | `.\.venv\Scripts\python.exe scripts\smoke_video_pipeline.py` | available |
| runtime diagnostics | `.\.venv\Scripts\python.exe scripts\collect_runtime_diagnostics.py` | available |
| packaged video flow | `.\.venv\Scripts\python.exe scripts\verify_packaged_video_flow.py` | available if package exists |

## Packaging Validation
| Check | Command | Status |
| --- | --- | --- |
| wheel/sdist | `.\.venv\Scripts\python.exe -m build --no-isolation` | available |
| metadata check | `.\.venv\Scripts\python.exe -m twine check dist\*.whl dist\*.tar.gz` | available if build artifacts exist |
| dependency preflight | `.\.venv\Scripts\python.exe scripts\release\check_dependencies.py --arch x64 --channel dev --skip-portable` | available |
| Windows payload | `.\.venv\Scripts\python.exe scripts\release\build_windows.py --arch x64 --channel dev` | available |
| canonical Windows build dry-run | `powershell -NoProfile -ExecutionPolicy Bypass -File .\windows-build.ps1 -DryRun -Clean -SkipTests -SkipSmoke` | available |

## Windows-Specific Validation
| Check | Command | Status |
| --- | --- | --- |
| PowerShell build wrapper | `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows-build.ps1 -Channel dev -Arch x64` | available; forwards to root `.\windows-build.ps1` |
| portable validation | `.\.venv\Scripts\python.exe scripts\release\validate_portable.py --archive <portable_zip>` | available when artifact exists |
| installer validation | `.\.venv\Scripts\python.exe scripts\release\validate_installer.py --artifact <installer_exe> --test-repair --test-uninstall --test-upgrade --test-downgrade-block` | available when artifact exists |
| installed GUI smoke | `.\.venv\Scripts\python.exe scripts\release\smoke_installed_gui.py --install-root <install_root> --timeout 20 --headless-safe --no-network` | available when install root exists |

## Linux-Specific Validation
| Check | Command | Status |
| --- | --- | --- |
| Linux wrapper | `bash scripts/linux-build.sh --channel dev --arch x64` | blocked on current Windows host unless Linux/WSL is used |
| Linux payload validation | `python scripts/release/validate_linux_payload.py --arch x64` | Linux lane only |
| Linux portable validation | `python scripts/release/validate_linux_portable.py --archive <linux_tar>` | Linux lane only |

## Security Validation
| Check | Command | Status |
| --- | --- | --- |
| security unit tests | `.\.venv\Scripts\python.exe -m pytest -q tests/test_security.py` | available |
| browser/native tests | `.\.venv\Scripts\python.exe -m pytest -q tests/test_browser_integration.py` | available |
| redaction tests | `.\.venv\Scripts\python.exe -m pytest -q tests/test_pipeline_logger_redaction.py` | available |
| archive traversal tests | `.\.venv\Scripts\python.exe -m pytest -q tests/test_archive_extraction.py` | available |

## Documentation Validation
| Check | Command | Status |
| --- | --- | --- |
| generated doc diff | `git diff -- AGENTS.md AGENT.md CLAUDE.md docs/agent` | required |
| Claude reviewer diff | `git diff -- .claude/agents` | required if reviewer agents exist |
| doc inventory completeness | compare `rg --files -g "*.md"` with `docs/agent/DOCUMENTATION_INDEX.md` | required |
| no app-code edits | `git diff --name-only -- firedm scripts tests pyproject.toml` | required for docs-only tasks |

## Manual Validation Checklist
- Launch source GUI.
- Launch packaged GUI if present.
- Run safe small direct download.
- Test cancel/resume.
- Test single-video metadata extraction.
- Test playlist selection and queue handoff.
- Test ffmpeg-required DASH/HLS media only when permitted and tools are present.
- Test missing-ffmpeg reporting.
- Check installer uninstall preserves user data by default.

## Commands Found Locally
- verified: `rg`
- verified: `git`
- verified: `python`
- verified: repo `.venv` Python
- verified: `.venv` pytest
- verified: `.venv` ruff
- verified: `.venv` mypy
- verified: `claude`
- observed: `claude --print` supports non-interactive read-only review when tool list excludes write/edit/bash tools.

## Commands Not Found / Blocked
- blocked: `uname` not available in PowerShell host.
- blocked: `markdownlint` not detected.
- blocked: `prettier` not detected.
- blocked: Linux build commands not executed on current Windows host.
- blocked: Native repo-local `.claude/agent-memory/` layout not verified.
