# FireDM Hostile Audit — Command Log

All commands are recorded inline. Working directory is the FireDM repo
local root unless otherwise noted.

## CMD-001: Resolve LOCAL_ROOT and lock branch + commit

Working directory:
G:/Personal Builds/Revive-FireDM/FireDM

Command:
```bash
git rev-parse --show-toplevel && git branch --show-current && git rev-parse HEAD && git status --short
```

Exit code:
```text
0
```

Stdout:
```text
G:/Personal Builds/Revive-FireDM/FireDM
main
4dddd9cc9c51b9d17b44236af67ef145078f644a
 M artifacts/extractor/default_selection_proof.json
 M artifacts/regression/regression_suite_result.json
 M artifacts/smoke/playlist_result.json
 M artifacts/smoke/single_video_result.json
 M firedm/config.py
 M firedm/controller.py
 M firedm/setting.py
 M firedm/utils.py
 M firedm/video.py
?? artifacts/security/
?? tests/test_security.py
```

Interpretation:
LOCAL_ROOT confirmed. Branch `main`. HEAD `4dddd9c`. Working tree dirty:
five `firedm/*.py` source files and four `artifacts/*` JSONs are
pre-existing modifications; `artifacts/security/` and
`tests/test_security.py` are untracked and predate this audit run.

## CMD-002: Capture toolchain versions

Command:
```bash
git --version && python --version && python -m pip --version
```

Exit code:
```text
0
```

Stdout:
```text
git version 2.53.0.windows.2
Python 3.10.11
pip 23.0.1 from C:\Users\SavanthGC\AppData\Local\Programs\Python\Python310\lib\site-packages\pip (python 3.10)
```

Interpretation:
Audit runs against Python 3.10.11 (the only `requires-python` declared in
`pyproject.toml`), git 2.53 on Windows, pip 23.0.1.

## CMD-003: Verify key runtime dependencies importable

Command:
```bash
python -c "import pycurl; print('pycurl', pycurl.version)"
python -c "import certifi; print('certifi', certifi.__version__)"
python -c "import yt_dlp; print('yt_dlp', yt_dlp.version.__version__)"
python -c "import pytest; print('pytest', pytest.__version__)"  # initially missing
```

Exit codes:
```text
0, 0, 0, 1 (pytest), then 0 after install
```

Stdout (relevant excerpts):
```text
pycurl PycURL/"7.45.7" libcurl/8.15.0-DEV (OpenSSL/3.5.2) Schannel zlib/1.3.1 brotli/1.1.0 libssh2/1.11.1_DEV nghttp2/1.67.0
certifi 2026.04.22
yt_dlp 2026.03.17
ModuleNotFoundError: No module named 'pytest'
```

Interpretation:
pycurl, certifi, yt_dlp present in the user's site-packages. pytest was
absent and was installed via `python -m pip install --user "pytest>=9.0"`
(see CMD-004). No other pip changes.

## CMD-004: Install pytest into the user site-packages (only audit dep change)

Command:
```bash
python -m pip install --user "pytest>=9.0"
```

Exit code:
```text
0
```

Stdout (excerpt):
```text
Successfully installed exceptiongroup-1.3.1 iniconfig-2.3.0 pluggy-1.6.0 pygments-2.20.0 pytest-9.0.3 typing-extensions-4.15.0
```

Interpretation:
pytest 9.0.3 (matches `pyproject.toml` `[project.optional-dependencies].test`
which declares `pytest>=9.0`). Installed --user; does not modify the
project's frozen requirements.

## CMD-005: Create audit artifact directories

Command:
```bash
mkdir -p artifacts/security/pocs tests/security
```

Exit code:
```text
0
```

Interpretation:
`artifacts/security/pocs/` and `tests/security/` available. The repo
already uses `tests/test_security.py` (single-file convention); the
`tests/security/` dir is created for any per-candidate fixture but
remains empty if not needed.

## CMD-006: Project structure discovery — top-level config files

