"""Validate the FireDM Linux portable archive (tar.gz)."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "firedm",
    "FireDM-GUI",
    "_internal/certifi/cacert.pem",
    "_internal/tkinter/__init__.py",
    "README_PORTABLE.txt",
    "payload-manifest.json",
)


@dataclass
class LinuxPortableCheck:
    name: str
    required: bool
    status: str
    path: str = ""
    detail: str = ""


def safe_extract(archive: Path, destination: Path) -> Path:
    if not tarfile.is_tarfile(archive):
        raise SystemExit(f"Not a tar archive: {archive}")
    with tarfile.open(archive, "r:*") as tar:
        members = tar.getmembers()
        for member in members:
            target = (destination / member.name).resolve()
            root = destination.resolve()
            if target != root and root not in target.parents:
                raise SystemExit(f"Archive path escapes extraction root: {member.name}")
        tar.extractall(destination)
    candidate = destination / "FireDM"
    if candidate.is_dir():
        return candidate
    raise SystemExit("Linux portable archive missing top-level FireDM/ directory")


def detect_optional_tool(root: Path, name: str) -> LinuxPortableCheck:
    local = root / "tools" / name
    if local.is_file():
        return LinuxPortableCheck(name, False, "ok", str(local), "app-local tool bundled")
    found = shutil.which(name)
    if found:
        return LinuxPortableCheck(name, False, "ok", found, "external tool detected")
    return LinuxPortableCheck(name, False, "warning", "", "not bundled; optional for media post-processing")


def run_smoke(root: Path, executable: str, args: list[str], label: str) -> LinuxPortableCheck:
    exe = root / executable
    if platform.system() != "Linux":
        return LinuxPortableCheck(label, False, "warning", str(exe), "smoke skipped outside Linux")
    if not bool(exe.stat().st_mode & stat.S_IXUSR):
        return LinuxPortableCheck(label, True, "missing", str(exe), "executable bit not set")
    try:
        result = subprocess.run([str(exe), *args], cwd=root, capture_output=True, text=True, timeout=30)
    except Exception as exc:
        return LinuxPortableCheck(label, True, "missing", str(exe), str(exc))
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        return LinuxPortableCheck(label, True, "missing", str(exe), output.strip())
    return LinuxPortableCheck(label, True, "ok", str(exe), output.splitlines()[0] if output.splitlines() else "")


def validate_root(root: Path, *, skip_smoke: bool = False) -> dict[str, Any]:
    checks: list[LinuxPortableCheck] = []
    for rel in REQUIRED_FILES:
        path = root / rel
        checks.append(LinuxPortableCheck(rel, True, "ok" if path.is_file() else "missing", str(path)))

    for executable in ("firedm", "FireDM-GUI"):
        path = root / executable
        if not path.is_file():
            continue
        if platform.system() != "Linux":
            # POSIX executable bits are meaningless on Windows/macOS file systems;
            # record as a non-required informational check so the validator is
            # still runnable in CI on non-Linux hosts.
            checks.append(
                LinuxPortableCheck(
                    f"{executable} executable bit",
                    False,
                    "warning",
                    str(path),
                    "executable bit check skipped (not Linux)",
                )
            )
        else:
            is_executable = bool(path.stat().st_mode & stat.S_IXUSR)
            checks.append(
                LinuxPortableCheck(
                    f"{executable} executable bit",
                    True,
                    "ok" if is_executable else "missing",
                    str(path),
                    "" if is_executable else "user execute bit missing",
                )
            )

    checks.append(detect_optional_tool(root, "ffmpeg"))
    checks.append(detect_optional_tool(root, "ffprobe"))

    metadata_path = root / "payload-manifest.json"
    metadata: dict[str, Any] = {}
    if metadata_path.is_file():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            checks.append(LinuxPortableCheck("payload manifest JSON", True, "ok", str(metadata_path)))
        except json.JSONDecodeError as exc:
            checks.append(LinuxPortableCheck("payload manifest JSON", True, "missing", str(metadata_path), str(exc)))

    if not skip_smoke:
        checks.append(run_smoke(root, "firedm", ["--help"], "linux portable help smoke"))
        checks.append(run_smoke(root, "firedm", ["--imports-only"], "linux portable import smoke"))

    payload = {
        "schema": 1,
        "platform": "linux",
        "root": str(root),
        "metadata": metadata,
        "checks": [asdict(item) for item in checks],
    }
    payload["summary"] = {
        "required_missing": [item.name for item in checks if item.required and item.status != "ok"],
        "warnings": [item.name for item in checks if not item.required and item.status != "ok"],
    }
    return payload


def print_report(payload: dict[str, Any]) -> None:
    print("name | required | status | detail")
    print("--- | --- | --- | ---")
    for item in payload["checks"]:
        print(f"{item['name']} | {str(item['required']).lower()} | {item['status']} | {item.get('detail', '')}")


def resolve_root(args: argparse.Namespace) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if args.root:
        return Path(args.root).resolve(), None
    if not args.archive:
        raise SystemExit("Pass --archive or --root")
    archive = Path(args.archive).resolve()
    if not archive.is_file():
        raise SystemExit(f"Linux portable archive missing: {archive}")
    temp = tempfile.TemporaryDirectory(prefix="firedm-linux-portable-validation-")
    extracted = safe_extract(archive, Path(temp.name))
    return extracted, temp


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate FireDM Linux portable tar.gz archive or extracted root.")
    parser.add_argument("--archive")
    parser.add_argument("--root")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--skip-smoke", action="store_true")
    args = parser.parse_args()
    temp: tempfile.TemporaryDirectory[str] | None = None
    try:
        root, temp = resolve_root(args)
        payload = validate_root(root, skip_smoke=args.skip_smoke)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print_report(payload)
        missing = payload["summary"]["required_missing"]
        if missing:
            raise SystemExit(f"Linux portable validation failed: {', '.join(missing)}")
        print(f"Linux portable validation passed: {root}")
    finally:
        if temp is not None:
            temp.cleanup()


if __name__ == "__main__":
    main()
