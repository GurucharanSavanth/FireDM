from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import traceback
import winreg
import zipfile
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path

APP_NAME = "FireDM"
PUBLISHER = "Gurucharan Savanth"
UNINSTALL_ROOT = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
STATE_RELATIVE_PATH = Path("installer") / "install-state.json"


def runtime_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def load_manifest() -> dict:
    manifest_path = runtime_dir() / "installer-manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"Installer manifest missing: {manifest_path}")
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Installer manifest is corrupt: {manifest_path}") from exc


def locate_payload_zip(manifest: dict) -> Path:
    payload_name = manifest["payloadZip"]
    candidates = [runtime_dir() / payload_name]
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / payload_name)
    candidates.append(Path.cwd() / payload_name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError(f"Installer payload missing: {payload_name}")


def default_install_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("LOCALAPPDATA is not defined")
    return Path(local_app_data) / "Programs" / APP_NAME


def windows_arch() -> str:
    arch = os.environ.get("PROCESSOR_ARCHITEW6432") or os.environ.get("PROCESSOR_ARCHITECTURE") or platform.machine()
    arch = arch.lower()
    if arch in {"amd64", "x64"}:
        return "x64"
    if arch in {"arm64", "aarch64"}:
        return "arm64"
    if arch in {"x86", "i386"}:
        return "x86"
    return arch


def parse_version(version: str) -> tuple[int, ...]:
    parts = []
    for piece in version.replace("-", ".").split("."):
        if piece.isdigit():
            parts.append(int(piece))
        else:
            if not parts:
                raise ValueError(f"Malformed version: {version!r}")
            break
    if not parts:
        raise ValueError(f"Malformed version: {version!r}")
    return tuple(parts)


def version_relation(installed_version: str, installer_version: str) -> str:
    installed_tuple = parse_version(installed_version)
    installer_tuple = parse_version(installer_version)
    if installed_tuple > installer_tuple:
        return "newer-installed"
    if installed_tuple == installer_tuple:
        return "same-version"
    return "upgrade"


def ensure_within(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    root_resolved = root.resolve()
    if resolved == root_resolved or root_resolved in resolved.parents:
        return resolved
    raise RuntimeError(f"Unsafe path outside expected root: {resolved}")


def unsafe_root_message(path: Path) -> str | None:
    resolved = path.resolve()
    if len(resolved.parts) < 3:
        return f"Refusing unsafe shallow path: {resolved}"

    env_roots = [
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
    ]
    for name in env_roots:
        raw = os.environ.get(name)
        if raw and resolved == Path(raw).resolve():
            return f"Refusing to operate on {name} root: {resolved}"
    return None


def assert_safe_root(path: Path) -> Path:
    resolved = path.resolve()
    message = unsafe_root_message(resolved)
    if message:
        raise RuntimeError(message)
    return resolved


def safe_rmtree(path: Path) -> None:
    path = assert_safe_root(path)
    if not path.exists():
        return
    shutil.rmtree(path)


def safe_extract(zip_path: Path, destination: Path) -> None:
    assert_safe_root(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            target = ensure_within(destination / member.filename, destination)
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)


def file_sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_payload_zip(zip_path: Path, manifest: dict) -> None:
    expected = manifest.get("payloadSha256")
    if not expected:
        raise RuntimeError("Installer manifest missing payloadSha256")
    actual = file_sha256(zip_path)
    if actual.lower() != str(expected).lower():
        raise RuntimeError(f"Installer payload checksum mismatch: expected {expected}, got {actual}")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            bad_member = zf.testzip()
    except zipfile.BadZipFile as exc:
        raise RuntimeError(f"Installer payload is not a valid zip: {zip_path}") from exc
    if bad_member:
        raise RuntimeError(f"Installer payload member failed CRC: {bad_member}")


def normalize_log_path(raw_path: str | None) -> Path | None:
    if not raw_path:
        return None
    path = Path(raw_path).resolve()
    if path.exists() and path.is_dir():
        raise RuntimeError(f"Installer log path is a directory: {path}")
    assert_safe_root(path)
    return path


def write_log(path: Path | None, message: str) -> None:
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()} {message}\n")


def quote_cmd(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def create_launcher(install_dir: Path) -> Path:
    launcher = install_dir / "FireDM-Launcher.cmd"
    lines = [
        "@echo off",
        "set FIREDM_INSTALL_DIR=%~dp0",
        "set FIREDM_RUNTIME_DIR=%~dp0_internal",
        "set FIREDM_TOOLS_DIR=%~dp0tools",
        "set FIREDM_CONFIG_DIR=%APPDATA%\\FireDM",
        "set FIREDM_CACHE_DIR=%LOCALAPPDATA%\\FireDM\\cache",
        "set FIREDM_LOG_DIR=%LOCALAPPDATA%\\FireDM\\logs",
        "set PYTHONUTF8=1",
        'start "" "%~dp0FireDM-GUI.exe"',
        "",
    ]
    launcher.write_text("\r\n".join(lines), encoding="utf-8")
    return launcher


def run_powershell_shortcut(shortcut: Path, target: Path, workdir: Path, icon: Path) -> None:
    script = "\n".join(
        [
            "param(",
            "  [Parameter(Mandatory=$true)][string]$Shortcut,",
            "  [Parameter(Mandatory=$true)][string]$Target,",
            "  [Parameter(Mandatory=$true)][string]$WorkDir,",
            "  [Parameter(Mandatory=$true)][string]$Icon",
            ")",
            "$ErrorActionPreference = 'Stop'",
            "$s = (New-Object -ComObject WScript.Shell).CreateShortcut($Shortcut)",
            "$s.TargetPath = $Target",
            "$s.WorkingDirectory = $WorkDir",
            "$s.IconLocation = $Icon",
            "$s.Save()",
        ]
    )
    script_path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8") as handle:
            script_path = Path(handle.name)
            handle.write(script)
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                "-Shortcut",
                str(shortcut),
                "-Target",
                str(target),
                "-WorkDir",
                str(workdir),
                "-Icon",
                str(icon),
            ],
            check=True,
        )
    finally:
        if script_path:
            with suppress(OSError):
                script_path.unlink(missing_ok=True)


