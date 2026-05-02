"""Security regression suite for the 2026-04-26 hostile audit pass.

Each test corresponds to one finding in `artifacts/security/audit_2026-04-26.md`.
The tests assert the *post-patch* behavior: every test fails on the unpatched
codebase and passes after the matching fix in `firedm/`.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# F-CRIT-1: get_pkg_version() must NOT exec arbitrary version.py contents
# ---------------------------------------------------------------------------


def test_get_pkg_version_does_not_exec_version_py(tmp_path, monkeypatch):
    """A package's version.py must be parsed, not executed.

    Any actor able to write to a third-party site-packages folder previously
    achieved ACE inside the FireDM process the next time
    `controller.check_for_update` ran. The fix replaces ``exec(txt, ns)`` with
    a literal AST extraction of ``__version__``.
    """
    pkg_root = tmp_path / "site_pkgs"
    pkg_dir = pkg_root / "evilpkg"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "__init__.py").write_text("")

    marker = tmp_path / "ACE_MARKER.txt"
    (pkg_dir / "version.py").write_text(
        "__version__ = '0.0.1'\n"
        "import os\n"
        f"open(r'{marker}', 'w').write('PWNED')\n"
    )

    monkeypatch.syspath_prepend(str(pkg_root))

    from firedm.utils import get_pkg_version

    version = get_pkg_version("evilpkg")
    assert version == "0.0.1"
    assert not marker.exists(), (
        "get_pkg_version executed arbitrary Python from version.py "
        "(ACE regression -- F-CRIT-1)"
    )


# ---------------------------------------------------------------------------
# F-CRIT-2: pycurl-backed download() must reject non-HTTP schemes
# ---------------------------------------------------------------------------


def test_download_refuses_file_scheme(tmp_path):
    """`file://` URLs must not be readable through utils.download().

    libcurl is built with file/ftp/dict/gopher/smb/telnet/tftp protocol
    support; without an explicit allowlist any of those schemes can be
    smuggled into FireDM's download/get_headers callers (CRITICAL info
    disclosure / SSRF).
    """
    sentinel = tmp_path / "leak_target.txt"
    sentinel.write_text("SECRET_DATA")

    posix = str(sentinel).replace(os.sep, "/")
    file_url = "file:///" + urllib.parse.quote(posix.lstrip("/"))

    from firedm import config
    config.log_level = 0
    from firedm.utils import download

    data = download(file_url, decode=True, verbose=False)
    assert "SECRET_DATA" not in (data or ""), (
        "download() returned local file contents via file:// URL "
        "(SSRF regression -- F-CRIT-2)"
    )


def test_download_refuses_ftp_scheme(monkeypatch):
    """Non-HTTP(S) schemes must be rejected before pycurl is invoked."""
    from firedm import config
    config.log_level = 0
    from firedm.utils import download

    # Use a deliberately invalid host so we never actually contact a server.
    data = download("ftp://invalid-host-firedm-test/secret", decode=True, verbose=False)
    assert data is None, (
        "download() forwarded an ftp:// URL to libcurl "
        "(SSRF regression -- F-CRIT-2)"
    )


# ---------------------------------------------------------------------------
# F-CRIT-3: setting.cfg loader must drop unknown / unsafe keys
# ---------------------------------------------------------------------------


def test_load_setting_drops_unknown_keys(tmp_path, monkeypatch):
    """`load_setting()` must not turn arbitrary JSON keys into config attrs.

    The unpatched loader did `config.__dict__.update(settings)`. A poisoned
    setting.cfg could inject NEW attributes (e.g. `log_popup_callback`,
    `APP_URL`) and override trusted constants. The fix filters incoming
    keys against `config.settings_keys`.
    """
    from firedm import config, setting

    sentinel_attr = "__hostile_injected_attr__"
    if hasattr(config, sentinel_attr):
        delattr(config, sentinel_attr)

    monkeypatch.setattr(config, "sett_folder", str(tmp_path))
    payload = {
        sentinel_attr: "PWNED",
        "APP_URL": "https://attacker.example/firedm",
        "ffmpeg_actual_path": r"C:\Trojan\ffmpeg.exe",
    }
    (tmp_path / "setting.cfg").write_text(json.dumps(payload))

    original_app_url = config.APP_URL
    setting.load_setting()

    assert not hasattr(config, sentinel_attr) or getattr(config, sentinel_attr) != "PWNED", (
        "load_setting injected an unknown attribute into config "
        "(schema-poisoning regression -- F-CRIT-3)"
    )
    assert original_app_url == config.APP_URL, (
        "load_setting overrode a trusted constant via setting.cfg "
        "(schema-poisoning regression -- F-CRIT-3)"
    )


def test_load_setting_keeps_legitimate_keys(tmp_path, monkeypatch):
    """The schema filter must keep keys declared in `settings_keys`."""
    from firedm import config, setting

    monkeypatch.setattr(config, "sett_folder", str(tmp_path))
    payload = {"max_concurrent_downloads": 7, "auto_rename": True}
    (tmp_path / "setting.cfg").write_text(json.dumps(payload))

    original_concurrent = config.max_concurrent_downloads
    setting.load_setting()
    assert config.max_concurrent_downloads == 7
    assert config.auto_rename is True

    # restore
    config.max_concurrent_downloads = original_concurrent


# ---------------------------------------------------------------------------
# F-HIGH-4: load_d_map() must not restore on_completion_command from disk
# ---------------------------------------------------------------------------


def test_load_d_map_strips_on_completion_command(tmp_path, monkeypatch):
    """Crafted downloads.dat must not be allowed to seed an arbitrary command.

    `Controller._post_download()` runs `d.on_completion_command` via
    `run_command()` with no confirmation. A hostile downloads.dat that sets
    on_completion_command for an item the user later resumes is ACE.
    """
    from firedm import config, setting

    monkeypatch.setattr(config, "sett_folder", str(tmp_path))

    poisoned = {
        "uid_evil": {
            "_name": "loot.bin",
            "folder": str(tmp_path),
            "_status": config.Status.cancelled,
            "on_completion_command": "calc.exe",
            "shutdown_pc": True,
        }
    }
    (tmp_path / "downloads.dat").write_text(json.dumps(poisoned))
    (tmp_path / "thumbnails.dat").write_text("{}")

    d_map = setting.load_d_map()
    assert "uid_evil" in d_map
    item = d_map["uid_evil"]
    assert item.on_completion_command in ("", None), (
        "load_d_map() restored on_completion_command from disk "
        "(ACE regression -- F-HIGH-4)"
    )
    assert item.shutdown_pc is False, (
        "load_d_map() restored shutdown_pc from disk "
        "(privilege regression -- F-HIGH-4)"
    )


# ---------------------------------------------------------------------------
# F-HIGH-5: download_thumbnail() must validate the URL scheme
# ---------------------------------------------------------------------------


def test_download_thumbnail_refuses_file_scheme(tmp_path):
    """Hostile metadata cannot leak local files via ``thumbnail_url='file://...'``.

    Hostile yt-dlp metadata used to be able to set thumbnail_url to
    ``file:///c:/users/victim/secret.txt``; FireDM would then read it and
    write the contents next to the video file as ``<video>.png``.
    """
    sentinel = tmp_path / "thumb_secret.txt"
    sentinel.write_text("THUMB_LEAK")

    posix = str(sentinel).replace(os.sep, "/")
    file_url = "file:///" + urllib.parse.quote(posix.lstrip("/"))

    from firedm import config
    config.log_level = 0
    from firedm.config import Status
    from firedm.controller import download_thumbnail
    from firedm.model import ObservableDownloadItem

    target_dir = tmp_path / "downloads"
    target_dir.mkdir()
    d = ObservableDownloadItem()
    d.folder = str(target_dir)
    d.name = "victim_video.mp4"
    d._status = Status.completed
    d.thumbnail_url = file_url
    d.url = "https://example.com/victim_video.mp4"
    d.eff_url = d.url

    download_thumbnail(d)

    png_path = os.path.splitext(d.target_file)[0] + ".png"
    leaked = ""
    if os.path.isfile(png_path):
        with open(png_path, "rb") as fh:
            leaked = fh.read().decode("utf-8", errors="ignore")
    assert "THUMB_LEAK" not in leaked, (
        "download_thumbnail() copied local file contents via file:// URL "
        "(SSRF/info-disclosure regression -- F-HIGH-5)"
    )


# ---------------------------------------------------------------------------
# F-HIGH-6: load_user_extractors() must not exec untrusted .py without opt-in
# ---------------------------------------------------------------------------


def test_load_user_extractors_requires_explicit_opt_in(tmp_path, monkeypatch):
    """A `.py` dropped into the extractors folder must not auto-execute.

    The previous behavior auto-imported every `.py` in
    `<sett_folder>/extractors/` on startup. Anyone able to write to the
    user's settings dir got ACE. The fix gates the loader behind an
    explicit `config.allow_user_extractors=True` flag (default False).
    """
    import firedm.video as video_mod
    from firedm import config

    extractors_folder = tmp_path / "extractors"
    extractors_folder.mkdir()
    marker = tmp_path / "EXTRACTOR_ACE_MARKER.txt"
    (extractors_folder / "evil.py").write_text(
        "import os\n"
        f"open(r'{marker}', 'w').write('EXTRACTOR_PWNED')\n"
    )

    monkeypatch.setattr(config, "sett_folder", str(tmp_path))
    monkeypatch.setattr(config, "allow_user_extractors", False, raising=False)

    # Pass a stub engine so we can call the loader without a real extractor.
    class _StubExtractor:
        class InfoExtractor:
            pass

        class _ALL_CLASSES_HOLDER:
            _ALL_CLASSES = []

        extractor = _ALL_CLASSES_HOLDER()

    video_mod.load_user_extractors(engine=_StubExtractor())
    assert not marker.exists(), (
        "load_user_extractors() executed an untrusted .py without opt-in "
        "(ACE regression -- F-HIGH-6)"
    )
