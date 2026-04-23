"""Smoke tests for the diagnostics a packaged build must expose.

These run against the source tree and assert that every diagnostic
command the packaged app relies on produces non-empty, parseable output.
Commit 9 adds the actual PyInstaller invocation.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


def _run(args, timeout=60):
    result = subprocess.run(
        [PY, *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result


def test_firedm_help_runs_from_source():
    r = _run(["-m", "firedm", "--help"])
    assert r.returncode == 0, r.stderr
    assert "firedm" in (r.stdout + r.stderr).lower()


def test_firedm_imports_only_runs_from_source():
    """`--imports-only` was added to validate that the app can import its
    dependencies at startup. Packaged builds rely on this for CI smoke."""
    r = _run([str(REPO_ROOT / "firedm.py"), "--imports-only"])
    assert r.returncode == 0, r.stderr


def test_verify_extractor_default_script_passes():
    """Runtime proof that `yt_dlp` is selected. The script always writes
    `artifacts/extractor/default_selection_proof.json` — we read that
    instead of parsing noisy stdout."""
    r = _run(["scripts/verify_extractor_default.py"], timeout=120)
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
    proof = REPO_ROOT / "artifacts" / "extractor" / "default_selection_proof.json"
    assert proof.exists(), "verify script must produce the proof artifact"
    data = json.loads(proof.read_text(encoding="utf-8"))
    assert data["passed"] is True
    assert data["active"] == "yt_dlp"


def test_smoke_video_pipeline_script_passes():
    r = _run(["scripts/smoke_video_pipeline.py"], timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
