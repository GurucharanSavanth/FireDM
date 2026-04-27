from __future__ import annotations

import argparse
import importlib.metadata as metadata
import platform

from build_id import build_release_name, build_tag_name, parse_build_id
from common import LICENSES_DIR, ensure_dir, license_inventory_name, read_version, write_json

COMPONENTS = [
    "FireDM",
    "pycurl",
    "yt-dlp",
    "yt-dlp-ejs",
    "Pillow",
    "certifi",
    "pystray",
    "awesometkinter",
    "plyer",
    "packaging",
]


def component_record(name: str) -> dict:
    try:
        dist = metadata.distribution(name)
        meta = dist.metadata
        return {
            "name": name,
            "version": dist.version,
            "license": meta.get("License") or meta.get("License-Expression") or "unknown",
            "summary": meta.get("Summary", ""),
            "homePage": meta.get("Home-page") or meta.get("Project-URL") or "",
            "status": "observed",
        }
    except metadata.PackageNotFoundError:
        return {
            "name": name,
            "version": "",
            "license": "unknown",
            "summary": "",
            "homePage": "",
            "status": "blocked: package metadata not found",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect bundled component license metadata.")
    parser.add_argument("--build-id", required=True)
    args = parser.parse_args()
    build_parts = parse_build_id(args.build_id)
    ensure_dir(LICENSES_DIR)
    records = [component_record(name) for name in COMPONENTS]
    records.extend(
        [
            {
                "name": "Python runtime",
                "version": platform.python_version(),
                "license": "Python Software Foundation License",
                "summary": "Bundled by PyInstaller payload",
                "homePage": "https://www.python.org/",
                "status": "inferred from current build runtime",
            },
            {
                "name": "FFmpeg/ffprobe",
                "version": "",
                "license": "blocked",
                "summary": "Not bundled by this installer pass",
                "homePage": "https://ffmpeg.org/",
                "status": "blocked pending redistribution/source/checksum decision",
            },
        ]
    )
    payload = {
        "projectVersion": read_version(),
        "build_id": args.build_id,
        "build_date": build_parts.date,
        "build_index": build_parts.index,
        "tag_name": build_tag_name(args.build_id),
        "release_name": build_release_name(args.build_id),
        "components": records,
    }
    canonical = LICENSES_DIR / license_inventory_name(args.build_id)
    write_json(canonical, payload)
    write_json(LICENSES_DIR / "license-inventory.json", payload)
    print(f"License inventory written: {canonical}")


if __name__ == "__main__":
    main()
