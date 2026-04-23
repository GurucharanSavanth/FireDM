import os
import subprocess
import sys
import unittest
from pathlib import Path

from firedm.FireDM import is_gui_mode, pars_args

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