Command:
```bash
ls -la requirements*.txt setup.py setup.cfg pyproject.toml MANIFEST.in pytest.ini tox.ini
```

Stdout (relevant):
```text
pyproject.toml          (4519 bytes)
requirements.txt        (206 bytes)
setup.py                (39 bytes)
```

`setup.cfg`, `MANIFEST.in`, `pytest.ini`, `tox.ini`: absent in current
checkout (`ls` exit 2 for each).

Interpretation:
Single-source-of-truth is `pyproject.toml`. `pytest` config lives under
`[tool.pytest.ini_options]` (`testpaths = ["tests"]`, `addopts = "-ra"`,
`xfail_strict = true`). `ruff` configured for selected modules,
`mypy` configured for the modernized seam (excludes legacy modules).

## CMD-007: List tracked file count + firedm package modules

Command:
```bash
git ls-files | wc -l && git ls-files 'firedm/*.py' | sort
```

Stdout:
```text
146
firedm/FireDM.py
firedm/__init__.py
firedm/__main__.py
firedm/about.py
firedm/app_paths.py
firedm/brain.py
firedm/cmdview.py
firedm/config.py
firedm/controller.py
firedm/dependency.py
firedm/downloaditem.py
firedm/extractor_adapter.py
firedm/ffmpeg_commands.py
firedm/ffmpeg_service.py
firedm/iconsbase64.py
firedm/model.py
firedm/pipeline_logger.py
firedm/playlist_builder.py
firedm/playlist_entry.py
firedm/setting.py
firedm/systray.py
firedm/themes.py
firedm/tkview.py
firedm/tool_discovery.py
firedm/update.py
firedm/utils.py
firedm/version.py
firedm/video.py
firedm/view.py
firedm/worker.py
```

Interpretation:
146 tracked files; 30 modules in the `firedm/` package. The audit
focuses on the modernized seams plus the legacy modules that handle
network/filesystem/subprocess (utils.py, controller.py, video.py,
update.py, setting.py).

## CMD-008: Static security inventory — dynamic execution / import

Commands (executed via Grep on `firedm/`):
```text
rg "\b(exec|eval|compile)\s*\("        firedm/
rg "importlib|spec_from_file_location|exec_module|load_source|__import__"  firedm/
```

Notable hits:
```text
firedm/utils.py:1304     spec.loader.exec_module(module)        # import_file()
firedm/utils.py:1237     # SECURITY: never `exec()` the file  # AST parse path
firedm/video.py:811      module = import_file(fp)              # only via load_user_extractors (gated)
firedm/video.py:793      # SECURITY: the loader exec()s every .py via importlib.exec_module()
firedm/extractor_adapter.py:46  importlib.import_module        # extractor name from config (allowlist)
firedm/dependency.py:33  importlib.util.find_spec(pkg)         # presence check only
firedm/FireDM.py:368     importlib.import_module(module)       # hardcoded module list (import_diagnostics)
firedm/utils.py:934      importlib.util.find_spec(pkg_name)    # presence check only
firedm/tkview.py:206     window.eval('tk::PlaceWindow . center')  # Tk built-in, fixed string
```

Interpretation:
The only path that actually runs arbitrary attacker-controlled `.py`
content is `import_file(fp, exec_module=True)` (utils.py:1298-1305),
reachable solely through `load_user_extractors` (video.py:790-830) which
is gated by `config.allow_user_extractors=False` per F-HIGH-6. Other
hits are `importlib.import_module` against fixed allowlists or stdlib
diagnostics. `get_pkg_version` (utils.py:1214-1295) is the AST-parsed
path that closed F-CRIT-1.

## CMD-009: Static security inventory — subprocess sinks

Command:
```text
rg "subprocess\.|Popen\(|os\.system|os\.popen|os\.startfile|shell\s*=\s*True"  firedm/
```

