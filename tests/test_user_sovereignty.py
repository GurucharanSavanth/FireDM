"""Tests that no feature is hard-disabled without a user-override path.

Covers USER_SOVEREIGNTY_POLICY.md Articles 1, 2, 3, 4, 6, and the §8 carve-out.
"""

from __future__ import annotations

import pytest

from firedm import config
from firedm.plugins.policy import (
    PERMANENTLY_BLOCKED,
    USER_OVERRIDABLE_BLOCKED,
    BLOCKED_PLUGIN_REASONS,
    blocked_plugin_reason,
    is_blocked_plugin,
    is_permanently_blocked,
)


# ---------------------------------------------------------------------------
# Article 3 — Persistence: required keys exist in settings_keys
# ---------------------------------------------------------------------------

class TestSettingsKeysPersistence:
    def test_advanced_features_master_gate_persisted(self):
        assert 'advanced_features_enabled' in config.settings_keys

    def test_keep_temp_persisted(self):
        assert 'keep_temp' in config.settings_keys

    def test_test_mode_persisted(self):
        assert 'test_mode' in config.settings_keys

    def test_allow_user_extractors_persisted(self):
        assert 'allow_user_extractors' in config.settings_keys

    def test_allow_user_plugins_persisted(self):
        assert 'allow_user_plugins' in config.settings_keys

    def test_engine_bridge_diagnostics_persisted(self):
        assert 'engine_bridge_diagnostics_enabled' in config.settings_keys

    def test_all_user_overridable_plugins_have_toggle_key(self):
        """Every USER_OVERRIDABLE_BLOCKED plugin must have a config toggle key."""
        for plugin_id in USER_OVERRIDABLE_BLOCKED:
            toggle_key = f'enable_plugin_{plugin_id}'
            assert toggle_key in config.settings_keys, (
                f"Missing toggle key '{toggle_key}' for plugin '{plugin_id}'. "
                "Add it to config.settings_keys (Article 3)."
            )


# ---------------------------------------------------------------------------
# Article 8 — DRM permanent carve-out
# ---------------------------------------------------------------------------

class TestPermanentCarveOut:
    def test_drm_decryption_is_permanently_blocked(self):
        assert 'drm_decryption' in PERMANENTLY_BLOCKED

    def test_drm_decryption_not_in_user_overridable(self):
        assert 'drm_decryption' not in USER_OVERRIDABLE_BLOCKED

    def test_drm_decryption_has_no_toggle_key_in_settings(self):
        assert 'enable_plugin_drm_decryption' not in config.settings_keys

    def test_drm_decryption_cannot_be_unblocked_by_user_toggle(self, monkeypatch):
        monkeypatch.setattr(config, 'advanced_features_enabled', True)
        monkeypatch.setattr(config, 'enable_plugin_drm_decryption', True, raising=False)
        # must still be blocked regardless of any toggle
        assert is_permanently_blocked('drm_decryption')
        assert is_blocked_plugin('drm_decryption')
        assert blocked_plugin_reason('drm_decryption') != ''

    def test_is_permanently_blocked_helper(self):
        assert is_permanently_blocked('drm_decryption')
        for plugin_id in USER_OVERRIDABLE_BLOCKED:
            assert not is_permanently_blocked(plugin_id)


# ---------------------------------------------------------------------------
# Article 2 — User-overridable blocks respect the master gate + per-plugin key
# ---------------------------------------------------------------------------

class TestUserOverridableBlocks:
    def test_overridable_plugins_blocked_by_default(self, monkeypatch):
        monkeypatch.setattr(config, 'advanced_features_enabled', False)
        for plugin_id in USER_OVERRIDABLE_BLOCKED:
            assert is_blocked_plugin(plugin_id), (
                f"Plugin '{plugin_id}' should be blocked when master gate is OFF."
            )

    def test_overridable_plugin_stays_blocked_without_master_gate(self, monkeypatch):
        """Per-plugin toggle alone is not enough — master gate must also be ON."""
        monkeypatch.setattr(config, 'advanced_features_enabled', False)
        for plugin_id in USER_OVERRIDABLE_BLOCKED:
            monkeypatch.setattr(config, f'enable_plugin_{plugin_id}', True, raising=False)
            assert is_blocked_plugin(plugin_id), (
                f"Plugin '{plugin_id}' must stay blocked without the master gate."
            )

    def test_overridable_plugin_unblocked_with_both_gates(self, monkeypatch):
        """Master gate ON + per-plugin toggle ON = plugin is unblocked."""
        monkeypatch.setattr(config, 'advanced_features_enabled', True)
        for plugin_id in USER_OVERRIDABLE_BLOCKED:
            monkeypatch.setattr(config, f'enable_plugin_{plugin_id}', True, raising=False)
            assert not is_blocked_plugin(plugin_id), (
                f"Plugin '{plugin_id}' should be unblocked when both gates are ON."
            )

    def test_overridable_plugin_stays_blocked_without_per_plugin_key(self, monkeypatch):
        """Master gate ON but per-plugin toggle OFF = still blocked."""
        monkeypatch.setattr(config, 'advanced_features_enabled', True)
        for plugin_id in USER_OVERRIDABLE_BLOCKED:
            monkeypatch.setattr(config, f'enable_plugin_{plugin_id}', False, raising=False)
            assert is_blocked_plugin(plugin_id), (
                f"Plugin '{plugin_id}' must stay blocked when per-plugin key is OFF."
            )


# ---------------------------------------------------------------------------
# Sanity — BLOCKED_PLUGIN_REASONS is the union of both tiers
# ---------------------------------------------------------------------------

class TestPolicyStructure:
    def test_blocked_plugin_reasons_is_union(self):
        expected = {**PERMANENTLY_BLOCKED, **USER_OVERRIDABLE_BLOCKED}
        assert BLOCKED_PLUGIN_REASONS == expected

    def test_tiers_are_disjoint(self):
        overlap = set(PERMANENTLY_BLOCKED) & set(USER_OVERRIDABLE_BLOCKED)
        assert not overlap, f"Plugin IDs appear in both tiers: {overlap}"

    def test_config_defaults(self):
        assert config.advanced_features_enabled is False
        for plugin_id in USER_OVERRIDABLE_BLOCKED:
            assert getattr(config, f'enable_plugin_{plugin_id}', False) is False
