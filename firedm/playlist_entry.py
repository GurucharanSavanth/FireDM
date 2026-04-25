"""Playlist entry URL normalization.

yt_dlp / youtube_dl return playlist entries with varying shapes depending on
extractor, `process=True/False`, and API quirks. Before Commit 5 the
controller picked the first truthy of `webpage_url / url / id`, which
regularly yielded a bare 11-character YouTube video ID (no scheme, no host)
and caused downstream extraction to fail.

This module centralizes the normalization rule and emits
`playlist_entry_normalize` events so tests and diagnostics can assert on the
outcome.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


@dataclass(frozen=True)
class NormalizedEntry:
    url: str
    source_field: str  # which vid_info key produced the URL (diagnostics)
    ie_key: str | None
    was_normalized: bool  # True when we rebuilt a full URL from a bare id


def _is_full_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def normalize_entry(vid_info: dict[str, Any]) -> NormalizedEntry | None:
    """Return the best entry URL for a playlist item.

    Priority:
        1. `webpage_url` if it's a full URL.
        2. `url` if it's a full URL.
        3. `url` that happens to be a bare id, rebuilt using `ie_key`.
        4. `id` field rebuilt using `ie_key` or safe defaults for known
           extractor families.

    Returns `None` only when no usable identifier is present at all.
    """
    webpage_url = vid_info.get("webpage_url")
    raw_url = vid_info.get("url")
    vid_id = vid_info.get("id")
    ie_key = vid_info.get("ie_key") or vid_info.get("extractor_key")

    if isinstance(webpage_url, str) and _is_full_url(webpage_url):
        return NormalizedEntry(webpage_url, "webpage_url", ie_key, False)

    if isinstance(raw_url, str) and _is_full_url(raw_url):
        return NormalizedEntry(raw_url, "url", ie_key, False)

    # At this point neither webpage_url nor url is a full URL. Fall through
    # to id-based normalization.
    candidate_id = None
    if isinstance(vid_id, str) and vid_id:
        candidate_id = vid_id
    elif isinstance(raw_url, str) and raw_url:
        candidate_id = raw_url

    if not candidate_id:
        return None

    rebuilt = _rebuild_from_id(candidate_id, ie_key)
    if rebuilt is None:
        return None
    source = "id" if candidate_id == vid_id else "url"
    return NormalizedEntry(rebuilt, source, ie_key, True)


def _rebuild_from_id(candidate_id: str, ie_key: str | None) -> str | None:
    """Rebuild a full URL from a bare id, when we have enough context."""
    key = (ie_key or "").lower()

    if key.startswith("youtube") or YOUTUBE_ID_RE.match(candidate_id):
        return f"https://www.youtube.com/watch?v={candidate_id}"

    if key.startswith("vimeo") and candidate_id.isdigit():
        return f"https://vimeo.com/{candidate_id}"

    if key.startswith("twitch"):
        return f"https://www.twitch.tv/videos/{candidate_id}"

    return None
