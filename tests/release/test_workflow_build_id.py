from __future__ import annotations

from pathlib import Path

import pytest


def test_draft_release_workflow_build_id_inputs_and_triggers():
    yaml = pytest.importorskip("yaml")
    workflow_path = Path(".github/workflows/draft-release.yml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    triggers = payload.get("on") or payload.get(True)
    dispatch_inputs = triggers["workflow_dispatch"]["inputs"]

    for key in ("channel", "arch", "build_id", "date", "publish_release", "draft", "prerelease"):
        assert key in dispatch_inputs

    assert "branches" not in triggers.get("push", {})
    assert triggers["push"]["tags"] == ["build-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_V*"]
    text = workflow_path.read_text(encoding="utf-8")
    assert "scripts\\release\\build_windows.py" in text
    assert "scripts\\release\\github_release.py" in text
    assert "publish_release" in text
    assert "FireDM_release_manifest_${{ env.build_id }}.json" in text


def test_windows_build_script_uses_build_id_release_names():
    script = Path("scripts/windows-build.ps1").read_text(encoding="utf-8")

    assert "[string]$BuildId" in script
    assert "[string]$BuildDate" in script
    assert "scripts\\release\\build_id.py" in script
    assert "FireDM-$BuildId-windows-x64" in script
    assert "SHA256SUMS_$BuildId.txt" in script
    assert "FireDM_release_manifest_$BuildId.json" in script
    assert "FireDM_release_notes_$BuildId.md" in script
    assert "build-metadata.json" in script
    assert "$BuildInfo.tag" in script
    assert "FireDM-$Version-windows-x64" not in script
