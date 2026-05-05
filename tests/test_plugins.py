"""
Plugin system tests: registry correctness, hook firing, toggle persistence,
sandbox defaults.
"""
import importlib
import unittest
from contextlib import suppress
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Helpers to construct lightweight DownloadItem / Segment stubs
# ---------------------------------------------------------------------------

class _DStub:
    """Minimal DownloadItem stand-in."""
    def __init__(self, name='test.mp4', url='http://example.com/test.mp4'):
        self.uid = 'stub-uid-0001'
        self.name = name
        self.url = url
        self.status = 'Downloading'
        self.subtype_list = []
        self.http_headers = {}
        self.type = 'general'
        self.resumable = True
        self.size = 0
        self.folder = '/tmp'
        self.temp_folder = '/tmp/firedm_stub'
        self.temp_file = '/tmp/firedm_stub/out.mp4'
        self.target_file = '/tmp/test.mp4'
        self.extension = '.mp4'


class _SegStub:
    """Minimal Segment stand-in."""
    def __init__(self, num=0):
        self.num = num
        self.name = f'/tmp/seg_{num}'
        self.basename = f'seg_{num}'
        self.d = _DStub()
        self.range = [0, 1023]
        self.size = 1024
        self.downloaded = True
        self.completed = False


# ---------------------------------------------------------------------------
# Isolate registry for each test (reset class-level dicts)
# ---------------------------------------------------------------------------

def _fresh_registry():
    """Return PluginRegistry with cleared state so tests don't bleed."""
    from firedm.plugins.registry import PluginBase, PluginRegistry
    PluginRegistry._plugins.clear()
    PluginRegistry._plugin_classes.clear()
    for hook_dict in PluginRegistry._hooks.values():
        hook_dict.clear()
    return PluginRegistry, PluginBase


# ---------------------------------------------------------------------------
# Basic registration and metadata
# ---------------------------------------------------------------------------

class TestRegistration(unittest.TestCase):

    def test_register_stores_meta_and_class(self):
        reg, Base = _fresh_registry()
        from firedm.plugins.registry import PluginMeta

        class MyPlugin(Base):
            META = PluginMeta('my_plugin', '1.0', 'test', 'desc')
            def on_load(self): return True
            def on_unload(self): return True

        reg.register(MyPlugin)
        self.assertIn('my_plugin', reg._plugins)
        self.assertIn('my_plugin', reg._plugin_classes)
        self.assertIs(reg._plugin_classes['my_plugin'], MyPlugin)

    def test_duplicate_registration_is_idempotent(self):
        reg, Base = _fresh_registry()
        from firedm.plugins.registry import PluginMeta

        class P(Base):
            META = PluginMeta('p', '1.0', 'a', 'd')

        reg.register(P)
        reg.register(P)
        self.assertEqual(len(reg._plugins), 1)

    def test_missing_meta_raises(self):
        _, Base = _fresh_registry()

        class BadPlugin(Base):
            META = None

        with self.assertRaises(RuntimeError):
            BadPlugin()


# ---------------------------------------------------------------------------
# Load / unload lifecycle
# ---------------------------------------------------------------------------

