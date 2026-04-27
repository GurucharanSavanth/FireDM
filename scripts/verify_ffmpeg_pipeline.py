"""Validate the ffmpeg discovery + command construction pipeline.

Writes:
    artifacts/ffmpeg/ffmpeg_pipeline_result.json
    artifacts/ffmpeg/merge_command_audit.md

Exit code 0 when ffmpeg is located AND all command builders produce the
expected shape. Exit 1 if ffmpeg cannot be located. The discovery check
only affects the exit code (not the audit) so the audit is always written
for documentation purposes.
"""

from __future__ import annotations

import json
import shlex
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = REPO_ROOT / "artifacts" / "ffmpeg"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO_ROOT))

from firedm import config  # noqa: E402
from firedm.ffmpeg_commands import (  # noqa: E402
    build_audio_convert_command,
    build_hls_process_command,
    build_merge_command,
    dash_audio_extension_for,
)
from firedm.ffmpeg_service import collect_media_tool_health  # noqa: E402


def main() -> int:
    media_tools = collect_media_tool_health(
        saved_ffmpeg_path=config.ffmpeg_actual_path or "",
        search_dirs=(config.current_directory, config.global_sett_folder or ""),
        operating_system=config.operating_system,
    )
    ff_info = media_tools["ffmpeg"]
    ffprobe_info = media_tools["ffprobe"]

    ffmpeg_path = str(ff_info["path"] or "ffmpeg")

    merge = build_merge_command(
        video_file="video.mp4", audio_file="audio.m4a",
        output_file="out.mp4", ffmpeg_path=ffmpeg_path,
    )
    hls = build_hls_process_command(
        m3u8_path="local.m3u8", output_file="out.mp4",
        ffmpeg_path=ffmpeg_path,
    )
    audio_conv = build_audio_convert_command(
        input_file="in.m4a", output_file="out.mp3",
        ffmpeg_path=ffmpeg_path,
    )

    merge_fast_argv = shlex.split(merge.fast)
    hls_fast_argv = shlex.split(hls.fast)
    audio_fast_argv = shlex.split(audio_conv.fast)

    dash_rules = {
        "mp4": dash_audio_extension_for("mp4"),
        "webm": dash_audio_extension_for("webm"),
        "mkv": dash_audio_extension_for("mkv"),
    }

    result = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "ffmpeg": ff_info,
        "ffprobe": ffprobe_info,
        "merge_command": {
            "fast_uses_stream_copy": "-c copy" in merge.fast,
            "slow_reencodes": "-c copy" not in merge.slow,
            "argv_fast_length": len(merge_fast_argv),
        },
        "hls_command": {
            "protocol_whitelist_set": "-protocol_whitelist" in hls.fast,
            "allowed_extensions_all": "-allowed_extensions" in hls.fast,
            "argv_fast_length": len(hls_fast_argv),
        },
        "audio_convert_command": {
            "fast_uses_acodec_copy": "-acodec copy" in audio_conv.fast,
            "argv_fast_length": len(audio_fast_argv),
        },
        "dash_audio_extension_rules": dash_rules,
    }

    (ARTIFACTS / "ffmpeg_pipeline_result.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )

    audit_lines = [
        "# FFmpeg Merge Command Audit\n",
        f"- Timestamp: `{result['timestamp']}`",
        f"- ffmpeg path: `{ff_info['path'] or '(not located)'}`",
        f"- ffmpeg version: `{ff_info['version'] or '(unknown)'}`",
        f"- ffmpeg usable: `{ff_info['usable']}`",
        f"- ffprobe path: `{ffprobe_info['path'] or '(not located)'}`",
        f"- ffprobe usable: `{ffprobe_info['usable']}`",
        "",
        "## Merge command (DASH video + audio → single container)",
        "",
        "Fast (stream copy):",
        "```",
        merge.fast,
        "```",
        "",
        "Slow (transcode fallback):",
        "```",
        merge.slow,
        "```",
        "",
        "## HLS process command",
        "",
        "Fast:",
        "```",
        hls.fast,
        "```",
        "",
        "## Audio convert command",
        "",
        "Fast:",
        "```",
        audio_conv.fast,
        "```",
        "",
        "## DASH audio extension pairing rules",
        "",
        "| Video ext | Audio ext |",
        "| --- | --- |",
    ]
    for video_ext, audio_ext in dash_rules.items():
        audit_lines.append(f"| `{video_ext}` | `{audio_ext}` |")
    audit_lines.append("")
    audit_lines.append(
        "These rules live in `firedm/ffmpeg_commands.py :: dash_audio_extension_for`."
    )

    (ARTIFACTS / "merge_command_audit.md").write_text("\n".join(audit_lines), encoding="utf-8")

    print(json.dumps(result, indent=2))
    return 0 if ff_info["usable"] else 1


if __name__ == "__main__":
    sys.exit(main())
