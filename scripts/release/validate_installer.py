from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import winreg
from contextlib import suppress
from pathlib import Path


def run(
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    log_dir: Path | None = None,
    label: str = "command",
) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(args), flush=True)
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        safe_label = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in label)
        (log_dir / f"{safe_label}.stdout.txt").write_text(result.stdout or "", encoding="utf-8")
        (log_dir / f"{safe_label}.stderr.txt").write_text(result.stderr or "", encoding="utf-8")
    return result


def assert_ok(result: subprocess.CompletedProcess[str]) -> None:
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def assert_failed(result: subprocess.CompletedProcess[str], message: str) -> None:
    if result.returncode == 0:
        raise SystemExit(message)


def uninstall_key(registry_id: str) -> str:
    return rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{registry_id}"


def registry_exists(registry_id: str) -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, uninstall_key(registry_id)):
            return True
    except OSError:
        return False


def registry_value(registry_id: str, name: str) -> str:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, uninstall_key(registry_id)) as key:
        return str(winreg.QueryValueEx(key, name)[0])


def set_registry_version(registry_id: str, version: str) -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, uninstall_key(registry_id), 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, version)


def remove_registry(registry_id: str) -> None:
    with suppress(OSError):
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, uninstall_key(registry_id))


def temp_env(temp_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    appdata = temp_root / "UserData" / "Roaming"
    local = temp_root / "UserData" / "Local"
    profile = temp_root / "UserProfile"
    for path in (appdata, local, profile / "Desktop"):
        path.mkdir(parents=True, exist_ok=True)
    env["APPDATA"] = str(appdata)
    env["LOCALAPPDATA"] = str(local)
    env["USERPROFILE"] = str(profile)
    return env


def remove_validation_temp_root(path: Path) -> None:
    resolved = path.resolve()
    temp_base = Path(tempfile.gettempdir()).resolve()
    if temp_base != resolved and temp_base not in resolved.parents:
        raise RuntimeError(f"Refusing to remove non-temp validation root: {resolved}")
    if not resolved.name.startswith("firedm-installer-validation-"):
        raise RuntimeError(f"Refusing to remove unexpected validation root: {resolved}")
    shutil.rmtree(resolved)


def start_menu_shortcut(env: dict[str, str], shortcut_name: str) -> Path:
    return (
        Path(env["APPDATA"])
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "FireDM"
        / f"{shortcut_name}.lnk"
    )


def desktop_shortcut(env: dict[str, str], shortcut_name: str) -> Path:
    return Path(env["USERPROFILE"]) / "Desktop" / f"{shortcut_name}.lnk"


def install_args(
    installer: Path,
    install_dir: Path,
    registry_id: str,
    shortcut_name: str,
    log_path: Path,
    *extra: str,
) -> list[str]:
    return [
        str(installer),
        "--silent",
        "--install-dir",
        str(install_dir),
        "--registry-id",
        registry_id,
        "--shortcut-name",
        shortcut_name,
        "--log",
        str(log_path),
        *extra,
    ]


def assert_required_install_tree(install_dir: Path) -> None:
    required = [
        "firedm.exe",
        "FireDM-GUI.exe",
        "FireDM-Launcher.cmd",
        "_internal/tkinter/__init__.py",
        "_internal/_tcl_data/init.tcl",
        "_internal/_tk_data/tk.tcl",
        "installer/install-state.json",
    ]
    missing = [item for item in required if not (install_dir / item).is_file()]
    if missing:
        raise SystemExit(f"Installed files missing: {missing}")


def read_install_state(install_dir: Path) -> dict:
    return json.loads((install_dir / "installer" / "install-state.json").read_text(encoding="utf-8"))


def smoke_installed_cli(install_dir: Path, log_dir: Path | None = None, env: dict[str, str] | None = None) -> None:
    smoke = run([str(install_dir / "firedm.exe"), "--help"], cwd=install_dir, env=env, log_dir=log_dir, label="installed_help")
    assert_ok(smoke)
    imports = run(
        [str(install_dir / "firedm.exe"), "--imports-only"],
        cwd=install_dir,
        env=env,
        log_dir=log_dir,
        label="installed_imports",
    )
    assert_ok(imports)


def write_synthetic_state_version(install_dir: Path, version: str) -> None:
    state = read_install_state(install_dir)
    state["installedVersion"] = version
    (install_dir / "installer" / "install-state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate FireDM installer in an isolated temp install root.")
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--keep", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--keep-temp-on-failure", action="store_true")
    parser.add_argument("--log-dir")
    parser.add_argument("--test-upgrade", action="store_true")
    parser.add_argument("--test-downgrade-block", action="store_true")
    parser.add_argument("--test-repair", action="store_true")
    parser.add_argument("--test-uninstall", action="store_true")
    args = parser.parse_args()

    selected_tests = args.test_upgrade or args.test_downgrade_block or args.test_repair or args.test_uninstall
    if not selected_tests:
        args.test_repair = True
        args.test_uninstall = True

    installer = Path(args.artifact).resolve()
    if not installer.is_file():
        raise SystemExit(f"Installer missing: {installer}")

    temp_root = Path(tempfile.mkdtemp(prefix="firedm-installer-validation-"))
    install_dir = temp_root / "InstallRoot" / "FireDM"
    log_path = temp_root / "install.log"
    registry_id = "FireDM-InstallerValidation"
    shortcut_name = "FireDM Validation"
    env = temp_env(temp_root)
    log_dir = Path(args.log_dir).resolve() if args.log_dir else temp_root / "logs"
    before_path = os.environ.get("PATH", "")
    failed = False

    try:
        remove_registry(registry_id)
        help_result = run([str(installer), "--help"], env=env, log_dir=log_dir, label="installer_help")
        assert_ok(help_result)
        if "--silent" not in help_result.stdout:
            raise SystemExit("Installer help output did not include --silent.")

        install_result = run(
            install_args(
                installer,
                install_dir,
                registry_id,
                shortcut_name,
                log_path,
                "--desktop-shortcut",
            ),
            env=env,
            log_dir=log_dir,
            label="install",
        )
        assert_ok(install_result)
        assert_required_install_tree(install_dir)
        if not registry_exists(registry_id):
            raise SystemExit("Validation uninstall registry entry missing.")
        if not start_menu_shortcut(env, shortcut_name).is_file():
            raise SystemExit("Start Menu shortcut was not created.")
        if not desktop_shortcut(env, shortcut_name).is_file():
            raise SystemExit("Desktop shortcut was not created.")
        smoke_installed_cli(install_dir, log_dir=log_dir, env=env)

        version = registry_value(registry_id, "DisplayVersion")
        user_config = Path(env["APPDATA"]) / "FireDM" / "setting.cfg"
        user_config.parent.mkdir(parents=True, exist_ok=True)
        user_config.write_text("preserve=true\n", encoding="utf-8")

        if args.test_upgrade:
            stale_file = install_dir / "stale-old-file.txt"
            stale_file.write_text("old", encoding="utf-8")
            set_registry_version(registry_id, "0.0.1")
            write_synthetic_state_version(install_dir, "0.0.1")
            upgrade = run(
                install_args(installer, install_dir, registry_id, shortcut_name, log_path, "--desktop-shortcut"),
                env=env,
                log_dir=log_dir,
                label="upgrade",
            )
            assert_ok(upgrade)
            if stale_file.exists():
                raise SystemExit("Upgrade did not remove stale program file.")
            if not user_config.is_file():
                raise SystemExit("Upgrade removed user config.")
            if registry_value(registry_id, "DisplayVersion") != version:
                raise SystemExit("Upgrade did not restore current DisplayVersion.")
            if not read_install_state(install_dir).get("previousStateSeen"):
                raise SystemExit("Upgrade did not record previous installer state.")

        if args.test_repair:
            launcher = install_dir / "FireDM-GUI.exe"
            launcher.unlink()
            repair = run(
                install_args(installer, install_dir, registry_id, shortcut_name, log_path, "--repair", "--desktop-shortcut"),
                env=env,
                log_dir=log_dir,
                label="repair",
            )
            assert_ok(repair)
            if not launcher.is_file():
                raise SystemExit("Repair did not restore FireDM-GUI.exe.")

        if args.test_downgrade_block:
            set_registry_version(registry_id, "9999.0.0")
            downgrade = run(
                install_args(installer, install_dir, registry_id, shortcut_name, log_path),
                env=env,
                log_dir=log_dir,
                label="downgrade_block",
            )
            assert_failed(downgrade, "Downgrade was not blocked.")
            if not install_dir.exists():
                raise SystemExit("Downgrade block removed the install directory.")

        if args.test_uninstall:
            uninstall = run(
                install_args(installer, install_dir, registry_id, shortcut_name, log_path, "--uninstall"),
                env=env,
                log_dir=log_dir,
                label="uninstall",
            )
            assert_ok(uninstall)
            for _ in range(30):
                if not install_dir.exists():
                    break
                time.sleep(0.2)
            if install_dir.exists():
                raise SystemExit("Uninstall did not remove install directory.")
            if registry_exists(registry_id):
                raise SystemExit("Uninstall did not remove validation registry entry.")
            if start_menu_shortcut(env, shortcut_name).exists():
                raise SystemExit("Uninstall did not remove Start Menu shortcut.")
            if desktop_shortcut(env, shortcut_name).exists():
                raise SystemExit("Uninstall did not remove Desktop shortcut.")
            if not user_config.is_file():
                raise SystemExit("Uninstall removed user config by default.")

        if os.environ.get("PATH", "") != before_path:
            raise SystemExit("Validation detected parent PATH mutation.")
        print(f"Installer validation passed: {installer}")
    except BaseException:
        failed = True
        raise
    finally:
        if not args.keep and not (failed and args.keep_temp_on_failure):
            remove_registry(registry_id)
            if temp_root.exists():
                remove_validation_temp_root(temp_root)
        elif failed:
            print(f"Keeping validation temp root: {temp_root}", file=sys.stderr)


if __name__ == "__main__":
    main()
