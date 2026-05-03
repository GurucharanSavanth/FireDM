"""Download-engine abstraction seam.

This package defines typed contracts, configuration, and a registry for
future download adapters. The `InternalHTTPDownloadEngine` is registered by
the default factory but is intentionally **not** wired to the legacy runtime
yet — `Controller` -> `brain` -> `worker` remains the only code path that
actually moves bytes for current users.
"""

from .base import DownloadEngine
from .config import SCHEMA_VERSION as ENGINE_CONFIG_SCHEMA_VERSION
from .config import EngineConfig
from .factory import (
    DefaultRegistryResult,
    create_default_registry,
    select_engine,
)
from .internal_http import InternalHTTPDownloadEngine
from .models import (
    DownloadFailure,
    DownloadJob,
    DownloadProgress,
    DownloadRequest,
    DownloadResult,
    DownloadState,
    EngineCapability,
    EngineDescriptor,
    EngineHealth,
    EngineHealthStatus,
    EngineInputType,
    Header,
    PreflightResult,
)
from .registry import EngineRegistry, engine_health

__all__ = [
    "DefaultRegistryResult",
    "DownloadEngine",
    "DownloadFailure",
    "DownloadJob",
    "DownloadProgress",
    "DownloadRequest",
    "DownloadResult",
    "DownloadState",
    "ENGINE_CONFIG_SCHEMA_VERSION",
    "EngineCapability",
    "EngineConfig",
    "EngineDescriptor",
    "EngineHealth",
    "EngineHealthStatus",
    "EngineInputType",
    "EngineRegistry",
    "Header",
    "InternalHTTPDownloadEngine",
    "PreflightResult",
    "create_default_registry",
    "engine_health",
    "select_engine",
]
