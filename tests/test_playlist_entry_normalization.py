"""Tests for `firedm.playlist_entry.normalize_entry`."""

from __future__ import annotations

import pytest

from firedm.playlist_entry import normalize_entry


def test_prefers_full_webpage_url():
    ne = normalize_entry({
        "webpage_url": "https://www.youtube.com/watch?v=abc12345678",
        "url": "abc12345678",
        "id": "abc12345678",
        "ie_key": "Youtube",
    })
    assert ne.url == "https://www.youtube.com/watch?v=abc12345678"
    assert ne.was_normalized is False
    assert ne.source_field == "webpage_url"


def test_uses_full_url_when_webpage_url_missing():
    ne = normalize_entry({"url": "https://vimeo.com/12345", "id": "12345"})
    assert ne.url == "https://vimeo.com/12345"
    assert ne.was_normalized is False


def test_rebuilds_from_bare_youtube_id_via_ie_key():
    ne = normalize_entry({"id": "abc12345678", "ie_key": "Youtube"})
    assert ne.url == "https://www.youtube.com/watch?v=abc12345678"
    assert ne.was_normalized is True
    assert ne.source_field == "id"
    assert ne.ie_key == "Youtube"


def test_rebuilds_from_bare_youtube_id_even_without_ie_key():
    """11-char YouTube-shaped ids are inferred as YouTube when no ie_key
    is present — this is the common yt_dlp `process=False` shape."""
    ne = normalize_entry({"id": "C4C8JsgGrrY"})
    assert ne.url == "https://www.youtube.com/watch?v=C4C8JsgGrrY"
    assert ne.was_normalized is True


def test_rebuilds_when_url_field_is_bare_id():
    ne = normalize_entry({"url": "dQw4w9WgXcQ"})
    assert ne.url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert ne.was_normalized is True
    assert ne.source_field == "url"


def test_vimeo_numeric_id():
    ne = normalize_entry({"id": "76979871", "ie_key": "Vimeo"})
    assert ne.url == "https://vimeo.com/76979871"


def test_returns_none_when_no_identifier():
    assert normalize_entry({}) is None
    assert normalize_entry({"title": "nothing useful"}) is None


def test_non_youtube_bare_id_without_ie_key_returns_none():
    """We refuse to guess URLs for unknown extractors — caller must
    decide how to handle opaque ids to avoid silently mis-routing."""
    assert normalize_entry({"id": "12345"}) is None
