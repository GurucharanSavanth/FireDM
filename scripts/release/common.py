from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_id import build_release_name, build_tag_name, parse_build_id

REPO_ROOT = Path(__file__).resolve().parents[2]
DIST_DIR = REPO_ROOT / "dist"
PAYLOADS_DIR = DIST_DIR / "payloads"
INSTALLERS_DIR = DIST_DIR / "installers"
PORTABLE_DIR = DIST_DIR / "portable"
CHECKSUMS_DIR = DIST_DIR / "checksums"
SBOM_DIR = DIST_DIR / "sbom"
LICENSES_DIR = DIST_DIR / "licenses"
BUILD_DIR = REPO_ROOT / "build" / "release"

SUPPORTED_ARCHES = {"x64": "win-x64"}
SUPPORTED_LINUX_ARCHES = {"x64": "linux-x64"}
LINUX_PAYLOADS_DIR = DIST_DIR / "payloads-linux"
LINUX_PORTABLE_DIR = DIST_DIR / "portable-linux"


def repo_path(*parts: str) -> Path:
    return REPO_ROOT.joinpath(*parts)


def ensure_repo_child(path: Path) -> Path:
    resolved = path.resolve()
    root = REPO_ROOT.resolve()
    if resolved == root or root in resolved.parents:
        return resolved
    raise ValueError(f"Refusing path outside repository: {resolved}")


def clean_dir(path: Path) -> Path:
    resolved = ensure_repo_child(path)
    if resolved == REPO_ROOT.resolve():
        raise ValueError(f"Refusing to clean repository root: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def ensure_dir(path: Path) -> Path:
    resolved = ensure_repo_child(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def read_version() -> str:
    namespace: dict[str, Any] = {}
    exec((REPO_ROOT / "firedm" / "version.py").read_text(encoding="utf-8"), namespace)
    return str(namespace["__version__"])


def git_value(args: Iterable[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    ensure_repo_child(path).parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def repo_ref(path: Path) -> str:
    """Return a stable repository-relative path for manifests."""
    resolved = ensure_repo_child(path)
    return resolved.relative_to(REPO_ROOT.resolve()).as_posix()


def dist_ref(path: Path) -> str:
    """Return a stable dist-relative path for release metadata."""
    resolved = ensure_repo_child(path)
    dist_root = DIST_DIR.resolve()
    if resolved == dist_root or dist_root in resolved.parents:
        return resolved.relative_to(dist_root).as_posix()
    raise ValueError(f"Path is not under dist: {resolved}")


def run_checked(args: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(str(x) for x in args), flush=True)
    result = subprocess.run(args, cwd=cwd or REPO_ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def python_exe() -> str:
    return sys.executable


def arch_to_payload(arch: str) -> str:
    if arch not in SUPPORTED_ARCHES:
        raise argparse.ArgumentTypeError(f"unsupported arch {arch!r}; supported: {', '.join(SUPPORTED_ARCHES)}")
    return SUPPORTED_ARCHES[arch]


def require_supported_arch(parser: argparse.ArgumentParser, arch: str) -> str:
    try:
        return arch_to_payload(arch)
    except argparse.ArgumentTypeError as exc:
        parser.exit(2, f"{parser.prog}: error: {exc}\n")


def linux_arch_to_payload(arch: str) -> str:
    if arch not in SUPPORTED_LINUX_ARCHES:
        raise argparse.ArgumentTypeError(
            f"unsupported linux arch {arch!r}; supported: {', '.join(SUPPORTED_LINUX_ARCHES)}"
        )
    return SUPPORTED_LINUX_ARCHES[arch]


def require_supported_linux_arch(parser: argparse.ArgumentParser, arch: str) -> str:
    try:
        return linux_arch_to_payload(arch)
    except argparse.ArgumentTypeError as exc:
        parser.exit(2, f"{parser.prog}: error: {exc}\n")


def build_metadata(arch: str, channel: str, build_id: str) -> dict[str, Any]:
    build_parts = parse_build_id(build_id)
    return {
        "version": read_version(),
        "build_id": build_id,
        "build_date": build_parts.date,
        "build_index": build_parts.index,
        "tag_name": build_tag_name(build_id),
        "release_name": build_release_name(build_id),
        "channel": channel,
        "arch": arch,
        "payloadArch": arch_to_payload(arch),
        "buildTimeUtc": datetime.now(timezone.utc).isoformat(),
        "gitCommit": git_value(["rev-parse", "HEAD"]),
        "gitBranch": git_value(["branch", "--show-current"]),
        "workingTreeDirty": bool(git_value(["status", "--short"])),
        "host": {
            "python": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "sysPlatform": sys.platform,
            "osName": os.name,
        },
    }


def payload_root(arch: str) -> Path:
    return PAYLOADS_DIR / arch_to_payload(arch) / "FireDM"


def payload_manifest_path(arch: str) -> Path:
    return PAYLOADS_DIR / arch_to_payload(arch) / "payload-manifest.json"


def installer_manifest_name() -> str:
    return "installer-manifest.json"


def payload_zip_name(build_id: str, channel: str, arch: str) -> str:
    return f"FireDM_{build_id}_{channel}_win_{arch}_payload.zip"


def installer_name(build_id: str, channel: str, arch: str) -> str:
    return f"FireDM_Setup_{build_id}_{channel}_win_{arch}.exe"


def portable_name(build_id: str, channel: str, arch: str) -> str:
    return f"FireDM_{build_id}_{channel}_win_{arch}_portable.zip"


def installer_manifest_file_name(build_id: str, channel: str, arch: str) -> str:
    return f"FireDM_Setup_{build_id}_{channel}_win_{arch}.manifest.json"


def release_manifest_name(build_id: str) -> str:
    return f"FireDM_release_manifest_{build_id}.json"


def checksum_file_name(build_id: str) -> str:
    return f"SHA256SUMS_{build_id}.txt"


def license_inventory_name(build_id: str) -> str:
    return f"license-inventory_{build_id}.json"


def release_notes_name(build_id: str) -> str:
    return f"FireDM_release_notes_{build_id}.md"


def dependency_status_name(build_id: str) -> str:
    return f"dependency-status_{build_id}.json"


def linux_payload_root(arch: str) -> Path:
    return LINUX_PAYLOADS_DIR / linux_arch_to_payload(arch) / "FireDM"


def linux_payload_manifest_path(arch: str) -> Path:
    return LINUX_PAYLOADS_DIR / linux_arch_to_payload(arch) / "payload-manifest.json"


def linux_portable_name(build_id: str, channel: str, arch: str) -> str:
    return f"FireDM_{build_id}_{channel}_linux_{arch}_portable.tar.gz"


def linux_archive_name(build_id: str, channel: str, arch: str) -> str:
    return f"FireDM_{build_id}_{channel}_linux_{arch}.tar.gz"


def merged_release_manifest_name(build_id: str) -> str:
    return f"FireDM_release_manifest_{build_id}.json"


def per_platform_release_manifest_name(build_id: str, platform_name: str) -> str:
    return f"FireDM_release_manifest_{build_id}_{platform_name}.json"
