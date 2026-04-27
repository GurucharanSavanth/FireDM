"""
Helpers for locating and probing ffmpeg without coupling callers to shell parsing.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

from .tool_discovery import executable_name, resolve_binary_path

ToolRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class FFmpegInfo:
    found: bool
    path: str = ""
    version: str = ""
    usable: bool = False
    failure: str = ""
    returncode: int | None = None


def ffmpeg_binary_name(operating_system: str) -> str:
    return "ffmpeg.exe" if operating_system == "Windows" else "ffmpeg"


def ffprobe_binary_name(operating_system: str) -> str:
    return "ffprobe.exe" if operating_system == "Windows" else "ffprobe"


def parse_ffmpeg_version(output: str) -> str:
    match = re.search(r"ffmpeg version (.*?) Copyright", output, re.IGNORECASE)
    return match.group(1) if match else ""


def parse_ffprobe_version(output: str) -> str:
    match = re.search(r"ffprobe version (.*?) Copyright", output, re.IGNORECASE)
    return match.group(1) if match else ""


def _resolve_binary_path(
    name: str,
    *,
    saved_path: str = "",
    search_dirs: Iterable[str | os.PathLike[str]] = (),
    operating_system: str,
    path_lookup: Callable[[str], str | None] = shutil.which,
    include_winget: bool = True,
    winget_package_root: str | os.PathLike[str] | None = None,
) -> str:
    if saved_path:
        custom_path = Path(saved_path)
        return os.fspath(custom_path.resolve()) if custom_path.is_file() else ""

    return resolve_binary_path(
        name,
        search_dirs=search_dirs,
        operating_system=operating_system,
        path_lookup=path_lookup,
        include_winget=include_winget,
        winget_package_root=winget_package_root,
    )


def _sibling_tool_path(
    anchor_path: str,
    tool_name: str,
    *,
    operating_system: str,
) -> str:
    if not anchor_path:
        return ""

    candidate = Path(anchor_path).parent / executable_name(tool_name, operating_system)
    return os.fspath(candidate.resolve()) if candidate.is_file() else ""


def _default_version_runner(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )


def _short_failure(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:240]
    return ""


def _probe_tool(
    tool_path: str,
    *,
    parser: Callable[[str], str],
    runner: ToolRunner | None = None,
) -> FFmpegInfo:
    if not tool_path:
        return FFmpegInfo(found=False, failure="not found")

    run_version = runner or _default_version_runner
    try:
        result = run_version([tool_path, "-version"])
    except Exception as exc:
        return FFmpegInfo(
            found=True,
            path=tool_path,
            usable=False,
            failure=_short_failure(str(exc)) or exc.__class__.__name__,
        )

    output = (result.stdout or "") + (result.stderr or "")
    version = parser(output)
    if result.returncode != 0:
        return FFmpegInfo(
            found=True,
            path=tool_path,
            version=version,
            usable=False,
            failure=_short_failure(output) or f"exit code {result.returncode}",
            returncode=result.returncode,
        )

    return FFmpegInfo(
        found=True,
        path=tool_path,
        version=version,
        usable=True,
        returncode=result.returncode,
    )


def resolve_ffmpeg_path(
    *,
    saved_path: str = "",
    search_dirs: Iterable[str | os.PathLike[str]] = (),
    operating_system: str,
    path_lookup: Callable[[str], str | None] = shutil.which,
    include_winget: bool = True,
    winget_package_root: str | os.PathLike[str] | None = None,
) -> str:
    return _resolve_binary_path(
        "ffmpeg",
        saved_path=saved_path,
        search_dirs=search_dirs,
        operating_system=operating_system,
        path_lookup=path_lookup,
        include_winget=include_winget,
        winget_package_root=winget_package_root,
    )


def resolve_ffprobe_path(
    *,
    ffmpeg_path: str = "",
    saved_ffmpeg_path: str = "",
    search_dirs: Iterable[str | os.PathLike[str]] = (),
    operating_system: str,
    path_lookup: Callable[[str], str | None] = shutil.which,
    include_winget: bool = True,
    winget_package_root: str | os.PathLike[str] | None = None,
) -> str:
    for anchor_path in (ffmpeg_path, saved_ffmpeg_path):
        sibling_path = _sibling_tool_path(
            anchor_path,
            "ffprobe",
            operating_system=operating_system,
        )
        if sibling_path:
            return sibling_path

    return resolve_binary_path(
        "ffprobe",
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
    runner: ToolRunner | None = None,
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
    if not ffmpeg_path and saved_path:
        return FFmpegInfo(found=False, failure="custom path not found")
    return _probe_tool(ffmpeg_path, parser=parse_ffmpeg_version, runner=runner)


def locate_ffprobe(
    *,
    ffmpeg_path: str = "",
    saved_ffmpeg_path: str = "",
    search_dirs: Iterable[str | os.PathLike[str]] = (),
    operating_system: str,
    path_lookup: Callable[[str], str | None] = shutil.which,
    runner: ToolRunner | None = None,
    include_winget: bool = True,
    winget_package_root: str | os.PathLike[str] | None = None,
) -> FFmpegInfo:
    ffprobe_path = resolve_ffprobe_path(
        ffmpeg_path=ffmpeg_path,
        saved_ffmpeg_path=saved_ffmpeg_path,
        search_dirs=search_dirs,
        operating_system=operating_system,
        path_lookup=path_lookup,
        include_winget=include_winget,
        winget_package_root=winget_package_root,
    )
    return _probe_tool(ffprobe_path, parser=parse_ffprobe_version, runner=runner)


def collect_media_tool_health(
    *,
    saved_ffmpeg_path: str = "",
    search_dirs: Iterable[str | os.PathLike[str]] = (),
    operating_system: str,
    path_lookup: Callable[[str], str | None] = shutil.which,
    runner: ToolRunner | None = None,
    include_winget: bool = True,
    winget_package_root: str | os.PathLike[str] | None = None,
) -> dict[str, dict[str, object]]:
    ffmpeg = locate_ffmpeg(
        saved_path=saved_ffmpeg_path,
        search_dirs=search_dirs,
        operating_system=operating_system,
        path_lookup=path_lookup,
        runner=runner,
        include_winget=include_winget,
        winget_package_root=winget_package_root,
    )
    ffprobe = locate_ffprobe(
        ffmpeg_path=ffmpeg.path,
        saved_ffmpeg_path=saved_ffmpeg_path,
        search_dirs=search_dirs,
        operating_system=operating_system,
        path_lookup=path_lookup,
        runner=runner,
        include_winget=include_winget,
        winget_package_root=winget_package_root,
    )
    return {
        "ffmpeg": asdict(ffmpeg),
        "ffprobe": asdict(ffprobe),
    }