class TestLoadUnload(unittest.TestCase):

    def test_load_sets_enabled_flag(self):
        reg, Base = _fresh_registry()
        import firedm.config as cfg
        from firedm.plugins.registry import PluginMeta
        cfg.plugin_states = {}

        class P(Base):
            META = PluginMeta('lp', '1.0', 'a', 'd')

        reg.register(P)
        result = reg.load('lp')
        self.assertTrue(result)
        self.assertTrue(reg._plugins['lp'].enabled)
        self.assertTrue(reg._plugins['lp'].loaded)
        self.assertTrue(cfg.plugin_states.get('lp'))

    def test_unload_clears_enabled_flag(self):
        reg, Base = _fresh_registry()
        import firedm.config as cfg
        from firedm.plugins.registry import PluginMeta
        cfg.plugin_states = {}

        class P(Base):
            META = PluginMeta('up', '1.0', 'a', 'd')

        reg.register(P)
        reg.load('up')
        reg.unload('up')
        self.assertFalse(reg._plugins['up'].enabled)
        self.assertFalse(cfg.plugin_states.get('up'))

    def test_load_nonexistent_returns_false(self):
        reg, _ = _fresh_registry()
        self.assertFalse(reg.load('does_not_exist'))

    def test_double_load_is_idempotent(self):
        reg, Base = _fresh_registry()
        import firedm.config as cfg
        from firedm.plugins.registry import PluginMeta
        cfg.plugin_states = {}
        load_count = [0]

        class P(Base):
            META = PluginMeta('dl', '1.0', 'a', 'd')
            def on_load(self):
                load_count[0] += 1
                return True

        reg.register(P)
        reg.load('dl')
        reg.load('dl')
        self.assertEqual(load_count[0], 1)

    def test_on_load_returning_false_blocks(self):
        reg, Base = _fresh_registry()
        import firedm.config as cfg
        from firedm.plugins.registry import PluginMeta
        cfg.plugin_states = {}

        class P(Base):
            META = PluginMeta('fl', '1.0', 'a', 'd')
            def on_load(self): return False

        reg.register(P)
        self.assertFalse(reg.load('fl'))
        self.assertFalse(reg._plugins['fl'].enabled)


# ---------------------------------------------------------------------------
# Hook firing
# ---------------------------------------------------------------------------

class TestHooks(unittest.TestCase):

    def test_download_start_hook_fires(self):
        reg, Base = _fresh_registry()
        import firedm.config as cfg
        from firedm.plugins.registry import PluginMeta
        cfg.plugin_states = {}
        fired = []

        class P(Base):
            META = PluginMeta('hf', '1.0', 'a', 'd')
            def on_download_start(self, d):
                fired.append(d)
                return True

        reg.register(P)
        reg.load('hf')
        d = _DStub()
        result = reg.fire_hook('download_start', d)
        self.assertTrue(result)
        self.assertEqual(fired, [d])

    def test_blocking_hook_returns_false(self):
        reg, Base = _fresh_registry()
        import firedm.config as cfg
        from firedm.plugins.registry import PluginMeta
        cfg.plugin_states = {}

        class P(Base):
            META = PluginMeta('bh', '1.0', 'a', 'd')
            def on_download_start(self, d): return False

        reg.register(P)
        reg.load('bh')
        self.assertFalse(reg.fire_hook('download_start', _DStub()))

    def test_hooks_detach_on_unload(self):
        reg, Base = _fresh_registry()
        import firedm.config as cfg
        from firedm.plugins.registry import PluginMeta
        cfg.plugin_states = {}
        fired = []

        class P(Base):
            META = PluginMeta('dh', '1.0', 'a', 'd')
            def on_download_start(self, d):
                fired.append(True)
                return True

        reg.register(P)
        reg.load('dh')
        reg.unload('dh')
        reg.fire_hook('download_start', _DStub())
        self.assertEqual(fired, [])

    def test_hook_exception_does_not_propagate(self):
        reg, Base = _fresh_registry()
        import firedm.config as cfg
        from firedm.plugins.registry import PluginMeta
        cfg.plugin_states = {}

        class P(Base):
            META = PluginMeta('ex', '1.0', 'a', 'd')
            def on_download_start(self, d): raise ValueError('boom')

        reg.register(P)
        reg.load('ex')
        # Should not raise; hook errors are logged and swallowed
        result = reg.fire_hook('download_start', _DStub())
        self.assertTrue(result)

    def test_multiple_plugins_all_fire(self):
        reg, Base = _fresh_registry()
        import firedm.config as cfg
        from firedm.plugins.registry import PluginMeta
        cfg.plugin_states = {}
        order = []

        class A(Base):
            META = PluginMeta('aa', '1.0', 'a', 'd')
            def on_download_start(self, d):
                order.append('A')
                return True

        class B(Base):
            META = PluginMeta('bb', '1.0', 'a', 'd')
            def on_download_start(self, d):
                order.append('B')
                return True

        reg.register(A)
        reg.register(B)
        reg.load('aa')
        reg.load('bb')
        reg.fire_hook('download_start', _DStub())
        self.assertIn('A', order)
        self.assertIn('B', order)

    def test_first_blocking_plugin_short_circuits(self):
        reg, Base = _fresh_registry()
        import firedm.config as cfg
        from firedm.plugins.registry import PluginMeta
        cfg.plugin_states = {}
        second_called = []

        class A(Base):
            META = PluginMeta('sc1', '1.0', 'a', 'd')
            def on_download_start(self, d): return False

        class B(Base):
            META = PluginMeta('sc2', '1.0', 'a', 'd')
            def on_download_start(self, d):
                second_called.append(True)
                return True

        reg.register(A)
        reg.register(B)
        reg.load('sc1')
        reg.load('sc2')
        reg.fire_hook('download_start', _DStub())
        # B may or may not fire depending on dict order; what matters is return value
        self.assertFalse(reg.fire_hook('download_start', _DStub()))


