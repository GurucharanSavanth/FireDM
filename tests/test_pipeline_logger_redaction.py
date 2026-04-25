"""Regression tests for credential-bearing URL redaction in pipeline logs."""

from __future__ import annotations

from firedm.pipeline_logger import pipeline_event, redact_text_for_log, redact_url_for_log


def test_redact_url_for_log_keeps_host_path_and_redacts_signed_query_params():
    url = (
        "https://media.example.test/hls/master.m3u8?"
        "token=abc123&Signature=deadbeef&Expires=9999999999&"
        "AWSAccessKeyId=AKIA_TEST&quality=720p"
    )

    redacted = redact_url_for_log(url)

    assert redacted.startswith("https://media.example.test/hls/master.m3u8?")
    assert "quality=720p" in redacted
    assert "token=REDACTED" in redacted
    assert "Signature=REDACTED" in redacted
    assert "Expires=REDACTED" in redacted
    assert "AWSAccessKeyId=REDACTED" in redacted
    assert "abc123" not in redacted
    assert "deadbeef" not in redacted
    assert "9999999999" not in redacted
    assert "AKIA_TEST" not in redacted


def test_redact_text_for_log_redacts_urls_inside_exception_messages():
    msg = (
        "failed fetching https://cdn.example.test/video.ts?"
        "access_token=secret&part=3, retrying"
    )

    redacted = redact_text_for_log(msg)

    assert "https://cdn.example.test/video.ts" in redacted
    assert "part=3" in redacted
    assert "access_token=REDACTED" in redacted
    assert "secret" not in redacted


def test_pipeline_event_redacts_url_fields_and_detail(monkeypatch):
    captured: list[str] = []

    def fake_log(message, **_kwargs):
        captured.append(message)

    monkeypatch.setattr("firedm.utils.log", fake_log)

    signed = "https://cdn.example.test/master.m3u8?Policy=p1&X-Amz-Signature=sig&safe=value"
    pipeline_event("hls_url_refresh", "fail", detail=f"parser failed for {signed}", m3u8_url=signed)

    assert captured
    rendered = captured[0]
    assert "https://cdn.example.test/master.m3u8" in rendered
    assert "safe=value" in rendered
    assert "Policy=REDACTED" in rendered
    assert "X-Amz-Signature=REDACTED" in rendered
    assert "p1" not in rendered
    assert "sig" not in rendered
