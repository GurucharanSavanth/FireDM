# FireDM Audit Candidate Ledger

Audit pass: 2026-04-26 hostile re-audit.
Local root: `G:/Personal Builds/Revive-FireDM/FireDM`
HEAD: `4dddd9cc9c51b9d17b44236af67ef145078f644a` (branch `main`).

Each entry records the lifecycle of one candidate (`DISCOVERED →
SOURCE_CONFIRMED → REPRO_ATTEMPTED → REPRODUCED|REJECTED_*`).
Reproduction commands and exact outputs are recorded in
`command_log.md`. Only an `ADMITTED_FINDING` may appear in the final
report's Verified Findings section.

---

## CAND-01: APPDATA-planted ffmpeg.exe pre-empts system PATH

Candidate class: Command Injection / Tool-Discovery Hijack

Files:
- `firedm/tool_discovery.py`
- `firedm/ffmpeg_service.py`
- `firedm/controller.py`

Source location inspected:
- `firedm/tool_discovery.py:resolve_binary_path:43-74`
- `firedm/ffmpeg_service.py:resolve_ffmpeg_path:33-50`
- `firedm/ffmpeg_service.py:locate_ffmpeg:53-89`
- `firedm/controller.py:68-72`

Initial trigger: static inventory (Phase 2).

Hypothesized source:
- An attacker with write access to `%APPDATA%\.firedm` (or whichever
  directory is passed as `search_dirs[1]` aka
  `config.global_sett_folder`) plants a fake `ffmpeg.exe`.

Hypothesized sink:
- `subprocess.run([ffmpeg_path,'-version'])` (ffmpeg_service.py:83)
  and the subsequent ffmpeg invocations during merge / HLS
  post-processing.

Security boundary:
- Local user file system → subprocess execution. The user that owns
  `%APPDATA%\.firedm` is the same principal that runs FireDM. Any
  attacker who can write there already has **user-level code
  execution** on the same account, which subsumes execution inside
  FireDM.

Existing validation observed:
- `saved_path` (config.ffmpeg_actual_path) takes precedence over
  search_dirs (tool_discovery.py:54). When set, search_dirs are
  skipped.
- search_dirs comes from controller.py:70 — fixed pair
  `(config.current_directory, config.global_sett_folder)`. Neither
  is a generic CWD.

Verification plan:
1. Plant a fake `ffmpeg.exe` (Python stub) inside a `tmp_path`-based
   simulated `global_sett_folder`.
2. Call `resolve_ffmpeg_path` with operating_system='Windows',
   `search_dirs=[<simulated_appdata>]`, no saved_path,
   `path_lookup=lambda name: '/usr/bin/ffmpeg'` (simulating system
   PATH).
3. Assert resolver returns the planted path (i.e. `search_dirs`
   precedence is real).
4. Evaluate against trust boundary.

Pre-patch reproduction command: see `command_log.md` CMD-016.

Pre-patch result: `search_dirs` precedence over PATH lookup is
**confirmed**. However, the prerequisite (write access to
`%APPDATA%\.firedm`) means the attacker already controls the
victim's user account.

Patch status: not patched.

Regression status: not written.

Admission status: REJECTED_NO_SECURITY_BOUNDARY

Reason:
- An attacker with write access to `%APPDATA%\<user>\.firedm`
  already has user-level write access. They can directly modify
  FireDM source (or any other program the user runs), drop a
  scheduled task, or alter the user's startup folder. Hijacking the
  ffmpeg path inside FireDM is strictly weaker than capabilities
  the attacker already has. The boundary "untrusted-network →
  trusted-binary-execution" is not crossed by this candidate.

---

## CAND-02: ffmpeg argv leading-dash via filename

Candidate class: Command Injection (option-flag confusion)

Files:
- `firedm/utils.py`
- `firedm/ffmpeg_commands.py`
- `firedm/video.py`

Source location inspected:
- `firedm/utils.py:validate_file_name:438-465`
- `firedm/ffmpeg_commands.py:_quote:22-24`,
  `build_merge_command:36-50`,
  `build_hls_process_command:53-68`

