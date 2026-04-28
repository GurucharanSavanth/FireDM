from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scripts" / "release"
sys.path.insert(0, str(SCRIPT_DIR))

import check_dependencies  # noqa: E402


def test_required_package_missing_is_reported(monkeypatch):
    real_import = importlib.import_module

    def fake_import(name: str):
        if name == "pycurl":
            raise ModuleNotFoundError("No module named 'pycurl'")
        return real_import(name)

    monkeypatch.setattr(check_dependencies.importlib, "import_module", fake_import)

    result = check_dependencies.check_import("pycurl", "pycurl", "runtime", True)

    assert result.status == "missing"
    assert result.required is True
    assert "pycurl" in result.detail


def test_optional_ffmpeg_missing_is_warning(monkeypatch):
    monkeypatch.setattr(
        check_dependencies,
        "collect_media_tool_health",
        lambda **kwargs: {
            "ffmpeg": {"usable": False, "path": "", "version": "", "failure": "not found"},
            "ffprobe": {"usable": False, "path": "", "version": "", "failure": "not found"},
        },
    )

    results = check_dependencies.check_media_tools()

    assert {item.name for item in results} == {"ffmpeg", "ffprobe"}
    assert all(item.status == "warning" for item in results)
    assert all(item.required is False for item in results)


def test_optional_deno_missing_is_warning(monkeypatch):
    monkeypatch.setattr(check_dependencies, "resolve_binary_path", lambda *args, **kwargs: "")

    results = check_dependencies.check_external_tools()

    assert {item.name for item in results} == {"deno"}
    assert results[0].status == "warning"
    assert results[0].required is False


def test_json_payload_has_summary(monkeypatch):
    monkeypatch.setattr(check_dependencies, "check_payload", lambda root: [])
    monkeypatch.setattr(check_dependencies, "check_external_tools", lambda: [])
    monkeypatch.setattr(
        check_dependencies,
        "check_media_tools",
        lambda: [check_dependencies.CheckResult("ffmpeg", "optional-external-tool", False, "warning")],
    )
    args = argparse.Namespace(arch="x64", channel="dev", build_id="20260427_V1", portable_root=None, skip_portable=True)

    payload = check_dependencies.collect_results(args)

    assert payload["schema"] == 1
    assert "checks" in payload
    assert "summary" in payload
    assert "ffmpeg" in payload["summary"]["warnings"]
