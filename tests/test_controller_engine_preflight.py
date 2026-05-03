from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from firedm import config
from firedm.config import Status
from firedm.download_engines import (
    DownloadFailure,
    DownloadJob,
    DownloadProgress,
    DownloadRequest,
    DownloadResult,
    DownloadState,
    EngineHealth,
    EngineInputType,
    EngineRegistry,
    PreflightResult,
)
from firedm.download_engines.runtime_bridge import (
    BridgeOutcome,
    evaluate_engine_for_download_item,
)
from firedm.model import ObservableDownloadItem


class _NullView:
    def __init__(self, controller):
        self.controller = controller
        self.events = []

    def update_view(self, **kwargs):
        self.events.append(kwargs)

    def get_user_response(self, *args, **kwargs):
        return "Ok"


class _ImmediateThread:
    def __init__(self, target=None, args=(), kwargs=None, daemon=None):
        self.target = target
        self.args = args
        self.kwargs = kwargs or {}
        self.daemon = daemon

    def start(self):
        if self.target:
            self.target(*self.args, **self.kwargs)

    def join(self):
        return None


class _RecordingEngine:
    def __init__(
        self,
        *,
        health: EngineHealth | None = None,
        preflight: PreflightResult | None = None,
        schemes: tuple[str, ...] = ("http", "https"),
    ) -> None:
        self._health = health or EngineHealth.healthy("ok")
        self._preflight = preflight
        self._schemes = schemes
        self.requests: list[DownloadRequest] = []
        self.start_calls = 0

    @property
    def id(self) -> str:
        return "internal-http"

    @property
    def display_name(self) -> str:
        return "Recording engine"

    @property
    def supported_schemes(self) -> tuple[str, ...]:
        return self._schemes

    @property
    def supported_input_types(self) -> tuple[EngineInputType, ...]:
        return (EngineInputType.URL,)

    @property
    def capabilities(self):
        return ()

    def health_check(self) -> EngineHealth:
        return self._health

    def preflight(self, request: DownloadRequest) -> PreflightResult:
        self.requests.append(request)
        return self._preflight or PreflightResult(allowed=True, health=self._health)

    def start(self, job: DownloadJob) -> DownloadResult:
        self.start_calls += 1
        raise AssertionError("controller advisory bridge must not call start()")

    def pause(self, job_id: str) -> DownloadResult:
        return DownloadResult(job_id, DownloadState.PAUSED)

    def resume(self, job_id: str) -> DownloadResult:
        return DownloadResult(job_id, DownloadState.RUNNING)

    def cancel(self, job_id: str) -> DownloadResult:
        return DownloadResult(job_id, DownloadState.CANCELLED)

    def get_status(self, job_id: str) -> DownloadProgress:
        return DownloadProgress(job_id, DownloadState.PENDING)

    def shutdown(self) -> None:
        return None


def _download_item(tmp_path, *, url: str = "https://example.test/file.bin") -> ObservableDownloadItem:
    d = ObservableDownloadItem()
    d.folder = str(tmp_path)
    d.name = "file.bin"
    d.url = url
    d.eff_url = url
    d.type = "general"
    d.status = Status.pending
    d.resumable = True
    d.size = 2048
    d.total_size = 2048
    d.segments = [
        SimpleNamespace(range=(0, 1023)),
        SimpleNamespace(range=(1024, 2047)),
    ]
    d.total_parts = 2
    d.http_headers = {"User-Agent": "FireDM", "X-Test": "ok"}
    d.calculate_uid()
    return d


def _controller():
    from firedm import controller

    with (
        patch.object(controller, "check_ffmpeg", return_value=True),
        patch("firedm.video.load_extractor_engines"),
        patch.object(controller.Thread, "start"),
    ):
        return controller.Controller(
            view_class=_NullView,
            custom_settings={"ignore_dlist": True},
        )


def _run_download_once(ctrl, d, *, bridge_side_effect, monkeypatch):
    from firedm import controller

    monkeypatch.setattr(config, "refresh_url_retries", 0)
    with (
        patch("firedm.controller.evaluate_engine_for_download_item", side_effect=bridge_side_effect),
        patch("firedm.controller.Thread", _ImmediateThread),
        patch("firedm.controller.brain") as brain_mock,
        patch.object(ctrl, "report_d"),
        patch.object(ctrl, "_post_download"),
    ):
        ctrl._download(d, threaded=False)

    return controller, brain_mock


def test_runtime_bridge_builds_request_without_mutating_item_and_preserves_parity_fields(tmp_path, monkeypatch):
    d = _download_item(tmp_path)
    before = (
        d.url,
        d.eff_url,
        d.name,
        d.folder,
        d.resumable,
        len(d.segments),
        dict(d.http_headers),
    )
    engine = _RecordingEngine()
    monkeypatch.setattr(config, "enable_proxy", True)
    monkeypatch.setattr(config, "proxy", "http://user:secret@example.test:8080")

    outcome = evaluate_engine_for_download_item(
        d,
        registry=EngineRegistry((engine,)),
        enabled=True,
    )

    assert outcome.applied is True
    assert outcome.preflight is not None
    assert outcome.preflight.allowed is True
    assert outcome.request is engine.requests[0]
    request = outcome.request
    assert request is not None
    assert request.source == d.eff_url
    assert request.filename == d.name
    assert request.output_dir == Path(d.folder)
    assert [(header.name, header.value) for header in request.headers] == [
        ("User-Agent", "FireDM"),
        ("X-Test", "ok"),
    ]
    assert request.options["resumable"] is True
    assert request.options["segment_count"] == 2
    assert request.options["total_parts"] == 2
    assert request.options["proxy_enabled"] is True
    assert request.options["proxy_configured"] is True
    assert "proxy" not in request.options
    assert engine.start_calls == 0
    assert before == (
        d.url,
        d.eff_url,
        d.name,
        d.folder,
        d.resumable,
        len(d.segments),
        dict(d.http_headers),
    )


