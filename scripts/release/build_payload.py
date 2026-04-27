from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

from common import (
    BUILD_DIR,
    CHECKSUMS_DIR,
    PORTABLE_DIR,
    build_metadata,
    clean_dir,
    ensure_dir,
    file_sha256,
    payload_manifest_path,
    payload_root,
    portable_name,
    read_version,
    repo_path,
    require_supported_arch,
    run_checked,
    write_json,
)


def zip_directory(source: Path, destination: Path, root_name: str | None = None) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(source.rglob("*")):
            if path.is_dir():
                continue
            rel = path.relative_to(source)
            if root_name:
                rel = Path(root_name) / rel
            zf.write(path, rel.as_posix())


def copy_payload(arch: str) -> Path:
    if arch != "x64":
        raise SystemExit(f"{arch} payload build is blocked in this checkout; only x64 is implemented.")

    run_checked(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repo_path("scripts", "windows-build.ps1")),
            "-SkipTests",
            "-SkipLint",
            "-SkipPythonPackage",
            "-SkipTwineCheck",
        ]
    )

    source = repo_path("dist", "FireDM")
    if not (source / "firedm.exe").is_file() or not (source / "FireDM-GUI.exe").is_file():
        raise SystemExit("PyInstaller payload missing firedm.exe or FireDM-GUI.exe")

    destination = clean_dir(payload_root(arch))
    shutil.copytree(source, destination, dirs_exist_ok=True)
    return destination


def add_portable_readme(payload: Path, version: str, arch: str) -> None:
    readme = payload / "README_PORTABLE.txt"
    readme.write_text(
        "\n".join(
            [
                f"FireDM {version} portable package ({arch})",
                "",
                "Run FireDM-GUI.exe for the GUI or firedm.exe --help for CLI options.",
                "This portable package does not install shortcuts, registry entries, or PATH changes.",
                "Configuration may still follow FireDM runtime settings unless portable-mode support is explicitly added in the app.",
                "FFmpeg and Deno are external unless bundled in this package and listed in release-manifest.json.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def build_payload(args: argparse.Namespace) -> dict:
    version = read_version()
    payload = copy_payload(args.arch)
    add_portable_readme(payload, version, args.arch)

    files = []
    for path in sorted(payload.rglob("*")):
        if path.is_file():
            files.append(
                {
                    "path": path.relative_to(payload).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": file_sha256(path),
                }
            )

    metadata = build_metadata(args.arch, args.channel)
    metadata.update(
        {
            "kind": "payload",
            "payloadRoot": str(payload),
            "fileCount": len(files),
            "files": files,
            "blockedBundledTools": {
                "ffmpeg": "not bundled until redistribution license/source/checksum policy is finalized",
                "ffprobe": "not bundled until redistribution license/source/checksum policy is finalized",
                "deno": "not bundled; current project policy keeps Deno external",
            },
        }
    )
    write_json(payload_manifest_path(args.arch), metadata)

    portable_dir = ensure_dir(PORTABLE_DIR)
    portable_zip = portable_dir / portable_name(version, args.arch)
    if portable_zip.exists():
        portable_zip.unlink()
    zip_directory(payload, portable_zip)

    ensure_dir(CHECKSUMS_DIR)
    write_json(
        BUILD_DIR / "last-payload.json",
        {
            "payload": str(payload),
            "manifest": str(payload_manifest_path(args.arch)),
            "portableZip": str(portable_zip),
            "portableSha256": file_sha256(portable_zip),
        },
    )
    print(f"Payload ready: {payload}")
    print(f"Portable zip ready: {portable_zip}")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FireDM Windows architecture payload.")
    parser.add_argument("--arch", choices=["x64", "x86", "arm64"], required=True)
    parser.add_argument("--channel", default="dev")
    args = parser.parse_args()
    require_supported_arch(parser, args.arch)
    build_payload(args)


if __name__ == "__main__":
    main()
