"""Layer-3 controller -> engine bridge (diagnostic-only).

This module provides a *pure*, side-effect-free function that the legacy
`Controller._download` path can consult before kicking off the existing
`brain(d)` runtime. The bridge:

- Decides whether the request shape is something `InternalHTTPDownloadEngine`
  can plausibly preflight (HTTP/HTTPS scheme plus blocklists for media-specific
  `subtype_list` and `d.type` values).
- If applicable, builds a `DownloadRequest` from the legacy `DownloadItem`
  shape and calls `engine.preflight(request)` so its result can be observed
  by tests and structured logs.
- Returns a typed `BridgeOutcome`. The caller never gets a "go" signal that
  bypasses legacy: the bridge is diagnostic-only in this layer.

Behavior contract:
- `engine.start()` is **never** called by this bridge. The legacy
  `Controller -> brain -> worker` runtime path remains authoritative.
- `DownloadItem` (`d`) is **never** mutated. We only read attributes.
- Network is never touched. Only local validation happens.
- Bad headers in `d.http_headers` (CR/LF, colon-in-name) are dropped with
  diagnostic context; the bridge does not raise from a single bad header.
- Selection runs against an `EngineConfig()` with defaults. UI binding,
  persistence, per-scheme/per-input preferences, and the engine dropdown are
  separate future layers.

Skip rules (positive allowlist for the internal HTTP engine):
- `d.url`/`d.eff_url` non-empty.
- URL scheme is `http` or `https` (lowercase).
- `d.type` is not `'video'`, `'audio'`, or `'key'` -- those are routed through
  `pre_process_hls`, ffmpeg, or DRM gates by other modules. Plain file MIME
  types such as `application/octet-stream` can still run advisory preflight.
- `d.subtype_list` does not contain any of:
  `hls`, `dash`, `fragmented`, `f4m`, `ism`, `encrypted`.
  (Empty subtype_list and `['normal']` are accepted.)

Anything outside the allowlist is reported as `applied=False` with a
`skip_reason` string. The legacy path keeps full ownership in those cases.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .. import config as legacy_config
from .base import DownloadEngine
from .config import EngineConfig
from .factory import create_default_registry, select_engine
from .models import (
    DownloadRequest,
    EngineInputType,
    Header,
    PreflightResult,
)
from .registry import EngineRegistry

logger = logging.getLogger(__name__)


# Subtypes that are NOT directly transferable as a single HTTP file by the
# internal pycurl downloader. These flow through video.py / brain.py-specific
# code paths and must remain owned by the legacy runtime.
_NON_INTERNAL_HTTP_SUBTYPES: frozenset[str] = frozenset(
    {"hls", "dash", "fragmented", "f4m", "ism", "encrypted"}
)

# d.type values the internal HTTP engine refuses to claim. video/audio/key
# require ffmpeg merge, fragment join, or DRM key handling done by
# brain/video/extractor. Empty string and "general" / "text/html" are passed
# through so the bridge can run preflight on plain file downloads.
_NON_INTERNAL_HTTP_TYPES: frozenset[str] = frozenset({"video", "audio", "key"})

_SUPPORTED_SCHEMES: frozenset[str] = frozenset({"http", "https"})


@dataclass(frozen=True)
class BridgeOutcome:
    """Result of consulting the engine seam for a `DownloadItem`.

    Fields:
    - `applied`: True if the bridge actually evaluated an engine. False if
      a skip rule short-circuited evaluation.
    - `skip_reason`: short machine-friendly tag (`disabled`, `empty_url`,
      `unsupported_scheme`, `media_type`, `subtype`, `no_engine`, `no_dep`,
      etc.) when `applied=False`.
    - `engine_id`: id of the engine that ran preflight, or `None`.
    - `preflight`: the engine's `PreflightResult`, or `None`.
    - `request`: the `DownloadRequest` that was built and passed to
      preflight, or `None`. Useful for tests and structured logs.
    - `dropped_headers`: tuple of `(name, reason)` for headers dropped while
      constructing the request. Empty when nothing was dropped.

    The bridge is purely diagnostic in Layer 3: callers MUST treat
    `applied=True` with `preflight.allowed=False` as advisory only and
    continue with the legacy path. Promoting fatal preflight to a hard
    block belongs to a later layer.
    """

    applied: bool
    skip_reason: str | None = None
    engine_id: str | None = None
    preflight: PreflightResult | None = None
    request: DownloadRequest | None = None
    dropped_headers: tuple[tuple[str, str], ...] = ()


def _coerce_url(d: Any) -> str:
    """Pick the URL the legacy worker would actually use.

    Worker prefers `eff_url` when set; falls back to `url`. We mirror that.
    Returns `""` if neither is a non-empty string.
    """
    eff = getattr(d, "eff_url", "") or ""
    raw = getattr(d, "url", "") or ""
    candidate = eff if isinstance(eff, str) and eff else raw
    if not isinstance(candidate, str):
        return ""
    return candidate


def _coerce_filename(name: Any) -> str | None:
    """Return a filename safe for `DownloadRequest`, or `None` if unsafe.

    `DownloadRequest.__post_init__` rejects `\\`, `/`, and `\\0` inside the
    name. Empty strings are converted to `None` (the model treats `None`
    as "engine picks").
    """
    if not isinstance(name, str) or not name:
        return None
    if any(part in name for part in ("/", "\\", "\0")):
        return None
    return name


def _coerce_output_dir(folder: Any) -> Path | None:
    if not isinstance(folder, str) or not folder:
        return None
    try:
        return Path(folder)
    except (TypeError, ValueError):
        return None


def _safe_len(value: Any) -> int:
    try:
        return len(value)  # type: ignore[arg-type]
    except TypeError:
        return 0


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _build_request_options(d: Any) -> Mapping[str, Any]:
    """Copy non-secret parity fields into request options.

    Raw proxy URLs may contain credentials, so this diagnostic bridge records
    proxy presence only. A later persisted engine settings model must carry
    secret-bearing proxy data explicitly and redact it in diagnostics.
    """
    return {
        "resumable": bool(getattr(d, "resumable", False)),
        "segment_count": _safe_len(getattr(d, "segments", ()) or ()),
        "total_parts": _safe_int(getattr(d, "total_parts", 0)),
        "proxy_enabled": bool(getattr(legacy_config, "enable_proxy", False)),
        "proxy_configured": bool(getattr(legacy_config, "proxy", "")),
    }


def _coerce_headers(
    raw_headers: Any,
) -> tuple[tuple[Header, ...], tuple[tuple[str, str], ...]]:
    """Build a tuple of `Header` objects, dropping invalid ones safely.

    Returns `(accepted, dropped)`. `dropped` lists `(header_name, reason)`
    pairs for diagnostics. The bridge never raises on a single bad header
    so a hostile header value cannot block an entire download.
    """
    if not isinstance(raw_headers, Mapping):
        return ((), ())

    accepted: list[Header] = []
    dropped: list[tuple[str, str]] = []
    for name, value in raw_headers.items():
        try:
            header_name = str(name)
            header_value = "" if value is None else str(value)
        except Exception as exc:  # pragma: no cover - extremely defensive
            dropped.append((repr(name), f"stringify_failed:{type(exc).__name__}"))
            continue
        try:
            accepted.append(Header(name=header_name, value=header_value))
        except ValueError as exc:
            dropped.append((header_name, str(exc)))
    return tuple(accepted), tuple(dropped)


def _build_request(
    *,
    url: str,
    folder: Any,
    name: Any,
    raw_headers: Any,
    options: Mapping[str, Any] | None = None,
) -> tuple[DownloadRequest | None, tuple[tuple[str, str], ...], str | None]:
    """Construct a `DownloadRequest` defensively.

    Returns `(request, dropped_headers, error_reason)`. `request` is `None`
    when construction itself raises (for example because every alternative
    URL is malformed). `error_reason` is a short tag for telemetry.
    """
    headers, dropped_headers = _coerce_headers(raw_headers)
    output_dir = _coerce_output_dir(folder)
    filename = _coerce_filename(name)

    try:
        request = DownloadRequest(
            source=url,
            input_type=EngineInputType.URL,
            output_dir=output_dir,
            filename=filename,
            headers=headers,
            options=options or {},
        )
    except ValueError as exc:
        return None, dropped_headers, f"request_invalid:{exc}"
    except Exception as exc:  # pragma: no cover - very defensive
        return None, dropped_headers, f"request_error:{type(exc).__name__}"
    return request, dropped_headers, None


def _is_runtime_blocking_subtype(subtype_list: Any) -> str | None:
    """Return the first blocking subtype name, or `None`."""
    if not isinstance(subtype_list, (list, tuple, set, frozenset)):
        return None
    for item in subtype_list:
        if isinstance(item, str) and item in _NON_INTERNAL_HTTP_SUBTYPES:
            return item
    return None


def _is_runtime_blocking_type(media_type: Any) -> bool:
    return isinstance(media_type, str) and media_type in _NON_INTERNAL_HTTP_TYPES


def evaluate_engine_for_download_item(
    d: Any,
    *,
    registry: EngineRegistry | None = None,
    config: EngineConfig | None = None,
    enabled: bool = False,
) -> BridgeOutcome:
    """Diagnostic engine-bridge evaluation for a legacy `DownloadItem`.

    The function never mutates `d`, never starts a transfer, and never
    talks to the network. It is safe to call on the foreground or
    background thread.

    `enabled=False` (the default) makes the function a no-op:
    `BridgeOutcome(applied=False, skip_reason="disabled")`. The legacy
    runtime path must still run unconditionally afterwards. `Controller`
    enables the advisory bridge by default because it does not change
    execution; setting `firedm.config.engine_bridge_diagnostics_enabled=False`
    disables it for tests or forensic builds.
    """
    if not enabled:
        return BridgeOutcome(applied=False, skip_reason="disabled")

    cfg = config if config is not None else EngineConfig()
    reg: EngineRegistry = registry if registry is not None else create_default_registry(cfg).registry

    # Short-circuit on shapes the internal HTTP engine cannot own. These are
    # *not* preflight failures -- they are not the engine's job in the first
    # place, so we route them out cleanly so an irrelevant rejection does
    # not appear in diagnostics.
    if _is_runtime_blocking_type(getattr(d, "type", "")):
        return BridgeOutcome(applied=False, skip_reason="media_type")

    blocked_subtype = _is_runtime_blocking_subtype(getattr(d, "subtype_list", None))
    if blocked_subtype is not None:
        return BridgeOutcome(applied=False, skip_reason=f"subtype:{blocked_subtype}")

    url = _coerce_url(d)
    if not url:
        return BridgeOutcome(applied=False, skip_reason="empty_url")

    try:
        scheme = urlsplit(url).scheme.lower()
    except (ValueError, AttributeError):
        scheme = ""
    if scheme not in _SUPPORTED_SCHEMES:
        return BridgeOutcome(applied=False, skip_reason=f"unsupported_scheme:{scheme or 'empty'}")

    request, dropped_headers, error_reason = _build_request(
        url=url,
        folder=getattr(d, "folder", None),
        name=getattr(d, "name", None),
        raw_headers=getattr(d, "http_headers", None),
        options=_build_request_options(d),
    )
    if request is None:
        return BridgeOutcome(
            applied=False,
            skip_reason=error_reason or "request_invalid",
            dropped_headers=dropped_headers,
        )

    engine: DownloadEngine | None = select_engine(
        reg,
        cfg,
        scheme=scheme,
        input_type=EngineInputType.URL,
    )
    if engine is None:
        return BridgeOutcome(
            applied=False,
            skip_reason="no_engine",
            request=request,
            dropped_headers=dropped_headers,
        )

    try:
        preflight = engine.preflight(request)
    except Exception as exc:  # pragma: no cover - adapter-owned shape
        # An adapter bug must not crash the legacy runtime path. Log and
        # treat as no-engine so the caller falls back transparently.
        logger.warning(
            "download_engines.runtime_bridge: %s.preflight raised %s",
            getattr(engine, "id", "<unknown>"),
            type(exc).__name__,
        )
        return BridgeOutcome(
            applied=False,
            skip_reason=f"preflight_exception:{type(exc).__name__}",
            engine_id=getattr(engine, "id", None),
            request=request,
            dropped_headers=dropped_headers,
        )

    return BridgeOutcome(
        applied=True,
        skip_reason=None,
        engine_id=engine.id,
        preflight=preflight,
        request=request,
        dropped_headers=dropped_headers,
    )
