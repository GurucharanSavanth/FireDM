"""Pure adapters from legacy controller/backend shapes to frontend view models.

No GUI toolkit, controller, or config module import belongs here. Callers pass
plain objects, mappings, or typed engine models and receive immutable view
models that can be consumed by the current GUI or a future replacement UI.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from firedm.download_engines.models import DownloadFailure, EngineDescriptor, EngineHealth, EngineHealthStatus

from .view_models import (
    AUTO_ENGINE_ID,
    ConnectorWarningViewModel,
    ControllerStatusViewModel,
    DiagnosticsActionViewModel,
    EngineSelectorViewModel,
    FailureSeverity,
    FailureViewModel,
    HealthItemViewModel,
    HelpTopicViewModel,
    QueueItemState,
    QueueItemViewModel,
    QueueStatsViewModel,
    SettingsSummaryViewModel,
    UpdateStatus,
    UpdateStatusViewModel,
)

_LEGACY_STATUS_MAP: Mapping[str, QueueItemState] = {
    "Pending": QueueItemState.PENDING,
    "Scheduled": QueueItemState.SCHEDULED,
    "Downloading": QueueItemState.RUNNING,
    "Refreshing url": QueueItemState.RUNNING,
    "Paused": QueueItemState.PAUSED,
    "Processing": QueueItemState.PROCESSING,
    "Completed": QueueItemState.COMPLETED,
    "Failed": QueueItemState.FAILED,
    "Cancelled": QueueItemState.CANCELLED,
    "Canceled": QueueItemState.CANCELLED,
}


def _get_attr(source: Any, name: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed


def _safe_optional_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    parsed = _safe_float(value, default=-1.0)
    return parsed if parsed >= 0 else None


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed


def _safe_nonnegative_int(value: Any, default: int = 0) -> int:
    return max(_safe_int(value, default), 0)


def _safe_nonnegative_float(value: Any, default: float = 0.0) -> float:
    return max(_safe_float(value, default), 0.0)


def _safe_text(value: Any, default: str = "") -> str:
    if value in (None, ""):
        return default
    return str(value)


def _status_from_legacy(value: Any) -> QueueItemState:
    if isinstance(value, QueueItemState):
        return value
    if isinstance(value, str):
        return _LEGACY_STATUS_MAP.get(value, QueueItemState.PENDING)
    return QueueItemState.PENDING


def queue_item_from_legacy(item: Any, *, engine_id: str | None = None) -> QueueItemViewModel:
    uid = _safe_text(_get_attr(item, "uid"), default="pending")
    name = _safe_text(_get_attr(item, "name"), default="Unnamed download")
    total_size = _safe_nonnegative_int(_get_attr(item, "total_size", _get_attr(item, "size", 0)))
    total_size_value = total_size if total_size > 0 else None
    downloaded = _safe_nonnegative_int(_get_attr(item, "downloaded", 0))
    if total_size_value is not None:
        downloaded = min(downloaded, total_size_value)
    return QueueItemViewModel(
        uid=uid,
        name=name,
        status=_status_from_legacy(_get_attr(item, "status")),
        progress_percent=min(max(_safe_float(_get_attr(item, "progress", 0.0)), 0.0), 100.0),
        downloaded_bytes=downloaded,
        total_bytes=total_size_value,
        speed_bps=_safe_optional_float(_get_attr(item, "speed")),
        eta_seconds=_safe_optional_float(_get_attr(item, "eta")),
        engine_id=engine_id,
        resumable=bool(_get_attr(item, "resumable", False)),
        segment_count=_safe_nonnegative_int(_get_attr(item, "total_parts", 0)),
    )


def queue_stats_from_legacy(items: Iterable[Any]) -> QueueStatsViewModel:
    return QueueStatsViewModel.from_items(tuple(queue_item_from_legacy(item) for item in items))


def engine_selector_from_descriptors(
    descriptors: Sequence[EngineDescriptor],
    *,
    selected_engine_id: str = AUTO_ENGINE_ID,
    include_auto: bool = True,
) -> EngineSelectorViewModel:
    return EngineSelectorViewModel.from_descriptors(
        tuple(descriptors),
        selected_engine_id=selected_engine_id,
        include_auto=include_auto,
    )


def failure_from_download_failure(failure: DownloadFailure) -> FailureViewModel:
    detail_lines = (failure.detail,) if failure.detail else ()
    severity = FailureSeverity.WARNING if failure.recoverable else FailureSeverity.ERROR
    return FailureViewModel(
        code=failure.code,
        title=failure.code.replace("_", " ").title(),
        message=failure.message,
        severity=severity,
        recoverable=failure.recoverable,
        detail_lines=detail_lines,
        action_label="Retry" if failure.recoverable else None,
    )


def health_item_from_engine_health(item_id: str, label: str, health: EngineHealth) -> HealthItemViewModel:
    return HealthItemViewModel.from_engine_health(item_id, label, health)


def health_items_from_descriptors(descriptors: Sequence[EngineDescriptor]) -> tuple[HealthItemViewModel, ...]:
    return tuple(
        HealthItemViewModel.from_engine_health(descriptor.id, descriptor.display_name, descriptor.health)
        for descriptor in descriptors
    )


def update_status_from_mapping(data: Mapping[str, Any]) -> UpdateStatusViewModel:
    status_value = str(data.get("status", "idle")).lower()
    try:
        status = UpdateStatus(status_value)
    except ValueError:
        status = UpdateStatus.FAILED
    current = _safe_text(data.get("current_version"), default="unknown")
    latest = data.get("latest_version")
    error = data.get("error")
    if status == UpdateStatus.AVAILABLE and not latest:
        status = UpdateStatus.FAILED
        error = "missing latest version"
    if status == UpdateStatus.FAILED and not error:
        error = "update status failed"
    return UpdateStatusViewModel(
        status=status,
        current_version=current,
        latest_version=_safe_text(latest) if latest else None,
        message=_safe_text(data.get("message")),
        error=_safe_text(error) if error else None,
    )


def settings_summary_from_config(config_source: Any) -> SettingsSummaryViewModel:
    plugin_states = _get_attr(config_source, "plugin_states", {}) or {}
    if not isinstance(plugin_states, Mapping):
        plugin_states = {}
    return SettingsSummaryViewModel(
        download_folder=_safe_text(_get_attr(config_source, "download_folder"), default="."),
        temp_folder=_safe_text(_get_attr(config_source, "temp_folder")),
        max_concurrent_downloads=max(_safe_int(_get_attr(config_source, "max_concurrent_downloads", 1)), 1),
        max_connections=max(_safe_int(_get_attr(config_source, "max_connections", 1)), 1),
        speed_limit_bps=_safe_nonnegative_int(_get_attr(config_source, "speed_limit", 0)),
        proxy_enabled=bool(_get_attr(config_source, "enable_proxy", False)),
        proxy_configured=bool(_get_attr(config_source, "proxy", "")),
        clipboard_monitor_enabled=bool(_get_attr(config_source, "monitor_clipboard", False)),
        systray_enabled=bool(_get_attr(config_source, "enable_systray", False)),
        update_checks_enabled=bool(_get_attr(config_source, "check_for_update", False)),
        plugin_count=len(plugin_states),
        enabled_plugin_count=sum(1 for value in plugin_states.values() if bool(value)),
    )


def diagnostics_actions_from_health(
    health_items: Sequence[HealthItemViewModel],
) -> tuple[DiagnosticsActionViewModel, ...]:
    actions: list[DiagnosticsActionViewModel] = []
    for item in health_items:
        actions.append(
            DiagnosticsActionViewModel(
                action_id=f"inspect-{item.item_id}",
                label=f"Inspect {item.label}",
                enabled=item.status != EngineHealthStatus.HEALTHY,
                description=item.message,
                safe_to_run=True,
            )
        )
    return tuple(actions)


def help_topics_from_paths(paths: Sequence[str | Path]) -> tuple[HelpTopicViewModel, ...]:
    topics: list[HelpTopicViewModel] = []
    for path in paths:
        source_path = str(path).replace("\\", "/")
        stem = Path(source_path).stem
        topic_id = stem.lower().replace("_", "-").replace(" ", "-")
        if not topic_id:
            continue
        topics.append(
            HelpTopicViewModel(
                topic_id=topic_id,
                title=stem.replace("_", " ").replace("-", " ").title(),
                source_path=source_path,
            )
        )
    return tuple(topics)


def controller_status_from_parts(
    *,
    queue_items: Iterable[Any],
    engine_descriptors: Sequence[EngineDescriptor],
    update_data: Mapping[str, Any],
    selected_engine_id: str = AUTO_ENGINE_ID,
    warnings: Sequence[ConnectorWarningViewModel] = (),
) -> ControllerStatusViewModel:
    return ControllerStatusViewModel(
        queue=queue_stats_from_legacy(queue_items),
        engine_selector=engine_selector_from_descriptors(
            engine_descriptors,
            selected_engine_id=selected_engine_id,
        ),
        update_status=update_status_from_mapping(update_data),
        warnings=tuple(warnings),
    )
