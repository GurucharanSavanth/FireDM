import hashlib
import hmac
import json
import os
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from firedm import config
from firedm.plugins.browser_integration import BrowserIntegrationPlugin
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


def test_manifest_no_wildcards(temp_config):
    _reset_registry()
    PluginRegistry.register(BrowserIntegrationPlugin)
    with patch.object(BrowserIntegrationPlugin, '_register_windows_manifest', return_value=None):
        PluginRegistry.load('browser_integration')

    manifest_path = os.path.join(config.sett_folder, 'firedm_native.json')
    assert os.path.isfile(manifest_path)

    with open(manifest_path) as f:
        manifest = json.load(f)

    assert manifest['path'] != sys.executable
    assert os.path.isfile(manifest['path'])
    for origin in manifest.get('allowed_origins', []):
        assert '*' not in origin, f"Wildcard found in origin: {origin}"

    PluginRegistry.unload('browser_integration')


def test_manifest_launcher_runs_native_host_script(temp_config):
    _reset_registry()
    PluginRegistry.register(BrowserIntegrationPlugin)
    with patch.object(BrowserIntegrationPlugin, '_register_windows_manifest', return_value=None):
        assert PluginRegistry.load('browser_integration') is True

    manifest_path = os.path.join(config.sett_folder, 'firedm_native.json')
    with open(manifest_path, encoding='utf-8') as f:
        manifest = json.load(f)

    launcher = os.path.join(config.sett_folder, 'firedm-native-host.cmd')
    if config.operating_system == 'Windows':
        assert os.path.isfile(manifest['path'])
        if os.path.isfile(launcher):
            with open(launcher, encoding='utf-8') as f:
                content = f.read()
            assert 'native_host.py' in content or '--native-host' in content
        else:
            assert os.path.basename(manifest['path']).lower() in {
                'firedm-native-host.exe',
                'firedm-native-host.cmd',
                'firedm-native-host',
                'firedm.exe',
            }

    PluginRegistry.unload('browser_integration')


def test_controller_native_endpoint_disabled_by_default(tmp_path, monkeypatch):
    from firedm import controller

    class NullView:
        def __init__(self, controller):
            self.controller = controller

        def update_view(self, **kwargs):
            pass

        def get_user_response(self, *args, **kwargs):
            return 'Ok'

    monkeypatch.setattr(config, 'plugin_states', {})
    monkeypatch.setattr(config, 'sett_folder', str(tmp_path))

    called = []
    monkeypatch.setattr(controller, 'make_listener', lambda authkey: called.append(authkey))
    monkeypatch.setattr(controller, 'check_ffmpeg', lambda: None)
    monkeypatch.setattr(controller.video, 'load_extractor_engines', lambda: None)
    monkeypatch.setattr(controller.Thread, 'start', lambda self: None)

    ctrl = controller.Controller(view_class=NullView, custom_settings={'ignore_dlist': True})

    assert ctrl._native_listener is None
    assert called == []


def test_native_message_rejects_non_http_and_sensitive_headers():
    from firedm.controller import Controller

    ctrl = Controller.__new__(Controller)
    calls = []
    ctrl.browser_download = lambda **kwargs: calls.append(kwargs)

    assert ctrl._handle_native_message({'action': 'download', 'url': 'file:///tmp/secret'}) is False

    assert ctrl._handle_native_message({
        'action': 'download',
        'url': 'https://example.invalid/file.bin',
        'headers': {
            'User-Agent': 'ua',
            'Authorization': 'Bearer secret',
            'Cookie': 'sid=secret',
            'Bad\nHeader': 'x',
        },
    }) is True

    assert calls[0]['headers'] == {'User-Agent': 'ua'}


def test_origin_verification():
    from firedm.native_host import _verify_origin

    secret = b'test_secret_32_bytes_long_______'
    msg = {
        'origin': 'chrome-extension://abc123/',
        'nonce': 'random_nonce_123',
        'signature': '7d8c9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d'
    }

    assert _verify_origin(msg, secret) is False


def test_origin_verification_accepts_correct_signature():
    from firedm.native_host import _verify_origin

    secret = b'A' * 32
    origin = 'chrome-extension://abc123/'
    nonce = 'n1'
    sig = hmac.new(secret, f'{origin}:{nonce}'.encode(), hashlib.sha256).hexdigest()

    msg = {'origin': origin, 'nonce': nonce, 'signature': sig}
    assert _verify_origin(msg, secret) is True
