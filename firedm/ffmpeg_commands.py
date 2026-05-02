"""Pure helpers for building ffmpeg command lines.

Extracted from `firedm/video.py` so the command construction can be
unit-tested without invoking the binary and the exact argv is asserted
(not just a smoke pass/fail).

Each helper returns a pair `(fast_cmd, slow_cmd)`:

    * `fast_cmd` uses `-c copy` (stream copy) for matching containers.
    * `slow_cmd` re-encodes when fast fails.

The callers (`video.merge_video_audio`, `video.post_process_hls`,
`video.convert_audio`) try fast first and fall back to slow.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


def _quote(value: str) -> str:
    """Windows-friendly quoting. Double-quotes + escape embedded quotes."""
    return '"' + str(value).replace('"', '\\"') + '"'


@dataclass(frozen=True)
class FfmpegCommandPair:
    fast: str
    slow: str

    def as_tuple(self) -> tuple[str, str]:
        return self.fast, self.slow


def build_merge_command(
    *,
    video_file: str,
    audio_file: str,
    output_file: str,
    ffmpeg_path: str,
) -> FfmpegCommandPair:
    """Command line for merging a DASH video + audio into a container."""
    base = (
        f"{_quote(ffmpeg_path)} -loglevel error -stats -y "
        f"-i {_quote(video_file)} -i {_quote(audio_file)}"
    )
    fast = f"{base} -c copy {_quote(output_file)}"
    slow = f"{base} {_quote(output_file)}"
    return FfmpegCommandPair(fast=fast, slow=slow)


def build_hls_process_command(
    *,
    m3u8_path: str,
    output_file: str,
    ffmpeg_path: str,
) -> FfmpegCommandPair:
    """Command line for converting an HLS m3u8 pointer into a local file."""
    base = (
        f"{_quote(ffmpeg_path)} -loglevel error -stats -y "
        f'-protocol_whitelist "file,http,https,tcp,tls,crypto" '
        f"-allowed_extensions ALL "
        f"-i {_quote(m3u8_path)}"
    )
    fast = f'{base} -c copy "file:{output_file}"'
    slow = f'{base} "file:{output_file}"'
    return FfmpegCommandPair(fast=fast, slow=slow)


def build_audio_convert_command(
    *,
    input_file: str,
    output_file: str,
    ffmpeg_path: str,
) -> FfmpegCommandPair:
    """Command line for converting audio between containers."""
    base = (
        f"{_quote(ffmpeg_path)} -loglevel error -stats -y -i {_quote(input_file)}"
    )
    fast = f"{base} -acodec copy {_quote(output_file)}"
    slow = f"{base} {_quote(output_file)}"
    return FfmpegCommandPair(fast=fast, slow=slow)


def dash_audio_extension_for(video_extension: str) -> str:
    """Pick the best DASH audio container extension for a given video container.

    Rules (match historical behavior in `Video.select_audio`):
        * mp4  → m4a  (ffmpeg -c copy works cleanly)
        * webm → webm (only vorbis/opus audio in webm is valid)
        * anything else → mirror the video extension so caller can still
          attempt a stream copy.
    """
    if video_extension == "mp4":
        return "m4a"
    if video_extension == "webm":
        return "webm"
    return video_extension
