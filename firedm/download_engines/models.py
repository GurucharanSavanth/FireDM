"""Typed models for FireDM download-engine adapters."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

_ENGINE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


class EngineCapability(Enum):
    SEGMENTED_HTTP = "segmented_http"
    RESUME = "resume"
    RATE_LIMIT = "rate_limit"
    PROXY = "proxy"
    CUSTOM_HEADERS = "custom_headers"
    COOKIES_EXPLICIT_USER_SUPPLIED = "cookies_explicit_user_supplied"
    CHECKSUM = "checksum"
    BITTORRENT = "bittorrent"
    METALINK = "metalink"
    FTP = "ftp"
    SFTP = "sftp"
    MEDIA_EXTRACTION = "media_extraction"
    POST_PROCESSING = "post_processing"
    SUBTITLES = "subtitles"
    THUMBNAILS = "thumbnails"
    METADATA_EMBEDDING = "metadata_embedding"


class EngineInputType(Enum):
    URL = "url"
    MEDIA_URL = "media_url"
    TORRENT = "torrent"
    MAGNET = "magnet"
    METALINK = "metalink"
    LOCAL_FILE = "local_file"


class EngineHealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class DownloadState(Enum):
    PENDING = "pending"
    PREFLIGHTED = "preflighted"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def validate_engine_id(engine_id: str) -> None:
    if not isinstance(engine_id, str) or not _ENGINE_ID_RE.match(engine_id):
        raise ValueError(f"Invalid engine id: {engine_id!r}")


@dataclass(frozen=True)
class Header:
    name: str
    value: str

    def __post_init__(self) -> None:
        if not self.name or any(ch in self.name for ch in "\r\n:"):
            raise ValueError("Header name must be non-empty and must not contain CR, LF, or colon")
        if any(ch in self.value for ch in "\r\n"):
            raise ValueError("Header value must not contain CR or LF")


@dataclass(frozen=True)
class EngineHealth:
    status: EngineHealthStatus
    message: str = ""
    details: Mapping[str, str] = field(default_factory=dict)

    @property
    def usable(self) -> bool:
        return self.status in {EngineHealthStatus.HEALTHY, EngineHealthStatus.DEGRADED}

    @classmethod
    def healthy(cls, message: str = "ok", **details: str) -> EngineHealth:
        return cls(EngineHealthStatus.HEALTHY, message, details)

    @classmethod
    def degraded(cls, message: str, **details: str) -> EngineHealth:
        return cls(EngineHealthStatus.DEGRADED, message, details)

    @classmethod
    def unavailable(cls, message: str, **details: str) -> EngineHealth:
        return cls(EngineHealthStatus.UNAVAILABLE, message, details)


@dataclass(frozen=True)
class DownloadRequest:
    source: str
    input_type: EngineInputType = EngineInputType.URL
    output_dir: Path | None = None
    filename: str | None = None
    headers: tuple[Header, ...] = ()
    cookie_file: Path | None = None
    engine_id: str | None = None
    options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("DownloadRequest.source must be non-empty")
        if self.filename and any(part in self.filename for part in ("/", "\\", "\0")):
            raise ValueError("DownloadRequest.filename must be a file name, not a path")
        if self.engine_id is not None:
            validate_engine_id(self.engine_id)


@dataclass(frozen=True)
class DownloadJob:
    job_id: str
    request: DownloadRequest
    engine_id: str

    def __post_init__(self) -> None:
        if not self.job_id:
            raise ValueError("DownloadJob.job_id must be non-empty")
        validate_engine_id(self.engine_id)


@dataclass(frozen=True)
class DownloadFailure:
    code: str
    message: str
    recoverable: bool = False
    detail: str = ""

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("DownloadFailure.code must be non-empty")
        if not self.message:
            raise ValueError("DownloadFailure.message must be non-empty")


@dataclass(frozen=True)
class PreflightResult:
    allowed: bool
    health: EngineHealth
    failure: DownloadFailure | None = None

    def __post_init__(self) -> None:
        if self.allowed and self.failure is not None:
            raise ValueError("Allowed preflight cannot include a failure")
        if not self.allowed and self.failure is None:
            raise ValueError("Rejected preflight must include a failure")


@dataclass(frozen=True)
class DownloadProgress:
    job_id: str
    state: DownloadState
    bytes_downloaded: int = 0
    bytes_total: int | None = None
    speed_bps: float | None = None
    eta_seconds: float | None = None
    message: str = ""

    def __post_init__(self) -> None:
        if not self.job_id:
            raise ValueError("DownloadProgress.job_id must be non-empty")
        if self.bytes_downloaded < 0:
            raise ValueError("bytes_downloaded must be >= 0")
        if self.bytes_total is not None and self.bytes_total < 0:
            raise ValueError("bytes_total must be >= 0")
        if self.bytes_total is not None and self.bytes_downloaded > self.bytes_total:
            raise ValueError("bytes_downloaded cannot exceed bytes_total")
        if self.speed_bps is not None and self.speed_bps < 0:
            raise ValueError("speed_bps must be >= 0")
        if self.eta_seconds is not None and self.eta_seconds < 0:
            raise ValueError("eta_seconds must be >= 0")


@dataclass(frozen=True)
class DownloadResult:
    job_id: str
    state: DownloadState
    output_path: Path | None = None
    failure: DownloadFailure | None = None

    @property
    def success(self) -> bool:
        return self.state == DownloadState.COMPLETED and self.failure is None

    def __post_init__(self) -> None:
        if not self.job_id:
            raise ValueError("DownloadResult.job_id must be non-empty")
        if self.state == DownloadState.FAILED and self.failure is None:
            raise ValueError("Failed DownloadResult must include failure details")
        if self.state != DownloadState.FAILED and self.failure is not None:
            raise ValueError("Only failed DownloadResult may include failure details")


@dataclass(frozen=True)
class EngineDescriptor:
    id: str
    display_name: str
    supported_schemes: tuple[str, ...]
    supported_input_types: tuple[EngineInputType, ...]
    capabilities: tuple[EngineCapability, ...]
    health: EngineHealth

    def __post_init__(self) -> None:
        validate_engine_id(self.id)
