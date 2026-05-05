"""Playlist builder — turns extractor info into a list of Video objects.

Separated from `controller.create_video_playlist` so the parsing logic has
a narrow, testable surface and the controller stays an orchestrator.

The builder is agnostic of the Video class. Call sites pass a factory
(`observable_factory`) which the builder uses to construct each entry.
That keeps the controller module free of heavy construction logic while
preserving the observer/GUI wiring that only the controller knows about.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from .pipeline_logger import PipelineStage, pipeline_event, pipeline_exception
from .playlist_entry import normalize_entry

VideoFactory = Callable[[str, dict[str, Any]], Any]


@dataclass
class PlaylistBuildResult:
    kind: str  # "single", "playlist"
    url: str
    videos: list[Any] = field(default_factory=list)
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.videos) and not self.errors


def build_playlist_from_info(
    url: str,
    info: dict[str, Any],
    *,
    observable_factory: VideoFactory,
) -> PlaylistBuildResult:
    """Turn an extractor info dict into a list of Video-like objects.

    For a playlist / multi_video, each entry goes through
    `normalize_entry` and then `observable_factory`.

    For a single video, `observable_factory` is called once with the
    full info dict.

    Emits `playlist_parse` and `playlist_entry_normalize` events at every
    boundary so tests and diagnostics can assert the outcome.
    """
    pipeline_event(PipelineStage.PLAYLIST_PARSE, "start", url=url)

    _type = info.get('_type', 'video')
    has_entries = _type in ('playlist', 'multi_video') or 'entries' in info

    result = PlaylistBuildResult(kind="playlist" if has_entries else "single", url=url)

    if has_entries:
        _build_playlist_entries(url, info, observable_factory, result)
    else:
        _build_single_entry(url, info, observable_factory, result)

    status = "ok" if result.ok else "fail"
    pipeline_event(
        PipelineStage.PLAYLIST_PARSE,
        status,
        url=url,
        kind=result.kind,
        entries=len(result.videos),
        skipped=result.skipped,
        errors=len(result.errors),
    )
    return result


def _build_playlist_entries(
    url: str,
    info: dict[str, Any],
    factory: VideoFactory,
    result: PlaylistBuildResult,
) -> None:
    raw_entries: Iterable[Any] = list(info.get('entries') or [])
    playlist_title = info.get('title', '')

    for idx, v_info in enumerate(raw_entries):
        if not isinstance(v_info, dict):
            result.skipped += 1
            pipeline_event(
                PipelineStage.PLAYLIST_ENTRY_NORMALIZE,
                "fail",
                detail="entry is not a dict",
                idx=idx,
            )
            continue

        v_info.setdefault('formats', [])
        normalized = normalize_entry(v_info)
        if normalized is None:
            result.skipped += 1
            pipeline_event(
                PipelineStage.PLAYLIST_ENTRY_NORMALIZE,
                "fail",
                detail="no identifier or url",
                idx=idx,
            )
            continue

        pipeline_event(
            PipelineStage.PLAYLIST_ENTRY_NORMALIZE,
            "ok",
            idx=idx,
            source=normalized.source_field,
            rebuilt=normalized.was_normalized,
            ie_key=normalized.ie_key,
        )

        try:
            vid = factory(normalized.url, v_info)
        except Exception as e:
            result.skipped += 1
            result.errors.append(f"entry {idx}: {type(e).__name__}: {e}")
            pipeline_exception(
                PipelineStage.PLAYLIST_ENTRY_NORMALIZE,
                e,
                idx=idx,
                url=normalized.url,
            )
            continue

        # propagate playlist metadata so GUI folder naming works
        try:
            vid.playlist_title = playlist_title
            vid.playlist_url = url
        except Exception:
            # factory returned something that doesn't accept these attrs;
            # non-fatal for the build, so don't abort.
            pass

        result.videos.append(vid)


def _build_single_entry(
    url: str,
    info: dict[str, Any],
    factory: VideoFactory,
    result: PlaylistBuildResult,
) -> None:
    if not info.get('formats'):
        pipeline_event(
            PipelineStage.PLAYLIST_PARSE,
            "skip",
            detail="single entry has no formats",
            url=url,
        )
        return
    try:
        vid = factory(url, info)
    except Exception as e:
        result.errors.append(f"single: {type(e).__name__}: {e}")
        pipeline_exception(PipelineStage.PLAYLIST_PARSE, e, url=url, kind="single")
        return
    with contextlib.suppress(Exception):
        vid.processed = True
    result.videos.append(vid)