@pytest.mark.parametrize("scheme", ["ftp", "sftp"])
def test_runtime_bridge_ftp_and_sftp_remain_legacy_without_preflight(tmp_path, scheme):
    d = _download_item(tmp_path, url=f"{scheme}://example.test/file.bin")
    engine = _RecordingEngine()

    outcome = evaluate_engine_for_download_item(
        d,
        registry=EngineRegistry((engine,)),
        enabled=True,
    )

    assert outcome.applied is False
    assert outcome.skip_reason == f"unsupported_scheme:{scheme}"
    assert engine.requests == []
    assert engine.start_calls == 0


def test_runtime_bridge_engine_health_unavailable_falls_back_before_preflight(tmp_path):
    d = _download_item(tmp_path)
    engine = _RecordingEngine(health=EngineHealth.unavailable("missing"))

    outcome = evaluate_engine_for_download_item(
        d,
        registry=EngineRegistry((engine,)),
        enabled=True,
    )

    assert outcome.applied is False
    assert outcome.skip_reason == "no_engine"
    assert outcome.request is not None
    assert engine.requests == []
    assert engine.start_calls == 0


def test_runtime_bridge_fatal_preflight_is_advisory_and_does_not_start(tmp_path):
    d = _download_item(tmp_path)
    failure = DownloadFailure(
        code="ENGINE_UNAVAILABLE",
        message="dependency missing",
        recoverable=False,
    )
    preflight = PreflightResult(
        allowed=False,
        health=EngineHealth.healthy("preflight reached"),
        failure=failure,
    )
    engine = _RecordingEngine(preflight=preflight)

    outcome = evaluate_engine_for_download_item(
        d,
        registry=EngineRegistry((engine,)),
        enabled=True,
    )

    assert outcome.applied is True
    assert outcome.preflight is preflight
    assert outcome.preflight.allowed is False
    assert engine.requests == [outcome.request]
    assert engine.start_calls == 0


@pytest.mark.parametrize(
    ("media_type", "subtypes", "reason"),
    [
        ("general", ["hls"], "subtype:hls"),
        ("general", ["fragmented"], "subtype:fragmented"),
        ("video", ["normal"], "media_type"),
    ],
)
def test_runtime_bridge_hls_fragmented_and_video_paths_stay_legacy(tmp_path, media_type, subtypes, reason):
    d = _download_item(tmp_path)
    d.type = media_type
    d.subtype_list = subtypes
    engine = _RecordingEngine()

    outcome = evaluate_engine_for_download_item(
        d,
        registry=EngineRegistry((engine,)),
        enabled=True,
    )

    assert outcome.applied is False
    assert outcome.skip_reason == reason
    assert engine.requests == []
    assert engine.start_calls == 0


def test_runtime_bridge_drops_bad_headers_without_blocking_legacy(tmp_path):
    d = _download_item(tmp_path)
    d.http_headers = {
        "User-Agent": "FireDM",
        "Bad:Name": "x",
        "X-Bad": "ok\r\nInjected: yes",
    }
    engine = _RecordingEngine()

    outcome = evaluate_engine_for_download_item(
        d,
        registry=EngineRegistry((engine,)),
        enabled=True,
    )

    assert outcome.applied is True
    assert outcome.dropped_headers
    assert outcome.request is not None
    assert [(header.name, header.value) for header in outcome.request.headers] == [
        ("User-Agent", "FireDM"),
    ]


def test_controller_advisory_bridge_then_legacy_handoff_exactly_once(tmp_path, monkeypatch):
    ctrl = _controller()
    d = _download_item(tmp_path)
    bridge = Mock(
        return_value=BridgeOutcome(
            applied=True,
            engine_id="internal-http",
            preflight=PreflightResult(allowed=True, health=EngineHealth.healthy("ok")),
        )
    )

    _, brain_mock = _run_download_once(ctrl, d, bridge_side_effect=bridge, monkeypatch=monkeypatch)

    bridge.assert_called_once_with(d, enabled=True)
    brain_mock.assert_called_once_with(d)
    assert d.status != Status.completed


def test_controller_bridge_exception_still_uses_legacy_handoff_once(tmp_path, monkeypatch):
    ctrl = _controller()
    d = _download_item(tmp_path)

    _, brain_mock = _run_download_once(
        ctrl,
        d,
        bridge_side_effect=RuntimeError("bridge boom"),
        monkeypatch=monkeypatch,
    )

    brain_mock.assert_called_once_with(d)
    assert d.status != Status.completed


def test_controller_config_gate_can_disable_advisory_bridge(tmp_path, monkeypatch):
    ctrl = _controller()
    d = _download_item(tmp_path)
    monkeypatch.setattr(config, "engine_bridge_diagnostics_enabled", False, raising=False)
    bridge = Mock(return_value=BridgeOutcome(applied=False, skip_reason="disabled"))

    _, brain_mock = _run_download_once(ctrl, d, bridge_side_effect=bridge, monkeypatch=monkeypatch)

    bridge.assert_called_once_with(d, enabled=False)
    brain_mock.assert_called_once_with(d)
