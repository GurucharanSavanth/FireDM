"""Toolkit-neutral frontend view models for staged UI migration.

These dataclasses intentionally avoid GUI toolkit and controller imports. They
give the current GUI and a future replacement UI a shared display contract
while runtime ownership stays with the existing controller/brain/worker path.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from urllib.parse import urlsplit

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
class QueueStatsViewModel:
    total_count: int = 0
    active_count: int = 0
    paused_count: int = 0
    failed_count: int = 0
    completed_count: int = 0
    scheduled_count: int = 0
    pending_count: int = 0
    total_speed_bps: float = 0.0
    eta_seconds: float | None = None

    def __post_init__(self) -> None:
        counters = (
            self.total_count,
            self.active_count,
            self.paused_count,
            self.failed_count,
            self.completed_count,
            self.scheduled_count,
            self.pending_count,
        )
        if any(value < 0 for value in counters):
            raise ValueError("QueueStatsViewModel counts must be >= 0")
        if self.total_speed_bps < 0:
            raise ValueError("total_speed_bps must be >= 0")
        if self.eta_seconds is not None and self.eta_seconds < 0:
            raise ValueError("eta_seconds must be >= 0")

    @classmethod
    def from_items(cls, items: tuple[QueueItemViewModel, ...]) -> QueueStatsViewModel:
        active_states = {QueueItemState.RUNNING, QueueItemState.PROCESSING}
        paused_states = {QueueItemState.PAUSED, QueueItemState.CANCELLED}
        eta_values = tuple(item.eta_seconds for item in items if item.eta_seconds is not None and item.active)
        return cls(
            total_count=len(items),
            active_count=sum(1 for item in items if item.status in active_states),
            paused_count=sum(1 for item in items if item.status in paused_states),
            failed_count=sum(1 for item in items if item.status == QueueItemState.FAILED),
            completed_count=sum(1 for item in items if item.status == QueueItemState.COMPLETED),
            scheduled_count=sum(1 for item in items if item.status == QueueItemState.SCHEDULED),
            pending_count=sum(1 for item in items if item.status == QueueItemState.PENDING),
            total_speed_bps=sum(item.speed_bps or 0 for item in items if item.active),
            eta_seconds=max(eta_values) if eta_values else None,
        )


@dataclass(frozen=True)
class ControllerStatusViewModel:
    queue: QueueStatsViewModel
    engine_selector: EngineSelectorViewModel
    update_status: UpdateStatusViewModel
    warnings: tuple[ConnectorWarningViewModel, ...] = ()


@dataclass(frozen=True)
class SettingsSummaryViewModel:
    download_folder: str
    temp_folder: str = ""
    max_concurrent_downloads: int = 1
    max_connections: int = 1
    speed_limit_bps: int = 0
    proxy_enabled: bool = False
    proxy_configured: bool = False
    clipboard_monitor_enabled: bool = False
    systray_enabled: bool = False
    update_checks_enabled: bool = False
    plugin_count: int = 0
    enabled_plugin_count: int = 0

    def __post_init__(self) -> None:
        if not self.download_folder:
            raise ValueError("SettingsSummaryViewModel.download_folder must be non-empty")
        if self.max_concurrent_downloads < 1:
            raise ValueError("max_concurrent_downloads must be >= 1")
        if self.max_connections < 1:
            raise ValueError("max_connections must be >= 1")
        if self.speed_limit_bps < 0:
            raise ValueError("speed_limit_bps must be >= 0")
        if self.plugin_count < 0 or self.enabled_plugin_count < 0:
            raise ValueError("plugin counts must be >= 0")
        if self.enabled_plugin_count > self.plugin_count:
            raise ValueError("enabled_plugin_count cannot exceed plugin_count")


@dataclass(frozen=True)
class DiagnosticsActionViewModel:
    action_id: str
    label: str
    enabled: bool = True
    description: str = ""
    safe_to_run: bool = True
    output_path: str | None = None

    def __post_init__(self) -> None:
        validate_engine_id(self.action_id)
        if not self.label:
            raise ValueError("DiagnosticsActionViewModel.label must be non-empty")
        if self.output_path is not None and not self.output_path:
            raise ValueError("output_path must be non-empty when provided")


@dataclass(frozen=True)
class HelpTopicViewModel:
    topic_id: str
    title: str
    source_path: str
    summary: str = ""
    anchor: str | None = None

    def __post_init__(self) -> None:
        validate_engine_id(self.topic_id)
        if not self.title:
            raise ValueError("HelpTopicViewModel.title must be non-empty")
        if not self.source_path:
            raise ValueError("HelpTopicViewModel.source_path must be non-empty")
        if self.anchor is not None and not self.anchor:
            raise ValueError("anchor must be non-empty when provided")


@dataclass(frozen=True)
class ConnectorWarningViewModel:
    code: str
    message: str
    severity: FailureSeverity = FailureSeverity.WARNING
    field: str | None = None
    action_label: str | None = None

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("ConnectorWarningViewModel.code must be non-empty")
        if not self.message:
            raise ValueError("ConnectorWarningViewModel.message must be non-empty")
        if "\r" in self.message or "\n" in self.message:
            raise ValueError("ConnectorWarningViewModel.message must be a single-line string")
        if self.field is not None and not self.field:
            raise ValueError("field must be non-empty when provided")
        if self.action_label is not None and not self.action_label:
            raise ValueError("action_label must be non-empty when provided")


@dataclass(frozen=True)
class DownloadFormValidation:
    valid: bool
    errors: tuple[ConnectorWarningViewModel, ...] = ()
    warnings: tuple[ConnectorWarningViewModel, ...] = ()

    def __post_init__(self) -> None:
        if self.valid and self.errors:
            raise ValueError("valid DownloadFormValidation cannot include errors")
        if not self.valid and not self.errors:
            raise ValueError("invalid DownloadFormValidation must include errors")


@dataclass(frozen=True)
class DownloadFormViewModel:
    url: str = ""
    destination_folder: str = ""
    filename: str = ""
    selected_engine_id: str = AUTO_ENGINE_ID
    available_engine_ids: tuple[str, ...] = (AUTO_ENGINE_ID,)
    supported_schemes: tuple[str, ...] = ("http", "https")
    advanced_options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.selected_engine_id != AUTO_ENGINE_ID:
            validate_engine_id(self.selected_engine_id)
        if not self.available_engine_ids:
            raise ValueError("available_engine_ids must be non-empty")
        for engine_id in self.available_engine_ids:
            if engine_id != AUTO_ENGINE_ID:
                validate_engine_id(engine_id)
        normalized_schemes = tuple(scheme.lower().rstrip(":") for scheme in self.supported_schemes)
        if not normalized_schemes:
            raise ValueError("supported_schemes must be non-empty")
        if any(not scheme for scheme in normalized_schemes):
            raise ValueError("supported_schemes cannot include empty values")
        object.__setattr__(self, "supported_schemes", normalized_schemes)

    def validate(self) -> DownloadFormValidation:
        errors: list[ConnectorWarningViewModel] = []
        warnings: list[ConnectorWarningViewModel] = []
        url = self.url.strip()
        destination = self.destination_folder.strip()

        if not url:
            errors.append(
                ConnectorWarningViewModel(
                    code="empty_url",
                    message="Download URL is required.",
                    field="url",
                    severity=FailureSeverity.ERROR,
                )
            )
        else:
            scheme = urlsplit(url).scheme.lower().rstrip(":")
            if scheme not in self.supported_schemes:
                errors.append(
                    ConnectorWarningViewModel(
                        code="unsupported_scheme",
                        message=f"URL scheme {scheme or 'empty'} is not supported.",
                        field="url",
                        severity=FailureSeverity.ERROR,
                    )
                )

        if not destination:
            errors.append(
                ConnectorWarningViewModel(
                    code="destination_missing",
                    message="Destination folder is required.",
                    field="destination_folder",
                    severity=FailureSeverity.ERROR,
                )
            )

        if self.selected_engine_id not in self.available_engine_ids:
            errors.append(
                ConnectorWarningViewModel(
                    code="engine_unavailable",
                    message="Selected engine is not available.",
                    field="selected_engine_id",
                    severity=FailureSeverity.ERROR,
                )
            )
        elif self.selected_engine_id == AUTO_ENGINE_ID and len(self.available_engine_ids) == 1:
            warnings.append(
                ConnectorWarningViewModel(
                    code="auto_only",
                    message="Only automatic engine selection is available.",
                    field="selected_engine_id",
                )
            )

        return DownloadFormValidation(
            valid=not errors,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )


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
