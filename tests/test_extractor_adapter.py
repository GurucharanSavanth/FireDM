from types import SimpleNamespace

from firedm.extractor_adapter import (
    FALLBACK_EXTRACTOR,
    PRIMARY_EXTRACTOR,
    choose_extractor_name,
    load_extractor_module,
)


def test_primary_always_wins_even_when_user_configured_fallback():
    """Policy: the primary (`yt_dlp`) is always preferred when present, even
    if the user's persisted setting still says `youtube_dl`. This is how we
    retire the deprecated extractor from the mainline path without forcing
    a settings migration."""
    assert choose_extractor_name(FALLBACK_EXTRACTOR, [PRIMARY_EXTRACTOR, FALLBACK_EXTRACTOR]) == PRIMARY_EXTRACTOR


def test_falls_back_to_primary_when_configured_missing():
    assert choose_extractor_name(FALLBACK_EXTRACTOR, [PRIMARY_EXTRACTOR]) == PRIMARY_EXTRACTOR


def test_returns_fallback_only_when_primary_missing():
    assert choose_extractor_name(FALLBACK_EXTRACTOR, [FALLBACK_EXTRACTOR]) == FALLBACK_EXTRACTOR


def test_returns_none_when_empty():
    assert choose_extractor_name(PRIMARY_EXTRACTOR, []) is None


def test_load_extractor_module_reports_version():
    fake_module = SimpleNamespace(version=SimpleNamespace(__version__="2026.03.17"))

    loaded = load_extractor_module(PRIMARY_EXTRACTOR, importer=lambda _: fake_module)

    assert loaded.name == PRIMARY_EXTRACTOR
    assert loaded.module is fake_module
    assert loaded.version == "2026.03.17"
