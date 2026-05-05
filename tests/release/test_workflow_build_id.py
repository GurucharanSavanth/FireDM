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

    # push to main is now a trigger for rolling draft releases
    assert "main" in triggers.get("push", {}).get("branches", [])
    assert triggers["push"]["tags"] == ["build-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_V*"]
    text = workflow_path.read_text(encoding="utf-8")
    assert "scripts\\release\\build_windows.py" in text
    github_release_paths = ("scripts\\release\\github_release.py", "scripts/release/github_release.py")
    assert any(path in text for path in github_release_paths)
    assert "scripts/release/check_dependencies.py" in text
    assert "dependency-status_${{ env.build_id }}.json" in text
    assert "payload.zip" in text
    assert "publish_release" in text
    assert "FireDM_release_manifest_${{ env.build_id }}.json" in text


def test_windows_build_script_contract_is_root_canonical_with_wrapper():
    root_script = Path("windows-build.ps1").read_text(encoding="utf-8")
    wrapper = Path("scripts/windows-build.ps1").read_text(encoding="utf-8")

    assert "[string]$BuildId" in root_script
    assert "[string]$BuildDate" in root_script
    assert "[string]$Channel" in root_script
    assert '[ValidateSet("x64", "x86", "arm64")]' in root_script
    assert "[switch]$PayloadOnly" in root_script
    assert "[switch]$ValidateOnly" in root_script
    assert "[switch]$InstallLocalDeps" in root_script
    assert "CHANGELOG-COMPILED.md" in root_script
    assert "manifest.json" in root_script
    assert "checksums.sha256" in root_script
    assert "build.log" in root_script
    assert "does not publish GitHub releases" in root_script
    assert "Release output: $script:ReleaseRoot" in root_script
    assert "FireDM-$Version-windows-x64" not in root_script

    assert "$forward" in wrapper
    assert "build_windows.py" not in wrapper
