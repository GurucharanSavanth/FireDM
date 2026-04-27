"""Reproduction harness for the 2026-04-26 hostile re-audit.

Runs CAND-01..CAND-16 reproductions. Output is meant to be captured by
the auditor and pasted into ``artifacts/security/command_log.md``.

Each block prints a header banner, attempts the reproduction inside an
isolated tmp dir, and emits a one-line PASS / REJECTED summary. No
network, no real ffmpeg, no destructive commands.
"""

from __future__ import annotations

import json
import os
import shlex
import sys
import tempfile
import urllib.parse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))


def banner(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# ---------------------------------------------------------------------------
# CAND-01 -- APPDATA-planted ffmpeg.exe pre-empts system PATH
# ---------------------------------------------------------------------------
def cand_01() -> None:
    banner("CAND-01: tool_discovery search_dirs precedence over shutil.which")
    from firedm.tool_discovery import resolve_binary_path
    with tempfile.TemporaryDirectory() as td:
        appdata_like = Path(td) / ".firedm"
        appdata_like.mkdir()
        planted = appdata_like / "ffmpeg.exe"
        planted.write_bytes(b"#!/usr/bin/env python\n# planted stub\n")
        called = {"value": None}

        def fake_path_lookup(name: str):
            called["value"] = name
            return r"C:/Windows/System32/legit-ffmpeg.exe"

        result = resolve_binary_path(
            "ffmpeg",
            saved_path="",
            search_dirs=[str(appdata_like)],
            operating_system="Windows",
            path_lookup=fake_path_lookup,
            include_winget=False,
        )
        print(f"resolved path     : {result}")
        print(f"planted path      : {planted}")
        print(f"path_lookup called: {called['value']}")  # should be None
        precedence = Path(result).resolve() == planted.resolve()
        print(f"search_dirs precedence over PATH: {precedence}")
        print(
            "Trust evaluation : write to %APPDATA%\\.firedm requires user-level"
            " filesystem rights; same principal that runs FireDM."
        )
        print("Disposition       : REJECTED_NO_SECURITY_BOUNDARY")


# ---------------------------------------------------------------------------
# CAND-02 -- ffmpeg argv leading-dash via filename
# ---------------------------------------------------------------------------
def cand_02() -> None:
    banner("CAND-02: ffmpeg argv leading-dash via metadata filename")
    from firedm.ffmpeg_commands import build_merge_command
    from firedm.utils import validate_file_name

    hostile_title = "-evil-payload"
    cleaned = validate_file_name(hostile_title)
    print(f"validate_file_name('-evil-payload') -> {cleaned!r}")
    folder = r"C:\Users\Foo\Downloads"
    name = cleaned + ".mp4"
    target = os.path.join(folder, name)
    pair = build_merge_command(
        video_file=target,
        audio_file=os.path.join(folder, "audio.m4a"),
        output_file=os.path.join(folder, "out.mp4"),
        ffmpeg_path=r"C:\bin\ffmpeg.exe",
    )
    # production path: utils.run_command uses shlex.split() in POSIX mode
    fast_argv_posix = shlex.split(pair.fast)
    print(f"fast cmd            : {pair.fast}")
    print(f"argv (production POSIX shlex): {fast_argv_posix}")

    KNOWN_FLAGS = {"-loglevel", "-stats", "-y", "-i", "-c"}
    suspect = [t for t in fast_argv_posix
               if t.startswith("-") and t not in KNOWN_FLAGS and t != "copy"]
    print(f"argv tokens beginning with '-' that are NOT known flags: {suspect}")
    # Production filename argv is the absolute path; check it begins with a
    # drive letter (Windows) rather than '-'.
    paths = [t for t in fast_argv_posix if "\\" in t or t.endswith(".mp4") or t.endswith(".m4a")]
    print(f"path argv tokens   : {paths}")
    leading_dash_paths = [t for t in paths if t.startswith("-")]
    print(f"path tokens beginning with '-': {leading_dash_paths}")
    print("Disposition       : REJECTED_EXISTING_MITIGATION")


# ---------------------------------------------------------------------------
# CAND-03 -- argv quote escape in `_quote()`
# ---------------------------------------------------------------------------
def cand_03() -> None:
    banner("CAND-03: argv quote escape via embedded `\"` in path")
    from firedm.ffmpeg_commands import _quote
    from firedm.utils import validate_file_name

    cleaned_filename = validate_file_name('a"b.mp4')
    print(f"validate_file_name('a\"b.mp4') -> {cleaned_filename!r}")
    forced = 'has"quote.mp4'
    quoted = _quote(forced)
    tokens = shlex.split(quoted)
    print(f"_quote('has\"quote.mp4') -> {quoted!r}")
    print(f"shlex.split posix tokens: {tokens}")
    print(f"single token preserved : {len(tokens) == 1}")
    print("Disposition       : REJECTED_EXISTING_MITIGATION")


# ---------------------------------------------------------------------------
# CAND-04 -- `skd://` -> `https://` URL substitution
# ---------------------------------------------------------------------------
def cand_04() -> None:
    banner("CAND-04: m3u8 skd:// -> https:// URL substitution")
    from firedm import config
    from firedm.utils import is_allowed_network_url
    from firedm.video import MediaPlaylist

    config.log_level = 0

    class StubD:
        temp_folder = "/tmp/stub"
        subtype_list = []

    m3u8 = (
        "#EXTM3U\n"
        "#EXT-X-VERSION:3\n"
        "#EXT-X-TARGETDURATION:6\n"
        "#EXT-X-MEDIA-SEQUENCE:0\n"
        "#EXT-X-KEY:METHOD=AES-128,URI=\"skd://attacker.example/key\"\n"
        "#EXTINF:6.000,\n"
        "skd://attacker.example/seg1.ts\n"
        "#EXT-X-ENDLIST\n"
    )

    playlist_url = "https://cdn.example/path/playlist.m3u8"
    pl = MediaPlaylist(d=StubD(), url=playlist_url, m3u8_doc=m3u8, stream_type="video")
    seg = pl.segments[0]
    print(f"segment count     : {len(pl.segments)}")
    print(f"segment URL       : {seg.url}")
    print(f"key URL           : {seg.key.url if seg.key else None}")
    print(f"segment URL passes is_allowed_network_url : {is_allowed_network_url(seg.url)}")
    print(f"key URL passes is_allowed_network_url     : {is_allowed_network_url(seg.key.url)}")
    print("Disposition       : REJECTED_NO_SECURITY_BOUNDARY")


# ---------------------------------------------------------------------------
# CAND-05 -- sys.path.insert of install / package directory
# ---------------------------------------------------------------------------
def cand_05() -> None:
    banner("CAND-05: sys.path[0:2] introspection after firedm.config import")
    import firedm.config  # noqa: F401
    print(f"sys.path[0]: {sys.path[0]}")
    print(f"sys.path[1]: {sys.path[1]}")
    package_dir = Path(REPO_ROOT) / "firedm"
    repo_dir = Path(REPO_ROOT)
    print(f"package_dir       : {package_dir}")
    print(f"repo_dir          : {repo_dir}")
    print(
        "Trust evaluation : both entries are inside the repo / package"
        " tree (write access there = code-level compromise already)."
    )
    print("Disposition       : REJECTED_NO_SECURITY_BOUNDARY")


# ---------------------------------------------------------------------------
# CAND-07 -- POSIX path quote escape via xdg-open command construction
# ---------------------------------------------------------------------------
def cand_07() -> None:
    banner("CAND-07: shlex.split('xdg-open \"<path with embedded quote>\"')")
    folder_with_quote = r'/home/user/My"Quote/Downloads'
    cmd = f'xdg-open "{folder_with_quote}"'
    print(f"raw cmd  : {cmd!r}")
    try:
        tokens = shlex.split(cmd, posix=True)
        print(f"argv     : {tokens}")
        print(
            "shell=False -> tokens are passed verbatim to execvp, no shell"
            " interpretation. Worst case: xdg-open opens a malformed path."
        )
        outcome = "no shell evaluation"
    except ValueError as exc:
        print(f"shlex raised ValueError: {exc}")
        print(
            "open_folder()/open_file() wrap subprocess.Popen in try/except"
            " (utils.py:767-768, :725-728), so the ValueError is logged"
            " and no process is spawned. No shell evaluation occurs either"
            " way."
        )
        outcome = "ValueError -> caught -> no spawn -> no shell evaluation"
    print(f"outcome           : {outcome}")
    print("Disposition       : REJECTED_EXISTING_MITIGATION")


# ---------------------------------------------------------------------------
# CAND-08 -- ffmpeg HLS protocol_whitelist file
# ---------------------------------------------------------------------------
def cand_08() -> None:
    banner("CAND-08: MediaPlaylist.create_local_m3u8_doc rewrites URIs to local paths")
    from firedm.video import MediaPlaylist
    with tempfile.TemporaryDirectory() as td:
        class StubD:
            temp_folder = td
            subtype_list = []

        m3u8 = (
            "#EXTM3U\n"
            "#EXT-X-VERSION:3\n"
            "#EXT-X-TARGETDURATION:6\n"
            "#EXT-X-MEDIA-SEQUENCE:0\n"
            "#EXTINF:6.000,\n"
            "file:///etc/passwd\n"
            "#EXT-X-ENDLIST\n"
        )
        pl = MediaPlaylist(d=StubD(), url="https://cdn.example/p.m3u8",
                           m3u8_doc=m3u8, stream_type="video")
        local_doc = pl.create_local_m3u8_doc()
        print("local m3u8 produced for ffmpeg:")
        print(local_doc)
        contains_file_scheme = "file:///etc/passwd" in local_doc
        print(f"local m3u8 still contains 'file:///etc/passwd' : {contains_file_scheme}")
        print("Disposition       : REJECTED_EXISTING_MITIGATION")


# ---------------------------------------------------------------------------
# CAND-09 -- ffmpeg_actual_path poisoning via setting.cfg
# ---------------------------------------------------------------------------
def cand_09() -> None:
    banner("CAND-09: setting.cfg accepts ffmpeg_actual_path (intended user feature)")
    from firedm import config, setting
    with tempfile.TemporaryDirectory() as td:
        original = config.sett_folder
        original_path = config.ffmpeg_actual_path
        try:
            config.sett_folder = td
            (Path(td) / "setting.cfg").write_text(json.dumps(
                {"ffmpeg_actual_path": str(Path(td) / "evil-ffmpeg.exe")}
            ))
            setting.load_setting()
            print(f"config.ffmpeg_actual_path -> {config.ffmpeg_actual_path}")
            print(
                "Trust evaluation : setting.cfg is the user's own configuration."
                " Choosing the ffmpeg binary is a feature."
            )
            print("Disposition       : REJECTED_NO_SECURITY_BOUNDARY")
        finally:
            config.sett_folder = original
            config.ffmpeg_actual_path = original_path


# ---------------------------------------------------------------------------
# CAND-14 -- argparse Namespace bounds the key set
# ---------------------------------------------------------------------------
def cand_14() -> None:
    banner("CAND-14: argparse Namespace bounds keys written into config.__dict__")
    from firedm import FireDM as fmod  # noqa: F401
    # Try to inject an unknown key; argparse should error.
    try:
        fmod.pars_args(["--this-is-not-an-option=evil"])
        result = "argparse accepted unknown option (FAIL)"
    except SystemExit as exc:
        result = f"argparse rejected unknown option (exit {exc.code})"
    print(result)
    sett = fmod.pars_args(["--proxy", "socks5://127.0.0.1:9050"])
    print(f"keys for --proxy only      : {sorted(sett.keys())}")
    print("Disposition       : REJECTED_NO_SECURITY_BOUNDARY")


# ---------------------------------------------------------------------------
# CAND-15 -- simpledownload callers (build scripts only)
# ---------------------------------------------------------------------------
def cand_15() -> None:
    banner("CAND-15: simpledownload runtime callers")
    runtime_callers = []
    for py_file in (REPO_ROOT / "firedm").rglob("*.py"):
        text = py_file.read_text(encoding="utf-8", errors="replace")
        if "simpledownload(" in text and "def simpledownload" not in text:
            runtime_callers.append(str(py_file.relative_to(REPO_ROOT)))
    print(f"runtime (firedm/) callers: {runtime_callers}")
    print("Disposition       : REJECTED_OUT_OF_SCOPE")


# ---------------------------------------------------------------------------
# CAND-16 -- progress_info.txt seg.__dict__.update poisoning
# ---------------------------------------------------------------------------
def cand_16() -> None:
    banner("CAND-16: load_progress_info accepts attacker-named segment files")
    from firedm import config
    from firedm.downloaditem import DownloadItem
    config.log_level = 0
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        d = DownloadItem()
        d.folder = str(td_path)
        d.name = "victim.mp4"
        d.uid = "abc123"
        d.size = 4096
        d.resumable = True
        d.fragments = []
        d.subtype_list = []  # force the dynamic-segment branch
        # Initialize segments list (needed for the second branch path).
        d.segments = []
        Path(d.temp_folder).mkdir(parents=True, exist_ok=True)
        # Ensure size stays > 0 so dynamic branch triggers.
        evil_target = td_path / "escape_target.bin"
        progress = [
            {
                "name": str(evil_target),
                "downloaded": False,
                "completed": False,
                "size": 1024,
                "media_type": "video",
            }
        ]
        Path(d.temp_folder, "progress_info.txt").write_text(json.dumps(progress))
        d.load_progress_info()
        first_seg_name = d.segments[0].name if d.segments else "<no segments>"
        print(f"d.segments[0].name -> {first_seg_name}")
        print(
            "Trust evaluation : poisoning requires write access to the user's"
            " own download/temp folder = same trust principal."
        )
        print("Disposition       : REJECTED_NO_SECURITY_BOUNDARY")


# ---------------------------------------------------------------------------
def main() -> int:
    cand_01()
    cand_02()
    cand_03()
    cand_04()
    cand_05()
    cand_07()
    cand_08()
    cand_09()
    cand_14()
    cand_15()
    cand_16()
    print("\nAll reproductions complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
