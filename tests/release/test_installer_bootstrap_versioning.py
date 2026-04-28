from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows installer bootstrap tests require winreg")


def load_bootstrap():
    path = Path(__file__).resolve().parents[2] / "scripts" / "release" / "installer_bootstrap.py"
    spec = importlib.util.spec_from_file_location("installer_bootstrap_under_test_versioning", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_version_relation_upgrade_same_and_newer_installed():
    module = load_bootstrap()

    assert module.version_relation("1.0.0", "2.0.0") == "upgrade"
    assert module.version_relation("2.0.0", "2.0.0") == "same-version"
    assert module.version_relation("3.0.0", "2.0.0") == "newer-installed"


def test_version_relation_rejects_malformed_installed_version():
    module = load_bootstrap()

    with pytest.raises(ValueError, match="Malformed version"):
        module.version_relation("not-a-version", "2.0.0")


def test_parse_version_accepts_numeric_prefix_suffix():
    module = load_bootstrap()

    assert module.parse_version("2022.2.5-dev") == (2022, 2, 5)

