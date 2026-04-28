"""Verify that the maintained extractor is the default runtime extractor.

Exit code 0 on pass, non-zero on fail. Writes proof JSON under
`artifacts/extractor/default_selection_proof.json`.

Usage:
    .\.venv\Scripts\python.exe scripts\verify_extractor_default.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def default_output_dir() -> Path:
    return Path(os.environ.get("FIREDM_EXTRACTOR_ARTIFACTS_DIR", REPO_ROOT / "artifacts" / "extractor"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify FireDM extractor default selection.")
    parser.add_argument("--output-dir", default=str(default_output_dir()))
    args = parser.parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(REPO_ROOT))
    from firedm import config, video
    from firedm.extractor_adapter import (
        FALLBACK_EXTRACTOR,
        PRIMARY_EXTRACTOR,
        SERVICE,
    )

    video.load_extractor_engines()
    ready = SERVICE.wait_until_ready(timeout=45.0)

    snapshot = SERVICE.snapshot()
    snapshot["configured_before"] = config.active_video_extractor
    snapshot["ready_within_45s"] = ready

    # Simulate a user who persisted the deprecated extractor and verify the
    # policy still overrides it.
    config.active_video_extractor = FALLBACK_EXTRACTOR
    video.set_default_extractor(FALLBACK_EXTRACTOR)
    snapshot["after_fallback_override"] = {
        "configured_value": config.active_video_extractor,
        "active": SERVICE.active_name(),
    }

    expected_active = PRIMARY_EXTRACTOR if snapshot["primary_loaded"] else FALLBACK_EXTRACTOR
    passed = (
        ready
        and SERVICE.active_name() == expected_active
        and snapshot["primary_loaded"]  # the repo must ship a primary-capable env
        and (not snapshot["primary_loaded"] or SERVICE.active_name() == PRIMARY_EXTRACTOR)
    )
    snapshot["expected_active"] = expected_active
    snapshot["passed"] = bool(passed)
    snapshot["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    out = output_dir / "default_selection_proof.json"
    out.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(json.dumps(snapshot, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
