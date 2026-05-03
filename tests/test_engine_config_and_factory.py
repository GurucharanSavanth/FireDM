"""Tests for `EngineConfig`, `create_default_registry`, and `select_engine`.

These tests pin shape, validation, secret-leakage, and selection behavior so
later patches (UI binding, persistence, aria2c registration) do not silently
weaken the contract.
"""

from __future__ import annotations

import pytest

from firedm.download_engines import (
    DefaultRegistryResult,
    EngineCapability,
    EngineConfig,
    EngineHealth,
    EngineInputType,
    EngineRegistry,
    InternalHTTPDownloadEngine,
    create_default_registry,
    select_engine,
)
from firedm.download_engines import internal_http as internal_http_module
from firedm.download_engines.config import SCHEMA_VERSION
from firedm.download_engines.factory import _create_registry_for_tests

# ---------------------------------------------------------------------------
# Local fake engine (separate from the one in test_download_engines.py to
# keep test files independently runnable).
# ---------------------------------------------------------------------------


class _FakeEngine:
    def __init__(
        self,
        engine_id: str,
        *,
        schemes: tuple[str, ...] = ("http", "https"),
        input_types: tuple[EngineInputType, ...] = (EngineInputType.URL,),
        health: EngineHealth | None = None,
    ) -> None:
        self._id = engine_id
        self._schemes = schemes
        self._input_types = input_types
        self._health = health or EngineHealth.healthy()

    @property
    def id(self) -> str:
        return self._id

    @property
    def display_name(self) -> str:
        return f"Fake {self._id}"

    @property
    def supported_schemes(self) -> tuple[str, ...]:
        return self._schemes

    @property
    def supported_input_types(self) -> tuple[EngineInputType, ...]:
        return self._input_types

    @property
    def capabilities(self) -> tuple[EngineCapability, ...]:
        return ()

    def health_check(self) -> EngineHealth:
        return self._health

    def preflight(self, request):  # pragma: no cover - selection tests don't invoke
        raise AssertionError("preflight should not be called by selection tests")

    def start(self, job):  # pragma: no cover - selection tests don't invoke
        raise AssertionError("start should not be called by selection tests")

    def pause(self, job_id):  # pragma: no cover
        raise AssertionError("pause should not be called by selection tests")

    def resume(self, job_id):  # pragma: no cover
        raise AssertionError("resume should not be called by selection tests")

    def cancel(self, job_id):  # pragma: no cover
        raise AssertionError("cancel should not be called by selection tests")

    def get_status(self, job_id):  # pragma: no cover
        raise AssertionError("get_status should not be called by selection tests")

    def shutdown(self) -> None:  # pragma: no cover
        return None


# ---------------------------------------------------------------------------
# EngineConfig validation
# ---------------------------------------------------------------------------


def test_default_config_has_safe_defaults():
    cfg = EngineConfig()

    assert cfg.default_engine_id is None
    assert cfg.auto_select_enabled is True
    assert cfg.disabled_engine_ids == ()
    assert dict(cfg.per_scheme_preference) == {}
    assert dict(cfg.per_input_type_preference) == {}
    assert dict(cfg.engine_settings) == {}
    assert cfg.schema_version == SCHEMA_VERSION


def test_default_engine_id_must_be_valid_engine_id():
    with pytest.raises(ValueError, match="Invalid engine id"):
        EngineConfig(default_engine_id="Bad Engine")


def test_disabled_engine_ids_validated_and_dedupped():
    with pytest.raises(ValueError, match="Duplicate engine id"):
        EngineConfig(disabled_engine_ids=("internal-http", "internal-http"))

    with pytest.raises(ValueError, match="Invalid engine id"):
        EngineConfig(disabled_engine_ids=("Bad Engine",))


def test_default_cannot_also_be_disabled():
    with pytest.raises(ValueError, match="also in disabled_engine_ids"):
        EngineConfig(
            default_engine_id="internal-http",
            disabled_engine_ids=("internal-http",),
        )


def test_per_scheme_preference_normalizes_to_lowercase():
    cfg = EngineConfig(per_scheme_preference={"HTTPS:": "internal-http"})

    assert cfg.preferred_for_scheme("https") == "internal-http"
    assert cfg.preferred_for_scheme("HTTPS") == "internal-http"


def test_per_input_type_preference_requires_enum_keys():
    with pytest.raises(ValueError, match="must be EngineInputType"):
        EngineConfig(per_input_type_preference={"url": "internal-http"})  # type: ignore[dict-item]


def test_engine_settings_must_be_mapping():
    with pytest.raises(ValueError, match="must be a mapping"):
        EngineConfig(engine_settings={"internal-http": ["not", "mapping"]})  # type: ignore[dict-item]


