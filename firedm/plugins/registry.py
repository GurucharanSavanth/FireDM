# FireDM Plugin System — Generated Implementation
# File: firedm/plugins/registry.py
# Default State: DISABLED
# User Toggle: GUI → Settings → Plugin Manager
"""Plugin registry and hook dispatcher. All plugins default disabled."""

import ast
import importlib
import importlib.util
import inspect
import os
import sys
import textwrap
import threading
from typing import Callable, Dict, List, Type

from .. import config
from ..utils import log

__all__ = ["PluginBase", "PluginMeta", "PluginRegistry"]


class PluginMeta:
    __slots__ = (
        "name",
        "version",
        "author",
        "description",
        "default_enabled",
        "dependencies",
        "conflicts",
        "enabled",
        "loaded",
        "instance",
        "plugin_class",
        "filepath",
    )

    def __init__(
        self,
        name: str,
        version: str,
        author: str,
        description: str,
        default_enabled: bool = False,
        dependencies: List[str] = None,
        conflicts: List[str] = None,
    ):
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.default_enabled = bool(default_enabled)
        self.dependencies = dependencies or []
        self.conflicts = conflicts or []
        self.enabled = False
        self.loaded = False
        self.instance = None
        self.plugin_class = None
        self.filepath = ""


class PluginBase:
    META = None

    def __init__(self):
        if self.META is None:
            raise RuntimeError(f"{self.__class__.__name__} missing META")

    def on_load(self) -> bool:
        return True

    def on_unload(self) -> bool:
        return True

    def on_download_start(self, d) -> bool:
        return True

    def on_segment_complete(self, seg) -> bool:
        return True

    def on_download_complete(self, d) -> bool:
        return True

    def on_config_change(self, key, value):
        return True


