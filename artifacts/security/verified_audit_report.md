# FireDM Verified Hostile Security Audit Report

## Audit Scope

- Local Root: `G:/Personal Builds/Revive-FireDM/FireDM`
- Branch: `main`
- Commit: `4dddd9cc9c51b9d17b44236af67ef145078f644a`
- Platform: Windows 11 Home Single Language (10.0.26200), bash shell
- Python: 3.10.11
- Git: 2.53.0.windows.2
- Dependency / install method: `pyproject.toml` (PEP 621). Runtime
  deps already present in user site-packages
  (`pycurl 7.45.7`, `certifi 2026.04.22`, `yt_dlp 2026.03.17`).
  Audit installed `pytest 9.0.3` via `pip install --user "pytest>=9.0"`
  (matches `[project.optional-dependencies].test`).
- Audit mode: defensive, authorized, local-only. Loopback-only network,
  `tmp_path`-isolated filesystem, marker-file-only subprocess.
- Safety boundary: no remote targets, no destructive payloads, no
  credential access, no persistence, no metadata IPs, no real downloads.
- Pre-existing working tree changes: at audit start, the working tree
  already contained the F-CRIT-1..F-HIGH-6 mitigation patches plus four
  modified `artifacts/*` JSONs and an untracked `tests/test_security.py`.
  Those were the prior audit's output, not this audit's.

## Validation Commands

The full command log lives in
`artifacts/security/command_log.md` (CMD-001 through CMD-031). Below
are the security-relevant validation commands and their exact outputs.

```text
$ python -m pytest -q tests/test_security.py
........                                                                 [100%]
8 passed in 0.33s
```

```text
$ python -m pytest -q
........................................................................ [ 66%]
.....................................                                    [100%]
109 passed in 7.08s
```

```text
$ git diff --check
(only EOL warnings on artifacts/*.json; no whitespace/conflict-marker errors)
```

```text
$ git diff -- firedm/ > firedm-security-patch.diff
$ wc -l firedm-security-patch.diff
242 firedm-security-patch.diff
```

```text
$ git apply --check -R firedm-security-patch.diff
(exit 0 -- patch identity confirmed)
```

```text
$ git diff --name-only -- firedm/ tests/ artifacts/security/
firedm/config.py
firedm/controller.py
firedm/setting.py
firedm/utils.py
firedm/video.py
```

```text
$ python -m ruff check .
ModuleNotFoundError: No module named 'ruff'
$ python -m mypy --version
ModuleNotFoundError: No module named 'mypy'
```
(both linters absent in the audit interpreter; recorded per role spec.
 CI runs them on the modernized seam.)

## Executive Summary

| ID | Severity | Category | File | Function/Class | Lines | Status | CVSS |
|----|----------|----------|------|----------------|-------|--------|------|

No fully verified findings met the reporting threshold.

## Verified Findings

(none)

## Consolidated Patch

Reference:

```text
firedm-security-patch.diff
```

Patch applicability:

```text
$ git apply --check -R firedm-security-patch.diff
(exit 0)
```

The 242-line patch captured by `firedm-security-patch.diff` is the
**existing** F-CRIT-1..F-HIGH-6 mitigation already present in the
working tree at audit start. This audit pass authored **zero new
source-code patches** because no candidate reached `ADMITTED_FINDING`
(see candidate ledger for per-candidate evidence). The diff is
preserved verbatim so the prior mitigations remain a reviewable unit.

## Regression Suite

```text
$ python -m pytest -q
........................................................................ [ 66%]
.....................................                                    [100%]
109 passed in 7.08s
```

The 8 tests in `tests/test_security.py` (existing) cover F-CRIT-1
through F-HIGH-6 and re-passed against the current checkout. No new
tests were added by this audit pass.

## Files Changed (vs HEAD)

```text
firedm/config.py
firedm/controller.py
firedm/setting.py
firedm/utils.py
firedm/video.py
```

(All five are pre-existing modifications carrying the F-CRIT-1..F-HIGH-6
mitigations; none were modified by this audit pass.)

## Files Inspected

The audit read or grep-inspected the following files (non-exhaustive,
critical-path subset):

