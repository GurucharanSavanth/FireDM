# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


project_root = Path(SPECPATH).resolve().parent
main_script = project_root / "firedm.py"
icon_path = project_root / "icons" / "48x48.png"


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


def collect_linux_tk_assets():
    base = Path(sys.base_prefix)
    tk_datas = []

    for tkinter_root in (base / "lib" / "tkinter", base / "Lib" / "tkinter"):
        if not tkinter_root.is_dir():
            continue
        for path in tkinter_root.rglob("*"):
            if path.is_file():
                destination = Path("tkinter") / path.relative_to(tkinter_root).parent
                tk_datas.append((str(path), str(destination)))
        break

    return tk_datas


build_info_module = []
if (project_root / "firedm" / "_build_info.py").is_file():
    build_info_module.append("firedm._build_info")


tk_datas = collect_linux_tk_assets()
datas = safe_collect_data_files("certifi") + safe_collect_data_files("yt_dlp_ejs") + tk_datas
hiddenimports = sorted(
    set(
        safe_collect_submodules("awesometkinter")
        + safe_collect_submodules("pystray")
        + safe_collect_submodules("yt_dlp")
        + safe_collect_submodules("yt_dlp_ejs")
        + safe_collect_submodules("youtube_dl")
        + safe_collect_submodules("firedm.plugins")
        + build_info_module
        + ["_tkinter", "tkinter", "firedm.native_host", "firedm.native_messaging"]
    )
)

native_host_src = project_root / "firedm" / "native_host.py"
if native_host_src.is_file():
    datas.append((str(native_host_src), "firedm"))

extension_root = project_root / "browser_extension"
if extension_root.is_dir():
    for path in extension_root.rglob("*"):
        if path.is_file():
            destination = Path("browser_extension") / path.relative_to(extension_root).parent
            datas.append((str(path), str(destination)))

a = Analysis(
    [str(main_script)],
    pathex=[str(project_root)],
    binaries=[],
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
