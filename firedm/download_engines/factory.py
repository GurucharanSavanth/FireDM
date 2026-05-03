"""Factory helpers for assembling a default `EngineRegistry`.

Currently registers only `InternalHTTPDownloadEngine`. aria2c, yt-dlp, and any
other adapters will be added by future patches with their own dependency
probes and security review.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .base import DownloadEngine
from .config import EngineConfig
from .internal_http import InternalHTTPDownloadEngine
from .models import EngineInputType
from .registry import EngineRegistry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DefaultRegistryResult:
    """Outcome of `create_default_registry`.

    `registry` is the constructed registry. `effective_default_engine_id` is
    the requested default if that engine id is registered; otherwise it is
    `None`. Health is *not* checked here -- engine availability can flap
    independently of the configured default, so callers should still go
    through `select_engine` (which does check health) before issuing work.
    `warnings` is a tuple of human-readable strings describing downgrades
    (for example: requested default was disabled, or requested default is
    not a registered engine id).
    """

    registry: EngineRegistry
    effective_default_engine_id: str | None
    warnings: tuple[str, ...]


def create_default_registry(
    config: EngineConfig | None = None,
) -> DefaultRegistryResult:
    """Build the production registry for the current runtime.

    - Always registers `InternalHTTPDownloadEngine` unless the caller's
      `EngineConfig` explicitly lists it in `disabled_engine_ids`.
    - Never registers test/null engines. Tests that need them can use
      `EngineRegistry((FakeEngine(...),))` directly or call
      `_create_registry_for_tests`.
    - aria2c, yt-dlp, ffmpeg-post-process adapters are intentionally NOT
      registered yet; they will arrive in dedicated patches.
    """
    cfg = config if config is not None else EngineConfig()
    registry = EngineRegistry()
    warnings: list[str] = []

    internal_id = InternalHTTPDownloadEngine.ENGINE_ID
    if not cfg.is_disabled(internal_id):
        registry.register(InternalHTTPDownloadEngine())
    else:
        warnings.append(
            f"Engine {internal_id!r} is disabled by config; not registered"
        )

    effective_default = _resolve_effective_default(cfg, registry, warnings)

    for warning in warnings:
        logger.warning("download_engines.factory: %s", warning)

    return DefaultRegistryResult(
        registry=registry,
        effective_default_engine_id=effective_default,
        warnings=tuple(warnings),
    )


def _resolve_effective_default(
    config: EngineConfig,
    registry: EngineRegistry,
    warnings: list[str],
) -> str | None:
    requested = config.default_engine_id
    if requested is None:
        return None
    engine = registry.get(requested)
    if engine is None:
        warnings.append(
            f"Configured default engine {requested!r} is not registered; "
            f"falling back to auto-selection"
        )
        return None
    return requested


def select_engine(
    registry: EngineRegistry,
    config: EngineConfig,
    *,
    scheme: str | None = None,
    input_type: EngineInputType | None = None,
) -> DownloadEngine | None:
    """Resolve preferences -> registry.select for a given request shape.

    Resolution order:
    1. Per-scheme preference, if `scheme` is given and a preferred id matches.
    2. Per-input-type preference, if `input_type` is given and a preferred id
       matches.
    3. `config.default_engine_id`.
    4. If `config.auto_select_enabled`, fall back to the first usable engine
       returned by `registry.select(scheme=..., input_type=...)`.
    Returns `None` if nothing matches.

    Disabled engines are not registered, so they are never selected.
    """
    candidates: list[str | None] = []
    if scheme is not None:
        candidates.append(config.preferred_for_scheme(scheme))
    if input_type is not None:
        candidates.append(config.preferred_for_input_type(input_type))
    candidates.append(config.default_engine_id)

    for preferred in candidates:
        if preferred is None:
            continue
        engine = registry.select(
            preferred=preferred,
            scheme=scheme,
            input_type=input_type,
        )
        if engine is not None:
            return engine

    if config.auto_select_enabled:
        return registry.select(scheme=scheme, input_type=input_type)
    return None


def _create_registry_for_tests(
    extra_engines: tuple[DownloadEngine, ...] = (),
    *,
    include_internal: bool = True,
) -> EngineRegistry:
    """Internal helper for unit tests only.

    Production code should call `create_default_registry`. This helper is
    namespaced with a leading underscore so it does not appear in
    `__init__.py` re-exports.
    """
    registry = EngineRegistry()
    if include_internal:
        registry.register(InternalHTTPDownloadEngine())
    for engine in extra_engines:
        registry.register(engine)
    return registry
