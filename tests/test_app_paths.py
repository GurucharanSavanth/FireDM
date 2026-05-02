from pathlib import Path

from firedm.app_paths import choose_settings_dir, resolve_global_settings_dir


def test_resolve_global_settings_dir_windows():
    path = resolve_global_settings_dir(
        "FireDM",
        "Windows",
        env={"APPDATA": r"C:\Users\Test\AppData\Roaming"},
        home=r"C:\Users\Test",
    )

    assert path == Path(r"C:\Users\Test\AppData\Roaming") / ".FireDM"


def test_resolve_global_settings_dir_linux():
    path = resolve_global_settings_dir("FireDM", "Linux", home="/home/test")

    assert path == Path("/home/test/.config/FireDM")


def test_choose_settings_dir_prefers_existing_local(tmp_path):
    current_dir = tmp_path / "current"
    global_dir = tmp_path / "global"
    current_dir.mkdir()
    global_dir.mkdir()
    (current_dir / "setting.cfg").write_text("{}", encoding="utf-8")

    result = choose_settings_dir(current_dir, global_dir)

    assert result == current_dir


def test_choose_settings_dir_falls_back_to_global_when_local_not_writable(tmp_path):
    current_dir = tmp_path / "current"
    global_dir = tmp_path / "global"
    current_dir.mkdir()

    result = choose_settings_dir(current_dir, global_dir, writable_checker=lambda _: False)

    assert result == global_dir
    assert global_dir.exists()