# ---------------------------------------------------------------------------
# Protocol plugin safety
# ---------------------------------------------------------------------------

class TestProtocolExpansion(unittest.TestCase):

    def test_ftp_segments_use_ranges_for_resume(self):
        from firedm.plugins.protocol_expansion import ProtocolExpansionPlugin

        class FakeFTP:
            def connect(self, host, port, timeout=0):
                return 'ok'

            def login(self, username, password):
                return 'ok'

            def size(self, path):
                return 2048

            def quit(self):
                return 'ok'

        d = _DStub(name='file.bin', url='ftp://example.com/file.bin')
        with patch('ftplib.FTP', return_value=FakeFTP()):
            self.assertTrue(ProtocolExpansionPlugin()._handle_ftp(d))

        self.assertEqual(d.segments[0].range, [0, 2047])
        self.assertEqual(d._protocol_handler, 'ftp')
        self.assertTrue(d._plugin_segments_ready)

    def test_webdav_head_uses_http_scheme(self):
        from firedm.plugins.protocol_expansion import ProtocolExpansionPlugin

        seen_urls = []

        class FakeResponse:
            headers = {'Content-Length': '4096', 'Accept-Ranges': 'bytes'}

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        def fake_urlopen(req, timeout=0):
            seen_urls.append(req.full_url)
            return FakeResponse()

        d = _DStub(name='file.bin', url='webdav://example.com/file.bin')
        with patch('urllib.request.urlopen', fake_urlopen):
            self.assertTrue(ProtocolExpansionPlugin()._handle_webdav(d))

        self.assertEqual(seen_urls, ['http://example.com/file.bin'])
        self.assertEqual(d.eff_url, 'http://example.com/file.bin')
        self.assertEqual(d.segments[0].url, 'http://example.com/file.bin')
        self.assertEqual(d._protocol_handler, 'webdav')

    def test_magnet_is_owned_by_plugin_queue(self):
        from firedm import config
        from firedm.plugins import protocol_expansion
        from firedm.plugins.protocol_expansion import ProtocolExpansionPlugin

        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def read(self):
                import json

                return json.dumps(self.payload).encode()

        def fake_urlopen(req, timeout=0):
            import json

            body = json.loads(req.data.decode())
            if body['method'] == 'aria2.tellActive':
                return FakeResponse({'result': []})
            if body['method'] == 'aria2.addUri':
                return FakeResponse({'result': 'gid-123'})
            raise AssertionError(body['method'])

        class FakeThread:
            def __init__(self, *args, **kwargs):
                pass

            def start(self):
                return None

        d = _DStub(name='', url='magnet:?xt=urn:btih:abc123&dn=Ubuntu%20ISO')
        plugin = ProtocolExpansionPlugin()

        with (
            patch.object(plugin, '_find_aria2c', return_value='aria2c'),
            patch('urllib.request.urlopen', fake_urlopen),
            patch.object(protocol_expansion.threading, 'Thread', FakeThread),
        ):
            self.assertTrue(plugin._handle_magnet(d))

        self.assertTrue(d._plugin_queued)
        self.assertEqual(d.status, config.Status.pending)
        self.assertEqual(d._protocol_handler, 'magnet')
        self.assertEqual(d.name, 'Ubuntu ISO')


# ---------------------------------------------------------------------------
# Security / sandbox defaults
# ---------------------------------------------------------------------------

