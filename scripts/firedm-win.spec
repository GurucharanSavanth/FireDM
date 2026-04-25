# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


project_root = Path(SPECPATH).resolve().parent
main_script = project_root / "firedm.py"
icon_path = project_root / "icons" / "48_32_16.ico"


def safe_collect_data_files(package):
    try:
        return collect_data_files(package)
    except Exception:
        return []


def safe_collect_submodules(package):
    try:
        return collect_submodules(package)
    except Exception:
        return []


def collect_windows_tk_assets():
    # PyInstaller can warn that tkinter is broken when the Python stdlib Tcl/Tk
    # layout is present but not detected through its hook. Keep this explicit
    # collection until upstream detection handles this Windows baseline.
    base = Path(sys.base_prefix)
    tcl_root = base / "tcl"
    dll_root = base / "DLLs"

    tk_datas = []

    for tkinter_root in (base / "lib" / "tkinter", base / "Lib" / "tkinter"):
        if not tkinter_root.is_dir():
            continue
        for path in tkinter_root.rglob("*"):
            if path.is_file():
                destination = Path("tkinter") / path.relative_to(tkinter_root).parent
                tk_datas.append((str(path), str(destination)))
        break

    for source, destination_root in (
        (tcl_root / "tcl8.6", "_tcl_data"),
        (tcl_root / "tk8.6", "_tk_data"),
    ):
        if not source.is_dir():
            continue
        for path in source.rglob("*"):
            if path.is_file():
                destination = Path(destination_root) / path.relative_to(source).parent
                tk_datas.append((str(path), str(destination)))

    tk_binaries = []
    for name in ("_tkinter.pyd", "tcl86t.dll", "tk86t.dll"):
        path = dll_root / name
        if path.is_file():
            tk_binaries.append((str(path), "."))

    return tk_datas, tk_binaries


tk_datas, tk_binaries = collect_windows_tk_assets()
datas = safe_collect_data_files("certifi") + safe_collect_data_files("yt_dlp_ejs") + tk_datas
hiddenimports = sorted(
    set(
        safe_collect_submodules("awesometkinter")
        + safe_collect_submodules("pystray")
        + safe_collect_submodules("yt_dlp")
        + safe_collect_submodules("yt_dlp_ejs")
        + safe_collect_submodules("youtube_dl")
        + ["_tkinter", "tkinter"]
    )
)

a = Analysis(
    [str(main_script)],
    pathex=[str(project_root)],
    binaries=tk_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

console = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="firedm",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon=str(icon_path),
)

gui = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FireDM-GUI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(icon_path),
)

coll = COLLECT(
    console,
    gui,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="FireDM",
)