def test_engine_settings_namespaced_per_engine():
    cfg = EngineConfig(
        engine_settings={
            "internal-http": {"max_connections": 4},
            "aria2c": {"rpc_secret": "TOKEN"},
        }
    )

    assert cfg.engine_settings_for("internal-http") == {"max_connections": 4}
    assert cfg.engine_settings_for("aria2c") == {"rpc_secret": "TOKEN"}
    # Unknown engine yields an empty mapping, not the wrong namespace.
    assert dict(cfg.engine_settings_for("yt-dlp")) == {}


def test_engine_settings_excluded_from_repr_and_str():
    secret = "secret-rpc-token-DO-NOT-LEAK-12345"
    cfg = EngineConfig(
        default_engine_id="internal-http",
        engine_settings={"aria2c": {"rpc_secret": secret}},
    )

    representation = repr(cfg)
    string_form = str(cfg)

    assert secret not in representation
    assert secret not in string_form
    # Field name itself may be hidden; the engine id should not be either
    # — that is fine because it's the secret VALUE that matters.
    assert "rpc_secret" not in representation
    assert "rpc_secret" not in string_form


def test_schema_version_must_be_positive_int():
    with pytest.raises(ValueError, match="schema_version"):
        EngineConfig(schema_version=0)
    with pytest.raises(ValueError, match="schema_version"):
        EngineConfig(schema_version=-1)


def test_with_overrides_rejects_unknown_field():
    cfg = EngineConfig()

    with pytest.raises(ValueError, match="Unknown EngineConfig fields"):
        cfg.with_overrides(not_a_real_field=True)


def test_with_overrides_returns_new_instance():
    cfg = EngineConfig()

    updated = cfg.with_overrides(default_engine_id="internal-http")

    assert updated is not cfg
    assert cfg.default_engine_id is None
    assert updated.default_engine_id == "internal-http"


# ---------------------------------------------------------------------------
# Serialization round-trip
# ---------------------------------------------------------------------------


def test_to_dict_from_dict_round_trip():
    cfg = EngineConfig(
        default_engine_id="internal-http",
        auto_select_enabled=False,
        disabled_engine_ids=("legacy-engine",),
        per_scheme_preference={"https": "internal-http"},
        per_input_type_preference={EngineInputType.URL: "internal-http"},
        engine_settings={"internal-http": {"max_connections": 8}},
    )

    payload = cfg.to_dict()
    restored = EngineConfig.from_dict(payload)

    assert restored == cfg
    assert payload["per_input_type_preference"] == {"url": "internal-http"}


def test_from_dict_rejects_unknown_input_type():
    with pytest.raises(ValueError, match="Unknown input type"):
        EngineConfig.from_dict(
            {
                "schema_version": 1,
                "per_input_type_preference": {"not-a-type": "internal-http"},
            }
        )


def test_from_dict_rejects_future_schema_version():
    with pytest.raises(ValueError, match="Unsupported EngineConfig schema_version"):
        EngineConfig.from_dict({"schema_version": SCHEMA_VERSION + 1})


def test_from_dict_ignores_unknown_top_level_keys():
    cfg = EngineConfig.from_dict(
        {
            "schema_version": SCHEMA_VERSION,
            "default_engine_id": "internal-http",
            "future_unknown_key": "ignored",
        }
    )

    assert cfg.default_engine_id == "internal-http"


# ---------------------------------------------------------------------------
# Default registry factory
# ---------------------------------------------------------------------------


def test_default_registry_contains_internal_engine():
    result = create_default_registry()

    assert isinstance(result, DefaultRegistryResult)
    assert isinstance(result.registry, EngineRegistry)
    assert "internal-http" in result.registry.ids()


def test_default_registry_does_not_contain_aria2c_or_ytdlp():
    # Hard guard: those adapters are NOT implemented in this patch and must
    # not be registered, even speculatively.
    result = create_default_registry()

    registered = set(result.registry.ids())
    assert "aria2c" not in registered
    assert "yt-dlp" not in registered


def test_disabled_internal_engine_is_not_registered():
    cfg = EngineConfig(disabled_engine_ids=("internal-http",))

    result = create_default_registry(cfg)

    assert "internal-http" not in result.registry.ids()
    assert any("internal-http" in warn for warn in result.warnings)


def test_unknown_default_is_downgraded_with_structured_warning():
    cfg = EngineConfig(default_engine_id="not-registered")

    result = create_default_registry(cfg)

    assert result.effective_default_engine_id is None
    assert any("not registered" in warn for warn in result.warnings)


def test_known_default_is_preserved_as_effective_default():
    cfg = EngineConfig(default_engine_id="internal-http")

    result = create_default_registry(cfg)

    assert result.effective_default_engine_id == "internal-http"
    assert result.warnings == ()


# ---------------------------------------------------------------------------
# select_engine resolution order
# ---------------------------------------------------------------------------


