# 04 Class And Inheritance Review

Evidence labels: observed = local file/command output; changed = modified by this pass; inferred = local-code reasoning.

## Controller
- observed class: `firedm/controller.py::Controller`
- base classes: none
- constructor: `__init__(self, view_class, custom_settings={})`
- state owned: download map, queues, view, playlist state, plugin registry access, native endpoint state
- changed: added `_native_endpoint_ready`, `_native_listener`, `_native_control_thread`, `_native_control_stop`
- changed: endpoint lifecycle now starts only when `browser_integration` is enabled and stops during `quit`
- tests: `tests/test_browser_integration.py::test_controller_native_endpoint_disabled_by_default`, full pytest
- deferred risk: `custom_settings={}` mutable default remains legacy; not changed because broad constructor behavior is outside this patch group.

## BrowserIntegrationPlugin
- observed class: `firedm/plugins/browser_integration.py::BrowserIntegrationPlugin`
- base class: `PluginBase`
- constructor: inherited only
- changed: manifest path now resolves to installed executable or generated launcher, not raw `sys.executable`
- changed: runtime toggle starts/stops controller endpoint only when controller already exists
- tests: manifest path and launcher tests
- deferred risk: real browser extension launch not executed; allowed origins still require a real extension ID.

## DRMDecryptionPlugin
- observed class: `firedm/plugins/drm_decryption.py::DRMDecryptionPlugin`
- base class: `PluginBase`
- changed: active decryptor replaced by fail-closed unsupported placeholder
- behavior: `on_load()` returns `False`; no ClearKey/AES APIs exist
- tests: `tests/test_drm_clearkey.py`

## ProtocolExpansionPlugin
- observed class: `firedm/plugins/protocol_expansion.py::ProtocolExpansionPlugin`
- base class: `PluginBase`
- constructor: builds protocol handler map
- changed: magnet handler marks item `_plugin_queued`, sets pending status, assigns display name, notifies controller after aria2 completion/error
- tests: `tests/test_plugins.py::TestProtocolExpansion::test_magnet_is_owned_by_plugin_queue`
- deferred risk: real aria2 magnet transfer not executed.

## Plugin Registry
- observed classes: `PluginMeta`, `PluginBase`, `PluginRegistry`
- inheritance: plugins inherit `PluginBase`; registry holds class-level maps protected by `RLock`
- changed by prior local patch, not structurally changed in this pass
- verified: plugin load/unload/hook tests pass
- deferred risk: user-plugin import still executes trusted plugin files when explicitly enabled; default remains off.

## Download Model Family
- observed classes: `Segment`, `DownloadItem`, `Observable`, `ObservableDownloadItem`, `ObservableVideo`, `Video`, `Stream`
- inheritance: `ObservableDownloadItem(DownloadItem, Observable)`, `ObservableVideo(Video, Observable)`
- changed: no class structure changes in this pass
- observed defect candidate: `video.py::Key.__init__` calls `super().__init__(self)`; deferred because no active regression in current test gate and HLS key refactor needs focused coverage.