Initial trigger: static inventory + manual code reading.

Hypothesized source:
- Hostile yt-dlp metadata title beginning with `-` survives
  `validate_file_name` (which does not strip `-`).

Hypothesized sink:
- After `os.path.join(folder, name)` and `_quote(...)` and
  `shlex.split`, the file path becomes one argv element. ffmpeg
  receives it as a `-foo` option instead of an input filename.

Security boundary:
- Network metadata → ffmpeg argv → ffmpeg interpreter.

Existing validation observed:
- `os.path.join(folder, '-evil.mp4')` always returns a path
  beginning with the **folder** component (drive letter on Windows,
  `/` on POSIX), so the argv element does not begin with `-`. The
  filename's leading dash becomes a path-mid character.

Verification plan:
1. Construct a download item with `name = '-evil.mp4'` and
   `folder = tmp_path`.
2. Call `build_merge_command`, get `pair.fast`.
3. `shlex.split(pair.fast)` and inspect the argv element for the
   video file.
4. Assert that element begins with `tmp_path` (i.e. drive letter on
   Windows, `/` on POSIX) and not `-`.

Pre-patch reproduction command: see `command_log.md` CMD-017.

Pre-patch result: argv element begins with the absolute folder
path, not `-`. ffmpeg therefore reads it as a filename.

Patch status: not patched.

Regression status: not written.

Admission status: REJECTED_EXISTING_MITIGATION

Reason:
- Absolute-path joining at the call site neutralizes leading-dash
  filenames before ffmpeg sees them. This is structural rather
  than incidental — `os.path.join` requires a folder root.

---

## CAND-03: argv quote escape in `_quote()`

Candidate class: Command Injection

Files:
- `firedm/ffmpeg_commands.py`
- `firedm/utils.py`

Source location inspected:
- `firedm/ffmpeg_commands.py:_quote:22-24`
- `firedm/utils.py:validate_file_name:438-465`

Initial trigger: static review.

Hypothesized source:
- Embedded `"` in a path makes its way through `_quote()` →
  `shlex.split` and breaks argv tokenization.

Hypothesized sink:
- ffmpeg receives a malformed argv where one piece of the intended
  filename becomes the start of a new option.

Existing validation observed:
- `validate_file_name` strips `'` and `"` from any name (utils.py:
  448-449). On Windows, NTFS rejects `"` in path components, so
  the folder cannot contain it either.
- `_quote('a"b') == '"a\\"b"'` — `shlex.split` (POSIX mode default)
  unescapes the inner `\"` into a single `"` and yields one argv
  token containing `a"b`.

Verification plan:
1. `validate_file_name('a"b.mp4')` → assert `"` removed.
2. `_quote('weird/path "with quote".mp4')` → assert
   `shlex.split` produces a single argv element.

Pre-patch reproduction command: see `command_log.md` CMD-018.

Pre-patch result: filename loses `"` at validation; even when
`"` is forced into the input, `_quote`+`shlex.split` round-trips to
a single element.

Patch status: not patched.

Regression status: not written.

Admission status: REJECTED_EXISTING_MITIGATION

Reason:
- `validate_file_name` and `_quote` together close the escape.

---

## CAND-04: `skd://` → `https://` URL substitution

Candidate class: SSRF / Protocol Confusion

Files:
- `firedm/video.py`

Source location inspected:
- `firedm/video.py:MediaPlaylist.parse_m3u8_doc:1515-1580`
  (specifically the substitution at lines 1539-1541 and
  1564-1566).

Initial trigger: manual code reading.

Hypothesized source:
- A malicious m3u8 sets `URI="skd://attacker.example/path"` for a
  segment or key. The raw scheme is replaced with `https://`.

Hypothesized sink:
- After substitution and `urljoin`, the URL flows through
  `download(...)`. The pycurl protocol allowlist permits HTTPS, so
  the HTTPS request is dispatched normally.

Security boundary:
- Network → network. The substitution does not relax the protocol
  policy beyond what HTTPS already provides.

