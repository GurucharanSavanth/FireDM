from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def classify_failure(stdout: str, stderr: str, returncode: int | None) -> str:
    text = f"{stdout}\n{stderr}".lower()
    if "tcl" in text or "tkinter" in text or "_tkinter" in text:
        return "Tcl/Tk missing"
    if "modulenotfounderror" in text or "importerror" in text:
        return "import failure"
    if returncode is not None and returncode != 0:
        return "GUI crash"
    return "environment limitation"


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test installed FireDM GUI startup.")
    parser.add_argument("--install-root", required=True)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--headless-safe", action="store_true")
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--expect-launcher", default="FireDM-GUI.exe")
    args = parser.parse_args()

    root = Path(args.install_root).resolve()
    launcher = root / args.expect_launcher
    if not launcher.is_file():
        raise SystemExit(f"classification=launcher missing; missing={launcher}")
    if not (root / "_internal").is_dir():
        raise SystemExit(f"classification=runtime missing; missing={root / '_internal'}")
    if not (root / "_internal" / "_tk_data" / "tk.tcl").is_file():
        raise SystemExit("classification=Tcl/Tk missing; missing=_internal/_tk_data/tk.tcl")

    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    if args.no_network:
        env["FIREDM_NO_NETWORK"] = "1"
        env["FIREDM_DISABLE_UPDATE_CHECK"] = "1"

    try:
        process = subprocess.Popen(
            [str(launcher)],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
    except OSError as exc:
        raise SystemExit(f"classification=runtime missing; error={exc}") from exc

    try:
        stdout, stderr = process.communicate(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate(timeout=5)
        print(f"classification=started_timeout_terminated; timeout={args.timeout}; launcher={launcher}")
        if stdout:
            print("stdout:")
            print(stdout)
        if stderr:
            print("stderr:", file=sys.stderr)
            print(stderr, file=sys.stderr)
        return

    if process.returncode == 0:
        print(f"classification=exited_cleanly; launcher={launcher}")
        return

    classification = classify_failure(stdout or "", stderr or "", process.returncode)
    if stdout:
        print("stdout:")
        print(stdout)
    if stderr:
        print("stderr:", file=sys.stderr)
        print(stderr, file=sys.stderr)
    raise SystemExit(f"classification={classification}; returncode={process.returncode}; launcher={launcher}")


if __name__ == "__main__":
    main()

