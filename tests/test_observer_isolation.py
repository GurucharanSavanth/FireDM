"""Regression test: ``Observable._notify`` must isolate per-callback failures.

Before the fix, ``_notify`` re-raised the first callback exception, which
aborted the iteration and bubbled out of every property write on
``ObservableDownloadItem`` / ``ObservableVideo``. A single broken view
subscriber could therefore block every other subscriber from seeing the
same change and crash arbitrary setters.
"""

from __future__ import annotations

from firedm.model import Observable


def test_notify_runs_all_callbacks_when_one_raises():
    seen: list[str] = []

    def boom(**_kwargs):
        raise RuntimeError("simulated broken subscriber")

    def ok_a(**kwargs):
        seen.append(f"a:{kwargs.get('progress')}")

    def ok_b(**kwargs):
        seen.append(f"b:{kwargs.get('progress')}")

    obs = Observable(observer_callbacks=[boom, ok_a, ok_b])

    # _notify must NOT raise even though `boom` does, and must continue to
    # invoke the remaining callbacks.
    obs._notify(uid="u-1", progress=50)

    assert seen == ["a:50", "b:50"]


def test_notify_does_not_swallow_when_no_callbacks_fail():
    received: list[dict] = []

    def collect(**kwargs):
        received.append(kwargs)

    obs = Observable(observer_callbacks=[collect])
    obs._notify(uid="u-2", status="downloading")

    assert received == [{"uid": "u-2", "status": "downloading"}]


def test_notify_continues_after_multiple_failures():
    survivors: list[str] = []

    def broken_one(**_kwargs):
        raise ValueError("first broken")

    def broken_two(**_kwargs):
        raise KeyError("second broken")

    def survivor(**kwargs):
        survivors.append(kwargs.get("name", ""))

    obs = Observable(observer_callbacks=[broken_one, survivor, broken_two, survivor])
    obs._notify(uid="u-3", name="x.mp4")

    # survivor invoked twice, both broken callbacks isolated
    assert survivors == ["x.mp4", "x.mp4"]