Existing validation observed:
- pycurl PROTOCOLS allowlist remains in effect post-substitution.

Verification plan:
1. Construct an m3u8 with a `skd://attacker.example/key` URI.
2. Parse via `MediaPlaylist`.
3. Assert resulting `key.url` begins with `https://`.
4. Assert the URL passes `is_allowed_network_url`.

Pre-patch reproduction command: see `command_log.md` CMD-019.

Pre-patch result: substitution behaves as documented in source.

Patch status: not patched.

Regression status: not written.

Admission status: REJECTED_NO_SECURITY_BOUNDARY

Reason:
- Substituting `skd://` for `https://` lands inside the existing
  HTTPS allowlist. There is no escalation: any HTTPS host the
  m3u8 can name is no different from any other yt-dlp metadata
  URL, which FireDM already trusts to be HTTPS-fetched.

---

## CAND-05: `sys.path.insert` of install / package directory

Candidate class: Module Hijack / ACE

Files:
- `firedm/config.py`

Source location inspected:
- `firedm/config.py:69-75` (`current_directory`,
  `sys.path.insert(0, ...)`).

Initial trigger: static inventory.

Hypothesized source:
- An attacker drops a `.py` module with a hijacked name
  (e.g. `pycurl.py`) into `current_directory`. On next import,
  Python finds the attacker version first.

Hypothesized sink:
- Module-level code execution.

Security boundary:
- Filesystem write (to install dir) → arbitrary code execution.

Existing validation observed:
- In source mode, `current_directory =
  os.path.dirname(os.path.realpath(__file__))` = the firedm package
  directory itself. Writing there means modifying FireDM source
  files directly.
- In frozen mode (PyInstaller / cx_freeze), `current_directory`
  is the executable's directory (typically `Program Files\FireDM`
  on Windows — write-protected).

Verification plan:
1. Inspect `sys.path[:2]` after `import firedm.config`.
2. Assert paths are absolute and inside the install/package tree.

Pre-patch reproduction command: see `command_log.md` CMD-020.

Pre-patch result: `sys.path[0]` is the firedm package dir;
`sys.path[1]` is its parent. In a packaged install, both reside
under `Program Files`, write-protected for non-admin users. In a
source install, both are the developer's repo (which the developer
controls).

Patch status: not patched.

Regression status: not written.

Admission status: REJECTED_NO_SECURITY_BOUNDARY

Reason:
- The location `current_directory` is the FireDM installation
  itself. Writing there already implies the attacker controls
  FireDM's code, so module hijacking is strictly weaker than the
  capabilities the attacker already has. No untrusted-input →
  trusted-execution boundary is crossed.

---

## CAND-06: PyPI / GitHub update lacks signature/hash verification

Candidate class: Supply Chain

Files:
- `firedm/update.py`

Source location inspected:
- `firedm/update.py:check_for_new_version:55-90`
- `firedm/update.py:get_pkg_latest_version:93-166`
- `firedm/update.py:update_pkg:187-294`

Initial trigger: static review.

Hypothesized source:
- A future PyPI compromise or MitM CDN attack on the wheel/zip
  download could deliver a tampered package.

Hypothesized sink:
- `safe_extract_tar`/`safe_extract_zip` extracts the bytes into
  the install lib folder; pip-equivalent flow.

Existing validation observed:
- All transport is HTTPS via the pycurl allowlist.
- `safe_extract_*` defends against archive traversal.
- `packaging.version.parse` does not validate package signature.

Verification plan:
- N/A (out of FireDM-runtime scope).

Pre-patch reproduction command: not run.

Pre-patch result: not run.

Patch status: not patched.

Regression status: not written.

Admission status: REJECTED_OUT_OF_SCOPE

Reason:
- Stock `pip install` and `pip wheel` rely on HTTPS+CA only — they
  do not verify package signatures by default. Adding a
  cryptographic signature pipeline is a hardening recommendation,
  not a vulnerability against the documented threat model. No
  reproducible boundary breach against the current FireDM
  trust model.

