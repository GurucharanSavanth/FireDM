import os
import subprocess
import sys
import time
import types
import unittest
from pathlib import Path

from firedm.FireDM import is_gui_mode, open_config_editor, pars_args

REPO_ROOT = Path(__file__).resolve().parents[1]


class FireDMCLITest(unittest.TestCase):
    def run_firedm(self, *args):
        env = os.environ.copy()
        env.setdefault("PYTHONUTF8", "1")

        return subprocess.run(
            [sys.executable, "firedm.py", *args],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def run_module(self, *args):
        env = os.environ.copy()
        env.setdefault("PYTHONUTF8", "1")

        return subprocess.run(
            [sys.executable, "-m", "firedm", *args],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_parse_show_settings_flag(self):
        self.assertTrue(pars_args(["--show-settings"]).get("show_settings"))

    def test_gui_mode_detection(self):
        self.assertTrue(is_gui_mode(["firedm"]))
        self.assertTrue(is_gui_mode(["firedm", "--gui"]))
        self.assertFalse(is_gui_mode(["firedm", "--help"]))

    def test_show_settings_prints_config_path_and_exits(self):
        result = self.run_firedm("--show-settings", "--ignore-config")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("config file path:", result.stdout)
        self.assertNotIn("No url(s) to download", result.stdout)

    def test_module_help_succeeds(self):
        result = self.run_module("--help")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("usage:", result.stdout)

    @unittest.skipUnless(os.name == "nt", "Windows-only config path text")
    def test_windows_help_mentions_actual_config_folder(self):
        result = self.run_firedm("--help")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("APPDATA/.FireDM/", result.stdout)


def test_open_config_editor_uses_argv_without_shell(monkeypatch, tmp_path):
    called = {}

    def fake_run(args, *, check, shell):
        called["args"] = args
        called["check"] = check
        called["shell"] = shell
        return subprocess.CompletedProcess(args, 7)

    monkeypatch.setattr("firedm.FireDM.subprocess.run", fake_run)
    config_fp = tmp_path / "setting.cfg"

    result = open_config_editor(r"C:\Program Files\Editor\editor.exe", str(config_fp))

    assert result == 7
    assert called == {
        "args": [r"C:\Program Files\Editor\editor.exe", str(config_fp)],
        "check": False,
        "shell": False,
    }


def test_gui_mode_routes_to_lazy_imported_main_window(monkeypatch, tmp_path):
    from firedm import FireDM

    sys.modules.pop("firedm.tkview", None)
    fake_tkview = types.ModuleType("firedm.tkview")

    class FakeMainWindow:
        pass

    fake_tkview.MainWindow = FakeMainWindow
    monkeypatch.setitem(sys.modules, "firedm.tkview", fake_tkview)
    monkeypatch.setattr(FireDM, "load_setting", lambda: None)
    monkeypatch.setattr(FireDM.setting, "save_setting", lambda: None)
    monkeypatch.setattr(FireDM.config, "sett_folder", str(tmp_path))
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)

    calls = {}

    class FakeController:
        def __init__(self, view_class, custom_settings):
            calls["view_class"] = view_class
            calls["custom_settings"] = custom_settings

        def run(self):
            calls["run"] = True

        def quit(self):
            calls["quit"] = True

    monkeypatch.setattr(FireDM, "Controller", FakeController)

    FireDM.main(["firedm"])

    assert calls["view_class"] is FakeMainWindow
    assert calls["custom_settings"] == {"url": []}
    assert calls["run"] is True
    assert calls["quit"] is True