Notable hits:
```text
firedm/utils.py:549      subprocess.Popen(cmd, ..., shell=shell)   # run_command(); shell forced False at :526
firedm/utils.py:710      os.startfile(fp)                          # open_file Windows
firedm/utils.py:722,724,759,766  subprocess.Popen(shlex.split(cmd))   # open_file/open_folder POSIX & explorer
firedm/dependency.py:51  subprocess.run(cmd, shell=False)          # cmd = [sys.executable,'-m','pip','install',...] argv list
firedm/FireDM.py:46      subprocess.run([executable, config_fp], shell=False)   # editor launcher (CLI --edit-config)
firedm/ffmpeg_service.py:75  subprocess.run(cmd, capture_output=True, ...)     # cmd is list [ffmpeg_path,'-version']
firedm/video.py:724      subprocess.Popen(cmd, ...)                # run_ffmpeg helper (cmd already shlex.split'd)
firedm/tkview.py:3225    subprocess.Popen(['ps','-A'], ...)         # Linux process listing
firedm/tkview.py:3244    subprocess.Popen(cmd, ...)                # ps grep helper
```

Interpretation:
All execution sites use `shell=False` (or argv lists). User-supplied
strings that reach `run_command` are first split via `shlex.split` (a
quoting-aware POSIX tokenizer) before Popen, so the shell metacharacter
class is not invoked. `os.startfile` on Windows and `xdg-open "<path>"`
on POSIX are confined to download-item paths whose filenames pass
`validate_file_name` (utils.py:438-465), which strips both `'` and `"`.
Command hooks (`on_completion_command`) are user-policy strings — already
mitigated against persisted-state injection by F-HIGH-4
(`UNSAFE_DOWNLOAD_KEYS`).

## CMD-010: Static security inventory — pycurl / network / urlopen

Command:
```text
rg "pycurl|FOLLOWLOCATION|PROTOCOLS|REDIR_PROTOCOLS|urlopen"  firedm/
```

Notable hits:
```text
firedm/utils.py:148-149  FOLLOWLOCATION=1, MAXREDIRS=10
firedm/utils.py:156-158  PROTOCOLS = REDIR_PROTOCOLS = PROTO_HTTP|PROTO_HTTPS  (F-CRIT-2 / F-HIGH-5)
firedm/utils.py:355      response = urllib.request.urlopen(url)   # simpledownload(); only build-script callers
firedm/worker.py:184     set_curl_options(self.c, ...)            # PROTOCOLS allowlist applied per worker reuse
firedm/worker.py:186     setopt(URL, self.seg.url)                # AFTER set_curl_options -> allowlist active
```

Interpretation:
Runtime download paths (`utils.download`, `utils.get_headers`,
`worker.set_options`, `controller.download_thumbnail`) all share the
`set_curl_options` allowlist. `simpledownload` is the one stdlib
`urllib.request.urlopen` site (no pycurl protocol gate); however, the
only invokers are build scripts (`scripts/appimage/*`,
`scripts/exe_build/*`) that pass hardcoded GitHub/PyPI URLs. The
function is never reached from the GUI or CLI runtime user-input flow.

## CMD-011: Static security inventory — archive extraction

Command:
```text
rg "zipfile|tarfile|extractall|shutil\.unpack_archive"  firedm/
```

Notable hits:
```text
firedm/utils.py:1340     zipfile.ZipFile(z_fp,'r')
firedm/utils.py:1343     z.extractall(path=extract_folder)         # safe_extract_zip after _archive_member_target check
firedm/utils.py:1348     tarfile.open(tar_fp,'r')
firedm/utils.py:1352     reject if member.issym() or member.islnk()
firedm/utils.py:1354     tar.extractall(members=members)            # safe_extract_tar
```

Interpretation:
`_archive_member_target` (utils.py:1317-1335) rejects empty names,
absolute names (POSIX `/` prefix and Windows drive letters via
`ntpath.isabs`/`ntpath.splitdrive`), and names whose
`os.path.commonpath` lies outside the target. `safe_extract_tar` adds
symlink and hardlink rejection. The single caller of these helpers in
the runtime is `firedm/update.py:234-238`. No `shutil.unpack_archive`
callsite.

