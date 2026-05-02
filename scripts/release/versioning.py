"""Unified FireDM versioning facade.

Wraps the existing build_id machinery with the spec terminology
(``build_code`` == ``build_id``), exposes the canonical product version
reader, and writes the runtime ``firedm/_build_info.py`` module that
packaged builds use to surface build identity at runtime.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_id import (
    BuildIdSelection,
    build_release_name,
    build_tag_name,
    discover_existing_build_ids,
    format_build_id,
    next_build_id,
    parse_build_id,
    select_build_id,
    today_build_date,
    validate_build_id,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = REPO_ROOT / "firedm" / "version.py"
BUILD_INFO_TARGET = REPO_ROOT / "firedm" / "_build_info.py"

# Spec terminology: build_code == build_id (YYYYMMDD_VN). The canonical wire
# field name across manifests, scripts and workflows remains ``build_id``;
# ``build_code`` is exposed only as a stable synonym so external automation
# can read either field.
build_code_re = parse_build_id  # noqa: re-export


def get_product_version() -> str:
    """Return the canonical product version (``firedm/version.py``)."""
    namespace: dict[str, Any] = {}
    exec(VERSION_FILE.read_text(encoding="utf-8"), namespace)
    return str(namespace["__version__"])


def parse_build_code(value: str):
    """Parse a build code (synonym for ``parse_build_id``)."""
    return parse_build_id(value)


def format_build_code(date: str, index: int) -> str:
    """Format ``YYYYMMDD_VN`` (synonym for ``format_build_id``)."""
    return format_build_id(date, index)


def validate_build_code(value: str) -> bool:
    """Synonym for ``validate_build_id``."""
    return validate_build_id(value)


def discover_existing_build_codes(**kwargs: Any) -> set[str]:
    """Synonym for ``discover_existing_build_ids``."""
    return discover_existing_build_ids(**kwargs)


def next_build_code(date: str, sources) -> str:
    """Synonym for ``next_build_id``."""
    return next_build_id(date, sources)


def tag_name_for(build_code: str) -> str:
    """Return the git tag name for a build code."""
    return build_tag_name(build_code)


def release_name_for(build_code: str) -> str:
    """Return the GitHub release title for a build code."""
    return build_release_name(build_code)


def artifact_prefix_for(product: str, build_code: str, channel: str, platform_name: str, arch: str) -> str:
    """Return the artifact filename prefix for a release lane."""
    parse_build_id(build_code)
    return f"{product}_{build_code}_{channel}_{platform_name}_{arch}"


def select_build_code(**kwargs: Any) -> BuildIdSelection:
    """Synonym for ``select_build_id``."""
    return select_build_id(**kwargs)


@dataclass(frozen=True)
class BuildInfo:
    """Snapshot of the build identity captured at packaging time."""

    product_version: str
    build_code: str
    build_date: str
    build_index: int
    channel: str
    commit: str
    dirty_tree: bool
    platform: str
    arch: str
    build_time_utc: str
    build_time_local: str
    tag_name: str
    release_name: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_local() -> str:
    return datetime.now().astimezone().isoformat()


def make_build_info(
    *,
    build_code: str,
    channel: str,
    platform_name: str,
    arch: str,
    commit: str = "",
    dirty_tree: bool = False,
) -> BuildInfo:
    parts = parse_build_id(build_code)
    return BuildInfo(
        product_version=get_product_version(),
        build_code=build_code,
        build_date=parts.date,
        build_index=parts.index,
        channel=channel,
        commit=commit,
        dirty_tree=bool(dirty_tree),
        platform=platform_name,
        arch=arch,
        build_time_utc=_now_utc(),
        build_time_local=_now_local(),
        tag_name=tag_name_for(build_code),
        release_name=release_name_for(build_code),
    )


def build_info_module_text(info: BuildInfo) -> str:
    """Render a deterministic Python module exposing ``info`` as constants."""
    payload = info.as_dict()
    body = ",\n    ".join(f"{key!r}: {value!r}" for key, value in payload.items())
    return (
        '"""Generated FireDM build identity. Do not edit by hand."""\n'
        "from __future__ import annotations\n\n"
        "BUILD_INFO = {\n"
        f"    {body},\n"
        "}\n\n"
        f"PRODUCT_VERSION = {payload['product_version']!r}\n"
        f"BUILD_CODE = {payload['build_code']!r}\n"
        f"BUILD_ID = {payload['build_code']!r}\n"
        f"TAG_NAME = {payload['tag_name']!r}\n"
        f"RELEASE_NAME = {payload['release_name']!r}\n"
        f"CHANNEL = {payload['channel']!r}\n"
        f"PLATFORM = {payload['platform']!r}\n"
        f"ARCH = {payload['arch']!r}\n"
    )


def write_build_info(
    info: BuildInfo,
    *,
    target: Path | None = None,
    json_target: Path | None = None,
) -> Path:
    """Write the runtime ``_build_info.py`` module and an optional JSON sidecar."""
    target = target or BUILD_INFO_TARGET
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_info_module_text(info), encoding="utf-8")
    if json_target is not None:
        json_target.parent.mkdir(parents=True, exist_ok=True)
        json_target.write_text(json.dumps(info.as_dict(), indent=2) + "\n", encoding="utf-8")
    return target


def detect_host_platform_arch() -> tuple[str, str]:
    """Return a ``(platform, arch)`` pair for the running host."""
    sys_platform = sys.platform
    if sys_platform.startswith("win"):
        platform_name = "windows"
    elif sys_platform.startswith("linux"):
        platform_name = "linux"
    elif sys_platform == "darwin":
        platform_name = "macos"
    else:
        platform_name = sys_platform
    machine = (platform.machine() or "").lower()
    if machine in {"amd64", "x86_64"}:
        arch = "x64"
    elif machine in {"x86", "i386", "i686"}:
        arch = "x86"
    elif machine in {"arm64", "aarch64"}:
        arch = "arm64"
    else:
        arch = machine or "unknown"
    return platform_name, arch


def main() -> None:
    parser = argparse.ArgumentParser(description="FireDM unified versioning helpers (build code is a synonym for build id).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub_version = sub.add_parser("product-version", help="Print the product version from firedm/version.py.")
    sub_version.add_argument("--json", action="store_true", dest="json_output")

    sub_select = sub.add_parser("select-build-code", help="Select or validate a YYYYMMDD_VN build code.")
    sub_select.add_argument("--date")
    sub_select.add_argument("--build-code")
    sub_select.add_argument("--allow-overwrite", action="store_true")
    sub_select.add_argument("--include-remote-tags", action="store_true")
    sub_select.add_argument("--include-github-releases", action="store_true")
    sub_select.add_argument("--json", action="store_true", dest="json_output")

    sub_write = sub.add_parser("write-build-info", help="Write firedm/_build_info.py for packaged builds.")
    sub_write.add_argument("--build-code", required=True)
    sub_write.add_argument("--channel", required=True)
    sub_write.add_argument("--platform", required=True)
    sub_write.add_argument("--arch", required=True)
    sub_write.add_argument("--commit", default="")
    sub_write.add_argument("--dirty", action="store_true")
    sub_write.add_argument("--target")
    sub_write.add_argument("--json-target")

    args = parser.parse_args()

    if args.cmd == "product-version":
        version = get_product_version()
        if args.json_output:
            print(json.dumps({"product_version": version}, indent=2))
        else:
            print(version)
        return

    if args.cmd == "select-build-code":
        selection = select_build_id(
            date=args.date,
            build_id=args.build_code,
            allow_overwrite=args.allow_overwrite,
            include_remote_tags=args.include_remote_tags,
            include_github_releases=args.include_github_releases,
        )
        payload = asdict(selection)
        payload["build_code"] = payload["build_id"]
        if args.json_output:
            print(json.dumps(payload, indent=2))
        else:
            print(selection.build_id)
        return

    if args.cmd == "write-build-info":
        info = make_build_info(
            build_code=args.build_code,
            channel=args.channel,
            platform_name=args.platform,
            arch=args.arch,
            commit=args.commit,
            dirty_tree=args.dirty,
        )
        target = Path(args.target).resolve() if args.target else None
        json_target = Path(args.json_target).resolve() if args.json_target else None
        path = write_build_info(info, target=target, json_target=json_target)
        print(f"Wrote build info: {path}")
        return


__all__ = [
    "BUILD_INFO_TARGET",
    "BuildInfo",
    "VERSION_FILE",
    "artifact_prefix_for",
    "build_info_module_text",
    "detect_host_platform_arch",
    "discover_existing_build_codes",
    "format_build_code",
    "get_product_version",
    "make_build_info",
    "next_build_code",
    "parse_build_code",
    "release_name_for",
    "select_build_code",
    "tag_name_for",
    "today_build_date",
    "validate_build_code",
    "write_build_info",
]


if __name__ == "__main__":
    main()
