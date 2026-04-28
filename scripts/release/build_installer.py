from __future__ import annotations

import argparse
import os
import shutil
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
    installer_manifest_file_name,
    installer_manifest_name,
    installer_name,
    payload_root,
    payload_zip_name,
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
    payload = payload_root(args.arch)
    if not payload.is_dir():
        raise SystemExit(f"Payload missing: {payload}. Run build_payload.py first.")

    work = clean_dir(BUILD_DIR / "installer" / f"win-{args.arch}")
    payload_sidecar_name = payload_zip_name(args.build_id, args.channel, args.arch)
    payload_zip = work / payload_sidecar_name
    zip_payload(payload, payload_zip)

    manifest = build_metadata(args.arch, args.channel, args.build_id)
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
    output_name = installer_name(args.build_id, args.channel, args.arch)
    stale_flat_installer = INSTALLERS_DIR / output_name
    stale_flat_payload = INSTALLERS_DIR / payload_sidecar_name
    for stale_path in (stale_flat_installer, stale_flat_payload):
        if stale_path.exists():
            if not args.allow_overwrite:
                raise SystemExit(f"Stale flat installer artifact already exists: {stale_path}")
            if stale_path.is_dir():
                shutil.rmtree(stale_path)
            else:
                stale_path.unlink()
    installer_dir = INSTALLERS_DIR / Path(output_name).stem
    if installer_dir.exists() and not args.allow_overwrite:
        raise SystemExit(f"Installer bundle already exists: {installer_dir}")
    if installer_dir.exists():
        shutil.rmtree(installer_dir)
    installer = installer_dir / output_name
    if installer.exists() and not args.allow_overwrite:
        raise SystemExit(f"Installer already exists: {installer}")
    sidecar_payload = installer_dir / payload_sidecar_name
    if sidecar_payload.exists() and not args.allow_overwrite:
        raise SystemExit(f"Installer payload sidecar already exists: {sidecar_payload}")
    run_checked(
        [
            os.fspath(repo_path(".venv", "Scripts", "python.exe")) if (repo_path(".venv", "Scripts", "python.exe")).exists() else os.fspath(Path(os.sys.executable)),
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--noupx",
            "--onedir",
            "--name",
            Path(output_name).stem,
            "--distpath",
            os.fspath(INSTALLERS_DIR),
            "--workpath",
            os.fspath(work / "pyinstaller"),
            "--specpath",
            os.fspath(work),
            "--add-data",
            f"{manifest_path}{os.pathsep}.",
            os.fspath(repo_path("scripts", "release", "installer_bootstrap.py")),
        ]
    )
    shutil.copy2(payload_zip, sidecar_payload)
    if not installer.is_file():
        raise SystemExit(f"Expected installer was not created: {installer}")

    signature = maybe_sign_artifact(installer)
    manifest["installer"] = dist_ref(installer)
    manifest["installerPayload"] = dist_ref(sidecar_payload)
    manifest["installerSize"] = installer.stat().st_size
    manifest["installerSha256"] = file_sha256(installer)
    manifest["installerPayloadSize"] = sidecar_payload.stat().st_size
    manifest["installerPayloadSha256"] = file_sha256(sidecar_payload)
    manifest.update(signature)
    write_json(work / "built-installer-manifest.json", manifest)
    write_json(INSTALLERS_DIR / installer_manifest_file_name(args.build_id, args.channel, args.arch), manifest)
    ensure_dir(CHECKSUMS_DIR)
    print(f"Installer ready: {installer}")
    return installer


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FireDM Windows installer bootstrapper.")
    parser.add_argument("--arch", choices=["x64", "x86", "arm64"], required=True)
    parser.add_argument("--channel", default="dev")
    parser.add_argument("--build-id", required=True)
    parser.add_argument("--allow-overwrite", action="store_true")
    args = parser.parse_args()
    require_supported_arch(parser, args.arch)
    build_installer(args)


if __name__ == "__main__":
    main()
