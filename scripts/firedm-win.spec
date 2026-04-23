# -*- mode: python ; coding: utf-8 -*-

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


datas = safe_collect_data_files("certifi") + safe_collect_data_files("yt_dlp_ejs")
hiddenimports = sorted(
    set(
        safe_collect_submodules("awesometkinter")
        + safe_collect_submodules("pystray")
        + safe_collect_submodules("yt_dlp")
        + safe_collect_submodules("yt_dlp_ejs")
        + safe_collect_submodules("youtube_dl")
    )
)

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
