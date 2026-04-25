"""Regression: HLS refresh path uses a parser that actually exists in yt-dlp.

The previous code in ``firedm/video.py`` called
``InfoExtractor._parse_m3u8_formats``. yt-dlp 2026.x removed that name; only
``_parse_m3u8_formats_and_subtitles`` survives. Calling the old name crashes
HLS URL refresh with ``AttributeError`` once a real DASH/HLS download
triggers ``pre_process_hls``. The fix adapts to either name; this test
guards against another silent rename by:

1. asserting the modern API is present on the installed yt-dlp, and
2. asserting it returns the (formats, subtitles) tuple shape we depend on.

If yt-dlp removes both names in a future release, this test will fail and
maintainers must update ``video.py refresh_urls`` accordingly.
"""

from __future__ import annotations

import pytest

yt_dlp = pytest.importorskip("yt_dlp")


def test_yt_dlp_exposes_a_usable_m3u8_format_parser():
    from yt_dlp.extractor.common import InfoExtractor

    modern = getattr(InfoExtractor, "_parse_m3u8_formats_and_subtitles", None)
    legacy = getattr(InfoExtractor, "_parse_m3u8_formats", None)

    assert modern is not None or legacy is not None, (
        "yt-dlp removed both _parse_m3u8_formats and "
        "_parse_m3u8_formats_and_subtitles. video.refresh_urls needs a new "
        "parser path."
    )


def test_modern_m3u8_parser_returns_formats_subtitles_tuple():
    """Mirror the call shape used by ``video.refresh_urls`` after the fix.

    yt-dlp 2026.x requires a bound ``InfoExtractor`` instance with a
    ``YoutubeDL`` parent because ``_parse_m3u8_formats_and_subtitles``
    calls ``self.get_param``. Calling with ``None`` as ``self`` raises
    ``AttributeError``. ``video.refresh_urls`` constructs a minimal
    instance; this test does the same so a future yt-dlp change to the
    constructor or to the parser signature is caught immediately.
    """
    from yt_dlp import YoutubeDL
    from yt_dlp.extractor.common import InfoExtractor

    modern = getattr(InfoExtractor, "_parse_m3u8_formats_and_subtitles", None)
    if modern is None:
        pytest.skip("yt-dlp install is too old; legacy API only")

    # Minimal master playlist with one variant. Enough surface area for the
    # parser to construct a single format dict.
    m3u8_doc = (
        "#EXTM3U\n"
        "#EXT-X-VERSION:3\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=160000,CODECS=\"mp4a.40.2\"\n"
        "stream.m3u8\n"
    )

    ie = InfoExtractor(YoutubeDL({}))
    result = ie._parse_m3u8_formats_and_subtitles(
        m3u8_doc, "https://example.test/playlist.m3u8", m3u8_id="hls"
    )

    assert isinstance(result, tuple) and len(result) == 2, (
        "Modern parser must return (formats, subtitles); video.refresh_urls "
        "unpacks the tuple."
    )
    formats, _subs = result
    assert isinstance(formats, list), "formats must be a list"
    # at least one format entry rebuilt from BANDWIDTH=160000, with the
    # variant URL absolutized against the playlist URL
    assert any(
        isinstance(item, dict) and item.get("url", "").endswith("stream.m3u8")
        for item in formats
    ), f"expected a format pointing at the variant URL; got {formats!r}"