## CMD-012: Static security inventory — config / state mutation

Command:
```text
rg "__dict__\.update|setattr\(|json\.load|pickle|shelve"  firedm/
```

Notable hits:
```text
firedm/setting.py:187    config.__dict__.update(safe_settings)        # F-CRIT-3 schema-filtered
firedm/setting.py:73-74  sanitized_dict = {k:v for k,v in d_dict if k not in UNSAFE_DOWNLOAD_KEYS}
firedm/controller.py:49  config.__dict__.update(kwargs)               # internal set_option, kwargs are programmer-supplied
firedm/controller.py:392 d.__dict__.update(refreshed_d.__dict__)      # both ObservableDownloadItem instances
firedm/FireDM.py:426     config.__dict__.update(sett)                 # CLI argparse Namespace; bounded by `dest=` declarations
firedm/downloaditem.py:731,750  seg.__dict__.update(item)             # progress_info.txt entry; lives in d.temp_folder
firedm/utils.py:600      `# avoiding obj.__dict__.update(new_values)` # update_object hasattr() guard at :603
firedm/utils.py:605      setattr(obj, k, v)                           # only when hasattr() true
firedm/video.py:826      setattr(engine.extractor, ie_key, ie)        # gated user-extractor path
firedm/video.py:878      setattr(config, version_attr, extractor.version)  # version_attr from fixed allowlist
firedm/setting.py:60     json.load(f)  # downloads.dat
firedm/setting.py:83     json.load(f)  # thumbnails.dat
firedm/setting.py:153    json.load(f)  # setting.cfg (passed through schema filter)
firedm/utils.py:774      json.load(f)  # generic load_json helper
firedm/update.py:74,144  json.loads(contents)  # GitHub/PyPI release metadata
firedm/tkview.py:3344    json.loads(show_window())  # GUI dialog input
```

Interpretation:
- `setting.py:load_setting` (F-CRIT-3) and `setting.py:load_d_map`
  (F-HIGH-4) already cover the disk-borne mutation paths.
- `FireDM.py:426 config.__dict__.update(sett)` writes the argparse
  Namespace into config; `sett` keys are bounded by argparser
  `add_argument(dest=...)` declarations, so this path is reachable only
  by command-line input (the CLI user is the trust principal). Not a
  cross-trust-boundary mutation.
- `controller.py:49 set_option(**kwargs)` is module-internal API used
  with literal kwargs in callsites; no user-string-keyed dispatch.
- `downloaditem.py:731 seg.__dict__.update(item)` reads
  `progress_info.txt` from `self.temp_folder` (the user's own
  download/temp dir). An attacker with write access to that dir already
  crosses the user trust boundary.

## CMD-013: Static security inventory — filesystem path construction

Command:
```text
rg "os\.path\.join|expanduser|expandvars|realpath|abspath"  firedm/
```

Files hit (12):
```text
firedm/{config,controller,brain,downloaditem,FireDM,setting,systray,
tkview,update,utils,video,__main__}.py
```

Interpretation:
`validate_file_name` (utils.py:438-465) is the central name sanitizer
(strips `'`, `"`, control chars, characters outside BMP, and replaces
`~` `` ` `` `#` `$` `&` `*` `()` `\` `|` `[]` `{}` `;` `<>` `/` `?` `!`
`^` `,` `:` with underscore; truncates >255 chars). Path joining uses
`os.path.join` with sanitized components plus a controlled folder
root. `_archive_member_target` adds traversal containment for
extraction. Thumbnail name derived from sanitized base name plus
`.png` (controller.py:183). No use of metadata-derived `..` survives
the sanitizer's separator stripping.

## CMD-014: Static security inventory — frozen / packaging surface

Command:
```text
rg "_MEIPASS|sys\.frozen|PyInstaller|cx_freeze"
```

