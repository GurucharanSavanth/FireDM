"""Reproduce the P0 YouTube single-video and playlist bug.

This script drives FireDM's extractor pipeline in-process, without launching
the GUI, to prove how `create_video_playlist()` responds to real YouTube URLs.
It captures structured pass/fail diagnostics for every stage:

    1. extractor import readiness (race detection)
    2. active extractor selection
    3. single-video metadata extraction
    4. single-video stream menu generation
    5. single-video selected stream + URL resolution
    6. playlist metadata extraction
    7. playlist entry URL normalization (ID-only entries → real URLs)
    8. per-entry processing + stream menu generation

Outputs:
    artifacts/repro/single_video_repro.log
    artifacts/repro/playlist_repro.log
    artifacts/repro/repro_summary.json

Exit code is 0 if reproduction produced a definitive result (pass OR fail),
non-zero only if the harness itself crashed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = REPO_ROOT / "artifacts" / "repro"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

# Default targets chosen for stability: "Me at the zoo" (first YouTube video) is
# famously permanent; the Google Developers tutorial playlist is long-lived.
DEFAULT_SINGLE = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
DEFAULT_PLAYLIST = "https://www.youtube.com/playlist?list=PLt1SIbA8guusxiHz9bveV-UHs_biWFegU"


@dataclass
class StageResult:
    name: str
    passed: bool = False
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class ReproReport:
    target: str
    target_url: str
    stages: list[StageResult] = field(default_factory=list)
    overall_passed: bool = False
    harness_error: str | None = None


def _stage(report: ReproReport, name: str) -> StageResult:
    stage = StageResult(name=name)
    report.stages.append(stage)
    return stage


def _wait_for_extractor_ready(timeout: float) -> tuple[bool, str]:
    from firedm import video
    from firedm.extractor_adapter import PRIMARY_EXTRACTOR

    deadline = time.time() + timeout
    while time.time() < deadline:
        if video.ytdl is not None:
            break
        time.sleep(0.2)
    else:
        return False, "extractor did not initialize within timeout"

    selected = getattr(video.ytdl, "__name__", "?")
    return selected == PRIMARY_EXTRACTOR, f"active={selected}, preferred={PRIMARY_EXTRACTOR}"


def run_single_video(url: str, log_path: Path) -> ReproReport:
    report = ReproReport(target="single-video", target_url=url)
    log_lines: list[str] = [f"[repro] single-video url: {url}"]

    def _log(msg: str) -> None:
        log_lines.append(msg)
        print(msg, flush=True)

    try:
        from firedm import config, video
        from firedm.video import load_extractor_engines

        # Stage 1 — extractor readiness
        stage = _stage(report, "extractor_ready")
        load_extractor_engines()
        ready_primary, detail = _wait_for_extractor_ready(timeout=45.0)
        stage.detail = detail
        stage.data = {
            "active_module": getattr(video.ytdl, "__name__", None),
            "configured": config.active_video_extractor,
            "yt_dlp_version": config.yt_dlp_version,
            "youtube_dl_version": config.youtube_dl_version,
        }
        stage.passed = video.ytdl is not None
        _log(f"[stage extractor_ready] passed={stage.passed} detail={detail}")
        if not stage.passed:
            return report

        # Stage 2 — default-selection proof
        stage = _stage(report, "default_is_primary")
        stage.passed = ready_primary
        stage.detail = detail
        stage.data = {"active_is_primary": ready_primary}
        _log(f"[stage default_is_primary] passed={stage.passed}")

        # Stage 3 — create_video_playlist on single video URL
        from firedm.controller import create_video_playlist
        stage = _stage(report, "create_video_playlist")
        try:
            pl = create_video_playlist(url)
            stage.passed = bool(pl) and len(pl) == 1
            stage.detail = f"returned {len(pl) if pl else 0} items"
            stage.data = {"count": len(pl) if pl else 0}
            _log(f"[stage create_video_playlist] passed={stage.passed} {stage.detail}")
            if not stage.passed:
                return report
            vid = pl[0]
        except Exception as e:  # noqa: BLE001 — diagnostic tool, capture anything
            stage.error = f"{type(e).__name__}: {e}"
            stage.detail = stage.error
            _log(f"[stage create_video_playlist] raised: {stage.error}")
            _log(traceback.format_exc())
            return report

        # Stage 4 — stream menu populated
        stage = _stage(report, "stream_menu")
        stream_menu = getattr(vid, "stream_menu", [])
        all_streams = getattr(vid, "all_streams", [])
        stage.passed = bool(all_streams)
        stage.data = {
            "streams": len(all_streams),
            "menu_entries": len(stream_menu),
            "title": getattr(vid, "title", ""),
        }
        stage.detail = f"{len(all_streams)} streams, title={vid.title!r}"
        _log(f"[stage stream_menu] passed={stage.passed} {stage.detail}")

        # Stage 5 — selected stream has a resolvable URL
        stage = _stage(report, "selected_stream_url")
        try:
            vid.select_stream(index=1)
            sel = vid.selected_stream
            eff_url = getattr(vid, "eff_url", None) or (sel.url if sel else None)
            stage.passed = bool(eff_url)
            stage.data = {
                "selected_name": getattr(sel, "name", None),
                "mediatype": getattr(sel, "mediatype", None),
                "extension": getattr(sel, "extension", None),
                "has_eff_url": bool(eff_url),
            }
            stage.detail = f"selected={getattr(sel, 'name', None)}, has_url={bool(eff_url)}"
            _log(f"[stage selected_stream_url] passed={stage.passed} {stage.detail}")
        except Exception as e:  # noqa: BLE001
            stage.error = f"{type(e).__name__}: {e}"
            stage.detail = stage.error
            _log(f"[stage selected_stream_url] raised: {stage.error}")

        report.overall_passed = all(s.passed for s in report.stages)
    except Exception as e:  # noqa: BLE001
        report.harness_error = f"{type(e).__name__}: {e}"
        _log(f"[harness] crashed: {report.harness_error}")
        _log(traceback.format_exc())
    finally:
        log_path.write_text("\n".join(log_lines), encoding="utf-8")
    return report


def run_playlist(url: str, log_path: Path) -> ReproReport:
    report = ReproReport(target="playlist", target_url=url)
    log_lines: list[str] = [f"[repro] playlist url: {url}"]

    def _log(msg: str) -> None:
        log_lines.append(msg)
        print(msg, flush=True)

    try:
        from firedm import config, video
        from firedm.video import load_extractor_engines, process_video

        stage = _stage(report, "extractor_ready")
        load_extractor_engines()
        ready_primary, detail = _wait_for_extractor_ready(timeout=45.0)
        stage.detail = detail
        stage.data = {
            "active_module": getattr(video.ytdl, "__name__", None),
            "configured": config.active_video_extractor,
        }
        stage.passed = video.ytdl is not None
        _log(f"[stage extractor_ready] passed={stage.passed} detail={detail}")
        if not stage.passed:
            return report

        from firedm.controller import create_video_playlist
        stage = _stage(report, "create_video_playlist")
        try:
            pl = create_video_playlist(url)
            stage.passed = bool(pl) and len(pl) >= 2  # expect multiple entries
            stage.detail = f"returned {len(pl) if pl else 0} items"
            stage.data = {"count": len(pl) if pl else 0}
            _log(f"[stage create_video_playlist] passed={stage.passed} {stage.detail}")
            if not pl:
                return report
        except Exception as e:  # noqa: BLE001
            stage.error = f"{type(e).__name__}: {e}"
            stage.detail = stage.error
            _log(f"[stage create_video_playlist] raised: {stage.error}")
            _log(traceback.format_exc())
            return report

        # Stage — entry URL normalization
        stage = _stage(report, "entry_url_normalization")
        malformed = []
        for idx, v in enumerate(pl[:5]):
            u = getattr(v, "url", "") or ""
            ok = u.startswith("http://") or u.startswith("https://")
            if not ok:
                malformed.append({"idx": idx, "url": u, "title": getattr(v, "title", "")})
        stage.passed = not malformed
        stage.data = {"inspected": min(5, len(pl)), "malformed": malformed}
        stage.detail = f"inspected {min(5, len(pl))}, malformed={len(malformed)}"
        _log(f"[stage entry_url_normalization] passed={stage.passed} {stage.detail}")

        # Stage — process first entry (drives full per-item extraction)
        stage = _stage(report, "process_first_entry")
        try:
            first = pl[0]
            process_video(first)
            streams = getattr(first, "all_streams", [])
            stage.passed = bool(streams)
            stage.data = {
                "title": getattr(first, "title", ""),
                "streams": len(streams),
                "processed": getattr(first, "processed", False),
            }
            stage.detail = f"processed={first.processed}, streams={len(streams)}"
            _log(f"[stage process_first_entry] passed={stage.passed} {stage.detail}")
        except Exception as e:  # noqa: BLE001
            stage.error = f"{type(e).__name__}: {e}"
            stage.detail = stage.error
            _log(f"[stage process_first_entry] raised: {stage.error}")
            _log(traceback.format_exc())

        report.overall_passed = all(s.passed for s in report.stages)
    except Exception as e:  # noqa: BLE001
        report.harness_error = f"{type(e).__name__}: {e}"
        _log(f"[harness] crashed: {report.harness_error}")
        _log(traceback.format_exc())
    finally:
        log_path.write_text("\n".join(log_lines), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--single-url", default=DEFAULT_SINGLE)
    parser.add_argument("--playlist-url", default=DEFAULT_PLAYLIST)
    parser.add_argument("--skip-single", action="store_true")
    parser.add_argument("--skip-playlist", action="store_true")
    args = parser.parse_args()

    # Force repo root on sys.path so "firedm" imports from source.
    sys.path.insert(0, str(REPO_ROOT))

    summary: dict[str, Any] = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "targets": {}}

    if not args.skip_single:
        single_log = ARTIFACTS / "single_video_repro.log"
        single = run_single_video(args.single_url, single_log)
        summary["targets"]["single_video"] = {
            "url": single.target_url,
            "overall_passed": single.overall_passed,
            "harness_error": single.harness_error,
            "stages": [asdict(s) for s in single.stages],
        }

    if not args.skip_playlist:
        playlist_log = ARTIFACTS / "playlist_repro.log"
        playlist = run_playlist(args.playlist_url, playlist_log)
        summary["targets"]["playlist"] = {
            "url": playlist.target_url,
            "overall_passed": playlist.overall_passed,
            "harness_error": playlist.harness_error,
            "stages": [asdict(s) for s in playlist.stages],
        }

    out = ARTIFACTS / "repro_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[repro] wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
