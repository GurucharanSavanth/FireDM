from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class PortableCheck:
    name: str
    required: bool
    status: str
    path: str = ""
    detail: str = ""


REQUIRED_FILES = [
    "firedm.exe",
    "FireDM-GUI.exe",
    "_internal/tkinter/__init__.py",
    "_internal/_tcl_data/init.tcl",
    "_internal/_tk_data/tk.tcl",
    "_internal/certifi/cacert.pem",
    "README_PORTABLE.txt",
    "build-metadata.json",
    "payload-manifest.json",
]


def safe_extract(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            target = (destination / info.filename).resolve()
            root = destination.resolve()
            if target != root and root not in target.parents:
                raise SystemExit(f"Archive path escapes extraction root: {info.filename}")
        zf.extractall(destination)


def run_smoke(root: Path, executable: str, args: list[str], label: str) -> PortableCheck:
    exe = root / executable
    if platform.system() != "Windows":
        return PortableCheck(label, False, "warning", str(exe), "smoke skipped outside Windows")
    try:
        result = subprocess.run([str(exe), *args], cwd=root, capture_output=True, text=True, timeout=30)
    except Exception as exc:
        return PortableCheck(label, True, "missing", str(exe), str(exc))
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        return PortableCheck(label, True, "missing", str(exe), output.strip())
    return PortableCheck(label, True, "ok", str(exe), output.splitlines()[0] if output.splitlines() else "")


def detect_optional_tool(root: Path, name: str) -> PortableCheck:
    local = root / "tools" / f"{name}.exe"
    if local.is_file():
        return PortableCheck(name, False, "ok", str(local), "app-local tool bundled")
    found = shutil.which(name)
    if found:
        return PortableCheck(name, False, "ok", found, "external tool detected")
    return PortableCheck(name, False, "warning", "", "not bundled; optional for media post-processing")


def validate_root(root: Path, *, skip_smoke: bool = False) -> dict[str, Any]:
    checks: list[PortableCheck] = []
    for rel in REQUIRED_FILES:
        path = root / rel
        checks.append(PortableCheck(rel, True, "ok" if path.is_file() else "missing", str(path)))

    checks.append(detect_optional_tool(root, "ffmpeg"))
    checks.append(detect_optional_tool(root, "ffprobe"))

    metadata_path = root / "build-metadata.json"
    metadata: dict[str, Any] = {}
    if metadata_path.is_file():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            checks.append(PortableCheck("build metadata JSON", True, "ok", str(metadata_path)))
        except json.JSONDecodeError as exc:
            checks.append(PortableCheck("build metadata JSON", True, "missing", str(metadata_path), str(exc)))

    if not skip_smoke:
        checks.append(run_smoke(root, "firedm.exe", ["--help"], "portable help smoke"))
        checks.append(run_smoke(root, "firedm.exe", ["--imports-only"], "portable import smoke"))

    payload = {
        "schema": 1,
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
        raise SystemExit(f"Portable archive missing: {archive}")
    temp = tempfile.TemporaryDirectory(prefix="firedm-portable-validation-")
    root = Path(temp.name) / "portable"
    root.mkdir(parents=True)
    safe_extract(archive, root)
    return root, temp


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate FireDM portable ZIP or extracted portable root.")
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
            raise SystemExit(f"Portable validation failed: {', '.join(missing)}")
        print(f"Portable validation passed: {root}")
    finally:
        if temp is not None:
            temp.cleanup()


if __name__ == "__main__":
    main()
