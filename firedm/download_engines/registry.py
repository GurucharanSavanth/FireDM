"""Registry for download engine adapters."""

from __future__ import annotations

import threading

from .base import DownloadEngine
from .models import (
    EngineDescriptor,
    EngineHealth,
    EngineInputType,
    validate_engine_id,
)


def engine_health(engine: DownloadEngine) -> EngineHealth:
    """Run an engine health check without letting adapter bugs escape."""
    try:
        health: object = engine.health_check()
    except Exception as exc:  # pragma: no cover - exact exception shape is adapter-owned
        return EngineHealth.unavailable(f"{type(exc).__name__}: {exc}")
    if not isinstance(health, EngineHealth):
        return EngineHealth.unavailable("health_check returned invalid result")
    return health


def _normalized_schemes(engine: DownloadEngine) -> tuple[str, ...]:
    return tuple(dict.fromkeys(scheme.lower().rstrip(":") for scheme in engine.supported_schemes))


class EngineRegistry:
    """Thread-safe holder for engine adapters.

    The registry is intentionally local to callers for now. A global runtime
    registry will be introduced only when UI/controller integration is ready.
    """

    def __init__(self, engines: tuple[DownloadEngine, ...] = ()) -> None:
        self._lock = threading.RLock()
        self._engines: dict[str, DownloadEngine] = {}
        for engine in engines:
            self.register(engine)

    def register(self, engine: DownloadEngine) -> None:
        engine_id = engine.id
        validate_engine_id(engine_id)
        with self._lock:
            if engine_id in self._engines:
                raise ValueError(f"Download engine already registered: {engine_id}")
            self._engines[engine_id] = engine

    def unregister(self, engine_id: str) -> bool:
        validate_engine_id(engine_id)
        with self._lock:
            return self._engines.pop(engine_id, None) is not None

    def get(self, engine_id: str) -> DownloadEngine | None:
        validate_engine_id(engine_id)
        with self._lock:
            return self._engines.get(engine_id)

    def require(self, engine_id: str) -> DownloadEngine:
        engine = self.get(engine_id)
        if engine is None:
            raise KeyError(engine_id)
        return engine

    def ids(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._engines))

    def descriptors(self, *, include_unavailable: bool = True) -> tuple[EngineDescriptor, ...]:
        with self._lock:
            engines = tuple(self._engines.values())

        descriptors = []
        for engine in sorted(engines, key=lambda item: item.id):
            health = engine_health(engine)
            if not include_unavailable and not health.usable:
                continue
            descriptors.append(
                EngineDescriptor(
                    id=engine.id,
                    display_name=engine.display_name,
                    supported_schemes=_normalized_schemes(engine),
                    supported_input_types=tuple(engine.supported_input_types),
                    capabilities=tuple(engine.capabilities),
                    health=health,
                )
            )
        return tuple(descriptors)

    def select(
        self,
        *,
        preferred: str | None = None,
        scheme: str | None = None,
        input_type: EngineInputType | None = None,
    ) -> DownloadEngine | None:
        """Select a usable engine matching optional filters.

        `preferred` is honored only when that engine is registered, healthy or
        degraded, and supports the requested scheme/input type. Running jobs
        are not tracked here and cannot be migrated by this registry.
        """
        with self._lock:
            engines = tuple(self._engines.values())

        candidates = sorted(engines, key=lambda item: item.id)
        if preferred is not None:
            validate_engine_id(preferred)
            preferred_engine = next((engine for engine in candidates if engine.id == preferred), None)
            if preferred_engine and self._matches(preferred_engine, scheme=scheme, input_type=input_type):
                return preferred_engine
            return None

        for engine in candidates:
            if self._matches(engine, scheme=scheme, input_type=input_type):
                return engine
        return None

    @staticmethod
    def _matches(
        engine: DownloadEngine,
        *,
        scheme: str | None,
        input_type: EngineInputType | None,
    ) -> bool:
        if not engine_health(engine).usable:
            return False
        if scheme is not None and scheme.lower().rstrip(":") not in _normalized_schemes(engine):
            return False
        return not (input_type is not None and input_type not in engine.supported_input_types)
