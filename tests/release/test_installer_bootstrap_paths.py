from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows installer bootstrap tests require winreg")


def load_bootstrap():
    path = Path(__file__).resolve().parents[2] / "scripts" / "release" / "installer_bootstrap.py"
    spec = importlib.util.spec_from_file_location("installer_bootstrap_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_state(module, root: Path, registry_id: str = "FireDM-Test") -> None:
    state_path = root / module.STATE_RELATIVE_PATH
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        json.dumps({"installDir": str(root.resolve()), "registryId": registry_id}),
        encoding="utf-8",
    )


def test_safe_extract_rejects_path_traversal(tmp_path):
    module = load_bootstrap()
    archive = tmp_path / "payload.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../escape.txt", "bad")

    with pytest.raises(RuntimeError, match="outside expected root"):
        module.safe_extract(archive, tmp_path / "install" / "FireDM")

    assert not (tmp_path / "escape.txt").exists()


def test_payload_checksum_mismatch_is_rejected(tmp_path):
    module = load_bootstrap()
    archive = tmp_path / "payload.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("firedm.exe", "payload")

    with pytest.raises(RuntimeError, match="checksum mismatch"):
        module.verify_payload_zip(archive, {"payloadSha256": "0" * 64})


def test_payload_checksum_and_crc_success(tmp_path):
    module = load_bootstrap()
    archive = tmp_path / "payload.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("firedm.exe", "payload")

    module.verify_payload_zip(archive, {"payloadSha256": module.file_sha256(archive)})


def test_replace_refuses_unmanaged_existing_directory(tmp_path):
    module = load_bootstrap()
    install_root = tmp_path / "Programs" / "FireDM"
    install_root.mkdir(parents=True)
    (install_root / "user-file.txt").write_text("not installer owned", encoding="utf-8")

    with pytest.raises(RuntimeError, match="unmanaged install directory"):
        module.assert_can_replace_install_dir(install_root, "FireDM-Test")


def test_replace_allows_installer_owned_directory(tmp_path):
    module = load_bootstrap()
    install_root = tmp_path / "Programs" / "FireDM"
    install_root.mkdir(parents=True)
    write_state(module, install_root)

    module.assert_can_replace_install_dir(install_root, "FireDM-Test")


def test_uninstall_refuses_unmanaged_directory(tmp_path):
    module = load_bootstrap()
    install_root = tmp_path / "Programs" / "FireDM"
    install_root.mkdir(parents=True)
    (install_root / "firedm.exe").write_text("", encoding="utf-8")

    with pytest.raises(RuntimeError, match="unmanaged directory"):
        module.assert_can_uninstall_dir(install_root, "FireDM-Test")


def test_log_path_must_not_be_directory(tmp_path):
    module = load_bootstrap()

    with pytest.raises(RuntimeError, match="log path is a directory"):
        module.normalize_log_path(str(tmp_path))


def test_launcher_uses_process_local_environment_without_path_pollution(tmp_path):
    module = load_bootstrap()
    launcher = module.create_launcher(tmp_path)
    text = launcher.read_text(encoding="utf-8")

    assert "FIREDM_INSTALL_DIR" in text
    assert "PYTHONUTF8=1" in text
    assert "set PATH=" not in text.upper()
    assert "PYTHONPATH" not in text
    assert "PYTHONHOME" not in text


def test_shortcut_create_and_remove_use_expected_paths(monkeypatch, tmp_path):
    module = load_bootstrap()
    appdata = tmp_path / "AppData" / "Roaming"
    profile = tmp_path / "Profile"
    desktop = profile / "Desktop"
    desktop.mkdir(parents=True)
    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.setenv("USERPROFILE", str(profile))
    calls = []

    def fake_shortcut(shortcut, target, workdir, icon):
        calls.append((shortcut, target, workdir, icon))
        shortcut.parent.mkdir(parents=True, exist_ok=True)
        shortcut.write_text(str(target), encoding="utf-8")

    monkeypatch.setattr(module, "run_powershell_shortcut", fake_shortcut)
    install_root = tmp_path / "Programs" / "FireDM"
    install_root.mkdir(parents=True)
    (install_root / "FireDM-GUI.exe").write_text("", encoding="utf-8")

    created = module.create_shortcuts(install_root, "FireDM Test", desktop=True, start_menu=True)

    assert Path(created["startMenu"]).is_file()
    assert Path(created["desktop"]).is_file()
    assert all(call[1] == install_root / "FireDM-Launcher.cmd" for call in calls)
    assert all(call[2] == install_root for call in calls)
    assert all(call[3] == install_root / "FireDM-GUI.exe" for call in calls)

    module.remove_shortcuts({"shortcuts": created}, "FireDM Test")

    assert not Path(created["startMenu"]).exists()
    assert not Path(created["desktop"]).exists()

