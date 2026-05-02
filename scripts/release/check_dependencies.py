from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import platform
import shutil
import struct
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from common import DIST_DIR, dependency_status_name, ensure_dir, repo_path, write_json

REPO_ROOT = repo_path()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from firedm.ffmpeg_service import collect_media_tool_health  # noqa: E402
from firedm.tool_discovery import resolve_binary_path  # noqa: E402


@dataclass
class CheckResult:
    name: str
    category: str
    required: bool
    status: str
    version: str = ""
    path: str = ""
    detail: str = ""


PYTHON_PACKAGES = [
    ("FireDM", "firedm", "runtime", True),
    ("plyer", "plyer", "runtime", True),
    ("certifi", "certifi", "runtime", True),
    ("yt-dlp", "yt_dlp", "runtime", True),
    ("yt-dlp-ejs", "yt_dlp_ejs", "runtime", False),
    ("pycurl", "pycurl", "runtime", True),
    ("Pillow", "PIL", "runtime", True),
    ("pystray", "pystray", "runtime", True),
    ("awesometkinter", "awesometkinter", "runtime", True),
    ("packaging", "packaging", "runtime", True),
    ("youtube-dl", "youtube_dl", "optional-legacy", False),
    ("pytest", "pytest", "test", True),
    ("ruff", "ruff", "test", True),
    ("build", "build", "build", True),
    ("PyInstaller", "PyInstaller", "build", True),
    ("twine", "twine", "build", True),
    ("wheel", "wheel", "build", True),
    ("setuptools", "setuptools", "build", True),
]


def package_version(dist_name: str) -> str:
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return ""


def check_import(dist_name: str, module_name: str, category: str, required: bool) -> CheckResult:
    version = package_version(dist_name)
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        return CheckResult(dist_name, category, required, "missing" if required else "warning", version, detail=str(exc))
    path = str(getattr(module, "__file__", "") or "")
    return CheckResult(dist_name, category, required, "ok", version, path=path)


def check_command(name: str, category: str, required: bool, args: list[str] | None = None) -> CheckResult:
    path = shutil.which(name)
    if not path:
        return CheckResult(name, category, required, "missing" if required else "warning", detail="not on PATH")
    version = ""
    if args:
        try:
            result = subprocess.run([path, *args], check=False, capture_output=True, text=True, timeout=15)
            version = (result.stdout or result.stderr).splitlines()[0].strip() if (result.stdout or result.stderr) else ""
        except Exception as exc:
            return CheckResult(name, category, required, "warning", path=path, detail=f"version probe failed: {exc}")
    return CheckResult(name, category, required, "ok", version=version, path=path)


def check_python_runtime() -> list[CheckResult]:
    bits = struct.calcsize("P") * 8
    version = platform.python_version()
    results = [
        CheckResult(
            "Python",
            "runtime",
            True,
            "ok" if sys.version_info[:2] == (3, 10) else "missing",
            version=version,
            path=sys.executable,
            detail="FireDM Windows baseline requires Python 3.10.x",
        ),
        CheckResult(
            "Python bitness",
            "runtime",
            True,
            "ok" if bits == 64 else "missing",
            version=f"{bits}-bit",
            detail="Windows x64 lane requires 64-bit Python",
        ),
    ]
    return results


def check_tk() -> CheckResult:
    try:
        import tkinter

        version = str(tkinter.TkVersion)
    except Exception as exc:
        return CheckResult("Tcl/Tk", "gui-runtime", True, "missing", detail=str(exc))
    return CheckResult("Tcl/Tk", "gui-runtime", True, "ok", version=version, path=str(Path(tkinter.__file__).resolve()))


def check_certifi() -> CheckResult:
    try:
        import certifi

        ca_path = Path(certifi.where())
        status = "ok" if ca_path.is_file() else "missing"
        return CheckResult("certifi CA bundle", "runtime", True, status, package_version("certifi"), str(ca_path))
    except Exception as exc:
        return CheckResult("certifi CA bundle", "runtime", True, "missing", detail=str(exc))


def check_media_tools() -> list[CheckResult]:
    media = collect_media_tool_health(operating_system=platform.system())
    results = []
    for name in ("ffmpeg", "ffprobe"):
        info = media.get(name, {})
        usable = bool(info.get("usable"))
        results.append(
            CheckResult(
                name,
                "optional-external-tool",
                False,
                "ok" if usable else "warning",
                version=str(info.get("version") or ""),
                path=str(info.get("path") or ""),
                detail=str(info.get("failure") or "not bundled; install externally for media post-processing"),
            )
        )
    return results


