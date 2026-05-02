from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test an installed FireDM tree.")
    parser.add_argument("--install-root", required=True)
    args = parser.parse_args()
    root = Path(args.install_root).resolve()
    exe = root / "firedm.exe"
    if not exe.is_file():
        raise SystemExit(f"Missing installed firedm.exe: {exe}")
    for command in ([str(exe), "--help"], [str(exe), "--imports-only"]):
        result = subprocess.run(command, cwd=root, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            raise SystemExit(result.returncode)
    print(f"Installed app smoke passed: {root}")


if __name__ == "__main__":
    main()

