import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from firedm import config
from firedm.plugins.drm_decryption import DRMDecryptionPlugin
from firedm.plugins.registry import PluginRegistry


@pytest.fixture
def temp_config():
    old_folder = config.sett_folder
    config.sett_folder = tempfile.mkdtemp()
    yield
    config.sett_folder = old_folder


def _reset_registry():
    PluginRegistry._plugins.clear()
    PluginRegistry._plugin_classes.clear()
    for hook_dict in PluginRegistry._hooks.values():
        hook_dict.clear()


def test_drm_decryption_plugin_fails_closed(temp_config):
    _reset_registry()
    PluginRegistry.register(DRMDecryptionPlugin)

    assert PluginRegistry.load("drm_decryption") is False
    assert PluginRegistry.is_enabled("drm_decryption") is False
    assert PluginRegistry._plugins["drm_decryption"].loaded is False


def test_drm_placeholder_has_no_decryption_api(temp_config):
    plugin = DRMDecryptionPlugin()

    assert not hasattr(plugin, "_fetch_clearkey")
    assert not hasattr(plugin, "_decrypt_dash_segment")