---

## CAND-07: POSIX path quote escape in `xdg-open` / `explorer /select`

Candidate class: Command Injection

Files:
- `firedm/utils.py`

Source location inspected:
- `firedm/utils.py:open_file:697-728`,
  `open_folder:730-769`.

Initial trigger: static review.

Hypothesized source:
- A folder path (or filename) containing `"` reaches
  `open_folder`/`open_file`. The string is wrapped in `f'xdg-open
  "{folder}"'` then `shlex.split`'d. Embedded `"` could break the
  quoting and cause additional argv elements.

Hypothesized sink:
- `subprocess.Popen(shlex.split(cmd))`.

Existing validation observed:
- `validate_file_name` strips `"` from filenames.
- The folder component is the user's chosen download folder. On
  Windows, NTFS forbids `"` in path components. On POSIX, embedded
  `"` is technically possible but requires the user to type it into
  their folder picker.

Verification plan:
1. Construct a synthetic path `"<tmp_path>/has \"quote inside"`.
2. Monkeypatch `subprocess.Popen` to capture argv.
3. Call `open_folder(...)` on POSIX (skip on Windows) and assert no
   token is shell-interpretable as an additional command.

Pre-patch reproduction command: see `command_log.md` CMD-021.

Pre-patch result (POSIX): `shlex.split('xdg-open "a"b"')`
behavior — see CMD-021 for exact tokens. The `shlex` POSIX
parser produces a *malformed* split (an extra token), but the
extra token is just a literal substring of the path, not a shell
metacharacter or a separate process.

Patch status: not patched.

Regression status: not written.

Admission status: REJECTED_EXISTING_MITIGATION

Reason:
- `subprocess.Popen` with `shell=False` and an argv list does
  **not** invoke a shell. Even if `shlex.split` produces an extra
  token, no shell evaluation happens. The worst case is that
  `xdg-open` opens the wrong path or fails — neither crosses a
  security boundary.

---

## CAND-08: ffmpeg `-protocol_whitelist file,...` with attacker m3u8

Candidate class: SSRF / Local File Read

Files:
- `firedm/ffmpeg_commands.py`
- `firedm/video.py`

Source location inspected:
- `firedm/ffmpeg_commands.py:build_hls_process_command:53-68`
- `firedm/video.py:post_process_hls:1198-1237`
- `firedm/video.py:MediaPlaylist.create_local_m3u8_doc:1621-1629`

Initial trigger: static inventory.

Hypothesized source:
- ffmpeg consumes an m3u8 with `protocol_whitelist=file,http,https,...`.
  If the m3u8 contains `file:///etc/passwd` segment URIs, ffmpeg
  reads the local file.

Hypothesized sink:
- ffmpeg writes the resulting "segment" content into the merged
  output file.

Existing validation observed:
- `MediaPlaylist.create_local_m3u8_doc` rewrites every segment URL
  and key URL to a local path under `d.temp_folder` **before**
  serializing to disk for ffmpeg. The m3u8 ffmpeg reads contains
  only the local segment files FireDM downloaded.

Verification plan:
1. Construct a remote m3u8 with `URI="file:///etc/passwd"` segment.
2. Call `MediaPlaylist.create_local_m3u8_doc(...)`.
3. Assert the returned m3u8 has only local-path segment URIs.

Pre-patch reproduction command: see `command_log.md` CMD-022.

Pre-patch result: `create_local_m3u8_doc` rewrote the URI to
`<temp_folder>/<stream_type>_seg_1.ts`. The original `file://`
URI was discarded.

Patch status: not patched.

Regression status: not written.

Admission status: REJECTED_EXISTING_MITIGATION

Reason:
- The local m3u8 written for ffmpeg never contains
  attacker-controlled URIs. The `file` protocol whitelist exists to
  let ffmpeg read the local m3u8 and its local segment files —
  exactly what FireDM needs.

---

## CAND-09: `ffmpeg_actual_path` poisoning via setting.cfg

Candidate class: Command Injection

