from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from common import payload_root, require_supported_arch


def run(args: list[str], cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    return result.stdout + result.stderr


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate FireDM payload tree.")
    parser.add_argument("--arch", choices=["x64", "x86", "arm64"], required=True)
    args = parser.parse_args()
    require_supported_arch(parser, args.arch)
    root = payload_root(args.arch)

    required = [
        "firedm.exe",
        "FireDM-GUI.exe",
        "_internal/tkinter/__init__.py",
        "_internal/_tcl_data/init.tcl",
        "_internal/_tk_data/tk.tcl",
        "_internal/certifi/cacert.pem",
        "README_PORTABLE.txt",
    ]
    missing = [item for item in required if not (root / item).is_file()]
    if missing:
        raise SystemExit(f"Missing payload files: {missing}")

    help_output = run([str(root / "firedm.exe"), "--help"], root)
    import_output = run([str(root / "firedm.exe"), "--imports-only"], root)
    if "usage:" not in help_output.lower():
        raise SystemExit("Payload help smoke did not show usage.")
    if "imported module:" not in import_output:
        raise SystemExit("Payload import smoke did not import expected modules.")
    print(f"Payload validation passed: {root}")


if __name__ == "__main__":
    main()
