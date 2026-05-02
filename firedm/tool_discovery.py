"""Executable discovery helpers for external runtime tools."""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable, Iterable, Iterator, Mapping
from pathlib import Path

PathLookup = Callable[[str], str | None]


def executable_name(name: str, operating_system: str) -> str:
    if operating_system == "Windows" and not name.lower().endswith(".exe"):
        return f"{name}.exe"
    return name


def windows_winget_package_root(env: Mapping[str, str] | None = None) -> Path | None:
    env = env or os.environ
    local_app_data = env.get("LOCALAPPDATA")
    if not local_app_data:
        return None
    root = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
    return root if root.is_dir() else None


def env_tool_dirs(env: Mapping[str, str] | None = None) -> list[Path]:
    env = env or os.environ
    candidates = []
    tools_dir = env.get("FIREDM_TOOLS_DIR")
    if tools_dir:
        candidates.append(Path(tools_dir))
    install_dir = env.get("FIREDM_INSTALL_DIR")
    if install_dir:
        candidates.append(Path(install_dir) / "tools")
    return candidates


def iter_windows_winget_binaries(binary_name: str, root: str | os.PathLike[str] | None = None) -> Iterator[Path]:
    package_root = Path(root) if root else windows_winget_package_root()
    if not package_root or not package_root.is_dir():
        return

    try:
        matches = sorted(package_root.rglob(binary_name), key=lambda path: str(path).lower())
    except OSError:
        return

    for match in matches:
        if match.is_file():
            yield match.resolve()


def resolve_binary_path(
    name: str,
    *,
    saved_path: str = "",
    search_dirs: Iterable[str | os.PathLike[str]] = (),
    operating_system: str,
    path_lookup: PathLookup = shutil.which,
    include_winget: bool = True,
    winget_package_root: str | os.PathLike[str] | None = None,
) -> str:
    """Resolve a binary using explicit paths first, then PATH, then Winget."""
    if saved_path and Path(saved_path).is_file():
        return os.fspath(Path(saved_path).resolve())

    binary = executable_name(name, operating_system)

    for folder in [*search_dirs, *env_tool_dirs()]:
        if not folder:
            continue
        candidate = Path(folder) / binary
        if candidate.is_file():
            return os.fspath(candidate.resolve())

    system_path = path_lookup(binary)
    if system_path:
        return os.fspath(Path(system_path).resolve())

    if include_winget and operating_system == "Windows":
        for candidate in iter_windows_winget_binaries(binary, winget_package_root):
            return os.fspath(candidate)

    return ""
