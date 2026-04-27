# FireDM Plugin System - Generated Implementation
# File: firedm/plugins/browser_integration.py
# Default State: DISABLED
# User Toggle: GUI > Settings > Plugin Manager
"""Browser integration plugin - registers stdio native messaging host manifest."""

import json
import os
import sys
from pathlib import Path

from .. import config
from ..native_messaging import HOST_NAME
from ..utils import log
from .registry import PluginBase, PluginMeta, PluginRegistry

META = PluginMeta(
    name="browser_integration",
    version="1.0.0",
    author="FireDM",
    description="Native messaging host (stdio) for Chrome/Firefox/Edge capture",
    default_enabled=False,
)

_HOST_NAME = HOST_NAME


class BrowserIntegrationPlugin(PluginBase):
    META = META

    def on_load(self) -> bool:
        """Register native host manifest pointing to a native_host launcher."""
        try:
            host_path = self._resolve_native_host_launcher()

            manifest = {
                "name": _HOST_NAME,
                "description": "FireDM Native Host",
                "path": host_path,
                "type": "stdio",
                "allowed_origins": [],
            }

            origins_path = os.path.join(config.sett_folder, "allowed_origins.json")
            if os.path.isfile(origins_path):
                try:
                    with open(origins_path, "r", encoding="utf-8") as f:
                        manifest["allowed_origins"] = json.load(f)
                except Exception as e:
                    log("Browser integration: allowed_origins.json read error:", e)
                    manifest["allowed_origins"] = []
            else:
                manifest["allowed_origins"] = [
                    "chrome-extension://firedm-extension-id/",
                ]

            manifest_path = os.path.join(config.sett_folder, "firedm_native.json")
            os.makedirs(config.sett_folder, exist_ok=True)
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f)

            if config.operating_system == "Windows":
                self._register_windows_manifest(manifest_path)
            elif config.operating_system == "Linux":
                self._register_linux_manifest(manifest_path)
            elif config.operating_system == "Darwin":
                self._register_macos_manifest(manifest_path)

            log("Browser integration: manifests registered")
            self._start_controller_endpoint_if_ready()
            return True

        except Exception as e:
            log("Browser integration load failed:", e)
            return False

    def on_unload(self) -> bool:
        self._stop_controller_endpoint_if_ready()
        log("Browser integration: stopped")
        return True

    def _resolve_native_host_launcher(self):
        host_script = Path(__file__).resolve().parents[1] / "native_host.py"
        exe_dir = Path(sys.executable).resolve().parent

        candidates = []
        if config.operating_system == "Windows":
            candidates.extend(
                [
                    exe_dir / "FireDM-Native-Host.exe",
                    exe_dir / "firedm-native-host.exe",
                    exe_dir / "firedm-native-host.cmd",
                ]
            )
        else:
            candidates.extend(
                [
                    exe_dir / "firedm-native-host",
                    exe_dir / "FireDM-Native-Host",
                ]
            )

        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)

        return str(self._write_launcher(host_script))

    def _write_launcher(self, host_script: Path) -> Path:
        settings_folder = Path(config.sett_folder)
        settings_folder.mkdir(parents=True, exist_ok=True)
        if getattr(sys, "frozen", False):
            command = [str(Path(sys.executable).resolve()), "--native-host"]
        else:
            command = [str(Path(sys.executable).resolve()), str(host_script)]

        if config.operating_system == "Windows":
            launcher = settings_folder / "firedm-native-host.cmd"
            launcher.write_text(
                "@echo off\r\n" + " ".join(f'"{part}"' for part in command) + "\r\n",
                encoding="utf-8",
            )
        else:
            launcher = settings_folder / "firedm-native-host"
            quoted = " ".join("'" + part.replace("'", "'\"'\"'") + "'" for part in command)
            launcher.write_text("#!/bin/sh\nexec " + quoted + ' "$@"\n', encoding="utf-8")
            try:
                launcher.chmod(0o700)
            except OSError:
                pass
        return launcher

    def _start_controller_endpoint_if_ready(self):
        try:
            controller_module = sys.modules.get("firedm.controller")
            if controller_module is None:
                return
            Controller = controller_module.Controller

            ctrl = Controller._instance
            if ctrl is not None and getattr(ctrl, "_native_endpoint_ready", False):
                ctrl._start_native_control_endpoint(force=True)
        except Exception as e:
            log("Browser integration: controller endpoint start failed:", e)

    def _stop_controller_endpoint_if_ready(self):
        try:
            controller_module = sys.modules.get("firedm.controller")
            if controller_module is None:
                return
            Controller = controller_module.Controller

            ctrl = Controller._instance
            if ctrl is not None:
                ctrl._stop_native_control_endpoint()
        except Exception as e:
            log("Browser integration: controller endpoint stop failed:", e)

    def _register_windows_manifest(self, manifest_path):
        try:
            import winreg

            for key_path in (
                r"Software\Google\Chrome\NativeMessagingHosts\com.firedm.nativehost",
                r"Software\Mozilla\NativeMessagingHosts\com.firedm.nativehost",
            ):
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
                winreg.SetValue(key, "", winreg.REG_SZ, manifest_path)
                winreg.CloseKey(key)
        except Exception as e:
            log("Browser integration: Windows registry write failed:", e)

    def _register_linux_manifest(self, manifest_path):
        import shutil

        for dest_dir in (
            os.path.expanduser("~/.config/google-chrome/NativeMessagingHosts/"),
            os.path.expanduser("~/.mozilla/native-messaging-hosts/"),
        ):
            try:
                os.makedirs(dest_dir, exist_ok=True)
                dest = os.path.join(dest_dir, f"{_HOST_NAME}.json")
                shutil.copy2(manifest_path, dest)
            except Exception as e:
                log(f"Browser integration: Linux manifest install failed ({dest_dir}):", e)

    def _register_macos_manifest(self, manifest_path):
        import shutil

        for dest_dir in (
            os.path.expanduser("~/Library/Application Support/Google/Chrome/NativeMessagingHosts/"),
            os.path.expanduser("~/Library/Application Support/Mozilla/NativeMessagingHosts/"),
        ):
            try:
                os.makedirs(dest_dir, exist_ok=True)
                dest = os.path.join(dest_dir, f"{_HOST_NAME}.json")
                shutil.copy2(manifest_path, dest)
            except Exception as e:
                log(f"Browser integration: macOS manifest install failed ({dest_dir}):", e)


PluginRegistry.register(BrowserIntegrationPlugin)
