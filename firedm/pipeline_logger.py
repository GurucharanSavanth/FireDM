"""Structured pipeline logger for the video / download pipeline.

Every event goes through the app's existing `log()` helper so GUI log
windows and file logs keep working, but events carry a consistent
`[pipeline] stage=<stage> status=<status> key=value ...` prefix so they
are grep-friendly for diagnostics and assertable from tests.

The helper is intentionally dependency-free so it can run inside the
extractor-loading daemon threads that execute before settings are
initialized.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class PipelineStage:
    EXTRACTOR_LOAD = "extractor_load"
    EXTRACTOR_READY = "extractor_ready"
    EXTRACTOR_SELECT = "extractor_select"
    METADATA_FETCH = "metadata_fetch"
    PLAYLIST_PARSE = "playlist_parse"
    PLAYLIST_ENTRY_NORMALIZE = "playlist_entry_normalize"
    STREAM_BUILD = "stream_build"
    STREAM_SELECT = "stream_select"
    DOWNLOAD_ENQUEUE = "download_enqueue"
    DOWNLOAD_START = "download_start"
    FFMPEG_DISCOVER = "ffmpeg_discover"
    FFMPEG_MERGE = "ffmpeg_merge"


_REDACTED = "REDACTED"
_URL_RE = re.compile(r"https?://[^\s'\"<>]+", re.IGNORECASE)
_SENSITIVE_PARAM_PARTS = {
    "access",
    "access_token",
    "api_key",
    "auth",
    "authorization",
    "bearer",
    "cookie",
    "credential",
    "expires",
    "key",
    "keyid",
    "keypairid",
    "passwd",
    "password",
    "policy",
    "secret",
    "session",
    "sig",
    "signature",
    "token",
}


def _is_sensitive_param(name: str) -> bool:
    normalized = name.lower().replace("-", "_")
    parts = {part for part in re.split(r"[^a-z0-9]+", normalized) if part}
    if normalized in _SENSITIVE_PARAM_PARTS or parts & _SENSITIVE_PARAM_PARTS:
        return True
    return any(
        marker in normalized
        for marker in (
            "access_token",
            "accesskey",
            "api_key",
            "apikey",
            "authorization",
            "auth",
            "cookie",
            "credential",
            "expires",
            "keyid",
            "key_pair",
            "keypair",
            "password",
            "policy",
            "secret",
            "session",
            "signature",
            "token",
            "x_amz",
        )
    )


def _redact_query(query: str) -> str:
    if not query:
        return query

    pairs = parse_qsl(query, keep_blank_values=True)
    return urlencode(
        [
            (key, _REDACTED if _is_sensitive_param(key) else value)
            for key, value in pairs
        ],
        doseq=True,
    )


def redact_url_for_log(value: str) -> str:
    """Redact credential-bearing URL parts while keeping host/path useful."""
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value

    if not parsed.scheme or not parsed.netloc:
        return value

    netloc = parsed.netloc
    if "@" in netloc:
        _userinfo, host = netloc.rsplit("@", 1)
        netloc = f"{_REDACTED}@{host}"

    query = _redact_query(parsed.query)
    fragment = _redact_query(parsed.fragment) if "=" in parsed.fragment else parsed.fragment
    return urlunsplit((parsed.scheme, netloc, parsed.path, query, fragment))


def redact_text_for_log(value: str) -> str:
    """Redact URL credentials inside arbitrary log text."""

    def replace(match: re.Match[str]) -> str:
        raw = match.group(0)
        suffix = ""
        while raw and raw[-1] in ".,);]}":
            suffix = raw[-1] + suffix
            raw = raw[:-1]
        return redact_url_for_log(raw) + suffix

    return _URL_RE.sub(replace, value)


def _format_pairs(fields: dict[str, Any]) -> str:
    pairs = []
    for key, value in fields.items():
        if value is None:
            rendered = "None"
        elif isinstance(value, str):
            value = redact_text_for_log(value)
            rendered = value if all(ch not in value for ch in " \t\n") else repr(value)
        else:
            rendered = repr(value)
        pairs.append(f"{key}={rendered}")
    return " ".join(pairs)


def pipeline_event(
    stage: str,
    status: str,
    *,
    detail: str = "",
    **fields: Any,
) -> None:
    """Emit a structured pipeline event through the existing logger.

    Args:
        stage: one of the `PipelineStage.*` constants (or a free-form string).
        status: `"start"`, `"ok"`, `"fail"`, `"skip"`, `"warn"`.
        detail: short human-readable description.
        **fields: extra key/value pairs (rendered as `key=value`).
    """
    from .utils import log  # local import avoids circulars at module load

    body = f"[pipeline] stage={stage} status={status}"
    if fields:
        body += " " + _format_pairs(fields)
    if detail:
        detail = redact_text_for_log(detail)
        body += f" :: {detail}"
    log(body, log_level=2)


def pipeline_exception(stage: str, exc: BaseException, **fields: Any) -> None:
    """Emit a `fail` event for an exception without re-raising."""
    pipeline_event(
        stage,
        "fail",
        detail=f"{type(exc).__name__}: {exc}",
        **fields,
    )
