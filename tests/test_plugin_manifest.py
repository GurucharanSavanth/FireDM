from __future__ import annotations

import pytest

from firedm.plugins.manifest import (
    PLUGIN_STATUS_AVAILABLE,
    PLUGIN_STATUS_BLOCKED,
    PLUGIN_STATUS_DISABLED,
    PluginManifestEntry,
    PluginManifestSection,
    discover_plugin_manifest,
    entry_from_meta,
    render_text_summary,
)
from firedm.plugins.policy import BLOCKED_PLUGIN_REASONS
from firedm.plugins.registry import PluginBase, PluginMeta, PluginRegistry


@pytest.fixture(autouse=True)
def _reset_plugin_registry():
    PluginRegistry._plugins.clear()
    PluginRegistry._plugin_classes.clear()
    for hook in PluginRegistry._hooks.values():
        hook.clear()
    yield
    PluginRegistry._plugins.clear()
    PluginRegistry._plugin_classes.clear()
    for hook in PluginRegistry._hooks.values():
        hook.clear()


class _SamplePlugin(PluginBase):
    META = PluginMeta(
        name="sample",
        version="0.1.0",
        author="tests",
        description="sample plugin for manifest tests",
    )


def test_entry_validates_status_and_blocked_reason():
    PluginManifestEntry(plugin_id="x", display_name="X", version="1", status=PLUGIN_STATUS_DISABLED)

    with pytest.raises(ValueError, match="invalid plugin status"):
        PluginManifestEntry(plugin_id="x", display_name="X", version="1", status="bogus")
    with pytest.raises(ValueError, match="blocked plugin requires blocked_reason"):
        PluginManifestEntry(plugin_id="x", display_name="X", version="1", status=PLUGIN_STATUS_BLOCKED)


def test_entry_from_meta_classifies_disabled_by_default():
    PluginRegistry.register(_SamplePlugin)
    meta = PluginRegistry.get_plugin_list()[0]

    entry = entry_from_meta(meta)

    assert entry.plugin_id == "sample"
    assert entry.status == PLUGIN_STATUS_DISABLED
    assert entry.enabled is False
    assert entry.loaded is False


def test_discover_returns_section_with_blocked_overrides():
    PluginRegistry.register(_SamplePlugin)

    section = discover_plugin_manifest(scan=False, blocked_overrides=(("sample", "needs review"),))

    assert isinstance(section, PluginManifestSection)
    assert section.included == ()
    assert len(section.blocked) == 1
    assert section.blocked[0].status == PLUGIN_STATUS_BLOCKED
    assert section.blocked[0].blocked_reason == "needs review"


def test_discover_lists_loaded_plugin_as_available():
    PluginRegistry.register(_SamplePlugin)
    assert PluginRegistry.load("sample") is True

    section = discover_plugin_manifest(scan=False)

    assert len(section.included) == 1
    assert section.included[0].status == PLUGIN_STATUS_AVAILABLE
    assert section.included[0].loaded is True


def test_to_serializable_yields_release_manifest_shape():
    PluginRegistry.register(_SamplePlugin)
    section = discover_plugin_manifest(
        scan=False,
        blocked_overrides=(("sample", "blocked for tests"),),
    )

    data = section.to_serializable()

    assert set(data.keys()) == {"included", "blocked", "planned", "discovery_warnings"}
    assert data["blocked"][0]["plugin_id"] == "sample"
    assert data["blocked"][0]["blocked_reason"] == "blocked for tests"
    assert data["blocked"][0]["dependencies"] == []


def test_render_text_summary_contains_counts_or_empty_marker():
    empty = render_text_summary(PluginManifestSection())
    assert "no plugins discovered" in empty

    PluginRegistry.register(_SamplePlugin)
    summary = render_text_summary(discover_plugin_manifest(scan=False))
    assert "included sample" in summary


def test_real_scan_finds_builtin_plugins_without_enabling_them():
    section = discover_plugin_manifest()

    plugin_ids = {entry.plugin_id for entry in section.all_entries}
    expected_subset = {
        "anti_detection",
        "browser_integration",
        "drm_decryption",
        "native_extractors",
        "post_processing",
        "protocol_expansion",
        "queue_scheduler",
    }
    assert expected_subset.issubset(plugin_ids), plugin_ids
    blocked_ids = {entry.plugin_id for entry in section.blocked}
    assert set(BLOCKED_PLUGIN_REASONS).issubset(blocked_ids)
    for entry in section.included:
        assert entry.enabled is False


def test_blocked_policy_plugins_have_release_reasons():
    section = discover_plugin_manifest()

    reasons = {entry.plugin_id: entry.blocked_reason for entry in section.blocked}

    for plugin_id, reason in BLOCKED_PLUGIN_REASONS.items():
        assert reasons[plugin_id] == reason
