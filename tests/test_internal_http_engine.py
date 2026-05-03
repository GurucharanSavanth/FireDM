"""Tests for the InternalHTTPDownloadEngine adapter skeleton.

The adapter is intentionally not wired to the legacy `Controller -> brain ->
worker` runtime in this patch. These tests pin that contract so a future
patch cannot silently flip behavior without an explicit test update.
"""

from __future__ import annotations

import importlib
from unittest.mock import patch

import pytest

from firedm.download_engines import (
    DownloadFailure,
    DownloadJob,
    DownloadProgress,
    DownloadRequest,
    DownloadResult,
    DownloadState,
    EngineCapability,
    EngineHealthStatus,
    EngineInputType,
    InternalHTTPDownloadEngine,
)
from firedm.download_engines import internal_http as internal_http_module


def _make_request(
    source: str = "https://example.test/file.bin",
    *,
    input_type: EngineInputType = EngineInputType.URL,
) -> DownloadRequest:
    return DownloadRequest(source=source, input_type=input_type)


def test_engine_id_and_display_name_are_stable():
    engine = InternalHTTPDownloadEngine()

    assert engine.id == "internal-http"
    assert engine.display_name == "FireDM Internal (pycurl)"


def test_engine_capabilities_match_known_legacy_support():
    engine = InternalHTTPDownloadEngine()

    capabilities = set(engine.capabilities)

    # Truthful subset only — features owned by other modules must not be
    # advertised by this engine.
    assert EngineCapability.SEGMENTED_HTTP in capabilities
    assert EngineCapability.RESUME in capabilities
    assert EngineCapability.RATE_LIMIT in capabilities
    assert EngineCapability.PROXY in capabilities
    assert EngineCapability.CUSTOM_HEADERS in capabilities
    assert EngineCapability.COOKIES_EXPLICIT_USER_SUPPLIED in capabilities

    for forbidden in (
        EngineCapability.MEDIA_EXTRACTION,
        EngineCapability.POST_PROCESSING,
        EngineCapability.SUBTITLES,
        EngineCapability.THUMBNAILS,
        EngineCapability.METADATA_EMBEDDING,
        EngineCapability.BITTORRENT,
        EngineCapability.METALINK,
        EngineCapability.FTP,
        EngineCapability.SFTP,
        EngineCapability.CHECKSUM,
    ):
        assert forbidden not in capabilities, forbidden


def test_default_supported_schemes_are_http_only():
    engine = InternalHTTPDownloadEngine()

    assert engine.supported_schemes == ("http", "https")
    assert engine.supported_input_types == (EngineInputType.URL,)


def test_health_check_is_healthy_when_pycurl_importable():
    engine = InternalHTTPDownloadEngine()

    with patch.object(
        internal_http_module, "_pycurl_available", return_value=True
    ):
        health = engine.health_check()

    assert health.status == EngineHealthStatus.HEALTHY
    assert health.usable is True
    assert health.details.get("backend") == "pycurl"


def test_health_check_is_unavailable_when_dependency_missing():
    engine = InternalHTTPDownloadEngine()

    with patch.object(
        internal_http_module, "_pycurl_available", return_value=False
    ):
        health = engine.health_check()

    assert health.status == EngineHealthStatus.UNAVAILABLE
    assert health.usable is False
    assert "pycurl" in health.message.lower()


def test_pycurl_available_returns_true_when_module_findable(monkeypatch):
    # Sanity guard around the find_spec wrapper, in case stdlib ever
    # stops returning a spec object for an importable module.
    real_find_spec = importlib.util.find_spec

    def fake_find_spec(name: str):
        if name == "pycurl":
            return real_find_spec("collections")  # any non-None spec
        return real_find_spec(name)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)

    assert internal_http_module._pycurl_available() is True


def test_pycurl_available_returns_false_when_find_spec_returns_none(monkeypatch):
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: None if name == "pycurl" else None
    )

    assert internal_http_module._pycurl_available() is False


def test_preflight_accepts_supported_https_url():
    engine = InternalHTTPDownloadEngine()

    with patch.object(
        internal_http_module, "_pycurl_available", return_value=True
    ):
        result = engine.preflight(_make_request("https://example.test/x"))

    assert result.allowed is True
    assert result.failure is None
    assert result.health.usable is True


def test_preflight_rejects_unsupported_scheme_with_structured_failure():
    engine = InternalHTTPDownloadEngine()

    with patch.object(
        internal_http_module, "_pycurl_available", return_value=True
    ):
        result = engine.preflight(_make_request("ftp://example.test/file"))

    assert result.allowed is False
    assert isinstance(result.failure, DownloadFailure)
    assert result.failure.code == "UNSUPPORTED_SCHEME"


