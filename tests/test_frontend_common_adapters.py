from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

import firedm.frontend_common.adapters as adapters
from firedm.download_engines import EngineDescriptor, EngineHealth, EngineInputType
from firedm.download_engines.models import DownloadFailure, EngineCapability, EngineHealthStatus
from firedm.frontend_common import QueueItemState, UpdateStatus


@dataclass
class LegacyItem:
    uid: str = "uid-1"
    name: str = "file.bin"
    status: str = "Downloading"
    progress: float = 25.0
    downloaded: int = 25
    total_size: int = 100
    speed: float = 50.0
    eta: int = 2
    resumable: bool = True
    total_parts: int = 4


def _descriptor(engine_id: str, health: EngineHealth) -> EngineDescriptor:
    return EngineDescriptor(
        id=engine_id,
        display_name=f"Engine {engine_id}",
        supported_schemes=("http", "https"),
        supported_input_types=(EngineInputType.URL,),
        capabilities=(EngineCapability.RESUME,),
        health=health,
    )


def test_legacy_download_item_maps_to_queue_item_without_mutation():
    item = LegacyItem()
    before = item.__dict__.copy()

    vm = adapters.queue_item_from_legacy(item, engine_id="internal-http")

    assert vm.uid == "uid-1"
    assert vm.name == "file.bin"
    assert vm.status == QueueItemState.RUNNING
    assert vm.progress_percent == 25.0
    assert vm.downloaded_bytes == 25
    assert vm.total_bytes == 100
    assert vm.speed_bps == 50.0
    assert vm.eta_seconds == 2
    assert vm.engine_id == "internal-http"
    assert vm.resumable is True
    assert vm.segment_count == 4
    assert item.__dict__ == before


def test_queue_stats_adapter_counts_legacy_states():
    stats = adapters.queue_stats_from_legacy(
        (
            LegacyItem(uid="a", status="Downloading", speed=100),
            LegacyItem(uid="b", status="Paused", speed=200),
            LegacyItem(uid="c", status="Failed"),
            LegacyItem(uid="d", status="Completed"),
            LegacyItem(uid="e", status="Scheduled"),
        )
    )

    assert stats.active_count == 1
    assert stats.paused_count == 1
    assert stats.failed_count == 1
    assert stats.completed_count == 1
    assert stats.scheduled_count == 1
    assert stats.total_speed_bps == 100


def test_engine_descriptors_map_to_selector_and_health_items():
    descriptors = (
        _descriptor("internal-http", EngineHealth.healthy("ready", version="1.0")),
        _descriptor("aria2c", EngineHealth.unavailable("missing")),
    )

    selector = adapters.engine_selector_from_descriptors(descriptors)
    health = adapters.health_items_from_descriptors(descriptors)

    assert [option.engine_id for option in selector.options] == ["auto", "internal-http", "aria2c"]
    assert [item.item_id for item in health] == ["internal-http", "aria2c"]
    assert health[0].status == EngineHealthStatus.HEALTHY
    assert health[1].usable is False


def test_failure_maps_to_user_safe_text():
    failure = DownloadFailure(
        code="ENGINE_UNAVAILABLE",
        message="Selected engine is unavailable.",
        recoverable=True,
        detail="dependency missing",
    )

    vm = adapters.failure_from_download_failure(failure)

    assert vm.code == "ENGINE_UNAVAILABLE"
    assert vm.title == "Engine Unavailable"
    assert vm.message == "Selected engine is unavailable."
    assert vm.recoverable is True
    assert vm.action_label == "Retry"
    assert vm.detail_lines == ("dependency missing",)


def test_update_mapping_controls_button_dialog_state():
    available = adapters.update_status_from_mapping(
        {"status": "available", "current_version": "2022.2.5", "latest_version": "2026.5.3"}
    )
    failed = adapters.update_status_from_mapping({"status": "available", "current_version": "2022.2.5"})

    assert available.status == UpdateStatus.AVAILABLE
    assert available.latest_version == "2026.5.3"
    assert failed.status == UpdateStatus.FAILED
    assert failed.error == "missing latest version"


def test_settings_diagnostics_help_and_controller_status_adapters():
    settings = adapters.settings_summary_from_config(
        {
            "download_folder": "C:/Downloads",
            "temp_folder": "C:/Temp",
            "max_concurrent_downloads": 3,
            "max_connections": 10,
            "speed_limit": 1024,
            "enable_proxy": True,
            "proxy": "configured",
            "plugin_states": {"browser": False, "scheduler": True},
        }
    )
    health = adapters.health_items_from_descriptors(
        (_descriptor("internal-http", EngineHealth.unavailable("pycurl missing")),)
    )
    actions = adapters.diagnostics_actions_from_health(health)
    topics = adapters.help_topics_from_paths(("docs/user/BUILT_IN_HELP.md", "docs/user/ENGINE_SELECTION.md"))
    status = adapters.controller_status_from_parts(
        queue_items=(LegacyItem(),),
        engine_descriptors=(_descriptor("internal-http", EngineHealth.healthy()),),
        update_data={"status": "current", "current_version": "2022.2.5"},
    )

    assert settings.proxy_enabled is True
    assert settings.proxy_configured is True
    assert settings.plugin_count == 2
    assert settings.enabled_plugin_count == 1
    assert actions[0].action_id == "inspect-internal-http"
    assert actions[0].enabled is True
    assert [topic.topic_id for topic in topics] == ["built-in-help", "engine-selection"]
    assert status.queue.active_count == 1
    assert status.update_status.status == UpdateStatus.CURRENT


def test_frontend_common_adapters_do_not_import_gui_toolkits_or_controller():
    source = Path(adapters.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_roots.add(alias.name.split(".", 1)[0])
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
            imported_modules.add(node.module)

    forbidden_roots = {"tkin" + "ter", "Py" + "Side6", "Py" + "Q" + "t6"}
    assert imported_roots.isdisjoint(forbidden_roots)
    assert "firedm.controller" not in imported_modules
    assert "firedm.config" not in imported_modules