def start_menu_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA is not defined")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / APP_NAME


def desktop_dir() -> Path:
    userprofile = os.environ.get("USERPROFILE")
    if not userprofile:
        raise RuntimeError("USERPROFILE is not defined")
    return Path(userprofile) / "Desktop"


def create_shortcuts(install_dir: Path, shortcut_name: str, desktop: bool, start_menu: bool) -> dict:
    launcher = create_launcher(install_dir)
    icon = install_dir / "FireDM-GUI.exe"
    created: dict[str, str] = {}
    if start_menu:
        menu = start_menu_dir()
        menu.mkdir(parents=True, exist_ok=True)
        shortcut = menu / f"{shortcut_name}.lnk"
        run_powershell_shortcut(shortcut, launcher, install_dir, icon)
        created["startMenu"] = str(shortcut)
    if desktop:
        shortcut = desktop_dir() / f"{shortcut_name}.lnk"
        run_powershell_shortcut(shortcut, launcher, install_dir, icon)
        created["desktop"] = str(shortcut)
    return created


def remove_shortcuts(state: dict | None, shortcut_name: str) -> None:
    paths = []
    if state:
        shortcuts = state.get("shortcuts", {})
        paths.extend(shortcuts.values())
    paths.append(str(start_menu_dir() / f"{shortcut_name}.lnk"))
    paths.append(str(desktop_dir() / f"{shortcut_name}.lnk"))
    for raw in set(paths):
        if not raw:
            continue
        with suppress(OSError):
            Path(raw).unlink(missing_ok=True)
    try:
        menu = start_menu_dir()
        if menu.exists() and not any(menu.iterdir()):
            menu.rmdir()
    except OSError:
        pass


def uninstall_key(registry_id: str) -> str:
    return rf"{UNINSTALL_ROOT}\{registry_id}"


def read_installed_version(registry_id: str) -> tuple[str, str]:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, uninstall_key(registry_id)) as key:
            version = winreg.QueryValueEx(key, "DisplayVersion")[0]
            location = winreg.QueryValueEx(key, "InstallLocation")[0]
            return str(version), str(location)
    except OSError:
        return "", ""


def write_uninstall_registry(
    registry_id: str,
    install_dir: Path,
    version: str,
    channel: str,
    arch: str,
    uninstaller: Path,
) -> None:
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, uninstall_key(registry_id)) as key:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, version)
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(install_dir / "FireDM-GUI.exe"))
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'{quote_cmd(str(uninstaller))} --uninstall')
        winreg.SetValueEx(
            key,
            "QuietUninstallString",
            0,
            winreg.REG_SZ,
            f'{quote_cmd(str(uninstaller))} --uninstall --silent',
        )
        winreg.SetValueEx(key, "URLInfoAbout", 0, winreg.REG_SZ, "https://github.com/GurucharanSavanth/FireDM")
        winreg.SetValueEx(key, "FireDMChannel", 0, winreg.REG_SZ, channel)
        winreg.SetValueEx(key, "FireDMArchitecture", 0, winreg.REG_SZ, arch)


