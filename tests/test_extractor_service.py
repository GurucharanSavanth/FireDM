"""Tests for firedm.extractor_adapter.ExtractorService.

The service owns the "which extractor is active right now" decision. These
tests use synthetic extractor modules so they never touch the network and
never depend on `yt_dlp` / `youtube_dl` being installed.
"""

from __future__ import annotations

from types import SimpleNamespace

from firedm.extractor_adapter import (
    FALLBACK_EXTRACTOR,
    PRIMARY_EXTRACTOR,
    ExtractorModule,
    ExtractorService,
)


def _module(name: str, version: str = "1.0.0") -> ExtractorModule:
    fake = SimpleNamespace(__name__=name)
    return ExtractorModule(name=name, module=fake, version=version)


def test_new_service_is_not_ready():
    svc = ExtractorService()
    assert svc.active_name() is None
    assert svc.active_module() is None
    assert svc.wait_until_ready(timeout=0.05) is False


def test_primary_load_becomes_active_immediately():
    svc = ExtractorService()
    svc.record_load(_module(PRIMARY_EXTRACTOR, "2026.03.17"))
    assert svc.active_name() == PRIMARY_EXTRACTOR
    assert svc.is_primary_active() is True
    assert svc.wait_until_ready(timeout=0.05) is True


def test_fallback_alone_becomes_active():
    svc = ExtractorService()
    svc.record_load(_module(FALLBACK_EXTRACTOR))
    assert svc.active_name() == FALLBACK_EXTRACTOR
    assert svc.is_primary_active() is False


def test_primary_overrides_fallback_regardless_of_load_order():
    """Fallback loads first (slow network, cached import, whatever). When the
    primary eventually loads, the service must promote it immediately —
    this is the guarantee that prevents the "last thread wins" race."""
    svc = ExtractorService()
    svc.record_load(_module(FALLBACK_EXTRACTOR))
    assert svc.active_name() == FALLBACK_EXTRACTOR
    svc.record_load(_module(PRIMARY_EXTRACTOR))
    assert svc.active_name() == PRIMARY_EXTRACTOR


def test_set_configured_does_not_downgrade_away_from_primary():
    """Even if the user has `active_video_extractor="youtube_dl"` persisted
    from a legacy install, the service refuses to downgrade the active
    extractor while the primary is loaded."""
    svc = ExtractorService()
    svc.record_load(_module(PRIMARY_EXTRACTOR))
    svc.record_load(_module(FALLBACK_EXTRACTOR))
    svc.set_configured(FALLBACK_EXTRACTOR)
    assert svc.active_name() == PRIMARY_EXTRACTOR


def test_snapshot_reports_both_engines():
    svc = ExtractorService()
    svc.record_load(_module(PRIMARY_EXTRACTOR, "2026.03.17"))
    svc.record_load(_module(FALLBACK_EXTRACTOR, "2021.12.17"))
    snap = svc.snapshot()
    assert snap["active"] == PRIMARY_EXTRACTOR
    assert snap["primary_loaded"] is True
    assert snap["fallback_loaded"] is True
    assert snap["versions"][PRIMARY_EXTRACTOR] == "2026.03.17"
    assert snap["versions"][FALLBACK_EXTRACTOR] == "2021.12.17"