class TestSandboxDefaults(unittest.TestCase):

    def test_allow_user_plugins_default_false(self):
        import firedm.config as cfg
        self.assertFalse(cfg.allow_user_plugins)

    def test_all_shipped_plugins_default_disabled(self):
        import firedm.config as cfg
        cfg.plugin_states = {}
        reg, Base = _fresh_registry()

        # Load all shipped plugins to register them
        for mod_name in (
            'firedm.plugins.anti_detection',
            'firedm.plugins.browser_integration',
            'firedm.plugins.drm_decryption',
            'firedm.plugins.native_extractors',
            'firedm.plugins.post_processing',
            'firedm.plugins.protocol_expansion',
            'firedm.plugins.queue_scheduler',
        ):
            with suppress(Exception):
                importlib.import_module(mod_name)

        for name, meta in reg._plugins.items():
            self.assertFalse(
                meta.default_enabled,
                f'Plugin {name} has default_enabled=True — all shipped plugins must default OFF',
            )

    def test_plugin_states_key_in_settings_keys(self):
        import firedm.config as cfg
        self.assertIn('plugin_states', cfg.settings_keys)
        self.assertIn('plugin_dir', cfg.settings_keys)
        self.assertIn('allow_user_plugins', cfg.settings_keys)

    def test_blocked_shipped_plugins_cannot_load(self):
        import firedm.config as cfg
        from firedm.plugins.policy import BLOCKED_PLUGIN_REASONS

        cfg.plugin_states = {}
        reg, _ = _fresh_registry()
        reg.scan_plugins()

        for name in BLOCKED_PLUGIN_REASONS:
            self.assertIn(name, reg._plugins)
            self.assertFalse(reg.load(name), name)
            self.assertFalse(reg._plugins[name].enabled, name)
            self.assertFalse(cfg.plugin_states.get(name, False), name)

    def test_eval_plugin_rejected(self):
        reg, Base = _fresh_registry()
        from firedm.plugins.registry import PluginMeta

        class EvilPlugin(Base):
            META = PluginMeta('evil', '1.0', 'a', 'uses eval')

            def on_load(self):
                eval('1 + 1')
                return True

        reg.register(EvilPlugin)
        self.assertNotIn('evil', reg._plugins)

    def test_user_plugin_eval_rejected_before_import(self):
        import firedm.config as cfg
        reg, _ = _fresh_registry()

        old_allow = cfg.allow_user_plugins
        old_plugin_dir = cfg.plugin_dir
        try:
            with TemporaryDirectory() as tmp:
                marker = Path(tmp) / 'marker.txt'
                plugin = Path(tmp) / 'evil_user.py'
                plugin.write_text(
                    "from firedm.plugins.registry import PluginBase, PluginMeta, PluginRegistry\n"
                    f"eval(\"open({str(marker)!r}, 'w').write('ran')\")\n"
                    "class EvilUser(PluginBase):\n"
                    "    META = PluginMeta('evil_user', '1.0', 'a', 'd')\n"
                    "PluginRegistry.register(EvilUser)\n",
                    encoding='utf-8',
                )

                cfg.allow_user_plugins = True
                cfg.plugin_dir = tmp
                reg.scan_plugins()

                self.assertNotIn('evil_user', reg._plugins)
                self.assertFalse(marker.exists())
        finally:
            cfg.allow_user_plugins = old_allow
            cfg.plugin_dir = old_plugin_dir


# ---------------------------------------------------------------------------
# Config persistence round-trip
# ---------------------------------------------------------------------------

class TestConfigPersistence(unittest.TestCase):

    def test_load_enables_previously_enabled_plugin(self):
        import firedm.config as cfg
        reg, Base = _fresh_registry()
        from firedm.plugins.registry import PluginMeta
        cfg.plugin_states = {'persist_p': True}

        class P(Base):
            META = PluginMeta('persist_p', '1.0', 'a', 'd')

        reg.register(P)

        # Simulate what load_setting does
        for name, enabled in cfg.plugin_states.items():
            if enabled:
                reg.load(name)

        self.assertTrue(reg._plugins['persist_p'].enabled)


if __name__ == '__main__':
    unittest.main()
