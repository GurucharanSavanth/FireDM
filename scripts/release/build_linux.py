"""Build the FireDM Linux release lane (x64)."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import sys
import tarfile
from pathlib import Path

from build_id import select_build_id
from common import (
    BUILD_DIR,
    CHECKSUMS_DIR,
    DIST_DIR,
    LICENSES_DIR,
    LINUX_PAYLOADS_DIR,
    LINUX_PORTABLE_DIR,
    build_metadata,
    checksum_file_name,
    clean_dir,
    dependency_status_name,
    dist_ref,
    ensure_dir,
    file_sha256,
    git_value,
    license_inventory_name,
    linux_archive_name,
    linux_payload_manifest_path,
    linux_payload_root,
    per_platform_release_manifest_name,
    read_version,
    release_notes_name,
    repo_path,
    require_supported_linux_arch,
    run_checked,
    write_json,
)
from versioning import make_build_info, write_build_info


SUPPORTED_LINUX_ARCHES = ("x64",)


def run_script(script: str, *args: str) -> None:
    run_checked([sys.executable, str(repo_path("scripts", "release", script)), *args])


def write_portable_readme(payload: Path, version: str, arch: str) -> None:
    readme = payload / "README_PORTABLE.txt"
    readme.write_text(
        "\n".join(
            [
                f"FireDM {version} portable package (linux-{arch})",
                "",
                "Run ./FireDM-GUI for the GUI or ./firedm --help for CLI options.",
                "This portable package does not install desktop entries, icons, or PATH changes.",
                "Configuration may still follow FireDM runtime settings unless portable-mode support is explicitly added in the app.",
                "FFmpeg and Deno remain external unless bundled in this package and listed in release-manifest.json.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def make_executable(path: Path) -> None:
    if not path.is_file():
        return
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def package_payload(arch: str, channel: str, build_id: str, allow_overwrite: bool) -> Path:
    if arch not in SUPPORTED_LINUX_ARCHES:
        raise SystemExit(f"{arch} linux payload build is blocked in this checkout; only x64 is implemented.")

    info = make_build_info(
        build_code=build_id,
        channel=channel,
        platform_name="linux",
        arch=arch,
        commit=git_value(["rev-parse", "HEAD"]),
        dirty_tree=bool(git_value(["status", "--short"])),
    )
    write_build_info(info)

    work = clean_dir(BUILD_DIR / "linux" / f"linux-{arch}")
    spec = repo_path("scripts", "firedm-linux.spec")
    if not spec.is_file():
        raise SystemExit(f"Linux PyInstaller spec missing: {spec}")

    pyinstaller_dist = work / "pyinstaller-dist"
    pyinstaller_work = work / "pyinstaller-work"
    pyinstaller_dist.mkdir(parents=True, exist_ok=True)
    pyinstaller_work.mkdir(parents=True, exist_ok=True)
    run_checked(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--noupx",
            "--distpath",
            str(pyinstaller_dist),
            "--workpath",
            str(pyinstaller_work),
            str(spec),
        ]
    )

    source = pyinstaller_dist / "FireDM"
    if not source.is_dir():
        raise SystemExit(f"PyInstaller did not produce FireDM/ under {pyinstaller_dist}")
    if not (source / "firedm").is_file() or not (source / "FireDM-GUI").is_file():
        raise SystemExit("PyInstaller payload missing firedm or FireDM-GUI executables")

    destination = clean_dir(linux_payload_root(arch))
    if allow_overwrite and destination.exists():
        shutil.rmtree(destination)
        destination.mkdir(parents=True)
    shutil.copytree(source, destination, dirs_exist_ok=True)
    for executable in (destination / "firedm", destination / "FireDM-GUI"):
        make_executable(executable)
    return destination


def write_payload_manifest(arch: str, channel: str, build_id: str, payload: Path) -> dict:
    files = []
    for path in sorted(payload.rglob("*")):
        if path.is_file():
            mode = path.stat().st_mode
            files.append(
                {
                    "path": path.relative_to(payload).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": file_sha256(path),
                    "executable": bool(mode & stat.S_IXUSR),
                }
            )
    metadata = build_metadata(arch, channel, build_id)
    metadata.update(
        {
            "kind": "linux-payload",
            "platform": "linux",
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
    write_json(linux_payload_manifest_path(arch), metadata)
    write_json(payload / "payload-manifest.json", metadata)
    return metadata


def make_archive(arch: str, channel: str, build_id: str, payload: Path, allow_overwrite: bool) -> Path:
    portable = ensure_dir(LINUX_PORTABLE_DIR)
    archive = portable / linux_archive_name(build_id, channel, arch)
    if archive.exists():
        if not allow_overwrite:
            raise SystemExit(f"Linux archive already exists: {archive}")
        archive.unlink()
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(payload, arcname="FireDM")
    return archive


def write_per_platform_manifest(
    *,
    arch: str,
    channel: str,
    build_id: str,
    selection,
    payload: Path,
    archive: Path,
    dependency_status: Path,
    license_inventory: Path,
    release_body: Path,
    payload_manifest: dict,
) -> Path:
    manifest_path = DIST_DIR / per_platform_release_manifest_name(build_id, "linux")
    manifest = {
        "version": read_version(),
        "build_id": build_id,
        "build_code": build_id,
        "build_date": selection.date,
        "build_index": selection.index,
        "tag_name": selection.tag,
        "release_name": selection.release_name,
        "channel": channel,
        "arch": arch,
        "platform": "linux",
        "gitCommit": payload_manifest.get("gitCommit", ""),
        "gitBranch": payload_manifest.get("gitBranch", ""),
        "workingTreeDirty": payload_manifest.get("workingTreeDirty", False),
        "buildIdSource": {
            "sourceDateMode": selection.source_date_mode,
            "collisionStatus": selection.collision_status,
            "discoveredExistingIds": selection.discovered_existing_ids,
        },
        "validation": {
            "linux_payload": "passed",
            "linux_portable": "passed",
        },
        "artifacts": [
            {
                "kind": "linuxPortableArchive",
                "path": dist_ref(archive),
                "platform": "linux",
                "arch": arch,
                "size": archive.stat().st_size,
                "sha256": file_sha256(archive),
                "signed": False,
                "validation_status": "passed",
            },
            {
                "kind": "linuxPayloadManifest",
                "path": dist_ref(linux_payload_manifest_path(arch)),
                "platform": "linux",
                "arch": arch,
                "size": linux_payload_manifest_path(arch).stat().st_size,
                "sha256": file_sha256(linux_payload_manifest_path(arch)),
                "signed": False,
            },
            {
                "kind": "licenseInventory",
                "path": dist_ref(license_inventory),
                "platform": "linux",
                "arch": arch,
                "size": license_inventory.stat().st_size if license_inventory.is_file() else 0,
                "sha256": file_sha256(license_inventory) if license_inventory.is_file() else "",
                "signed": False,
            },
            {
                "kind": "releaseNotes",
                "path": dist_ref(release_body),
                "platform": "linux",
                "arch": arch,
                "size": release_body.stat().st_size,
                "sha256": file_sha256(release_body),
                "signed": False,
            },
            {
                "kind": "dependencyStatus",
                "path": dist_ref(dependency_status),
                "platform": "linux",
                "arch": arch,
                "size": dependency_status.stat().st_size if dependency_status.is_file() else 0,
                "sha256": file_sha256(dependency_status) if dependency_status.is_file() else "",
                "signed": False,
            },
        ],
        "checksumsPath": f"checksums/{checksum_file_name(build_id)}",
        "ffmpegBundled": False,
        "ffmpegPolicy": "not bundled; detected as optional external tool",
        "blockedArtifacts": {
            "appImage": "blocked until AppImage tooling is integrated and validated",
            "deb": "blocked until dpkg/.deb packaging is integrated",
            "rpm": "blocked until rpm packaging is integrated",
        },
    }
    write_json(manifest_path, manifest)
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FireDM Linux release lane.")
    parser.add_argument("--arch", choices=["x64"], required=True)
    parser.add_argument("--channel", default="dev")
    parser.add_argument("--date", help="Override build date as YYYYMMDD.")
    parser.add_argument("--build-id", help="Explicit build ID as YYYYMMDD_VN.")
    parser.add_argument("--build-code", help="Synonym for --build-id.")
    parser.add_argument("--allow-overwrite", action="store_true")
    parser.add_argument("--include-remote-tags", action="store_true")
    parser.add_argument("--include-github-releases", action="store_true")
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()
    require_supported_linux_arch(parser, args.arch)
    if args.channel == "stable":
        os.environ["FIREDM_REQUIRE_SIGNING"] = "1"
    build_code = args.build_id or args.build_code

    if sys.platform != "linux":
        raise SystemExit("build_linux.py must run on Linux. PyInstaller is not a cross-compiler.")

    selection = select_build_id(
        date=args.date,
        build_id=build_code,
        allow_overwrite=args.allow_overwrite,
        include_remote_tags=args.include_remote_tags,
        include_github_releases=args.include_github_releases,
    )
    build_id = selection.build_id

    print(f"Build code: {build_id}")
    print(f"Tag: {selection.tag}")
    print(f"Release name: {selection.release_name}")

    dependency_status = DIST_DIR / dependency_status_name(build_id)
    run_checked(
        [
            sys.executable,
            str(repo_path("scripts", "release", "check_dependencies.py")),
            "--arch",
            args.arch,
            "--channel",
            args.channel,
            "--build-id",
            build_id,
            "--skip-portable",
            "--json",
            "--output",
            str(dependency_status),
        ]
    )

    payload = package_payload(args.arch, args.channel, build_id, args.allow_overwrite)
    write_portable_readme(payload, read_version(), args.arch)
    payload_manifest = write_payload_manifest(args.arch, args.channel, build_id, payload)
    archive = make_archive(args.arch, args.channel, build_id, payload, args.allow_overwrite)

    run_script("collect_licenses.py", "--build-id", build_id)
    license_inventory = LICENSES_DIR / license_inventory_name(build_id)
    release_body = DIST_DIR / release_notes_name(build_id)
    if not release_body.is_file():
        release_body.write_text(
            "\n".join(
                [
                    f"# FireDM {build_id} Linux {args.arch} {args.channel}",
                    "",
                    f"Linux x64 portable archive built by `scripts/release/build_linux.py`.",
                    "",
                    f"Tag: `{selection.tag}`",
                    f"Release name: `{selection.release_name}`",
                    "",
                    "FFmpeg/ffprobe stay detect-only. AppImage/.deb/.rpm lanes remain blocked.",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    if not args.skip_validation:
        run_script("validate_linux_payload.py", "--arch", args.arch)
        run_script("validate_linux_portable.py", "--archive", str(archive))

    manifest_path = write_per_platform_manifest(
        arch=args.arch,
        channel=args.channel,
        build_id=build_id,
        selection=selection,
        payload=payload,
        archive=archive,
        dependency_status=dependency_status,
        license_inventory=license_inventory,
        release_body=release_body,
        payload_manifest=payload_manifest,
    )

    ensure_dir(CHECKSUMS_DIR)
    print(f"Linux portable ready: {archive}")
    print(f"Linux per-platform manifest: {manifest_path}")
    return None


if __name__ == "__main__":
    main()
