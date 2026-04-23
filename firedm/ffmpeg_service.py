"""
Helpers for locating and probing ffmpeg without coupling callers to shell parsing.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from .tool_discovery import resolve_binary_path


@dataclass(frozen=True)
class FFmpegInfo:
    found: bool
    path: str = ""
    version: str = ""


def ffmpeg_binary_name(operating_system: str) -> str:
    return "ffmpeg.exe" if operating_system == "Windows" else "ffmpeg"


def parse_ffmpeg_version(output: str) -> str:
    match = re.search(r"ffmpeg version (.*?) Copyright", output, re.IGNORECASE)
    return match.group(1) if match else ""


def resolve_ffmpeg_path(
    *,
    saved_path: str = "",
    search_dirs: Iterable[str | os.PathLike[str]] = (),
    operating_system: str,
    path_lookup: Callable[[str], str | None] = shutil.which,
    include_winget: bool = True,
    winget_package_root: str | os.PathLike[str] | None = None,
) -> str:
    return resolve_binary_path(
        "ffmpeg",
        saved_path=saved_path,
        search_dirs=search_dirs,
        operating_system=operating_system,
        path_lookup=path_lookup,
        include_winget=include_winget,
        winget_package_root=winget_package_root,
    )


def locate_ffmpeg(
    *,
    saved_path: str = "",
    search_dirs: Iterable[str | os.PathLike[str]] = (),
    operating_system: str,
    path_lookup: Callable[[str], str | None] = shutil.which,
    runner: Callable[[list[str]], subprocess.CompletedProcess[str]] | None = None,
    include_winget: bool = True,
    winget_package_root: str | os.PathLike[str] | None = None,
) -> FFmpegInfo:
    ffmpeg_path = resolve_ffmpeg_path(
        saved_path=saved_path,
        search_dirs=search_dirs,
        operating_system=operating_system,
        path_lookup=path_lookup,
        include_winget=include_winget,
        winget_package_root=winget_package_root,
    )
    if not ffmpeg_path:
        return FFmpegInfo(found=False)

    runner = runner or (
        lambda cmd: subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    )

    result = runner([ffmpeg_path, "-version"])
    output = (result.stdout or "") + (result.stderr or "")
    return FFmpegInfo(
        found=True,
        path=ffmpeg_path,
        version=parse_ffmpeg_version(output),
    )
