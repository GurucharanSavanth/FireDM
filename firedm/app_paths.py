"""
Path resolution helpers for application settings and writable runtime folders.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from pathlib import Path


def resolve_global_settings_dir(
    app_name: str,
    operating_system: str,
    *,
    env: Mapping[str, str] | None = None,
    home: str | Path | None = None,
    current_directory: str | Path | None = None,
) -> Path:
    env = env or os.environ
    home_dir = Path(home) if home is not None else Path.home()

    if operating_system == "Windows":
        roaming = env.get("APPDATA")
        if roaming:
            return Path(roaming) / f".{app_name}"
        return home_dir / "AppData" / "Roaming" / f".{app_name}"

    if operating_system == "Linux":
        return home_dir / ".config" / app_name

    if operating_system == "Darwin":
        return home_dir / "Library" / "Application Support" / app_name

    fallback = current_directory if current_directory is not None else home_dir
    return Path(fallback)


def directory_is_writable(path: str | Path) -> bool:
    target = Path(path)
    probe = target / ".firedm-write-test"

    try:
        with probe.open("w", encoding="utf-8") as handle:
            handle.write("0")
        probe.unlink()
        return True
    except OSError:
        return False


def choose_settings_dir(
    current_directory: str | Path,
    global_settings_dir: str | Path,
    *,
    settings_filename: str = "setting.cfg",
    writable_checker: Callable[[str | Path], bool] = directory_is_writable,
) -> Path:
    current_path = Path(current_directory)
    global_path = Path(global_settings_dir)

    if (current_path / settings_filename).is_file():
        return current_path

    if (global_path / settings_filename).is_file():
        return global_path

    if writable_checker(current_path):
        return current_path

    global_path.mkdir(parents=True, exist_ok=True)
    return global_path