Files:
- `firedm/setting.py`
- `firedm/config.py`

Source location inspected:
- `firedm/config.py:18-28` (`settings_keys` includes
  `ffmpeg_actual_path`).
- `firedm/setting.py:165-187` (load_setting).

Initial trigger: static review of accepted-keys list.

Hypothesized source:
- A poisoned `setting.cfg` sets `ffmpeg_actual_path` to a path under
  attacker control. On next launch, FireDM uses that binary.

Hypothesized sink:
- `subprocess.run([ffmpeg_actual_path, '-version'])` and subsequent
  ffmpeg invocations.

Security boundary:
- The user's own `setting.cfg` is read. The "attacker" is whoever
  can write to `%APPDATA%\<user>\.firedm\setting.cfg`, which
  requires user-level access already.

Existing validation observed:
- `load_setting` schema-filters keys.
  `ffmpeg_actual_path` is on the schema (a legitimate user-set
  field). No further validation of the path's contents.

Verification plan:
1. Write a setting.cfg with a temp `ffmpeg_actual_path`.
2. `setting.load_setting()`.
3. Assert `config.ffmpeg_actual_path` matches.

Pre-patch reproduction command: see `command_log.md` CMD-023.

Pre-patch result: confirmed; the user-set path is honored, as
intended by the feature.

Patch status: not patched.

Regression status: not written.

Admission status: REJECTED_NO_SECURITY_BOUNDARY

