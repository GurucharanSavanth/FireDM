"""Tests for the deprecated-extractor fallback paths.

Policy:
    - If only the fallback (`youtube_dl`) loads, the service makes it
      active but logs the state clearly.
    - If neither loads, every extractor-dependent call fails fast with a
      structured error, never a silent hang.
"""

from __future__ import annotations

from types import SimpleNamespace

from firedm.extractor_adapter import (
    FALLBACK_EXTRACTOR,
    PRIMARY_EXTRACTOR,
    ExtractorModule,
    ExtractorService,
    choose_extractor_name,
)


def _module(name: str) -> ExtractorModule:
    return ExtractorModule(name=name, module=SimpleNamespace(__name__=name))


def test_only_fallback_loaded_becomes_active():
    svc = ExtractorService()
    svc.record_load(_module(FALLBACK_EXTRACTOR))
    assert svc.active_name() == FALLBACK_EXTRACTOR
    assert svc.is_primary_active() is False
    assert svc.wait_until_ready(timeout=0.1) is True


def test_primary_promotion_is_sticky_even_if_fallback_loads_after():
    """Once the primary is active, a subsequent fallback load must not
    demote it back to fallback."""
    svc = ExtractorService()
    svc.record_load(_module(PRIMARY_EXTRACTOR))
    svc.record_load(_module(FALLBACK_EXTRACTOR))
    assert svc.active_name() == PRIMARY_EXTRACTOR


def test_choose_extractor_name_returns_fallback_when_primary_absent():
    assert choose_extractor_name(FALLBACK_EXTRACTOR, [FALLBACK_EXTRACTOR]) == FALLBACK_EXTRACTOR


def test_choose_extractor_name_returns_none_when_nothing_loaded():
    assert choose_extractor_name(FALLBACK_EXTRACTOR, []) is None
    assert choose_extractor_name(None, []) is None


def test_no_engines_loaded_signals_not_ready():
    """A consumer that waits briefly for an extractor must get a
    deterministic False and proceed to emit its own fail event."""
    svc = ExtractorService()
    assert svc.wait_until_ready(timeout=0.1) is False
    assert svc.active_module() is None


def test_config_preference_cannot_override_policy_downward():
    """Even when `active_video_extractor` is pinned to the fallback via
    `set_configured`, the primary wins once both are loaded."""
    svc = ExtractorService()
    svc.record_load(_module(PRIMARY_EXTRACTOR))
    svc.record_load(_module(FALLBACK_EXTRACTOR))
    svc.set_configured(FALLBACK_EXTRACTOR)
    assert svc.active_name() == PRIMARY_EXTRACTOR


def test_configured_preference_honored_when_primary_unavailable():
    """If the primary never loaded, a user-pinned fallback preference is
    still respected (because it's the only option anyway)."""
    svc = ExtractorService()
    svc.record_load(_module(FALLBACK_EXTRACTOR))
    svc.set_configured(FALLBACK_EXTRACTOR)
    assert svc.active_name() == FALLBACK_EXTRACTOR
