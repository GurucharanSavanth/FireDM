"""Policy regression: the deprecated extractor is never the default."""

from __future__ import annotations

from types import SimpleNamespace

from firedm.extractor_adapter import (
    FALLBACK_EXTRACTOR,
    PRIMARY_EXTRACTOR,
    ExtractorModule,
    ExtractorService,
    choose_extractor_name,
)


def test_choose_extractor_name_primary_first():
    # Even with the deprecated extractor named as "configured," policy
    # forces the primary when both are available.
    assert choose_extractor_name(FALLBACK_EXTRACTOR, [PRIMARY_EXTRACTOR, FALLBACK_EXTRACTOR]) == PRIMARY_EXTRACTOR


def test_service_never_returns_fallback_when_primary_ready():
    svc = ExtractorService()
    svc.record_load(ExtractorModule(name=PRIMARY_EXTRACTOR, module=SimpleNamespace(__name__=PRIMARY_EXTRACTOR)))
    svc.record_load(ExtractorModule(name=FALLBACK_EXTRACTOR, module=SimpleNamespace(__name__=FALLBACK_EXTRACTOR)))
    assert svc.active_name() == PRIMARY_EXTRACTOR
    # Attempt to force fallback (simulating legacy persisted user setting).
    svc.set_configured(FALLBACK_EXTRACTOR)
    assert svc.active_name() == PRIMARY_EXTRACTOR


def test_service_wait_is_bounded():
    svc = ExtractorService()
    assert svc.wait_until_ready(timeout=0.1) is False
