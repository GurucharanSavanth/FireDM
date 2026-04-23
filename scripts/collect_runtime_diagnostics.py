"""Dump a runtime diagnostics snapshot for the FireDM pipeline.

Writes `artifacts/diagnostics/runtime_snapshot.json` with everything a
maintainer needs to triage a user bug report:

    - Python version, platform
    - Extractor service state (active, primary, fallback, versions)
    - ffmpeg discovery + version
    - Active config values relevant to video extraction
    - Key runtime folders (`sett_folder`, `global_sett_folder`,
      `download_folder`, `temp_folder`)
    - Pipeline logger stage constants (sanity check)
"""

from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = REPO_ROOT / "artifacts" / "diagnostics"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from firedm import config, video
    from firedm.extractor_adapter import SERVICE
    from firedm.ffmpeg_service import locate_ffmpeg
    from firedm.pipeline_logger import PipelineStage

    video.load_extractor_engines()
    SERVICE.wait_until_ready(timeout=30.0)

    ff = locate_ffmpeg(
        saved_path=config.ffmpeg_actual_path or "",
        search_dirs=(config.current_directory, config.global_sett_folder or ""),
        operating_system=config.operating_system,
    )

    snapshot = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "python": sys.version,
        "platform": platform.platform(),
        "extractor_service": SERVICE.snapshot(),
        "legacy_ytdl_global": getattr(video.ytdl, "__name__", None),
        "ffmpeg": {
            "path": ff.path,
            "version": ff.version,
            "found": ff.found,
        },
        "config": {
            "active_video_extractor": config.active_video_extractor,
            "yt_dlp_version": config.yt_dlp_version,
            "youtube_dl_version": config.youtube_dl_version,
            "download_folder": config.download_folder,
            "sett_folder": config.sett_folder,
            "global_sett_folder": config.global_sett_folder,
            "temp_folder": config.temp_folder,
            "use_cookies": config.use_cookies,
            "max_concurrent_downloads": config.max_concurrent_downloads,
        },
        "pipeline_stages": {
            attr: getattr(PipelineStage, attr)
            for attr in dir(PipelineStage)
            if not attr.startswith("_")
        },
    }

    out = ARTIFACTS / "runtime_snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(json.dumps(snapshot, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