Notable hits in code:
```text
firedm/config.py:43      FROZEN = getattr(sys,"frozen", False)        # detects both cx_freeze AND PyInstaller (sys.frozen)
firedm/config.py:69-75   if hasattr(sys,'frozen'): current_directory = os.path.dirname(sys.executable)  # else firedm package dir
firedm/update.py:174,205 if config.FROZEN: ... cx_freeze update path  # update via release zip
```

Interpretation:
`config.FROZEN` is True for both PyInstaller (`sys.frozen='onefile'`
or `'onedir'`) and cx_freeze. `current_directory` is the executable's
directory in frozen mode (typically write-protected on Windows
`Program Files`) or the firedm package directory in source mode. In
source mode, `current_directory` is **not** the user's CWD — it is the
package install location. The `sys.path.insert(0, current_directory)`
at config.py:74-75 therefore puts `firedm/` (and its parent) on sys.path,
not whatever folder the user launched from.

## CMD-015: Static security inventory — protocol marker strings

Command:
```text
rg "file://|ftp://|169\.254\.169\.254"
```

Notable hits in code (excluding existing security tests / audit
artifacts which intentionally name these strings):
```text
firedm/controller.py:175  # comment: file:///c:/users/victim/secret.txt scenario for F-HIGH-5
firedm/utils.py:151-152   # comment: libcurl refuses file://, ftp://, dict://, gopher://, smb:// telnet:// tftp://
firedm/tkview.py:146      url_reg = re.compile(r"^(https?|ftps?|file)://")  # clipboard URL filter
```

Interpretation:
`tkview.py:146` clipboard URL regex permits `file://` matches, but the
matched string is fed through `<<urlChangeEvent>>` to the user-action
handler, which ultimately routes it through `utils.download` /
`worker.set_options` (both bound by the pycurl allowlist) or asks for
user confirmation. There is no direct fast-path from clipboard URL to
local file read.

## CMD-016 .. CMD-026: Candidate reproductions

Driver script: `artifacts/security/pocs/repro_all.py`
Captured output: `artifacts/security/pocs/repro_all_output.txt`

Command:
```bash
python artifacts/security/pocs/repro_all.py
```

Exit code: `0`

Output (verbatim, full text in `repro_all_output.txt`):

```text
==============================================================================
CAND-01: tool_discovery search_dirs precedence over shutil.which
==============================================================================
resolved path     : C:\Users\SavanthGC\AppData\Local\Temp\tmpm4z1tl98\.firedm\ffmpeg.exe
planted path      : C:\Users\SAVANT~1\AppData\Local\Temp\tmpm4z1tl98\.firedm\ffmpeg.exe
path_lookup called: None
search_dirs precedence over PATH: True
Trust evaluation : write to %APPDATA%\.firedm requires user-level filesystem rights; same principal that runs FireDM.
Disposition       : REJECTED_NO_SECURITY_BOUNDARY

==============================================================================
CAND-02: ffmpeg argv leading-dash via metadata filename
==============================================================================
validate_file_name('-evil-payload') -> '-evil-payload'
fast cmd            : "C:\bin\ffmpeg.exe" -loglevel error -stats -y -i "C:\Users\Foo\Downloads\-evil-payload.mp4" -i "C:\Users\Foo\Downloads\audio.m4a" -c copy "C:\Users\Foo\Downloads\out.mp4"
argv (production POSIX shlex): ['C:\\bin\\ffmpeg.exe', '-loglevel', 'error', '-stats', '-y', '-i', 'C:\\Users\\Foo\\Downloads\\-evil-payload.mp4', '-i', 'C:\\Users\\Foo\\Downloads\\audio.m4a', '-c', 'copy', 'C:\\Users\\Foo\\Downloads\\out.mp4']
argv tokens beginning with '-' that are NOT known flags: []
path argv tokens   : ['C:\\bin\\ffmpeg.exe', 'C:\\Users\\Foo\\Downloads\\-evil-payload.mp4', 'C:\\Users\\Foo\\Downloads\\audio.m4a', 'C:\\Users\\Foo\\Downloads\\out.mp4']
path tokens beginning with '-': []
Disposition       : REJECTED_EXISTING_MITIGATION

==============================================================================
CAND-03: argv quote escape via embedded `"` in path
==============================================================================
validate_file_name('a"b.mp4') -> 'ab.mp4'
_quote('has"quote.mp4') -> '"has\\"quote.mp4"'
shlex.split posix tokens: ['has"quote.mp4']
single token preserved : True
Disposition       : REJECTED_EXISTING_MITIGATION

