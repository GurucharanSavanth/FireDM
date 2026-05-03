from __future__ import annotations

import ast
from pathlib import Path

import pytest

import firedm.frontend_common.view_models as view_models
from firedm.download_engines import EngineCapability, EngineDescriptor, EngineHealth, EngineInputType
from firedm.frontend_common import (
    AUTO_ENGINE_ID,
    EngineSelectorViewModel,
    FailureSeverity,
    FailureViewModel,
    HealthItemViewModel,
    QueueItemState,
    QueueItemViewModel,
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


def test_frontend_common_view_models_do_not_import_gui_toolkits():
    source = Path(view_models.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert "tkinter" not in imported_roots
    assert "PySide6" not in imported_roots
    assert "PyQt6" not in imported_roots
    assert view_models.__file__ is not None
