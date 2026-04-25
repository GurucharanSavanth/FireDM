"""Adapter for extractor module loading and deterministic selection.

Policy:
    `yt_dlp` is the primary and the preferred default. `youtube_dl` is retained
    only as a secondary fallback; it is unmaintained upstream and must not be
    selected as the mainline extractor when `yt_dlp` is available.

The adapter exposes:
    - `load_extractor_module(name)` — pure import helper (no side effects).
    - `choose_extractor_name(configured, available)` — selection rule.
    - `ExtractorService` — runtime holder for the active extractor that
      tests and callers can query without racing two background threads.
"""

from __future__ import annotations

import importlib
import threading
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from types import ModuleType

SUPPORTED_EXTRACTORS = ("yt_dlp", "youtube_dl")
PRIMARY_EXTRACTOR = "yt_dlp"
FALLBACK_EXTRACTOR = "youtube_dl"


@dataclass(frozen=True)
class ExtractorModule:
    name: str
    module: ModuleType
    version: str = ""


def get_extractor_version(module: ModuleType) -> str:
    version_module = getattr(module, "version", None)
    return getattr(version_module, "__version__", "")


def load_extractor_module(
    name: str,
    *,
    reload_existing: bool = False,
    existing_module: ModuleType | None = None,
    importer: Callable[[str], ModuleType] = importlib.import_module,
) -> ExtractorModule:
    module = importlib.reload(existing_module) if reload_existing and existing_module is not None else importer(name)
    return ExtractorModule(name=name, module=module, version=get_extractor_version(module))


def choose_extractor_name(configured: str | None, available_extractors: Iterable[str]) -> str | None:
    """Pick the extractor name to use.

    Priority:
        1. `PRIMARY_EXTRACTOR` if available — this is a hard policy; we do not
           keep a deprecated extractor as the default just because the user
           previously set `active_video_extractor=youtube_dl`.
        2. `configured` if available (allows user override to the fallback if
           the primary import fails at runtime).
        3. First available extractor.
    """
    available = list(dict.fromkeys(available_extractors))
    if not available:
        return None

    if PRIMARY_EXTRACTOR in available:
        return PRIMARY_EXTRACTOR

    if configured in available:
        return configured

    return available[0]


class ExtractorService:
    """Runtime holder for the active extractor module.

    Tests and callers use `wait_until_ready()` / `current()` so there is
    exactly one source of truth. `video.py` keeps its legacy module globals
    for now but mirrors them off this service on every state change.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._ready = threading.Event()
        self._modules: dict[str, ModuleType] = {}
        self._versions: dict[str, str] = {}
        self._active_name: str | None = None

    def record_load(self, loaded: ExtractorModule) -> None:
        with self._lock:
            self._modules[loaded.name] = loaded.module
            self._versions[loaded.name] = loaded.version
            self._reselect_active_locked(preferred=None)
            if self._active_name is not None:
                self._ready.set()

    def set_configured(self, preferred: str | None) -> None:
        with self._lock:
            self._reselect_active_locked(preferred=preferred)
            if self._active_name is not None:
                self._ready.set()

    def _reselect_active_locked(self, preferred: str | None) -> None:
        chosen = choose_extractor_name(preferred, self._modules.keys())
        self._active_name = chosen

    def current(self) -> tuple[str | None, ModuleType | None]:
        with self._lock:
            if self._active_name is None:
                return None, None
            return self._active_name, self._modules.get(self._active_name)

    def active_name(self) -> str | None:
        return self.current()[0]

    def active_module(self) -> ModuleType | None:
        return self.current()[1]

    def module(self, name: str) -> ModuleType | None:
        with self._lock:
            return self._modules.get(name)

    def version(self, name: str) -> str:
        with self._lock:
            return self._versions.get(name, "")

    def wait_until_ready(self, timeout: float) -> bool:
        """Block up to `timeout` seconds for a default to be chosen.

        Returns True if the service has an active extractor when the wait
        finishes, False on timeout. Never sleeps-forever — callers get a
        deterministic signal to act on.
        """
        if self._ready.is_set():
            return True
        deadline = time.time() + max(0.0, timeout)
        while time.time() < deadline:
            if self._ready.wait(timeout=min(0.5, max(0.05, deadline - time.time()))):
                return True
        return self._ready.is_set()

    def is_primary_active(self) -> bool:
        return self.active_name() == PRIMARY_EXTRACTOR

    def snapshot(self) -> dict[str, object]:
        """Plain dict for diagnostics / JSON artifacts."""
        with self._lock:
            return {
                "active": self._active_name,
                "primary": PRIMARY_EXTRACTOR,
                "fallback": FALLBACK_EXTRACTOR,
                "primary_loaded": PRIMARY_EXTRACTOR in self._modules,
                "fallback_loaded": FALLBACK_EXTRACTOR in self._modules,
                "versions": dict(self._versions),
            }


# Module-level singleton — imported by video.py, tests, and scripts.
SERVICE = ExtractorService()
