from __future__ import annotations

import pytest

from firedm.download_engines import (
    DownloadFailure,
    DownloadJob,
    DownloadProgress,
    DownloadRequest,
    DownloadResult,
    DownloadState,
    EngineCapability,
    EngineHealth,
    EngineHealthStatus,
    EngineInputType,
    EngineRegistry,
    Header,
    PreflightResult,
)


class FakeEngine:
    def __init__(
        self,
        engine_id: str,
        *,
        health: EngineHealth | None = None,
        schemes: tuple[str, ...] = ("http", "https"),
    ) -> None:
        self._id = engine_id
        self._health = health or EngineHealth.healthy()
        self._schemes = schemes

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
        return (EngineInputType.URL,)

    @property
    def capabilities(self) -> tuple[EngineCapability, ...]:
        return (EngineCapability.RESUME,)

    def health_check(self) -> EngineHealth:
        return self._health

    def preflight(self, request: DownloadRequest) -> PreflightResult:
        return PreflightResult(allowed=True, health=self._health)

    def start(self, job: DownloadJob) -> DownloadResult:
        return DownloadResult(job.job_id, DownloadState.PENDING)

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


class BrokenHealthEngine(FakeEngine):
    def health_check(self) -> EngineHealth:
        raise RuntimeError("boom")


def test_header_rejects_injection_characters():
    Header("User-Agent", "FireDM")

    with pytest.raises(ValueError, match="Header name"):
        Header("Bad:Name", "x")
    with pytest.raises(ValueError, match="Header value"):
        Header("User-Agent", "ok\r\nInjected: yes")


def test_download_request_validates_filename_and_engine_id():
    DownloadRequest("https://example.test/file", filename="file.bin", engine_id="internal-http")

    with pytest.raises(ValueError, match="file name"):
        DownloadRequest("https://example.test/file", filename=r"..\evil.bin")
    with pytest.raises(ValueError, match="Invalid engine id"):
        DownloadRequest("https://example.test/file", engine_id="Bad Engine")


def test_progress_and_result_invariants():
    DownloadProgress("job-1", DownloadState.RUNNING, bytes_downloaded=5, bytes_total=10)

    with pytest.raises(ValueError, match="cannot exceed"):
        DownloadProgress("job-1", DownloadState.RUNNING, bytes_downloaded=11, bytes_total=10)
    with pytest.raises(ValueError, match="must include"):
        DownloadResult("job-1", DownloadState.FAILED)
    with pytest.raises(ValueError, match="Only failed"):
        DownloadResult("job-1", DownloadState.RUNNING, failure=DownloadFailure("x", "bad"))


def test_registry_rejects_duplicate_and_invalid_engine_ids():
    registry = EngineRegistry()
    registry.register(FakeEngine("internal"))

    with pytest.raises(ValueError, match="already registered"):
        registry.register(FakeEngine("internal"))
    with pytest.raises(ValueError, match="Invalid engine id"):
        registry.register(FakeEngine("Bad Engine"))


def test_registry_descriptor_catches_broken_health_check():
    registry = EngineRegistry((BrokenHealthEngine("broken"),))

    descriptor = registry.descriptors()[0]

    assert descriptor.id == "broken"
    assert descriptor.health.status == EngineHealthStatus.UNAVAILABLE
    assert "RuntimeError" in descriptor.health.message


def test_registry_selects_only_usable_supported_engine():
    registry = EngineRegistry(
        (
            FakeEngine("aria2c", health=EngineHealth.unavailable("missing"), schemes=("http", "https", "ftp")),
            FakeEngine("internal", schemes=("http", "https")),
        )
    )

    selected = registry.select(scheme="https", input_type=EngineInputType.URL)

    assert selected is not None
    assert selected.id == "internal"
    assert registry.select(preferred="aria2c", scheme="ftp", input_type=EngineInputType.URL) is None


def test_registry_descriptors_can_exclude_unavailable_engines():
    registry = EngineRegistry(
        (
            FakeEngine("aria2c", health=EngineHealth.unavailable("missing")),
            FakeEngine("internal"),
        )
    )

    descriptors = registry.descriptors(include_unavailable=False)

    assert [item.id for item in descriptors] == ["internal"]
