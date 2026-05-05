# Validation Pipeline

Status: changed 2026-05-02.

This document is the modernization-program-facing companion to
[`docs/agent/VALIDATION_MATRIX.md`](../agent/VALIDATION_MATRIX.md). The matrix
is the canonical command map; this file lists the validation steps that gate
each layer transition and the planned extensions.

## Current Validation Commands (implemented)
| Step | Command | Scope | Expected outcome |
| --- | --- | --- | --- |
| Full pytest baseline | `.\.venv\Scripts\python.exe -m pytest -q` | repo | 287 passed, 1 skipped (Windows POSIX exec-bit fixture skip) |
| Targeted engine pytest | `.\.venv\Scripts\python.exe -m pytest -q tests\test_download_engines.py tests\test_engine_config_and_factory.py tests\test_internal_http_engine.py` | engine package | all pass |
| Compileall (firedm) | `.\.venv\Scripts\python.exe -m compileall .\firedm` | firedm package | success |
| Compileall (release scripts) | `.\.venv\Scripts\python.exe -m compileall .\scripts\release` | release scripts | success |
| Ruff (engine package) | `.\.venv\Scripts\python.exe -m ruff check firedm\download_engines tests\test_download_engines.py tests\test_internal_http_engine.py tests\test_engine_config_and_factory.py` | engine package + tests | all checks passed |
| Mypy (scoped) | `.\.venv\Scripts\python.exe -m mypy` | scoped file list in `pyproject.toml` | no issues |
| No-shell grep | `rg "shell=True\|os\.system\|subprocess\.call" firedm\download_engines` | engine package | no matches |
| Doc-claim grep | `rg <claim-pattern> docs` (claim pattern matches a tool name followed by an `implemented` claim — see `tools/check_doc_claims.md` notes below) | docs tree | no matches |
| Whitespace diff | `git diff --check` | working tree | no whitespace errors |
| Markdown index completeness | compare `rg --files -g "*.md"` to `docs\agent\DOCUMENTATION_INDEX.md` | docs tree | every Markdown file is indexed |

Use `.venv/Scripts/python.exe` explicitly. The system-PATH Python on this host
lacks `pyyaml`, which causes 6 release tests to skip on it (`test_workflow_build_id.py`
and `test_github_actions_cross_platform_release.py`). Those tests pass in the
project venv. The 1 skip in the venv baseline is the Windows POSIX exec-bit
fixture in `tests/release/test_linux_build_contract.py:59`.

### Doc-claim grep pattern
The doc-claim regression detects any prose that asserts a tool name as
implemented when the tool is still planned. The pattern is recorded here so
agents can paste it without re-deriving the regex:

- Tool names that must never be marked implemented while still planned:
  `release_build` (build orchestrator script), `self-update` (updater code),
  `aria2c` (engine adapter), `yt-dlp` (engine adapter).
- Claim word: `implemented`.
- Pattern shape: alternation of `<tool>.*<claim>` per tool.

To run the check, alternate each tool against `.*implemented` in a single
ripgrep pattern. The check passes when ripgrep prints no matches.

## Per-Layer Validation Gates
| Layer | Minimum gate to advance |
| --- | --- |
| L0 | docs diff + grep + pytest baseline 287/1 |
| L1 | engine package pytest + ruff + mypy on `models.py`, `base.py`, `registry.py` |
| L2 | full pytest 287/1 + ruff + mypy on `factory.py`, `config.py`, `internal_http.py` |
| L3 | parity regression for resume / segmentation / HLS / fragmented / FTP / SFTP / proxy + full pytest |
| L4 | tool-discovery unit tests + redaction regression + AST grep proving no `shell=True` in new code |
| L5 | aria2c missing-binary / bad-version / RPC bind / RPC redaction / path-validation tests |
| L6 | yt-dlp missing-formats / DRM-rejected / cookie-opt-in / merge / redaction tests |
| L7 | extractor / HLS parser / ffmpeg fast-and-slow merge tests + manual single-video smoke |
| L8 | preflight unit tests + header CR/LF injection regression |
| L9 | queue admission + scheduler tests + controller lifecycle regression |
| L10 | view-event tests + manual GUI smoke (engine dropdown, queue profile selection) |
| L11 | atomic-write + restore-after-crash + no-execute-from-saved-state regression |
| L12 | release-build dry-run smoke + artifact layout test (no real network publish) |
| L13 | manifest schema test + SBOM presence test |
| L14 | updater test matrix (no-update / available / prerelease / wrong-asset / checksum / interrupt / rate-limit / TLS / rollback / cancel) |
| L15 | docs-diff + index completeness + built-in help fixture render |
| L16 | doc presence + reviewer output format check |
| L17 | release tests + workflow review (dry-run only on protected branches) |
| L18 | requires real legacy-OS host or VM smoke; no modern-lane gate covers it |

## Planned Extensions (not yet implemented)
- planned: Security grep set covering `shell=True`, `os.system`, `eval(`, `exec(`, raw cookies in logs, raw authorization headers in logs, and unsafe deserialization. Promote to required gate before L5/L6/L11.
- changed: Dry-run build-script smoke exercises root `windows-build.ps1` with `-DryRun -Clean`; it must not call `pyinstaller` or `nuitka`, and it verifies argument parsing, cleanup preview, manifest, changelog, checksum, and root `release` layout.
- planned: Manifest schema test that validates the per-release manifest JSON against a committed JSON Schema in `docs/release/`. Required gate for Layer 13.
- planned: SBOM presence test that asserts the release artifact folder contains a `bom.json` with non-empty `components`. Required gate for Layer 13.
- planned: Updater test matrix (Layer 14) running in a temp folder with a faked GitHub Releases API server.
- planned: Parity regression harness (Layer 3) that records legacy `brain` byte-by-byte output for a fixture URL, then reruns through the wired engine and asserts identical bytes plus identical resume/range behavior.

## How To Add A Layer Gate
1. Implement the layer in a single bounded patch.
2. Add the new gate command to `docs/agent/VALIDATION_MATRIX.md` under the right section.
3. Add a row to the per-layer gate table in this file.
4. Promote the gate to "required" only after it has run green at least twice in different sessions.
5. Update `docs/architecture/MODERNIZATION_MASTER_PLAN.md` to reflect the new validation-gate cell.

## Stop Conditions
- Stop if the baseline 287/1 regresses for any reason. Do not promote a layer with a regressing baseline.
- Stop if a security grep returns a new match that did not exist in the prior layer.
- Stop if `git diff --check` reports whitespace errors after a docs-only edit.
- Stop if the doc-claim grep finds an "implemented" claim for a file that does not exist.