def remove_uninstall_registry(registry_id: str) -> None:
    with suppress(OSError):
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, uninstall_key(registry_id))


def load_state(install_dir: Path) -> dict | None:
    state_path = install_dir / STATE_RELATIVE_PATH
    if not state_path.is_file():
        return None
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_state(install_dir: Path, state: dict) -> None:
    state_dir = install_dir / "installer"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "install-state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def copy_self_to_install_dir(install_dir: Path) -> Path:
    installer_dir = install_dir / "installer"
    installer_dir.mkdir(parents=True, exist_ok=True)
    destination = installer_dir / "FireDM-Uninstall.exe"
    if getattr(sys, "frozen", False):
        shutil.copy2(sys.executable, destination)
        source_internal = Path(sys.executable).resolve().parent / "_internal"
        if source_internal.is_dir():
            destination_internal = installer_dir / "_internal"
            if destination_internal.exists():
                shutil.rmtree(destination_internal)
            shutil.copytree(source_internal, destination_internal)
    else:
        destination.with_suffix(".txt").write_text(
            "Source-mode installer validation did not copy a frozen uninstaller.\n",
            encoding="utf-8",
        )
    return destination


def is_directory_empty(path: Path) -> bool:
    if not path.exists():
        return True
    try:
        return not any(path.iterdir())
    except OSError:
        return False


def state_owns_install_dir(state: dict | None, install_dir: Path, registry_id: str) -> bool:
    if not state:
        return False
    try:
        state_dir = Path(str(state.get("installDir", ""))).resolve()
    except OSError:
        return False
    return state_dir == install_dir.resolve() and str(state.get("registryId", "")) == registry_id


def assert_can_replace_install_dir(install_dir: Path, registry_id: str) -> None:
    install_dir = assert_safe_root(install_dir)
    if not install_dir.exists() or is_directory_empty(install_dir):
        return
    if state_owns_install_dir(load_state(install_dir), install_dir, registry_id):
        return
    raise RuntimeError(f"Refusing to replace unmanaged install directory: {install_dir}")


def assert_can_uninstall_dir(install_dir: Path, registry_id: str) -> None:
    install_dir = assert_safe_root(install_dir)
    if not install_dir.exists():
        return
    if state_owns_install_dir(load_state(install_dir), install_dir, registry_id):
        return
    raise RuntimeError(f"Refusing to uninstall unmanaged directory: {install_dir}")


def install(args: argparse.Namespace, manifest: dict) -> int:
    if sys.platform != "win32":
        raise RuntimeError("This installer supports Windows only")

    actual_arch = windows_arch()
    expected_arch = manifest["arch"]
    if expected_arch != actual_arch and not (expected_arch == "x64" and actual_arch == "arm64"):
        raise RuntimeError(f"Installer architecture {expected_arch} does not match this machine ({actual_arch})")

    install_dir = assert_safe_root(Path(args.install_dir) if args.install_dir else default_install_dir())
    version = manifest["version"]
    installed_version, installed_location = read_installed_version(args.registry_id)
    if installed_version:
        try:
            relation = version_relation(installed_version, version)
        except ValueError as exc:
            if not args.allow_downgrade:
                raise RuntimeError(
                    f"Installed version cannot be compared safely: {installed_version!r}. "
                    "Use --allow-downgrade only for maintainer-approved recovery."
                ) from exc
            relation = "unknown"
        if relation == "newer-installed" and not args.allow_downgrade:
            raise RuntimeError(
                f"Downgrade blocked: installed {installed_version}, installer {version}. "
                "Use --allow-downgrade only for maintainer-approved rollback."
            )
        if not args.install_dir and installed_location:
            install_dir = assert_safe_root(Path(installed_location))

    payload_zip = locate_payload_zip(manifest)
    verify_payload_zip(payload_zip, manifest)

    backup_state = load_state(install_dir)
    if install_dir.exists():
        assert_can_replace_install_dir(install_dir, args.registry_id)
        safe_rmtree(install_dir)
    install_dir.mkdir(parents=True, exist_ok=True)
    safe_extract(payload_zip, install_dir)
    launcher = create_launcher(install_dir)
    shortcuts = create_shortcuts(
        install_dir,
        shortcut_name=args.shortcut_name,
        desktop=args.desktop_shortcut,
        start_menu=not args.no_start_menu,
    )
    uninstaller = copy_self_to_install_dir(install_dir)

    state = {
        "installedVersion": version,
        "channel": manifest["channel"],
        "arch": manifest["arch"],
        "installDir": str(install_dir),
        "installedAtUtc": datetime.now(timezone.utc).isoformat(),
        "payloadSha256": manifest.get("payloadSha256"),
        "installerSha256": manifest.get("installerSha256"),
        "registryId": args.registry_id,
        "shortcutName": args.shortcut_name,
        "shortcuts": shortcuts,
        "launcher": str(launcher),
        "previousStateSeen": bool(backup_state),
        "userDataPolicy": "preserve-by-default",
    }
    write_state(install_dir, state)
    if not args.no_registry:
        write_uninstall_registry(args.registry_id, install_dir, version, manifest["channel"], manifest["arch"], uninstaller)
    if args.launch:
        subprocess.Popen([str(install_dir / "FireDM-GUI.exe")], cwd=install_dir)
    return 0


