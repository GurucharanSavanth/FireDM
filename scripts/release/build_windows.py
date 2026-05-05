from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from build_id import select_build_id
from common import (
    CHECKSUMS_DIR,
    DIST_DIR,
    INSTALLERS_DIR,
    LICENSES_DIR,
    checksum_file_name,
    dependency_status_name,
    dist_ref,
    file_sha256,
    installer_manifest_file_name,
    installer_name,
    license_inventory_name,
    portable_name,
    read_version,
    release_manifest_name,
    release_notes_name,
    repo_path,
    require_supported_arch,
    run_checked,
    write_json,
)


def run_script(script: str, *args: str) -> None:
    run_checked([sys.executable, str(repo_path("scripts", "release", script)), *args])


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FireDM Windows release lane.")
    parser.add_argument("--arch", choices=["x64", "x86", "arm64"], required=True)
    parser.add_argument("--channel", default="dev")
    parser.add_argument("--date", help="Override build date as YYYYMMDD.")
    parser.add_argument("--build-id", help="Explicit build ID as YYYYMMDD_VN.")
    parser.add_argument("--allow-overwrite", action="store_true")
    parser.add_argument("--include-remote-tags", action="store_true")
    parser.add_argument("--include-github-releases", action="store_true")
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()
    require_supported_arch(parser, args.arch)
    if args.channel == "stable":
        os.environ["FIREDM_REQUIRE_SIGNING"] = "1"

    selection = select_build_id(
        date=args.date,
        build_id=args.build_id,
        allow_overwrite=args.allow_overwrite,
        include_remote_tags=args.include_remote_tags,
        include_github_releases=args.include_github_releases,
    )
    build_id = selection.build_id
    passthrough = ["--build-id", build_id]
    if args.allow_overwrite:
        passthrough.append("--allow-overwrite")

    print(f"Build ID: {build_id}")
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

    run_script("build_payload.py", "--arch", args.arch, "--channel", args.channel, *passthrough)
    run_script("validate_payload.py", "--arch", args.arch)
    run_script("build_installer.py", "--arch", args.arch, "--channel", args.channel, *passthrough)
    run_script("collect_licenses.py", "--build-id", build_id)

    version = read_version()
    installer_file_name = installer_name(build_id, args.channel, args.arch)
    installer = INSTALLERS_DIR / Path(installer_file_name).stem / installer_file_name
    portable = DIST_DIR / "portable" / portable_name(build_id, args.channel, args.arch)
    if not args.skip_validation:
        run_script("validate_portable.py", "--archive", str(portable))
        run_script(
            "validate_installer.py",
            "--artifact",
            str(installer),
            "--test-repair",
            "--test-uninstall",
            "--test-upgrade",
            "--test-downgrade-block",
        )

    installer_sha256 = file_sha256(installer)
    portable_sha256 = file_sha256(portable) if portable.is_file() else ""
    installer_sidecar = INSTALLERS_DIR / installer_manifest_file_name(build_id, args.channel, args.arch)
    installer_payload = installer.parent / f"FireDM_{build_id}_{args.channel}_win_{args.arch}_payload.zip"
    installer_metadata = {}
    if installer_sidecar.is_file():
        installer_metadata = json.loads(installer_sidecar.read_text(encoding="utf-8"))
    license_inventory = LICENSES_DIR / license_inventory_name(build_id)
    release_body = DIST_DIR / release_notes_name(build_id)
    checksums = CHECKSUMS_DIR / checksum_file_name(build_id)
    release_manifest = DIST_DIR / release_manifest_name(build_id)
    per_platform_manifest = DIST_DIR / f"FireDM_release_manifest_{build_id}_windows.json"

    release_body.write_text(
        "\n".join(
            [
                f"# FireDM {build_id} Windows {args.arch} {args.channel}",
                "",
                f"This release lane contains the {args.arch} installed-tree payload, {args.arch} installer bootstrapper, portable ZIP, release manifest, license inventory, and SHA256 checksums.",
                "",
                f"Tag: `{selection.tag}`",
                f"Release name: `{selection.release_name}`",
                "",
                "Artifacts are unsigned unless a maintainer signs them after build. x86, ARM64, MSI, and MSIX lanes are blocked until their toolchains and payloads are validated.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    manifest = {
        "version": version,
        "build_id": build_id,
        "build_date": selection.date,
        "build_index": selection.index,
        "tag_name": selection.tag,
        "release_name": selection.release_name,
        "channel": args.channel,
        "arch": args.arch,
        "gitCommit": installer_metadata.get("gitCommit", ""),
        "gitBranch": installer_metadata.get("gitBranch", ""),
        "workingTreeDirty": installer_metadata.get("workingTreeDirty", False),
        "buildIdSource": {
            "sourceDateMode": selection.source_date_mode,
            "collisionStatus": selection.collision_status,
            "discoveredExistingIds": selection.discovered_existing_ids,
        },
        "validation": {
            "payload": "passed",
            "portable": "skipped" if args.skip_validation else "passed",
            "installer": "skipped" if args.skip_validation else "passed",
        },
        "artifacts": [
            {
                "kind": "installer",
                "path": dist_ref(installer),
                "arch": args.arch,
                "size": installer.stat().st_size,
                "sha256": installer_sha256,
                "signed": bool(installer_metadata.get("signed", False)),
                "signatureStatus": installer_metadata.get("signatureStatus", "unknown"),
            },
            {
                "kind": "installerManifest",
                "path": dist_ref(installer_sidecar),
                "arch": args.arch,
                "size": installer_sidecar.stat().st_size if installer_sidecar.is_file() else 0,
                "sha256": file_sha256(installer_sidecar) if installer_sidecar.is_file() else "",
                "signed": False,
            },
            {
                "kind": "installerPayload",
                "path": dist_ref(installer_payload),
                "arch": args.arch,
                "size": installer_payload.stat().st_size if installer_payload.is_file() else 0,
                "sha256": file_sha256(installer_payload) if installer_payload.is_file() else "",
                "signed": False,
            },
            {
                "kind": "portableZip",
                "path": dist_ref(portable),
                "arch": args.arch,
                "size": portable.stat().st_size if portable.is_file() else 0,
                "sha256": portable_sha256,
                "signed": False,
            },
            {
                "kind": "licenseInventory",
                "path": dist_ref(license_inventory),
                "arch": args.arch,
                "size": license_inventory.stat().st_size if license_inventory.is_file() else 0,
                "sha256": file_sha256(license_inventory) if license_inventory.is_file() else "",
                "signed": False,
            },
            {
                "kind": "releaseNotes",
                "path": dist_ref(release_body),
                "arch": args.arch,
                "size": release_body.stat().st_size,
                "sha256": file_sha256(release_body),
                "signed": False,
            },
            {
                "kind": "dependencyStatus",
                "path": dist_ref(dependency_status),
                "arch": args.arch,
                "size": dependency_status.stat().st_size if dependency_status.is_file() else 0,
                "sha256": file_sha256(dependency_status) if dependency_status.is_file() else "",
                "signed": False,
            },
        ],
        "checksumsPath": dist_ref(checksums),
        "dependencyStatusPath": dist_ref(dependency_status),
        "ffmpegBundled": False,
        "ffmpegPolicy": "not bundled; detected as optional external tool",
        "compatibilityAliases": {
            "releaseManifest": "release-manifest.json",
            "checksums": "checksums/SHA256SUMS.txt",
            "licenseInventory": "licenses/license-inventory.json",
            "releaseNotes": "release-body.md",
        },
        "legacyArtifacts": {
            "installer": dist_ref(installer),
            "installerSha256": installer_sha256,
            "portableZip": dist_ref(portable),
            "portableSha256": portable_sha256,
            "checksums": dist_ref(checksums),
        },
        "blockedArtifacts": {
            "winUniversal": "blocked until x86 and ARM64 payloads are built and validated",
            "msi": "blocked until WiX tooling is available",
            "msix": "blocked until MSIX signing/tooling is configured",
        },
    }
    manifest["platform"] = "windows"
    manifest["build_code"] = build_id
    write_json(release_manifest, manifest)
    write_json(per_platform_manifest, manifest)
    write_json(DIST_DIR / "release-manifest.json", manifest)
    (DIST_DIR / "release-body.md").write_text(release_body.read_text(encoding="utf-8"), encoding="utf-8")
    run_script("generate_checksums.py", "--build-id", build_id)
    print(f"Windows release lane ready: {installer}")


if __name__ == "__main__":
    main()
