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

from typing import Any


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


def _format_pairs(fields: dict[str, Any]) -> str:
    pairs = []
    for key, value in fields.items():
        if value is None:
            rendered = "None"
        elif isinstance(value, str):
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
