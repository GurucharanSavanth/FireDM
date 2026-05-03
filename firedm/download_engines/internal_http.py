"""InternalHTTPDownloadEngine adapter skeleton.

This adapter exposes the legacy pycurl-backed segmented downloader through the
new `DownloadEngine` protocol *without* replacing or wiring the legacy runtime.

Behavior contract for this skeleton:
- `health_check()` only inspects whether the legacy downloader's hard
  dependency (`pycurl`) is importable. It never opens a connection, never
  starts a transfer, and never instantiates a `Curl` handle.
- `preflight()` performs local-only validation. It never makes a network
  request and never reads files outside the request shape itself.
- `start()` returns a structured `DownloadResult(state=FAILED,
  failure=DownloadFailure(code="ENGINE_NOT_CONNECTED", ...))`. It deliberately
  does **not** call `brain()` / `worker.Worker` / pycurl. The legacy
  `Controller -> brain -> worker` runtime path is unchanged by this patch.
- `pause`, `resume`, `cancel`, `get_status` mirror that contract: they return
  a structured failure result instead of pretending to manage a job.
- `shutdown()` is a no-op because the adapter owns no resources.

Truthful capability flags only: this engine advertises segmented HTTP, resume,
custom headers, and explicit user-supplied cookies because the legacy worker
already supports them. It does **not** advertise post-processing, subtitles,
metadata embedding, or media extraction — those are owned by other
modules/services and will be wired through dedicated adapters in later
patches.

Security boundaries preserved:
- No subprocess invocation.
- No `shell=True`.
- No arbitrary local file reads (preflight inspects request fields only).
- Header CR/LF injection is rejected upstream by `download_engines.models.Header`.
- No secret material is logged or returned in failure messages.
"""

from __future__ import annotations

import importlib.util
from urllib.parse import urlparse

from .models import (
    DownloadFailure,
    DownloadJob,
    DownloadProgress,
    DownloadRequest,
    DownloadResult,
    DownloadState,
    EngineCapability,
    EngineHealth,
    EngineInputType,
    PreflightResult,
)

# Internal pycurl path supports more schemes via libcurl, but this skeleton is
# intentionally conservative. ftp/ftps/sftp routing is owned by `worker._ftp_download`
# / `_sftp_download` (sftp also requires paramiko). They will be advertised by
# this adapter only after a dedicated dependency-aware probe lands.
_DEFAULT_SUPPORTED_SCHEMES: tuple[str, ...] = ("http", "https")


def _pycurl_available() -> bool:
    """Return True if the legacy downloader's hard dependency can be imported.

    Uses `importlib.util.find_spec` so the check is cheap and does not execute
    pycurl module-level code.
    """
    try:
        return importlib.util.find_spec("pycurl") is not None
    except (ImportError, ValueError):  # pragma: no cover - find_spec edge cases
        return False