def test_preflight_rejects_when_dependency_missing():
    engine = InternalHTTPDownloadEngine()

    with patch.object(
        internal_http_module, "_pycurl_available", return_value=False
    ):
        result = engine.preflight(_make_request())

    assert result.allowed is False
    assert isinstance(result.failure, DownloadFailure)
    assert result.failure.code == "ENGINE_UNAVAILABLE"


def test_preflight_rejects_unsupported_input_type():
    engine = InternalHTTPDownloadEngine()

    with patch.object(
        internal_http_module, "_pycurl_available", return_value=True
    ):
        result = engine.preflight(
            DownloadRequest(
                source="https://example.test/x",
                input_type=EngineInputType.MAGNET,
            )
        )

    assert result.allowed is False
    assert isinstance(result.failure, DownloadFailure)
    assert result.failure.code == "UNSUPPORTED_INPUT_TYPE"


def test_start_returns_engine_not_connected_failure():
    engine = InternalHTTPDownloadEngine()
    request = _make_request()
    job = DownloadJob(job_id="job-1", request=request, engine_id=engine.id)

    result = engine.start(job)

    assert isinstance(result, DownloadResult)
    assert result.state == DownloadState.FAILED
    assert result.success is False
    assert result.failure is not None
    assert result.failure.code == "ENGINE_NOT_CONNECTED"
    # Detail must explicitly mark unwired runtime so callers cannot
    # mistake this for a transient failure they should retry.
    assert result.failure.detail == "not_implemented_for_runtime"


def test_pause_resume_cancel_all_return_engine_not_connected():
    engine = InternalHTTPDownloadEngine()

    for method_name in ("pause", "resume", "cancel"):
        result = getattr(engine, method_name)("job-1")
        assert isinstance(result, DownloadResult)
        assert result.state == DownloadState.FAILED, method_name
        assert result.failure is not None
        assert result.failure.code == "ENGINE_NOT_CONNECTED", method_name


def test_get_status_returns_pending_snapshot_for_unwired_engine():
    engine = InternalHTTPDownloadEngine()

    progress = engine.get_status("job-1")

    assert isinstance(progress, DownloadProgress)
    assert progress.state == DownloadState.PENDING
    assert progress.bytes_downloaded == 0
    assert "not connected" in progress.message


def test_shutdown_is_noop_and_returns_none():
    engine = InternalHTTPDownloadEngine()

    # `shutdown()` returns None; we exercise it for the side-effect-free
    # contract and confirm no exception escapes.
    result = engine.shutdown()  # type: ignore[func-returns-value]
    assert result is None


def test_engine_does_not_import_brain_or_worker_at_module_level():
    import sys

    # Reload to make this test independent of import order.
    sys.modules.pop("firedm.download_engines.internal_http", None)
    importlib.import_module("firedm.download_engines.internal_http")

    src = (
        importlib.import_module("firedm.download_engines.internal_http").__file__
    )
    assert src is not None
    with open(src, encoding="utf-8") as handle:
        text = handle.read()

    # Module-level legacy imports would mean importing the engine package
    # implicitly imports the heavy legacy modules. Lazy/method-level imports
    # are still allowed.
    for forbidden in (
        "from firedm.brain",
        "from firedm.worker",
        "from .brain",
        "from .worker",
        "import firedm.brain",
        "import firedm.worker",
    ):
        assert forbidden not in text, forbidden


def test_engine_module_does_not_use_subprocess_or_shell():
    """Parse the module AST and confirm there is no subprocess import,
    no `os.system` call, and no `shell=True` keyword argument.

    Plain substring checks would false-positive on docstrings that *describe*
    the no-subprocess invariant. AST inspection only sees real code.
    """
    import ast
    import sys

    sys.modules.pop("firedm.download_engines.internal_http", None)
    module = importlib.import_module("firedm.download_engines.internal_http")
    src = module.__file__
    assert src is not None
    with open(src, encoding="utf-8") as handle:
        text = handle.read()
    tree = ast.parse(text)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "subprocess", "subprocess import"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "subprocess", "from subprocess import"
        if isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant):
                    assert keyword.value.value is not True, "shell=True"
            # os.system(...) call detection
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "os"
                and func.attr == "system"
            ):
                raise AssertionError("os.system call")


def test_custom_supported_schemes_normalize_lowercase_and_dedup():
    engine = InternalHTTPDownloadEngine(supported_schemes=("HTTPS:", "https", "HTTP"))

    assert engine.supported_schemes == ("https", "http")


def test_engine_satisfies_protocol():
    from firedm.download_engines import DownloadEngine

    engine = InternalHTTPDownloadEngine()

    # runtime_checkable Protocol; structural subtype check.
    assert isinstance(engine, DownloadEngine)


def test_pause_resume_cancel_reject_blank_job_ids():
    engine = InternalHTTPDownloadEngine()

    for method_name in ("pause", "resume", "cancel"):
        with pytest.raises(ValueError):
            getattr(engine, method_name)("")
