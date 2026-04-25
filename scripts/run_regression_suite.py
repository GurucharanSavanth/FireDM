"""Run the critical regression suite for the revived video/download pipeline.

Invokes pytest on the targeted regression test files and writes
`artifacts/regression/regression_suite_result.json` with a summary the CI
matrix (and Commit 10 handover docs) can consume.

Exit code mirrors pytest's exit code. Non-zero means a regression.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = REPO_ROOT / "artifacts" / "regression"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

TARGETS = [
    "tests/test_extractor_service.py",
    "tests/test_extractor_default_selection.py",
    "tests/test_extractor_adapter.py",
    "tests/test_legacy_extractor_fallback.py",
    "tests/test_playlist_entry_normalization.py",
    "tests/test_playlist_flow.py",
    "tests/test_single_video_flow.py",
    "tests/test_stream_selection.py",
    "tests/test_ffmpeg_pipeline.py",
    "tests/test_download_handoff.py",
    "tests/test_controller_video_integration.py",
]


def main() -> int:
    start = time.time()
    cmd = [sys.executable, "-m", "pytest", "--tb=short", "-q", *TARGETS]
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    duration = time.time() - start

    lines = (proc.stdout or "").splitlines()
    summary_line = next((ln for ln in reversed(lines) if "passed" in ln or "failed" in ln), "")

    result = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "exit_code": proc.returncode,
        "duration_seconds": round(duration, 2),
        "targets": TARGETS,
        "pytest_summary_line": summary_line,
        "stdout_tail": lines[-30:],
    }
    (ARTIFACTS / "regression_suite_result.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