class InternalHTTPDownloadEngine:
    """Adapter that bridges the new engine seam to the legacy internal downloader.

    This adapter is intentionally **not** wired to the legacy runtime in this
    patch. `start()` returns a structured ENGINE_NOT_CONNECTED failure to make
    the unwired state explicit and auditable. The legacy
    `Controller -> brain -> worker` path remains the only code path that
    actually moves bytes.
    """

    ENGINE_ID = "internal-http"
    DISPLAY_NAME = "FireDM Internal (pycurl)"

    def __init__(self, supported_schemes: tuple[str, ...] | None = None) -> None:
        if supported_schemes is None:
            supported_schemes = _DEFAULT_SUPPORTED_SCHEMES
        # Normalize: lowercase, no trailing colon, dedup, preserve order.
        self._schemes: tuple[str, ...] = tuple(
            dict.fromkeys(scheme.lower().rstrip(":") for scheme in supported_schemes)
        )

    @property
    def id(self) -> str:
        return self.ENGINE_ID

    @property
    def display_name(self) -> str:
        return self.DISPLAY_NAME

    @property
    def supported_schemes(self) -> tuple[str, ...]:
        return self._schemes

    @property
    def supported_input_types(self) -> tuple[EngineInputType, ...]:
        # Only direct URL inputs are claimed. Media extraction (yt-dlp) and
        # torrent/magnet handling belong to dedicated adapters.
        return (EngineInputType.URL,)

    @property
    def capabilities(self) -> tuple[EngineCapability, ...]:
        # Only capabilities the legacy worker is known to support.
        return (
            EngineCapability.SEGMENTED_HTTP,
            EngineCapability.RESUME,
            EngineCapability.RATE_LIMIT,
            EngineCapability.PROXY,
            EngineCapability.CUSTOM_HEADERS,
            EngineCapability.COOKIES_EXPLICIT_USER_SUPPLIED,
        )

    def health_check(self) -> EngineHealth:
        if _pycurl_available():
            return EngineHealth.healthy(
                "internal pycurl backend importable",
                backend="pycurl",
            )
        return EngineHealth.unavailable(
            "pycurl is not installed",
            backend="pycurl",
        )

    def preflight(self, request: DownloadRequest) -> PreflightResult:
        health = self.health_check()
        if not health.usable:
            return PreflightResult(
                allowed=False,
                health=health,
                failure=DownloadFailure(
                    code="ENGINE_UNAVAILABLE",
                    message="Internal HTTP engine dependency missing",
                    recoverable=False,
                    detail=health.message,
                ),
            )

        if request.input_type not in self.supported_input_types:
            return PreflightResult(
                allowed=False,
                health=health,
                failure=DownloadFailure(
                    code="UNSUPPORTED_INPUT_TYPE",
                    message=(
                        f"Internal HTTP engine does not handle input type "
                        f"{request.input_type.value}"
                    ),
                    recoverable=False,
                ),
            )

        try:
            scheme = urlparse(request.source).scheme.lower()
        except (ValueError, AttributeError):
            scheme = ""
        if scheme not in self._schemes:
            return PreflightResult(
                allowed=False,
                health=health,
                failure=DownloadFailure(
                    code="UNSUPPORTED_SCHEME",
                    message=(
                        f"Internal HTTP engine does not support scheme "
                        f"{scheme!r}"
                    ),
                    recoverable=False,
                ),
            )

        return PreflightResult(allowed=True, health=health)

    def start(self, job: DownloadJob) -> DownloadResult:
        # Intentionally NOT wired. The legacy runtime path
        # (controller._download -> brain -> worker) remains authoritative.
        # Returning a structured failure here makes the unwired state
        # explicit so callers cannot silently assume success.
        return DownloadResult(
            job_id=job.job_id,
            state=DownloadState.FAILED,
            failure=DownloadFailure(
                code="ENGINE_NOT_CONNECTED",
                message=(
                    "InternalHTTPDownloadEngine is a skeleton; legacy "
                    "Controller -> brain -> worker path is still authoritative"
                ),
                recoverable=False,
                detail="not_implemented_for_runtime",
            ),
        )

    def pause(self, job_id: str) -> DownloadResult:
        return self._not_connected_result(job_id)

    def resume(self, job_id: str) -> DownloadResult:
        return self._not_connected_result(job_id)

    def cancel(self, job_id: str) -> DownloadResult:
        return self._not_connected_result(job_id)

    def get_status(self, job_id: str) -> DownloadProgress:
        # Progress snapshots are stateful; for an unwired skeleton return a
        # PENDING snapshot so callers can detect "no progress recorded"
        # without a misleading exception path.
        return DownloadProgress(
            job_id=job_id,
            state=DownloadState.PENDING,
            message="engine not connected",
        )

    def shutdown(self) -> None:
        return None

    @staticmethod
    def _not_connected_result(job_id: str) -> DownloadResult:
        return DownloadResult(
            job_id=job_id,
            state=DownloadState.FAILED,
            failure=DownloadFailure(
                code="ENGINE_NOT_CONNECTED",
                message=(
                    "InternalHTTPDownloadEngine lifecycle is not wired; "
                    "use legacy controller path"
                ),
                recoverable=False,
                detail="not_implemented_for_runtime",
            ),
        )
