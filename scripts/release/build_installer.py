from __future__ import annotations

import argparse
import os
import subprocess
import zipfile
from pathlib import Path

from common import (
    BUILD_DIR,
    CHECKSUMS_DIR,
    INSTALLERS_DIR,
    build_metadata,
    clean_dir,
    dist_ref,
    ensure_dir,
    file_sha256,
    installer_manifest_name,
    installer_name,
    payload_root,
    payload_zip_name,
    read_version,
    repo_path,
    require_supported_arch,
    run_checked,
    write_json,
)


def signing_required() -> bool:
    return os.environ.get("FIREDM_REQUIRE_SIGNING", "").strip().lower() in {"1", "true", "yes"}


def run_sensitive(args: list[str], redacted: list[str]) -> None:
    print("+", " ".join(redacted), flush=True)
    result = subprocess.run(args, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def maybe_sign_artifact(artifact: Path) -> dict[str, object]:
    signtool = os.environ.get("FIREDM_SIGNTOOL", "").strip()
    cert_sha1 = os.environ.get("FIREDM_SIGN_CERT_SHA1", "").strip()
    pfx = os.environ.get("FIREDM_SIGN_PFX", "").strip()
    pfx_password = os.environ.get("FIREDM_SIGN_PFX_PASSWORD", "")
    timestamp_url = os.environ.get("FIREDM_SIGN_TIMESTAMP_URL", "").strip()

    if not signtool:
        if signing_required():
            raise SystemExit("FIREDM_REQUIRE_SIGNING is set but FIREDM_SIGNTOOL is not configured.")
        return {"signed": False, "signatureStatus": "unsigned: FIREDM_SIGNTOOL not configured"}

    sign_cmd = [signtool, "sign", "/fd", "SHA256"]
    redacted = [signtool, "sign", "/fd", "SHA256"]
    if timestamp_url:
        sign_cmd.extend(["/tr", timestamp_url, "/td", "SHA256"])
        redacted.extend(["/tr", timestamp_url, "/td", "SHA256"])
    if cert_sha1:
        sign_cmd.extend(["/sha1", cert_sha1])
        redacted.extend(["/sha1", cert_sha1])
    elif pfx:
        sign_cmd.extend(["/f", pfx])
        redacted.extend(["/f", pfx])
        if pfx_password:
            sign_cmd.extend(["/p", pfx_password])
            redacted.extend(["/p", "<redacted>"])
    elif signing_required():
        raise SystemExit("Signing requested but FIREDM_SIGN_CERT_SHA1 or FIREDM_SIGN_PFX is not configured.")
    else:
        return {"signed": False, "signatureStatus": "unsigned: certificate selector not configured"}
    sign_cmd.append(str(artifact))
    redacted.append(str(artifact))
    run_sensitive(sign_cmd, redacted)

    verify_cmd = [signtool, "verify", "/pa", "/v", str(artifact)]
    run_sensitive(verify_cmd, verify_cmd)
    return {"signed": True, "signatureStatus": "signed and verified with signtool"}


def zip_payload(payload: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(payload.rglob("*")):
            if path.is_dir():
                continue
            zf.write(path, path.relative_to(payload).as_posix())


def build_installer(args: argparse.Namespace) -> Path:
    if args.arch != "x64":
        raise SystemExit(f"{args.arch} installer is blocked in this checkout; only x64 is implemented.")
    version = read_version()
    payload = payload_root(args.arch)
    if not payload.is_dir():
        raise SystemExit(f"Payload missing: {payload}. Run build_payload.py first.")

    work = clean_dir(BUILD_DIR / "installer" / f"win-{args.arch}")
    payload_zip = work / payload_zip_name(version, args.arch)
    zip_payload(payload, payload_zip)

    manifest = build_metadata(args.arch, args.channel)
    manifest.update(
        {
            "kind": "installer",
            "product": "FireDM",
            "payloadZip": payload_zip.name,
            "payloadSha256": file_sha256(payload_zip),
            "installScopeDefault": "per-user",
            "defaultInstallDir": "%LOCALAPPDATA%\\Programs\\FireDM",
            "globalPathMutationDefault": False,
            "supports": {
                "freshInstall": True,
                "silentInstall": True,
                "startMenuShortcut": True,
                "desktopShortcut": True,
                "repair": True,
                "uninstall": True,
                "upgrade": True,
                "downgradeBlockedByDefault": True,
            },
            "blocked": {
                "universalBootstrapper": "only x64 payload exists",
                "msi": "WiX tooling unavailable locally",
                "msix": "MSIX signing/tooling not configured",
                "ffmpegBundling": "license/source/checksum review required",
            },
        }
    )
    manifest_path = work / installer_manifest_name()
    write_json(manifest_path, manifest)

    ensure_dir(INSTALLERS_DIR)
    output_name = installer_name(version, args.channel, args.arch)
    run_checked(
        [
            os.fspath(repo_path(".venv", "Scripts", "python.exe")) if (repo_path(".venv", "Scripts", "python.exe")).exists() else os.fspath(Path(os.sys.executable)),
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--onefile",
            "--name",
            Path(output_name).stem,
            "--distpath",
            os.fspath(INSTALLERS_DIR),
            "--workpath",
            os.fspath(work / "pyinstaller"),
            "--specpath",
            os.fspath(work),
            "--add-data",
            f"{payload_zip}{os.pathsep}.",
            "--add-data",
            f"{manifest_path}{os.pathsep}.",
            os.fspath(repo_path("scripts", "release", "installer_bootstrap.py")),
        ]
    )
    installer = INSTALLERS_DIR / output_name
    if not installer.is_file():
        raise SystemExit(f"Expected installer was not created: {installer}")

    signature = maybe_sign_artifact(installer)
    manifest["installer"] = dist_ref(installer)
    manifest["installerSize"] = installer.stat().st_size
    manifest["installerSha256"] = file_sha256(installer)
    manifest.update(signature)
    write_json(work / "built-installer-manifest.json", manifest)
    write_json(INSTALLERS_DIR / f"{Path(output_name).stem}.manifest.json", manifest)
    ensure_dir(CHECKSUMS_DIR)
    print(f"Installer ready: {installer}")
    return installer


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FireDM Windows installer bootstrapper.")
    parser.add_argument("--arch", choices=["x64", "x86", "arm64"], required=True)
    parser.add_argument("--channel", default="dev")
    args = parser.parse_args()
    require_supported_arch(parser, args.arch)
    build_installer(args)


if __name__ == "__main__":
    main()