```text
firedm/FireDM.py
firedm/__init__.py
firedm/__main__.py
firedm/app_paths.py
firedm/brain.py
firedm/cmdview.py
firedm/config.py
firedm/controller.py
firedm/dependency.py
firedm/downloaditem.py
firedm/extractor_adapter.py
firedm/ffmpeg_commands.py
firedm/ffmpeg_service.py
firedm/model.py
firedm/setting.py
firedm/tkview.py
firedm/tool_discovery.py
firedm/update.py
firedm/utils.py
firedm/video.py
firedm/worker.py
pyproject.toml
requirements.txt
setup.py
tests/test_security.py
tests/test_ffmpeg_service.py
tests/test_extractor_service.py
tests/test_ffmpeg_pipeline.py
tests/test_packaged_diagnostics.py
artifacts/security/audit_2026-04-26.md (prior audit reference)
```

## Candidate Ledger

Reference:

```text
artifacts/security/candidate_ledger.md
```

Sixteen candidates were enumerated; every one resolved to a
`REJECTED_*` terminal state. Per-candidate reproduction commands and
exact pre-patch results are recorded in `command_log.md`
(CMD-016..CMD-026).

| ID | Title | Terminal state |
|----|-------|----------------|
| CAND-01 | APPDATA-planted ffmpeg.exe pre-empts system PATH | REJECTED_NO_SECURITY_BOUNDARY |
| CAND-02 | ffmpeg argv leading-dash via filename | REJECTED_EXISTING_MITIGATION |
| CAND-03 | argv quote escape via embedded `"` | REJECTED_EXISTING_MITIGATION |
| CAND-04 | `skd://` → `https://` URL substitution | REJECTED_NO_SECURITY_BOUNDARY |
| CAND-05 | `sys.path.insert` of install/package dir | REJECTED_NO_SECURITY_BOUNDARY |
| CAND-06 | PyPI/GitHub package no signature/hash verification | REJECTED_OUT_OF_SCOPE |
| CAND-07 | POSIX path quote escape in `xdg-open`/`explorer /select` | REJECTED_EXISTING_MITIGATION |
| CAND-08 | ffmpeg HLS `-protocol_whitelist file,...` | REJECTED_EXISTING_MITIGATION |
| CAND-09 | `ffmpeg_actual_path` poisoning via setting.cfg | REJECTED_NO_SECURITY_BOUNDARY |
| CAND-10 | Windows reserved filename DoS | REJECTED_OUT_OF_SCOPE |
| CAND-11 | M3U8 segment-count DoS | REJECTED_OUT_OF_SCOPE |
| CAND-12 | Tk widget mutation from worker thread | REJECTED_OUT_OF_SCOPE |
| CAND-13 | `d.__dict__.update(refreshed_d.__dict__)` refresh path | REJECTED_NO_SECURITY_BOUNDARY |
| CAND-14 | `config.__dict__.update(sett)` from CLI Namespace | REJECTED_NO_SECURITY_BOUNDARY |
| CAND-15 | `simpledownload` uses `urllib.request.urlopen` | REJECTED_OUT_OF_SCOPE |
| CAND-16 | `seg.__dict__.update(item)` from `progress_info.txt` | REJECTED_NO_SECURITY_BOUNDARY |

## Attack Surface Map

Reference:

```text
artifacts/security/attack_surface_map.md
```

The map documents 15 subsystems (startup/CLI, controller, network,
extractor, HLS, ffmpeg/subprocess, config/state, update, tool
discovery, archive extraction, filesystem path, GUI opener, threading,
packaging, test infrastructure) with per-subsystem entry points,
trusted/untrusted inputs, dangerous sinks, existing validation, and
candidate IDs.

## Coverage Limitations

The following environmental constraints applied during the audit. None
of these are claims about the codebase:

- `ruff` and `mypy` were not installed in the audit interpreter; CI
  remains the source of truth for those checks
  (`pyproject.toml [tool.ruff]` and `[tool.mypy]`).
- All reproductions were Python-side only; no real ffmpeg invocation,
  no live PyPI/GitHub network calls, no live yt_dlp extraction.
- The audit ran on Python 3.10.11; the project pins
  `requires-python = ">=3.10,<3.11"`, so this exactly matches the
  supported runtime.
- The Windows-specific reproductions (CAND-01, CAND-02) were exercised
  through the cross-platform code paths driven by
  `operating_system="Windows"`. Real-Windows-binary semantics
  (`os.startfile`, `explorer /select`) were inspected statically.

## Final Statement

*"No fully verified findings met the reporting threshold."*

This is not a claim that the codebase has no vulnerabilities; it is a
statement that none of the candidates this audit enumerated reached
the role-spec admission gate. The existing F-CRIT-1..F-HIGH-6
mitigations remain in place and pass their regression tests against
the current checkout.
