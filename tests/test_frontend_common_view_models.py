from __future__ import annotations

import ast
from pathlib import Path

import pytest

import firedm.frontend_common.view_models as view_models
from firedm.download_engines import EngineCapability, EngineDescriptor, EngineHealth, EngineInputType
from firedm.frontend_common import (
    AUTO_ENGINE_ID,
    ConnectorWarningViewModel,
    DiagnosticsActionViewModel,
    DownloadFormViewModel,
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


def _descriptor(engine_id: str, health: EngineHealth) -> EngineDescriptor:
    return EngineDescriptor(
        id=engine_id,
        display_name=f"Engine {engine_id}",
        supported_schemes=("http", "https"),
        supported_input_types=(EngineInputType.URL,),
        capabilities=(EngineCapability.RESUME,),
        health=health,
    )


def test_engine_selector_builds_auto_and_engine_options():
    selector = EngineSelectorViewModel.from_descriptors(
        (
            _descriptor("internal", EngineHealth.healthy("ready")),
            _descriptor("aria2c", EngineHealth.unavailable("missing")),
        )
    )

    assert selector.selected.engine_id == AUTO_ENGINE_ID
    assert [option.engine_id for option in selector.options] == ["auto", "internal", "aria2c"]
    assert [option.engine_id for option in selector.selectable_options] == ["auto", "internal"]


def test_engine_selector_rejects_unknown_selected_engine():
    with pytest.raises(ValueError, match="selected_engine_id"):
        EngineSelectorViewModel.from_descriptors((), selected_engine_id="internal")


def test_engine_selector_rejects_duplicate_engine_ids():
    descriptor = _descriptor("internal", EngineHealth.healthy())

    with pytest.raises(ValueError, match="unique ids"):
        EngineSelectorViewModel.from_descriptors((descriptor, descriptor))


def test_queue_item_validates_progress_bytes_and_engine_id():
    item = QueueItemViewModel(
        uid="uid-1",
        name="file.bin",
        status=QueueItemState.RUNNING,
        progress_percent=25.0,
        downloaded_bytes=25,
        total_bytes=100,
        engine_id="internal",
        resumable=True,
        segment_count=4,
    )

    assert item.active is True
    assert item.terminal is False

    with pytest.raises(ValueError, match="between 0 and 100"):
        QueueItemViewModel(uid="uid-2", name="file.bin", status=QueueItemState.PENDING, progress_percent=101)
    with pytest.raises(ValueError, match="cannot exceed"):
        QueueItemViewModel(
            uid="uid-3",
            name="file.bin",
            status=QueueItemState.PENDING,
            downloaded_bytes=2,
            total_bytes=1,
        )
    with pytest.raises(ValueError, match="Invalid engine id"):
        QueueItemViewModel(uid="uid-4", name="file.bin", status=QueueItemState.PENDING, engine_id="Bad Engine")


def test_queue_item_terminal_states_are_explicit():
    item = QueueItemViewModel(uid="uid-1", name="file.bin", status=QueueItemState.COMPLETED, progress_percent=100)

    assert item.terminal is True
    assert item.active is False


def test_failure_view_model_validates_display_shape():
    failure = FailureViewModel(
        code="ENGINE_NOT_CONNECTED",
        title="Engine unavailable",
        message="The selected engine is not connected.",
        severity=FailureSeverity.WARNING,
        recoverable=True,
        detail_lines=("internal: unavailable",),
        action_label="Retry",
    )

    assert failure.recoverable is True

    with pytest.raises(ValueError, match="single-line"):
        FailureViewModel(code="x", title="Bad", message="bad", detail_lines=("line\nbreak",))


def test_health_item_can_be_built_from_engine_health():
    health = EngineHealth.degraded("usable with warning", version="1.0")

    item = HealthItemViewModel.from_engine_health("internal", "Internal HTTP", health)

    assert item.usable is True
    assert item.message == "usable with warning"
    assert item.detail_lines == ("version: 1.0",)


def test_update_status_requires_available_version_and_failure_error():
    ok = UpdateStatusViewModel(UpdateStatus.CURRENT, current_version="2022.2.5", message="current")

    assert ok.latest_version is None

    with pytest.raises(ValueError, match="latest_version"):
        UpdateStatusViewModel(UpdateStatus.AVAILABLE, current_version="2022.2.5")
    with pytest.raises(ValueError, match="error"):
        UpdateStatusViewModel(UpdateStatus.FAILED, current_version="2022.2.5")
    with pytest.raises(ValueError, match="single-line"):
        UpdateStatusViewModel(UpdateStatus.FAILED, current_version="2022.2.5", error="bad\nline")


def test_download_form_validation_reports_expected_errors_and_preserves_options():
    form = DownloadFormViewModel(
        url="ftp://example.test/file.bin",
        destination_folder="",
        selected_engine_id="aria2c",
        available_engine_ids=(AUTO_ENGINE_ID, "internal-http"),
        advanced_options={"download_later": True, "max_connections": 4},
    )

    validation = form.validate()

    assert validation.valid is False
    assert [error.code for error in validation.errors] == [
        "unsupported_scheme",
        "destination_missing",
        "engine_unavailable",
    ]
    assert form.advanced_options["download_later"] is True


def test_download_form_validation_accepts_http_destination_and_auto_warning():
    form = DownloadFormViewModel(url="https://example.test/file.bin", destination_folder="C:/Downloads")

    validation = form.validate()

    assert validation.valid is True
    assert [warning.code for warning in validation.warnings] == ["auto_only"]


def test_queue_stats_counts_states_speed_and_unknown_eta():
    items = (
        QueueItemViewModel(
            uid="active",
            name="active.bin",
            status=QueueItemState.RUNNING,
            speed_bps=100,
            eta_seconds=10,
        ),
        QueueItemViewModel(uid="paused", name="paused.bin", status=QueueItemState.PAUSED),
        QueueItemViewModel(uid="failed", name="failed.bin", status=QueueItemState.FAILED),
        QueueItemViewModel(uid="done", name="done.bin", status=QueueItemState.COMPLETED),
        QueueItemViewModel(uid="pending", name="pending.bin", status=QueueItemState.PENDING),
    )

    stats = QueueStatsViewModel.from_items(items)

    assert stats.total_count == 5
    assert stats.active_count == 1
    assert stats.paused_count == 1
    assert stats.failed_count == 1
    assert stats.completed_count == 1
    assert stats.pending_count == 1
    assert stats.total_speed_bps == 100
    assert stats.eta_seconds == 10
    assert QueueStatsViewModel.from_items(()).eta_seconds is None


def test_new_support_models_validate_shape():
    warning = ConnectorWarningViewModel(code="warn", message="Check setting")
    settings = SettingsSummaryViewModel(download_folder="C:/Downloads", plugin_count=2, enabled_plugin_count=1)
    diagnostic = DiagnosticsActionViewModel(action_id="inspect-ffmpeg", label="Inspect FFmpeg")
    topic = HelpTopicViewModel(topic_id="built-in-help", title="Built In Help", source_path="docs/user/BUILT_IN_HELP.md")

    assert warning.severity == FailureSeverity.WARNING
    assert settings.enabled_plugin_count == 1
    assert diagnostic.safe_to_run is True
    assert topic.source_path.endswith("BUILT_IN_HELP.md")


def test_frontend_common_view_models_do_not_import_gui_toolkits():
    source = Path(view_models.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    forbidden_toolkits = {"tkinter"}
    assert imported_roots.isdisjoint(forbidden_toolkits)
    assert view_models.__file__ is not None
