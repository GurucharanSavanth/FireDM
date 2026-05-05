"""Validate the FireDM Linux payload tree."""

from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
from pathlib import Path

from common import linux_payload_root, require_supported_linux_arch


REQUIRED_FILES = (
    "firedm",
    "FireDM-GUI",
    "_internal/certifi/cacert.pem",
    "_internal/tkinter/__init__.py",
    "README_PORTABLE.txt",
    "payload-manifest.json",
)


def run(args: list[str], cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    return result.stdout + result.stderr


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate FireDM Linux payload tree.")
    parser.add_argument("--arch", choices=["x64"], required=True)
    parser.add_argument("--skip-smoke", action="store_true")
    args = parser.parse_args()
    require_supported_linux_arch(parser, args.arch)
    root = linux_payload_root(args.arch)
    if not root.is_dir():
        raise SystemExit(f"Linux payload missing: {root}")

    missing = [item for item in REQUIRED_FILES if not (root / item).is_file()]
    if missing:
        raise SystemExit(f"Missing Linux payload files: {missing}")

    for executable in ("firedm", "FireDM-GUI"):
        path = root / executable
        if not bool(path.stat().st_mode & stat.S_IXUSR):
            raise SystemExit(f"Linux payload entry missing execute bit: {executable}")

    if args.skip_smoke or sys.platform != "linux":
        print(f"Linux payload structure validated (smoke skipped): {root}")
        return

    help_output = run([str(root / "firedm"), "--help"], root)
    import_output = run([str(root / "firedm"), "--imports-only"], root)
    if "usage:" not in help_output.lower():
        raise SystemExit("Linux payload help smoke did not show usage.")
    if "imported module:" not in import_output:
        raise SystemExit("Linux payload import smoke did not import expected modules.")
    print(f"Linux payload validation passed: {root}")


if __name__ == "__main__":
    main()
