"""Toolkit-neutral frontend view models for staged UI migration.

These dataclasses intentionally avoid Tkinter, PySide6, and controller imports.
They give the current Tk UI and a future Qt UI a shared display contract while
runtime ownership stays with the existing controller/brain/worker path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from firedm.download_engines.models import (
    EngineCapability,
    EngineDescriptor,
    EngineHealth,
    EngineHealthStatus,
    validate_engine_id,
)

AUTO_ENGINE_ID = "auto"


class FailureSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


class QueueItemState(Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UpdateStatus(Enum):
    IDLE = "idle"
    CHECKING = "checking"
    CURRENT = "current"
    AVAILABLE = "available"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass(frozen=True)
class EngineOptionViewModel:
    engine_id: str
    display_name: str
    available: bool
    status: EngineHealthStatus
    capabilities: tuple[EngineCapability, ...] = ()
    status_message: str = ""
    is_auto: bool = False

    def __post_init__(self) -> None:
        if self.engine_id != AUTO_ENGINE_ID:
            validate_engine_id(self.engine_id)
        if not self.display_name:
            raise ValueError("EngineOptionViewModel.display_name must be non-empty")

    @classmethod
    def auto(cls) -> EngineOptionViewModel:
        return cls(
            engine_id=AUTO_ENGINE_ID,
            display_name="Auto",
            available=True,
            status=EngineHealthStatus.HEALTHY,
            is_auto=True,
        )

    @classmethod
    def from_descriptor(cls, descriptor: EngineDescriptor) -> EngineOptionViewModel:
        return cls(
            engine_id=descriptor.id,
            display_name=descriptor.display_name,
            available=descriptor.health.usable,
            status=descriptor.health.status,
            capabilities=tuple(descriptor.capabilities),
            status_message=descriptor.health.message,
        )


@dataclass(frozen=True)
class EngineSelectorViewModel:
    options: tuple[EngineOptionViewModel, ...] = field(default_factory=tuple)
    selected_engine_id: str = AUTO_ENGINE_ID

    def __post_init__(self) -> None:
        ids = [option.engine_id for option in self.options]
        if len(ids) != len(set(ids)):
            raise ValueError("EngineSelectorViewModel options must have unique ids")
        if self.selected_engine_id not in ids:
            raise ValueError("selected_engine_id must match an available option")

    @property
    def selected(self) -> EngineOptionViewModel:
        return next(option for option in self.options if option.engine_id == self.selected_engine_id)

    @property
    def selectable_options(self) -> tuple[EngineOptionViewModel, ...]:
        return tuple(option for option in self.options if option.available)

    @classmethod
    def from_descriptors(
        cls,
        descriptors: tuple[EngineDescriptor, ...],
        *,
        selected_engine_id: str = AUTO_ENGINE_ID,
        include_auto: bool = True,
    ) -> EngineSelectorViewModel:
        options = tuple(EngineOptionViewModel.from_descriptor(item) for item in descriptors)
        if include_auto:
            options = (EngineOptionViewModel.auto(), *options)
        return cls(options=options, selected_engine_id=selected_engine_id)


@dataclass(frozen=True)
class QueueItemViewModel:
    uid: str
    name: str
    status: QueueItemState
    progress_percent: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int | None = None
    speed_bps: float | None = None
    eta_seconds: float | None = None
    engine_id: str | None = None
    resumable: bool = False
    segment_count: int = 0

    def __post_init__(self) -> None:
        if not self.uid:
            raise ValueError("QueueItemViewModel.uid must be non-empty")
        if not self.name:
            raise ValueError("QueueItemViewModel.name must be non-empty")
        if not 0 <= self.progress_percent <= 100:
            raise ValueError("progress_percent must be between 0 and 100")
        if self.downloaded_bytes < 0:
            raise ValueError("downloaded_bytes must be >= 0")
        if self.total_bytes is not None and self.total_bytes < 0:
            raise ValueError("total_bytes must be >= 0")
        if self.total_bytes is not None and self.downloaded_bytes > self.total_bytes:
            raise ValueError("downloaded_bytes cannot exceed total_bytes")
        if self.speed_bps is not None and self.speed_bps < 0:
            raise ValueError("speed_bps must be >= 0")
        if self.eta_seconds is not None and self.eta_seconds < 0:
            raise ValueError("eta_seconds must be >= 0")
        if self.engine_id is not None:
            validate_engine_id(self.engine_id)
        if self.segment_count < 0:
            raise ValueError("segment_count must be >= 0")

    @property
    def active(self) -> bool:
        return self.status in {QueueItemState.RUNNING, QueueItemState.PROCESSING}

    @property
    def terminal(self) -> bool:
        return self.status in {
            QueueItemState.COMPLETED,
            QueueItemState.FAILED,
            QueueItemState.CANCELLED,
        }


@dataclass(frozen=True)
class FailureViewModel:
    code: str
    title: str
    message: str
    severity: FailureSeverity = FailureSeverity.ERROR
    recoverable: bool = False
    detail_lines: tuple[str, ...] = ()
    action_label: str | None = None

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("FailureViewModel.code must be non-empty")
        if not self.title:
            raise ValueError("FailureViewModel.title must be non-empty")
        if not self.message:
            raise ValueError("FailureViewModel.message must be non-empty")
        if any("\r" in line or "\n" in line for line in self.detail_lines):
            raise ValueError("detail_lines must be single-line strings")
        if self.action_label is not None and not self.action_label:
            raise ValueError("action_label must be non-empty when provided")


@dataclass(frozen=True)
class HealthItemViewModel:
    item_id: str
    label: str
    status: EngineHealthStatus
    message: str = ""
    detail_lines: tuple[str, ...] = ()
    action_label: str | None = None

    def __post_init__(self) -> None:
        validate_engine_id(self.item_id)
        if not self.label:
            raise ValueError("HealthItemViewModel.label must be non-empty")
        if any("\r" in line or "\n" in line for line in self.detail_lines):
            raise ValueError("detail_lines must be single-line strings")
        if self.action_label is not None and not self.action_label:
            raise ValueError("action_label must be non-empty when provided")

    @property
    def usable(self) -> bool:
        return self.status in {EngineHealthStatus.HEALTHY, EngineHealthStatus.DEGRADED}

    @classmethod
    def from_engine_health(cls, item_id: str, label: str, health: EngineHealth) -> HealthItemViewModel:
        return cls(
            item_id=item_id,
            label=label,
            status=health.status,
            message=health.message,
            detail_lines=tuple(f"{key}: {value}" for key, value in sorted(health.details.items())),
        )


@dataclass(frozen=True)
class UpdateStatusViewModel:
    status: UpdateStatus
    current_version: str
    latest_version: str | None = None
    message: str = ""
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.current_version:
            raise ValueError("UpdateStatusViewModel.current_version must be non-empty")
        if self.status == UpdateStatus.AVAILABLE and not self.latest_version:
            raise ValueError("latest_version is required when an update is available")
        if self.status == UpdateStatus.FAILED and not self.error:
            raise ValueError("error is required when update status failed")
        if self.error is not None and any(ch in self.error for ch in "\r\n"):
            raise ValueError("error must be a single-line string")