def test_select_engine_uses_per_scheme_preference_first():
    registry = _create_registry_for_tests(
        extra_engines=(_FakeEngine("preferred-scheme", schemes=("https",)),),
    )
    cfg = EngineConfig(
        default_engine_id="internal-http",
        per_scheme_preference={"https": "preferred-scheme"},
    )

    selected = select_engine(
        registry, cfg, scheme="https", input_type=EngineInputType.URL
    )

    assert selected is not None
    assert selected.id == "preferred-scheme"


def test_select_engine_falls_back_through_input_type_then_default():
    registry = _create_registry_for_tests(
        extra_engines=(
            _FakeEngine("media-engine", input_types=(EngineInputType.MEDIA_URL,)),
        ),
    )
    cfg = EngineConfig(
        default_engine_id="internal-http",
        per_input_type_preference={EngineInputType.MEDIA_URL: "media-engine"},
    )

    selected = select_engine(
        registry, cfg, scheme="https", input_type=EngineInputType.MEDIA_URL
    )

    assert selected is not None
    assert selected.id == "media-engine"


def test_select_engine_uses_default_when_no_preferences_match():
    registry = _create_registry_for_tests()
    cfg = EngineConfig(default_engine_id="internal-http")

    # Simulate pycurl present so health is healthy and selection succeeds.
    from unittest.mock import patch

    with patch.object(
        internal_http_module, "_pycurl_available", return_value=True
    ):
        selected = select_engine(
            registry, cfg, scheme="https", input_type=EngineInputType.URL
        )

    assert selected is not None
    assert selected.id == "internal-http"


def test_select_engine_returns_none_when_auto_select_disabled_and_no_match():
    registry = _create_registry_for_tests()
    cfg = EngineConfig(default_engine_id=None, auto_select_enabled=False)

    selected = select_engine(
        registry, cfg, scheme="https", input_type=EngineInputType.URL
    )

    assert selected is None


def test_select_engine_auto_falls_back_when_enabled():
    registry = _create_registry_for_tests()
    cfg = EngineConfig(default_engine_id=None, auto_select_enabled=True)

    from unittest.mock import patch

    with patch.object(
        internal_http_module, "_pycurl_available", return_value=True
    ):
        selected = select_engine(
            registry, cfg, scheme="https", input_type=EngineInputType.URL
        )

    assert selected is not None
    assert selected.id == "internal-http"


def test_select_engine_skips_unhealthy_preferred_engine():
    registry = _create_registry_for_tests(
        extra_engines=(
            _FakeEngine(
                "preferred-broken",
                schemes=("https",),
                health=EngineHealth.unavailable("missing"),
            ),
        ),
    )
    cfg = EngineConfig(
        default_engine_id="internal-http",
        per_scheme_preference={"https": "preferred-broken"},
        auto_select_enabled=True,
    )

    from unittest.mock import patch

    with patch.object(
        internal_http_module, "_pycurl_available", return_value=True
    ):
        selected = select_engine(
            registry, cfg, scheme="https", input_type=EngineInputType.URL
        )

    # Preferred is unhealthy -> skip; default (internal-http) is healthy.
    assert selected is not None
    assert selected.id == "internal-http"


# ---------------------------------------------------------------------------
# Module-level safety guards
# ---------------------------------------------------------------------------


def test_factory_module_does_not_register_unimplemented_engines():
    # Defensive parse of the factory source so a future patch cannot
    # silently add aria2c/yt-dlp registration without updating this test.
    import firedm.download_engines.factory as factory_module

    src = factory_module.__file__
    assert src is not None
    with open(src, encoding="utf-8") as handle:
        text = handle.read()

    assert "Aria2DownloadEngine" not in text
    assert "YtDlpDownloadEngine" not in text
    assert "TorrentDownloadEngine" not in text


def test_engine_modules_have_no_subprocess_imports():
    """AST-level guard against subprocess/os.system/shell=True in the new
    config and factory modules. AST inspection avoids false positives from
    docstrings that describe the invariant in plain English.
    """
    import ast
    import importlib

    for module_name in (
        "firedm.download_engines.config",
        "firedm.download_engines.factory",
    ):
        module = importlib.import_module(module_name)
        src = module.__file__
        assert src is not None
        with open(src, encoding="utf-8") as handle:
            tree = ast.parse(handle.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "subprocess", module_name
            if isinstance(node, ast.ImportFrom):
                assert node.module != "subprocess", module_name
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == "shell" and isinstance(
                        keyword.value, ast.Constant
                    ):
                        assert keyword.value.value is not True, module_name
                func = node.func
                if (
                    isinstance(func, ast.Attribute)
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "os"
                    and func.attr == "system"
                ):
                    raise AssertionError(f"os.system call in {module_name}")


def test_internal_engine_exported_from_package():
    # Import-from-package smoke; catches regressions in __init__.py.
    assert InternalHTTPDownloadEngine is not None
    assert InternalHTTPDownloadEngine.ENGINE_ID == "internal-http"