Reason:
- `setting.cfg` is the user's own configuration. Choosing the
  ffmpeg binary is an explicit user feature ("Settings → ffmpeg
  path"). An attacker who can write `setting.cfg` already has
  user-level filesystem access and could, equivalently, modify any
  other config file or replace the FireDM source.

---

## CAND-10: Windows reserved filename DoS

Candidate class: DoS

Files:
- `firedm/utils.py`

Source location inspected:
- `firedm/utils.py:validate_file_name:438-465`.

Initial trigger: static review.

Hypothesized source:
- yt-dlp metadata title `CON.mp4` survives `validate_file_name`.

Hypothesized sink:
- File-creation in `<download_folder>/CON.mp4` fails on Windows
  because `CON` is a reserved device name.

Existing validation observed:
- None for reserved names.

Verification plan: not run; admission outcome already determined.

Pre-patch reproduction command: not run.

Pre-patch result: not run.

Patch status: not patched.

Regression status: not written.

Admission status: REJECTED_OUT_OF_SCOPE

Reason:
- The impact is denial of service on a single download item. There
  is no confidentiality / integrity boundary crossed.

---

## CAND-11: M3U8 segment count / parser DoS

Candidate class: DoS

Files:
- `firedm/video.py`

Source location inspected:
- `firedm/video.py:MediaPlaylist.parse_m3u8_doc:1515-1580`.

Initial trigger: static review.

Hypothesized source:
- A 50k+-segment m3u8 inflates `self.segments` list.

Hypothesized sink:
- Memory growth / CPU spend during parsing.

Verification plan: not run.

Pre-patch result: not run.

Admission status: REJECTED_OUT_OF_SCOPE

Reason:
- DoS only; out of audit scope per the role spec which targets
  confidentiality/integrity/ACE boundaries.

---

## CAND-12: Tk widget mutation from worker thread

Candidate class: Race Condition / Crash

Files:
- `firedm/controller.py`
- `firedm/tkview.py`

Source location inspected:
- `firedm/controller.py:_observer:462-485`,
  `_update_view:506`.

Initial trigger: static review.

Hypothesized source:
- `_observer` daemon thread calls `view.update_view(...)` directly,
  which ultimately mutates Tk widgets outside the main thread.

Verification plan: not run.

Pre-patch result: not run.

Admission status: REJECTED_OUT_OF_SCOPE

Reason:
- Crash / GUI corruption is a correctness defect, not a
  confidentiality/integrity boundary breach.

---

## CAND-13: `d.__dict__.update(refreshed_d.__dict__)` refresh path

Candidate class: Object Mutation

Files:
- `firedm/controller.py`

Source location inspected:
- `firedm/controller.py:392`.

Initial trigger: static inventory.

Hypothesized source:
- Hostile yt-dlp metadata refresh provides a `refreshed_d` whose
  `__dict__` includes attacker-chosen attribute names.

Existing validation observed:
- `refreshed_d` is a fresh `ObservableDownloadItem` constructed by
  FireDM's own model layer. Its attribute keys come from the
  Python class definition, not from external JSON. The values
  inside (e.g. `name`, `url`) come from extractor metadata, but
  the *keys* are bounded by the class.

Verification plan:
1. Construct a `refreshed_d` and confirm its `__dict__` keys are
   limited to `ObservableDownloadItem` fields.
2. Inspect line 392's effect on the original `d`.

Pre-patch reproduction command: not run (review-only).

Pre-patch result: keys are bounded; values are model fields.
Same trust model as the original item.

Admission status: REJECTED_NO_SECURITY_BOUNDARY

Reason:
- No new attribute can be injected because both objects are
  `ObservableDownloadItem` instances. The values are no more
  attacker-controlled than the original `d` already was.

---

## CAND-14: `config.__dict__.update(sett)` from CLI Namespace

Candidate class: Config Poisoning

Files:
- `firedm/FireDM.py`

Source location inspected:
- `firedm/FireDM.py:pars_args:53-319`,
  `firedm/FireDM.py:main:379-461` (line 426).

Initial trigger: static inventory.

Hypothesized source:
- A poisoned argv could inject unexpected config attributes.

Existing validation observed:
- `argparse` only emits keys for arguments declared with
  `add_argument(dest=...)` (lines 95-313). Default
  `argparse.SUPPRESS` causes missing args to be omitted from the
  Namespace — argparse cannot create unknown keys.
- The CLI principal is the user.

Verification plan:
1. Construct a synthetic argv; verify
   `vars(parser.parse_args(...))` only produces declared keys.

Pre-patch reproduction command: see `command_log.md` CMD-024.

Pre-patch result: argparse rejects undeclared options
(`error: unrecognized arguments`). The Namespace key set is bounded
by the parser declarations.

Admission status: REJECTED_NO_SECURITY_BOUNDARY

Reason:
- The CLI is, by definition, the user's input. There is no
  cross-trust-boundary mutation: the user is the trust principal.
  argparse provides the key-set bound.

---

## CAND-15: `simpledownload` uses `urllib.request.urlopen`

Candidate class: SSRF (build-script only)

Files:
- `firedm/utils.py`
- `scripts/appimage/*`, `scripts/exe_build/*`

Source location inspected:
- `firedm/utils.py:simpledownload:349-XXXX` (uses
  `urllib.request.urlopen`).
- callers: `scripts/appimage/appimage-quickbuild.py:44,60,161`,
  `scripts/exe_build/exe-fullbuild.py:124`,
  `scripts/exe_build/exe-quickbuild.py:39,55`.

Initial trigger: static inventory (the bypass of pycurl PROTOCOLS).

Hypothesized source:
- Any future caller passes a user-controlled URL to
  `simpledownload`.

Existing validation observed:
- The current callers are all build scripts with hardcoded GitHub
  / PyPI / SourceForge URLs. They are not invoked by the runtime
  application or any user-action handler.

Verification plan:
1. `git grep` confirms only build scripts call `simpledownload`.
2. Documented in the prior audit (`audit_2026-04-26.md`, F-MED-8
   Open Risks).

Pre-patch reproduction command: see `command_log.md` CMD-025.

Pre-patch result: confirmed — no runtime caller of
`simpledownload` from `firedm/`.

Admission status: REJECTED_OUT_OF_SCOPE

Reason:
- The function is unreachable from runtime user-input. The
  build scripts run with developer trust on hardcoded URLs.

---

## CAND-16: `seg.__dict__.update(item)` from `progress_info.txt`

Candidate class: Path Traversal / File Overwrite

Files:
- `firedm/downloaditem.py`

Source location inspected:
- `firedm/downloaditem.py:save_progress_info:665-671`,
  `load_progress_info:673-757`,
  particularly `seg.__dict__.update(item)` at lines 731 and 750.

Initial trigger: static inventory.

Hypothesized source:
- A poisoned `progress_info.txt` placed at
  `<download_folder>/firedm_<uid>/progress_info.txt`. On resume,
  `load_progress_info` reads it and calls `seg.__dict__.update(item)`
  for each entry.

Hypothesized sink:
- `seg.name` becomes the attacker-chosen path; `Worker.write`
  later opens it in write mode and dumps downloaded bytes.

Security boundary:
- Disk file in user temp folder → arbitrary file write.

Existing validation observed:
- After `seg.__dict__.update(item)` (downloaditem.py:731),
  `seg.tempfile` and `seg.url` are explicitly reassigned (734-739).
- `seg.name` is **not** re-validated — it remains whatever the
  attacker put in `progress_info.txt`.
- The path is `<self.temp_folder>/progress_info.txt`, where
  `self.temp_folder` is `<self.folder>/firedm_<self.uid>`. An
  attacker that can write there already has user-level filesystem
  access.

Verification plan:
1. Build a synthetic download item (`tmp_path` as folder, deterministic uid).
2. Write a `progress_info.txt` with one entry containing
   `name = '<tmp_path>/escape_target.bin'`.
3. Call `load_progress_info`.
4. Inspect `self.segments[0].name`.

Pre-patch reproduction command: see `command_log.md` CMD-026.

Pre-patch result: `seg.name` retains the attacker-chosen value.

Admission status: REJECTED_NO_SECURITY_BOUNDARY

Reason:
- The poisoning vector requires write access to the user's own
  download/temp folder. The attacker already has user-level
  capabilities that subsume FireDM file writes (they can directly
  write the same file with the same filesystem rights).
- The branch at line 728 (`if self.size and self.resumable and not
  self.fragments and 'hls' not in self.subtype_list`) further
  bounds the path: it triggers only when the original download had
  dynamic-segment construction.

---

## Summary

| ID | State | Reason |
|----|-------|--------|
| CAND-01 | REJECTED_NO_SECURITY_BOUNDARY | APPDATA write = user-level access already |
| CAND-02 | REJECTED_EXISTING_MITIGATION | absolute path joining neutralizes leading dash |
| CAND-03 | REJECTED_EXISTING_MITIGATION | validate_file_name + _quote together close escape |
| CAND-04 | REJECTED_NO_SECURITY_BOUNDARY | substitution targets HTTPS allowlist |
| CAND-05 | REJECTED_NO_SECURITY_BOUNDARY | sys.path entries are install/package dirs |
| CAND-06 | REJECTED_OUT_OF_SCOPE | matches stock pip trust model; no FireDM-specific defect |
| CAND-07 | REJECTED_EXISTING_MITIGATION | shell=False + argv list = no shell evaluation |
| CAND-08 | REJECTED_EXISTING_MITIGATION | local m3u8 has rewritten URIs only |
| CAND-09 | REJECTED_NO_SECURITY_BOUNDARY | setting.cfg = user config |
| CAND-10 | REJECTED_OUT_OF_SCOPE | DoS, not security boundary |
| CAND-11 | REJECTED_OUT_OF_SCOPE | DoS, not security boundary |
| CAND-12 | REJECTED_OUT_OF_SCOPE | correctness/crash, not security boundary |
| CAND-13 | REJECTED_NO_SECURITY_BOUNDARY | both sides are model-controlled instances |
| CAND-14 | REJECTED_NO_SECURITY_BOUNDARY | argparse bounds key set; CLI = user |
| CAND-15 | REJECTED_OUT_OF_SCOPE | only build scripts call simpledownload |
| CAND-16 | REJECTED_NO_SECURITY_BOUNDARY | temp folder write requires user-level access |

**No candidate reaches `ADMITTED_FINDING`.**

The audit concludes with the admission gate's allowed zero-finding
output: *"No fully verified findings met the reporting threshold."*
