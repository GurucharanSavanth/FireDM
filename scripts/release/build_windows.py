from __future__ import annotations

import argparse
import json
import sys

from common import (
    CHECKSUMS_DIR,
    DIST_DIR,
    INSTALLERS_DIR,
    dist_ref,
    file_sha256,
    installer_name,
    portable_name,
    read_version,
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
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()
    require_supported_arch(parser, args.arch)

    run_script("build_payload.py", "--arch", args.arch, "--channel", args.channel)
    run_script("validate_payload.py", "--arch", args.arch)
    run_script("build_installer.py", "--arch", args.arch, "--channel", args.channel)
    run_script("collect_licenses.py")

    version = read_version()
    installer = INSTALLERS_DIR / installer_name(version, args.channel, args.arch)
    if not args.skip_validation:
        run_script(
            "validate_installer.py",
            "--artifact",
            str(installer),
            "--test-repair",
            "--test-uninstall",
            "--test-upgrade",
            "--test-downgrade-block",
        )

    portable = DIST_DIR / "portable" / portable_name(version, args.arch)
    installer_sha256 = file_sha256(installer)
    portable_sha256 = file_sha256(portable) if portable.is_file() else ""
    installer_sidecar = INSTALLERS_DIR / f"{installer.stem}.manifest.json"
    installer_metadata = {}
    if installer_sidecar.is_file():
        installer_metadata = json.loads(installer_sidecar.read_text(encoding="utf-8"))
    manifest = {
        "version": version,
        "channel": args.channel,
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
                "kind": "portableZip",
                "path": dist_ref(portable),
                "arch": args.arch,
                "size": portable.stat().st_size if portable.is_file() else 0,
                "sha256": portable_sha256,
                "signed": False,
            },
        ],
        "checksumsPath": dist_ref(CHECKSUMS_DIR / "SHA256SUMS.txt"),
        "legacyArtifacts": {
            "installer": dist_ref(installer),
            "installerSha256": installer_sha256,
            "portableZip": dist_ref(portable),
            "portableSha256": portable_sha256,
            "checksums": dist_ref(CHECKSUMS_DIR / "SHA256SUMS.txt"),
        },
        "blockedArtifacts": {
            "winUniversal": "blocked until x86 and ARM64 payloads are built and validated",
            "msi": "blocked until WiX tooling is available",
            "msix": "blocked until MSIX signing/tooling is configured",
        },
    }
    write_json(DIST_DIR / "release-manifest.json", manifest)
    release_body = DIST_DIR / "release-body.md"
    release_body.write_text(
        "\n".join(
            [
                f"# FireDM {version} Windows {args.arch} {args.channel}",
                "",
                f"This release lane contains the {args.arch} installed-tree payload, {args.arch} installer bootstrapper, portable ZIP, release manifest, license inventory, and SHA256 checksums.",
                "",
                "Artifacts are unsigned unless a maintainer signs them after build. x86, ARM64, MSI, and MSIX lanes are blocked until their toolchains and payloads are validated.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    run_script("generate_checksums.py")
    print(f"Windows release lane ready: {installer}")


if __name__ == "__main__":
    main()
