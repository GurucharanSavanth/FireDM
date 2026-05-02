"""Validate the packaged FireDM distribution.

Runs a short diagnostic sequence against `dist\\FireDM\\firedm.exe`:

    1. `firedm.exe --help` exits 0 and produces expected usage text.
    2. `firedm.exe --show-settings` exits 0 and prints a settings folder.
    3. `firedm.exe --imports-only` exits 0 (all runtime deps importable).
    4. Launch `FireDM-GUI.exe` briefly and verify the process stays alive.

Writes:
    artifacts/packaged/packaged_startup.log
    artifacts/packaged/packaged_video_flow_result.json

Exit 0 on full pass; non-zero if any of the above regresses.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST = REPO_ROOT / "dist" / "FireDM"
ARTIFACTS = REPO_ROOT / "artifacts" / "packaged"
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def _run(args, timeout=60):
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return proc


def _exe(name: str) -> Path:
    path = DIST / name
    if not path.exists():
        raise FileNotFoundError(
            f"packaged binary missing: {path}. Run scripts/windows-build.ps1 first."
        )
    return path


def main() -> int:
    log_lines: list[str] = [f"[packaged-verify] timestamp={time.strftime('%Y-%m-%dT%H:%M:%S')}"]
    result: dict[str, object] = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "checks": {}}

    try:
        firedm_exe = _exe("firedm.exe")
        gui_exe = _exe("FireDM-GUI.exe")
    except FileNotFoundError as e:
        log_lines.append(f"[packaged-verify] FAIL {e}")
        result["error"] = str(e)
        result["overall_passed"] = False
        _dump(log_lines, result)
        return 1

    # --- 1. --help --------------------------------------------------------
    proc = _run([str(firedm_exe), "--help"])
    help_ok = proc.returncode == 0 and "firedm" in (proc.stdout + proc.stderr).lower()
    result["checks"]["help"] = {
        "exit_code": proc.returncode,
        "stdout_head": (proc.stdout or "").splitlines()[:4],
        "passed": help_ok,
    }
    log_lines.append(f"[packaged-verify] --help exit={proc.returncode} passed={help_ok}")

    # --- 2. --show-settings ----------------------------------------------
    proc = _run([str(firedm_exe), "--show-settings"])
    settings_ok = proc.returncode == 0 and "sett" in (proc.stdout or "").lower()
    result["checks"]["show_settings"] = {
        "exit_code": proc.returncode,
        "stdout_head": (proc.stdout or "").splitlines()[:10],
        "passed": settings_ok,
    }
    log_lines.append(f"[packaged-verify] --show-settings exit={proc.returncode} passed={settings_ok}")

    # --- 3. --imports-only (runtime deps) --------------------------------
    proc = _run([str(firedm_exe), "--imports-only"], timeout=120)
    imports_ok = proc.returncode == 0
    result["checks"]["imports_only"] = {
        "exit_code": proc.returncode,
        "stdout_head": (proc.stdout or "").splitlines()[:8],
        "stderr_head": (proc.stderr or "").splitlines()[:4],
        "passed": imports_ok,
    }
    log_lines.append(f"[packaged-verify] --imports-only exit={proc.returncode} passed={imports_ok}")

    # --- 4. GUI launch ---------------------------------------------------
    gui = subprocess.Popen([str(gui_exe)])
    time.sleep(4.0)
    gui_alive = gui.poll() is None
    if gui_alive:
        gui.terminate()
        try:
            gui.wait(timeout=10)
        except subprocess.TimeoutExpired:
            gui.kill()
    result["checks"]["gui_launch"] = {
        "alive_after_4s": gui_alive,
        "passed": gui_alive,
    }
    log_lines.append(f"[packaged-verify] GUI alive_after_4s={gui_alive}")

    overall = all(c.get("passed") for c in result["checks"].values())
    result["overall_passed"] = overall
    log_lines.append(f"[packaged-verify] overall_passed={overall}")

    _dump(log_lines, result)
    return 0 if overall else 1


def _dump(log_lines, result):
    (ARTIFACTS / "packaged_startup.log").write_text("\n".join(log_lines), encoding="utf-8")
    (ARTIFACTS / "packaged_video_flow_result.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print("\n".join(log_lines))


if __name__ == "__main__":
    sys.exit(main())
