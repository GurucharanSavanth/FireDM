from __future__ import annotations

from pathlib import Path

import pytest


def load_workflow():
    yaml = pytest.importorskip("yaml")
    workflow_path = Path(".github/workflows/draft-release.yml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    return payload, workflow_path.read_text(encoding="utf-8")


def test_workflow_yaml_parses_and_has_required_jobs():
    payload, _ = load_workflow()
    jobs = payload["jobs"]
    for job in ("resolve-build-code", "build-windows", "build-linux", "release"):
        assert job in jobs, f"missing job {job}"
    assert jobs["build-windows"]["runs-on"] == "windows-latest"
    assert jobs["build-linux"]["runs-on"] == "ubuntu-latest"
    assert jobs["release"]["runs-on"] == "ubuntu-latest"
    assert jobs["resolve-build-code"]["runs-on"] == "ubuntu-latest"


def test_workflow_inputs_include_cross_platform_toggles():
    payload, _ = load_workflow()
    triggers = payload.get("on") or payload.get(True)
    inputs = triggers["workflow_dispatch"]["inputs"]
    for key in (
        "channel",
        "arch",
        "build_id",
        "date",
        "include_windows",
        "include_linux",
        "publish_release",
        "draft",
        "prerelease",
    ):
        assert key in inputs, f"missing input {key}"


def test_workflow_share_one_build_code_via_resolver_outputs():
    payload, text = load_workflow()
    resolver = payload["jobs"]["resolve-build-code"]
    assert "outputs" in resolver
    outputs = resolver["outputs"]
    for key in ("build_code", "tag", "release_name", "channel"):
        assert key in outputs

    # Both build jobs depend on the resolver and consume its build_code output.
    assert "resolve-build-code" in payload["jobs"]["build-windows"]["needs"]
    assert "resolve-build-code" in payload["jobs"]["build-linux"]["needs"]
    assert "needs.resolve-build-code.outputs.build_code" in text


def test_workflow_release_job_gates_publish():
    payload, text = load_workflow()
    release = payload["jobs"]["release"]
    assert set(release["needs"]) == {"resolve-build-code", "build-windows", "build-linux"}
    # publish only when explicit input or tag push
    assert "inputs.publish_release" in text
    assert "GITHUB_REF_TYPE" in text
    assert "scripts/release/github_release.py" in text
    assert "merge_release_manifest.py" in text


def test_workflow_uploads_per_platform_artifacts():
    payload, text = load_workflow()
    assert "FireDM-Windows-${{ env.build_id }}" in text
    assert "FireDM-Linux-${{ needs.resolve-build-code.outputs.build_code }}" in text
    assert "FireDM_release_manifest_${{ env.build_id }}_windows.json" in text
    assert "FireDM_release_manifest_${{ needs.resolve-build-code.outputs.build_code }}_linux.json" in text


def test_workflow_push_triggers():
    payload, _ = load_workflow()
    triggers = payload.get("on") or payload.get(True)
    push = triggers.get("push", {})
    # branch push triggers draft release creation on main
    assert "main" in push.get("branches", [])
    # tag push still supported for explicit stable releases
    tag_pattern = push["tags"][0]
    assert tag_pattern.startswith("build-")
