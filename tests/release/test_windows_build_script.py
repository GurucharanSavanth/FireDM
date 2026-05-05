from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT_SCRIPT = REPO_ROOT / "windows-build.ps1"
WRAPPER_SCRIPT = REPO_ROOT / "scripts" / "windows-build.ps1"
RELEASE_DIR = REPO_ROOT / "release"


def powershell() -> str:
    exe = shutil.which("powershell")
    if not exe:
        pytest.skip("PowerShell is required for windows-build.ps1 tests")
    return exe


def run_root_script(*args: str, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            powershell(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT_SCRIPT),
            *args,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def test_root_windows_build_script_parses_with_powershell_parser():
    command = (
        "$errors = $null; "
        "$null = [System.Management.Automation.PSParser]::Tokenize("
        "(Get-Content -Raw .\\windows-build.ps1), [ref]$errors"
        "); "
        "if ($errors) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }"
    )
    result = subprocess.run(
        [powershell(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout


def test_root_script_declares_canonical_parameters_and_safe_cleanup_terms():
    text = ROOT_SCRIPT.read_text(encoding="utf-8")

    for token in (
        '[ValidateSet("Debug", "Release")]',
        '[ValidateSet("OneFolder", "OneFile", "PortableZip")]',
        '[ValidateSet("Auto", "PyInstaller", "Nuitka")]',
        "[switch]$Clean",
        "[switch]$NoClean",
        "[switch]$DryRun",
        "[switch]$SkipTests",
        "[switch]$SkipSmoke",
        "[string]$OutputDir",
        "[string]$Version",
    ):
        assert token in text

    assert "Remove-Item -LiteralPath" in text
    assert "Test-Path -LiteralPath $item.path" in text
    assert "Test-UnderRepo" in text
    assert 'Join-Path (Join-Path $script:RepoRoot "build") "windows-build\\staging"' in text
    assert 'Join-Path $script:ReleaseRoot "staging"' not in text
    assert "explicitly matched generated Windows release artifact under root release" in text
    assert "FireDM-.+-windows-(x64|x86|arm64)" in text
    assert 'Native tools such as PyInstaller write normal progress to stderr' in text
    assert "tests\\test_frontend_common_adapters.py" in text
    assert "tests\\test_plugin_manifest.py" in text
    assert "Invoke-PythonDistributionBuild" in text
    assert '"--outdir", $script:ReleaseRoot' in text
    assert "twine check" in text
    assert ".\\firedm\\plugins\\policy.py" in text
    assert "frontend_qt" not in text
    assert "PySide6" not in text
    assert "Get-PluginManifestSection" in text
    assert "git clean" not in text
    assert "Invoke-Expression" not in text


def test_scripts_windows_build_is_thin_wrapper_to_root_script():
    text = WRAPPER_SCRIPT.read_text(encoding="utf-8")

    assert "windows-build.ps1" in text
    assert "$forward" in text
    assert "build_windows.py" not in text
    assert "Remove-Item" not in text


def test_release_runtime_sources_are_git_allowlisted():
    text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

    for token in (
        "!windows-build.ps1",
        "!scripts/windows-build.ps1",
        "!firedm/frontend_common/",
        "!firedm/frontend_common/*.py",
    ):
        assert token in text
    assert "frontend_qt" not in text
    assert "firedm-qt.py" not in text


def test_dry_run_clean_writes_release_contract_without_deleting_sentinel():
    sentinel = REPO_ROOT / "build" / "codex-dry-run-sentinel.tmp"
    sentinel.parent.mkdir(exist_ok=True)
    sentinel.write_text("dry-run sentinel", encoding="utf-8")

    try:
        result = run_root_script("-DryRun", "-Clean", "-SkipTests", "-SkipSmoke")
        assert result.returncode == 0, result.stderr + result.stdout
        assert sentinel.exists()
    finally:
        sentinel.unlink(missing_ok=True)

    manifest = json.loads((RELEASE_DIR / "manifest.json").read_text(encoding="utf-8-sig"))
    checksums = (RELEASE_DIR / "checksums.sha256").read_text(encoding="ascii")
    changelog = (RELEASE_DIR / "CHANGELOG-COMPILED.md").read_text(encoding="utf-8-sig")

    for key in (
        "app_name",
        "app_version",
        "build_id",
        "build_time_utc",
        "repo_root",
        "git_present",
        "git_branch",
        "git_commit",
        "dirty_tree",
        "python_version",
        "powershell_version",
        "os_version",
        "gui_backend",
        "gui_entry_point",
        "build_backend",
        "build_kind",
        "build_mode",
        "entry_point",
        "spec_file",
        "included_dependencies",
        "included_plugins",
        "blocked_plugins",
        "planned_plugins",
        "plugin_discovery_warnings",
        "validation_commands",
        "validation_results",
        "cleanup_actions",
        "changelog_sources",
        "release_artifacts",
        "release_files",
        "sha256_hashes",
        "warnings",
        "blocked_items",
    ):
        assert key in manifest

    assert manifest["app_name"] == "FireDM"
    assert manifest["build_backend"] == "PyInstaller"
    assert manifest["build_kind"] == "OneFolder"
    assert manifest["compatibility"]["root_windows_build_ps1"] == "canonical"
    assert manifest["compatibility"]["scripts_windows_build_ps1"] == "thin wrapper"
    assert any(action["path"] == "build" for action in manifest["cleanup_actions"])
    assert any(artifact["path"] == "plugins-manifest.json" for artifact in manifest["release_artifacts"])
    assert any(item["code"] == "python-package-dry-run" for item in manifest["blocked_items"])
    assert (RELEASE_DIR / "plugins-manifest.json").exists()
    assert (RELEASE_DIR / "plugins-manifest.txt").exists()
    assert manifest["gui_backend"] == "tkinter"
    assert manifest["gui_entry_point"] == "firedm.py"
    assert "checksums.sha256" not in checksums
    assert checksums.strip()
    assert "validation_status" in changelog


def test_wrapper_accepts_legacy_arguments_in_dry_run():
    result = subprocess.run(
        [
            powershell(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(WRAPPER_SCRIPT),
            "-DryRun",
            "-SkipTests",
            "-SkipSmoke",
            "-Channel",
            "dev",
            "-Arch",
            "x64",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