def user_data_roots() -> list[Path]:
    roots = []
    appdata = os.environ.get("APPDATA")
    local = os.environ.get("LOCALAPPDATA")
    if appdata:
        roots.append(Path(appdata) / APP_NAME)
    if local:
        roots.append(Path(local) / APP_NAME)
    return roots


def maybe_remove_user_data() -> None:
    for root in user_data_roots():
        try:
            if root.name.lower() == APP_NAME.lower() and root.exists():
                safe_rmtree(root)
        except OSError:
            pass


def uninstall(args: argparse.Namespace) -> int:
    install_dir = Path(args.install_dir) if args.install_dir else None
    state = None
    if install_dir is None:
        _, installed_location = read_installed_version(args.registry_id)
        install_dir = Path(installed_location) if installed_location else default_install_dir()
    install_dir = assert_safe_root(install_dir)
    assert_can_uninstall_dir(install_dir, args.registry_id)

    if not args.uninstall_stage2 and getattr(sys, "frozen", False):
        try:
            if install_dir in Path(sys.executable).resolve().parents:
                temp_dir = Path(tempfile.mkdtemp(prefix="firedm-uninstall-"))
                temp_exe = temp_dir / "FireDM-Uninstall.exe"
                shutil.copy2(sys.executable, temp_exe)
                subprocess.Popen(
                    [
                        str(temp_exe),
                        "--uninstall",
                        "--uninstall-stage2",
                        "--silent",
                        "--install-dir",
                        str(install_dir),
                        "--registry-id",
                        args.registry_id,
                        "--shortcut-name",
                        args.shortcut_name,
                    ],
                    cwd=temp_dir,
                )
                return 0
        except OSError:
            pass

    state = load_state(install_dir)
    remove_shortcuts(state, args.shortcut_name)
    remove_uninstall_registry(args.registry_id)
    if install_dir.exists():
        safe_rmtree(install_dir)
    if args.remove_user_data:
        maybe_remove_user_data()
    return 0


def main() -> int:
    try:
        manifest = load_manifest()
    except Exception as exc:
        print(f"FireDM installer failed: {exc}", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description=f"FireDM {manifest['version']} Windows installer")
    parser.add_argument("--silent", action="store_true", help="Run without prompts.")
    parser.add_argument("--install-dir", help="Override install directory.")
    parser.add_argument("--desktop-shortcut", action="store_true", help="Create Desktop shortcut.")
    parser.add_argument("--no-start-menu", action="store_true", help="Do not create Start Menu shortcut.")
    parser.add_argument("--launch", action="store_true", help="Launch FireDM after install.")
    parser.add_argument("--repair", action="store_true", help="Repair/reinstall the same version.")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall FireDM.")
    parser.add_argument("--remove-user-data", action="store_true", help="Remove FireDM AppData/LocalAppData data on uninstall.")
    parser.add_argument("--allow-downgrade", action="store_true", help="Allow maintainer-approved downgrade.")
    parser.add_argument("--log", help="Write installer log to this path.")
    parser.add_argument("--registry-id", default=APP_NAME, help=argparse.SUPPRESS)
    parser.add_argument("--shortcut-name", default=APP_NAME, help=argparse.SUPPRESS)
    parser.add_argument("--no-registry", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--uninstall-stage2", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    log_path = normalize_log_path(args.log)
    try:
        write_log(log_path, f"start action={'uninstall' if args.uninstall else 'install'} version={manifest['version']}")
        result = uninstall(args) if args.uninstall else install(args, manifest)
        write_log(log_path, f"completed result={result}")
        return result
    except Exception as exc:
        write_log(log_path, f"failed {exc}")
        if not args.silent:
            print(f"FireDM installer failed: {exc}", file=sys.stderr)
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