==============================================================================
CAND-04: m3u8 skd:// -> https:// URL substitution
==============================================================================
segment count     : 1
segment URL       : https://attacker.example/seg1.ts
key URL           : https://attacker.example/key
segment URL passes is_allowed_network_url : True
key URL passes is_allowed_network_url     : True
Disposition       : REJECTED_NO_SECURITY_BOUNDARY

==============================================================================
CAND-05: sys.path[0:2] introspection after firedm.config import
==============================================================================
sys.path[0]: G:\Personal Builds\Revive-FireDM\FireDM\firedm
sys.path[1]: G:\Personal Builds\Revive-FireDM\FireDM
package_dir       : G:\Personal Builds\Revive-FireDM\FireDM\firedm
repo_dir          : G:\Personal Builds\Revive-FireDM\FireDM
Trust evaluation : both entries are inside the repo / package tree (write access there = code-level compromise already).
Disposition       : REJECTED_NO_SECURITY_BOUNDARY

==============================================================================
CAND-07: shlex.split('xdg-open "<path with embedded quote>"')
==============================================================================
raw cmd  : 'xdg-open "/home/user/My"Quote/Downloads"'
shlex raised ValueError: No closing quotation
open_folder()/open_file() wrap subprocess.Popen in try/except (utils.py:767-768, :725-728), so the ValueError is logged and no process is spawned. No shell evaluation occurs either way.
outcome           : ValueError -> caught -> no spawn -> no shell evaluation
Disposition       : REJECTED_EXISTING_MITIGATION

==============================================================================
CAND-08: MediaPlaylist.create_local_m3u8_doc rewrites URIs to local paths
==============================================================================
local m3u8 produced for ffmpeg:
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-PLAYLIST-TYPE:None
#EXT-X-TARGETDURATION:6
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:6.0,
C:/Users/SAVANT~1/AppData/Local/Temp/tmpelk86eux/video_seg_1.ts
#EXT-X-ENDLIST
local m3u8 still contains 'file:///etc/passwd' : False
Disposition       : REJECTED_EXISTING_MITIGATION

==============================================================================
CAND-09: setting.cfg accepts ffmpeg_actual_path (intended user feature)
==============================================================================
config.ffmpeg_actual_path -> C:\Users\SAVANT~1\AppData\Local\Temp\tmpculaji09\evil-ffmpeg.exe
Trust evaluation : setting.cfg is the user's own configuration. Choosing the ffmpeg binary is a feature.
Disposition       : REJECTED_NO_SECURITY_BOUNDARY

==============================================================================
CAND-14: argparse Namespace bounds keys written into config.__dict__
==============================================================================
argparse rejected unknown option (exit 2)
keys for --proxy only      : ['proxy', 'url']
Disposition       : REJECTED_NO_SECURITY_BOUNDARY

==============================================================================
CAND-15: simpledownload runtime callers
==============================================================================
runtime (firedm/) callers: []
Disposition       : REJECTED_OUT_OF_SCOPE

==============================================================================
CAND-16: load_progress_info accepts attacker-named segment files
==============================================================================
d.segments[0].name -> C:\Users\SAVANT~1\AppData\Local\Temp\tmpsmw5zmdn\escape_target.bin
Trust evaluation : poisoning requires write access to the user's own download/temp folder = same trust principal.
Disposition       : REJECTED_NO_SECURITY_BOUNDARY