def probe_tool_version(path: str, *args: str) -> str:
    try:
        result = subprocess.run([path, *args], check=False, capture_output=True, text=True, timeout=15)
    except Exception:
        return ""
    return (result.stdout or result.stderr).splitlines()[0].strip() if (result.stdout or result.stderr) else ""


def check_external_tools() -> list[CheckResult]:
    results = []
    for name, args, detail in (
        ("deno", ("--version",), "not bundled; optional yt-dlp JavaScript runtime"),
    ):
        path = resolve_binary_path(name, operating_system=platform.system())
        if not path:
            results.append(CheckResult(name, "optional-external-tool", False, "warning", detail="not found; " + detail))
            continue
        version = probe_tool_version(path, *args)
        results.append(
            CheckResult(
                name,
                "optional-external-tool",
                False,
                "ok" if version else "warning",
                version=version,
                path=path,
                detail=detail if version else "found but version probe failed; " + detail,
            )
        )
    return results


def check_payload(root: Path | None) -> list[CheckResult]:
    if root is None:
        root = repo_path("dist", "FireDM")
    required_files = [
        "firedm.exe",
        "FireDM-GUI.exe",
        "_internal/tkinter/__init__.py",
        "_internal/_tcl_data/init.tcl",
        "_internal/_tk_data/tk.tcl",
        "_internal/certifi/cacert.pem",
        "build-metadata.json",
    ]
    if not root.exists():
        return [CheckResult("portable payload", "portable", False, "warning", path=str(root), detail="payload not built yet")]
    results = []
    for rel in required_files:
        path = root / rel
        results.append(
            CheckResult(
                rel,
                "portable",
                True,
                "ok" if path.is_file() else "missing",
                path=str(path),
            )
        )
    return results


def collect_results(args: argparse.Namespace) -> dict[str, Any]:
    results: list[CheckResult] = []
    results.extend(check_python_runtime())
    results.extend(check_import(*pkg) for pkg in PYTHON_PACKAGES)
    results.append(check_tk())
    results.append(check_certifi())
    results.append(check_command("git", "build-tool", True, ["--version"]))
    if platform.system() == "Windows":
        results.append(check_command("powershell", "build-tool", True, ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"]))
    results.append(check_command("gh", "release-tool", False, ["--version"]))
    results.extend(check_media_tools())
    results.extend(check_external_tools())
    if not args.skip_portable:
        results.extend(check_payload(Path(args.portable_root).resolve() if args.portable_root else None))

    payload = {
        "schema": 1,
        "arch": args.arch,
        "channel": args.channel,
        "build_id": args.build_id or "",
        "host": {
            "python": sys.version,
            "platform": platform.platform(),
            "sysPlatform": sys.platform,
            "machine": platform.machine(),
            "path": sys.executable,
        },
        "checks": [asdict(item) for item in results],
    }
    payload["summary"] = {
        "required_missing": [item.name for item in results if item.required and item.status != "ok"],
        "warnings": [item.name for item in results if not item.required and item.status != "ok"],
    }
    return payload


def print_table(payload: dict[str, Any]) -> None:
    print("name | category | required | status | version | detail")
    print("--- | --- | --- | --- | --- | ---")
    for item in payload["checks"]:
        print(
            f"{item['name']} | {item['category']} | {str(item['required']).lower()} | "
            f"{item['status']} | {item.get('version', '')} | {item.get('detail', '')}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Check FireDM dependency, toolchain, and portable payload readiness.")
    parser.add_argument("--arch", default="x64")
    parser.add_argument("--channel", default="dev")
    parser.add_argument("--build-id")
    parser.add_argument("--portable-root")
    parser.add_argument("--skip-portable", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = collect_results(args)
    if args.output:
        output = Path(args.output)
        if not output.is_absolute():
            output = DIST_DIR / output
        ensure_dir(output.parent)
        write_json(output, payload)
    elif args.build_id:
        write_json(DIST_DIR / dependency_status_name(args.build_id), payload)

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print_table(payload)
    missing = payload["summary"]["required_missing"]
    if missing:
        raise SystemExit(f"Required dependency checks failed: {', '.join(missing)}")


if __name__ == "__main__":
    main()
