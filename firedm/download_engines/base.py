"""Protocol for future FireDM download engines."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import (
    DownloadJob,
    DownloadProgress,
    DownloadRequest,
    DownloadResult,
    EngineCapability,
    EngineHealth,
    EngineInputType,
    PreflightResult,
)


@runtime_checkable
class DownloadEngine(Protocol):
    """Runtime contract implemented by every download backend.

    The first migration step only defines this interface. Existing pycurl
    download behavior still runs through the legacy controller/brain/worker
    flow until adapters are introduced and tested.
    """

    @property
    def id(self) -> str:
        """Stable machine id, for example `internal` or `aria2c`."""

    @property
    def display_name(self) -> str:
        """Human-readable UI label."""

    @property
    def supported_schemes(self) -> tuple[str, ...]:
        """URL schemes accepted by this engine, lowercase and without colon."""

    @property
    def supported_input_types(self) -> tuple[EngineInputType, ...]:
        """Kinds of user input this engine can preflight/start."""

    @property
    def capabilities(self) -> tuple[EngineCapability, ...]:
        """Feature flags exposed to UI/settings/doctor surfaces."""

    def health_check(self) -> EngineHealth:
        """Return current availability without starting a download."""

    def preflight(self, request: DownloadRequest) -> PreflightResult:
        """Validate request shape and local engine readiness."""

    def start(self, job: DownloadJob) -> DownloadResult:
        """Start a job and return initial result state."""

    def pause(self, job_id: str) -> DownloadResult:
        """Pause a running job when supported."""

    def resume(self, job_id: str) -> DownloadResult:
        """Resume a paused job when supported."""

    def cancel(self, job_id: str) -> DownloadResult:
        """Cancel a running job."""

    def get_status(self, job_id: str) -> DownloadProgress:
        """Return current progress snapshot."""

    def shutdown(self) -> None:
        """Release engine resources."""