class PluginRegistry:
    _plugins: Dict[str, PluginMeta] = {}
    _plugin_classes: Dict[str, Type[PluginBase]] = {}
    _hooks: Dict[str, Dict[str, Callable]] = {
        "download_start": {},
        "segment_complete": {},
        "download_complete": {},
        "config_change": {},
    }
    _lock = threading.RLock()

    @classmethod
    def register(cls, plugin_class: Type[PluginBase]) -> None:
        with cls._lock:
            if not inspect.isclass(plugin_class) or not issubclass(plugin_class, PluginBase):
                log("Plugin registration rejected: invalid class")
                return

            meta = getattr(plugin_class, "META", None)
            if meta is None:
                log("Plugin registration rejected: missing META")
                return
            if not isinstance(meta, PluginMeta) or not meta.name:
                log("Plugin registration rejected: invalid META")
                return
            if meta.name in cls._plugins:
                return
            if cls._uses_forbidden_exec(plugin_class):
                log(f"Plugin rejected for eval/exec: {meta.name}")
                return

            # Security contract: plugins are never enabled by default.
            meta.default_enabled = False
            meta.enabled = False
            meta.loaded = False
            meta.instance = None
            meta.plugin_class = plugin_class
            meta.filepath = inspect.getsourcefile(plugin_class) or ""

            cls._plugins[meta.name] = meta
            cls._plugin_classes[meta.name] = plugin_class
            log(f"Plugin registered: {meta.name} v{meta.version}", log_level=2)

    @classmethod
    def load(cls, name: str) -> bool:
        with cls._lock:
            meta = cls._plugins.get(name)
            plugin_class = cls._plugin_classes.get(name)
            if not meta or not plugin_class:
                log(f"Plugin not found: {name}")
                return False
            if meta.loaded:
                return True

            for conflict in meta.conflicts:
                conflict_meta = cls._plugins.get(conflict)
                if conflict_meta and conflict_meta.enabled:
                    log(f"Plugin {name} conflicts with {conflict}")
                    return False

            for dep in meta.dependencies:
                dep_meta = cls._plugins.get(dep)
                if not dep_meta or not dep_meta.enabled:
                    log(f"Plugin {name} missing dependency: {dep}")
                    return False

            try:
                instance = plugin_class()
                if not instance.on_load():
                    meta.instance = None
                    return False

                meta.instance = instance
                meta.enabled = True
                meta.loaded = True
                cls._attach_hooks(name, instance)
                if not isinstance(config.plugin_states, dict):
                    config.plugin_states = {}
                config.plugin_states[name] = True
                log(f"Plugin enabled: {name}")
                return True
            except Exception as e:
                log(f"Plugin load failed: {name} - {e}")
                meta.instance = None
                meta.enabled = False
                meta.loaded = False
                return False

    @classmethod
    def unload(cls, name: str) -> bool:
        with cls._lock:
            meta = cls._plugins.get(name)
            if not meta or not meta.loaded:
                return False

            try:
                if meta.instance and not meta.instance.on_unload():
                    return False

                cls._detach_hooks(name)
                meta.enabled = False
                meta.loaded = False
                meta.instance = None
                if not isinstance(config.plugin_states, dict):
                    config.plugin_states = {}
                config.plugin_states[name] = False
                log(f"Plugin disabled: {name}")
                return True
            except Exception as e:
                log(f"Plugin unload error: {name} - {e}")
                return False

    @classmethod
    def _attach_hooks(cls, name: str, instance: PluginBase) -> None:
        cls._hooks["download_start"][name] = instance.on_download_start
        cls._hooks["segment_complete"][name] = instance.on_segment_complete
        cls._hooks["download_complete"][name] = instance.on_download_complete
        cls._hooks["config_change"][name] = instance.on_config_change

    @classmethod
    def _detach_hooks(cls, name: str) -> None:
        for hook_dict in cls._hooks.values():
            hook_dict.pop(name, None)

    @classmethod
    def fire_hook(cls, hook_name: str, *args, **kwargs) -> bool:
        """Return False if any handler blocks."""
        for plugin_name, handler in list(cls._hooks.get(hook_name, {}).items()):
            try:
                if handler(*args, **kwargs) is False:
                    log(f"Hook {hook_name} blocked by plugin: {plugin_name}", log_level=2)
                    return False
            except Exception as e:
                log(f"Hook {hook_name} error in {plugin_name}: {e}")
        return True

    @classmethod
    def scan_plugins(cls, plugin_dir: str = None) -> None:
        """Scan built-in plugins and user plugins only when explicitly allowed."""
        cls._scan_builtin_dir(plugin_dir or os.path.dirname(__file__))

        user_dir = getattr(config, "plugin_dir", "")
        if getattr(config, "allow_user_plugins", False) and user_dir:
            cls._scan_user_plugins(user_dir)

    @classmethod
    def get_plugin_list(cls) -> List[PluginMeta]:
        with cls._lock:
            return sorted(cls._plugins.values(), key=lambda meta: meta.name)

    @classmethod
    def is_enabled(cls, name: str) -> bool:
        meta = cls._plugins.get(name)
        return bool(meta and meta.enabled)

    @classmethod
    def _scan_builtin_dir(cls, plugin_dir: str) -> None:
        if not os.path.isdir(plugin_dir):
            return

        for fname in sorted(os.listdir(plugin_dir)):
            if not fname.endswith(".py") or fname.startswith("_") or fname in {"registry.py", "__init__.py"}:
                continue

            mod_name = f"firedm.plugins.{fname[:-3]}"
            try:
                mod = importlib.import_module(mod_name)
                cls._register_from_module(mod)
            except Exception as e:
                log(f"Plugin scan error: {fname} - {e}")

    @classmethod
    def _scan_user_plugins(cls, user_dir: str) -> None:
        if not os.path.isdir(user_dir):
            return

        for fname in sorted(os.listdir(user_dir)):
            if not fname.endswith(".py") or fname.startswith("_"):
                continue

            fpath = os.path.abspath(os.path.join(user_dir, fname))
            if cls._file_uses_forbidden_exec(fpath):
                log(f"User plugin rejected for eval/exec: {fname}")
                continue
            if os.name != "nt":
                try:
                    if os.stat(fpath).st_mode & 0o022:
                        log(f"User plugin rejected (writable by group/others): {fname}")
                        continue
                except OSError as e:
                    log(f"User plugin stat error: {fname} - {e}")
                    continue

            mod_name = f"firedm_user_plugin_{os.path.splitext(fname)[0]}"
            spec = importlib.util.spec_from_file_location(mod_name, fpath)
            if not spec or not spec.loader:
                continue

            try:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = mod
                spec.loader.exec_module(mod)
                cls._register_from_module(mod)
            except Exception as e:
                log(f"User plugin error: {fname} - {e}")

    @classmethod
    def _register_from_module(cls, mod) -> None:
        for _, obj in inspect.getmembers(mod):
            if (
                inspect.isclass(obj)
                and issubclass(obj, PluginBase)
                and obj is not PluginBase
                and getattr(obj, "META", None) is not None
            ):
                cls.register(obj)

    @staticmethod
    def _uses_forbidden_exec(plugin_class: Type[PluginBase]) -> bool:
        try:
            source = textwrap.dedent(inspect.getsource(plugin_class))
            tree = ast.parse(source)
        except Exception:
            return False

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"eval", "exec"}:
                    return True
        return False

    @staticmethod
    def _file_uses_forbidden_exec(path: str) -> bool:
        try:
            with open(path, encoding="utf-8") as file:
                tree = ast.parse(file.read(), filename=path)
        except Exception:
            return True

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"eval", "exec"}:
                    return True
        return False
