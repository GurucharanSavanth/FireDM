"""Validate that playlist entries are normalized to downloadable URLs.

Exercises a realistic mix of entry shapes (full URL, id-only, partial,
broken) through `firedm.playlist_entry.normalize_entry` and writes a
report under `artifacts/playlist/playlist_normalization_report.json`.

Exit code 0 when every entry that *should* normalize does, and every
entry that *should* be rejected is rejected.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = REPO_ROOT / "artifacts" / "playlist"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO_ROOT))

from firedm.playlist_entry import normalize_entry  # noqa: E402


CASES = [
    {
        "name": "full_webpage_url",
        "vid_info": {
            "webpage_url": "https://www.youtube.com/watch?v=abc1234567X",
            "url": "https://www.youtube.com/watch?v=abc1234567X",
            "id": "abc1234567X", "ie_key": "Youtube",
        },
        "expected_url": "https://www.youtube.com/watch?v=abc1234567X",
        "expected_normalized": False,
    },
    {
        "name": "bare_id_with_ie_key",
        "vid_info": {"id": "def2345678Y", "ie_key": "Youtube"},
        "expected_url": "https://www.youtube.com/watch?v=def2345678Y",
        "expected_normalized": True,
    },
    {
        "name": "bare_id_no_ie_key",
        "vid_info": {"id": "C4C8JsgGrrY"},
        "expected_url": "https://www.youtube.com/watch?v=C4C8JsgGrrY",
        "expected_normalized": True,
    },
    {
        "name": "url_field_holds_bare_id",
        "vid_info": {"url": "dQw4w9WgXcQ"},
        "expected_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "expected_normalized": True,
    },
    {
        "name": "vimeo_numeric",
        "vid_info": {"id": "76979871", "ie_key": "Vimeo"},
        "expected_url": "https://vimeo.com/76979871",
        "expected_normalized": True,
    },
    {
        "name": "empty_entry",
        "vid_info": {},
        "expected_url": None,
        "expected_normalized": None,
    },
    {
        "name": "numeric_id_no_ie_key_unknown_source",
        "vid_info": {"id": "12345"},
        "expected_url": None,
        "expected_normalized": None,
    },
]


def main() -> int:
    results = []
    all_ok = True
    for case in CASES:
        ne = normalize_entry(case["vid_info"])
        actual_url = ne.url if ne is not None else None
        actual_normalized = ne.was_normalized if ne is not None else None
        passed = (
            actual_url == case["expected_url"]
            and actual_normalized == case["expected_normalized"]
        )
        if not passed:
            all_ok = False
        results.append({
            "name": case["name"],
            "expected_url": case["expected_url"],
            "actual_url": actual_url,
            "expected_normalized": case["expected_normalized"],
            "actual_normalized": actual_normalized,
            "source_field": ne.source_field if ne else None,
            "passed": passed,
        })

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total": len(CASES),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "overall_passed": all_ok,
        "cases": results,
    }
    (ARTIFACTS / "playlist_normalization_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