All reproductions complete.
```

Interpretation:
- 11 candidate reproductions executed (CAND-06, CAND-10, CAND-11,
  CAND-12, CAND-13 are doc-only, see ledger).
- Every reproduction terminates with a `REJECTED_*` disposition.
- No candidate reaches the `ADMITTED_FINDING` state.
- The reproductions confirm the existing F-CRIT-1..F-HIGH-6 mitigations
  cover the underlying boundaries the new candidates probe.

## CMD-027: Targeted security tests

Command:
```bash
python -m pytest -q tests/test_security.py
```

Exit code: `0`

Output:
```text
........                                                                 [100%]
8 passed in 0.33s
```

Interpretation:
All 8 tests in `tests/test_security.py` pass. No new tests were added
by this audit (no new admitted findings); the 8 existing tests
correspond to F-CRIT-1, F-CRIT-2 (×2), F-CRIT-3 (×2), F-HIGH-4,
F-HIGH-5, F-HIGH-6.

## CMD-028: Full pytest suite

Command:
```bash
python -m pytest -q
```

Exit code: `0`

Output (tail):
```text
........................................................................ [ 66%]
.....................................                                    [100%]
109 passed in 7.08s
```

Interpretation:
109 tests pass; no failures, no errors, no skips.

## CMD-029: Linter / type-checker availability

Commands:
```bash
python -m ruff check .
python -m mypy --version
```

Exit codes: both 1 (`No module named ruff`, `No module named mypy`).

Interpretation:
Neither `ruff` nor `mypy` is installed in the active interpreter. The
repo's `pyproject.toml` declares them under
`[project.optional-dependencies].{dev,type}`. Per role-spec: record the
absence rather than treat it as evidence of vulnerability. CI runs
`ruff` and `mypy` on the modernized seam (per `pyproject.toml`) and is
the source of truth for those checks.

## CMD-030: Patch generation and integrity

Commands:
```bash
git diff --check                                # whitespace / conflict-marker scan
git diff -- firedm/ > firedm-security-patch.diff
git apply --check -R firedm-security-patch.diff # reverse-check identity
git diff --name-only -- firedm/ tests/ artifacts/security/
```

Exit codes:
```text
git diff --check        : 0 (only CRLF/LF EOL warnings on artifacts/*.json — informational only)
git apply --check -R    : 0
git diff --name-only    : 0
```

Outputs:

```text
firedm-security-patch.diff size: 242 lines
git diff --name-only:
firedm/config.py
firedm/controller.py
firedm/setting.py
firedm/utils.py
firedm/video.py
```

Interpretation:
- `git apply --check -R firedm-security-patch.diff` succeeds, which
  cryptographically confirms the on-disk patch matches the current
  working-tree-vs-HEAD diff exactly.
- The 242-line patch contains only the **prior** F-CRIT-1..F-HIGH-6
  mitigations already in the working tree at the start of this audit
  (HEAD is `4dddd9c` which precedes those uncommitted patches).
- This audit pass authored **zero new source-code patches** because
  no candidate reached `ADMITTED_FINDING`.

## CMD-031: Required-artifact existence check

Command:
```bash
python -c "from pathlib import Path
required = ['artifacts/security/command_log.md',
            'artifacts/security/attack_surface_map.md',
            'artifacts/security/candidate_ledger.md',
            'artifacts/security/verified_audit_report.md',
            'firedm-security-patch.diff',
            'tests/test_security.py']
for item in required: print(f'{item}: {\"OK\" if Path(item).exists() else \"MISSING\"}')"
```

Output (after `verified_audit_report.md` written):
```text
artifacts/security/command_log.md: OK
artifacts/security/attack_surface_map.md: OK
artifacts/security/candidate_ledger.md: OK
artifacts/security/verified_audit_report.md: OK
firedm-security-patch.diff: OK
tests/test_security.py: OK
```

Interpretation:
All required artifacts present.

