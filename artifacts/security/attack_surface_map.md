# FireDM Attack Surface Map

Audit pass: 2026-04-26 hostile re-audit.
Local root: `G:/Personal Builds/Revive-FireDM/FireDM`
HEAD: `4dddd9cc9c51b9d17b44236af67ef145078f644a` (branch `main`).
Each subsystem section follows the role-spec template. Candidate IDs
referenced here resolve to entries in `candidate_ledger.md`.

---

## Subsystem: startup / CLI / GUI entry

Files inspected:
- `firedm/FireDM.py`
- `firedm/__main__.py`
- `firedm/cmdview.py`
- `firedm/tkview.py` (entry references only)

Relevant entry points:
- `firedm/FireDM.py:main:379-461`
- `firedm/FireDM.py:pars_args:53-319`
- `firedm/FireDM.py:open_config_editor:43-50`

Trusted inputs:
- `argparse.Namespace` keys (bounded set declared at lines 95-313).
- `setting.cfg` (loaded via the schema-filtered
  `setting.load_setting`).

Untrusted or attacker-influenced inputs:
- Command-line arguments (user controls the CLI; the CLI user is the
  trust principal).
- `--batch-file <PATH>` reads a text file containing URLs; the file
  is opened by argparse `FileType('r')` and consumed by
  `parse_urls` — URLs subsequently pass through the network allowlist.

State / config inputs:
- `setting.cfg`, `downloads.dat`, `thumbnails.dat` (all under
  `config.sett_folder`).

Network inputs:
- None directly; deferred to the network subsystem.

Filesystem inputs:
- `--output <path>` — `os.path.realpath`'d at FireDM.py:408.

Security boundary:
- CLI/argparse user → application.

Dangerous sinks:
- `config.__dict__.update(sett)` (FireDM.py:426) — direct config dict
  write from argparse Namespace.
- `subprocess.run([executable, config_fp], shell=False)` — editor
  launcher (FireDM.py:46), reachable only via `--edit-config <EDITOR>`.

Existing validation:
- argparse `dest=` declarations bound the key set written into
  `config.__dict__`.
- `setting.load_setting` runs **before** argparse and applies the
  schema filter from `config.settings_keys`.

Missing or weak validation candidates:
- CAND-14: `config.__dict__.update(sett)` does not use the
  `settings_keys` filter; relies entirely on argparse for key
  containment.

Candidate test ideas:
- Build a synthetic `argparse.Namespace` with only documented dest
  names, confirm injection of unexpected keys is impossible from CLI
  alone.

Candidate status:
- Not a finding. Candidate requires reproduction.

---

## Subsystem: controller lifecycle

Files inspected:
- `firedm/controller.py`
- `firedm/brain.py`

Relevant entry points:
- `firedm/controller.py:Controller.__init__:300-360`
- `firedm/controller.py:set_option:46-52`
- `firedm/controller.py:_post_download:961-1002`
- `firedm/controller.py:_on_completion_watchdog:1546-1583`
- `firedm/controller.py:_observer:462-485`

Trusted inputs:
- DownloadItem objects produced by FireDM itself (model.py).

Untrusted or attacker-influenced inputs:
- Per-item `on_completion_command` (only when present in the item;
  F-HIGH-4 strips it from disk-loaded items).
- `refreshed_d.__dict__` data — refreshed via `process_url` against
  attacker-controllable network metadata.

Dangerous sinks:
- `run_command(d.on_completion_command)` (controller.py:995).
- `run_command(config.on_completion_command)` (controller.py:1571).
- `download_thumbnail` invokes `download(thumbnail_url)`.

Existing validation:
- F-HIGH-4: `setting.UNSAFE_DOWNLOAD_KEYS` strips
  `on_completion_command` and `shutdown_pc` on disk load.
- `config.on_completion_command` is **not** in
  `config.settings_keys`, so disk-loaded settings cannot inject the
  global hook (verified by reading config.py:18-28).
- F-HIGH-5: `download_thumbnail` calls `is_allowed_network_url` before
  invoking `download` (controller.py:175-189).

Missing or weak validation candidates:
- CAND-13: `controller.py:392 d.__dict__.update(refreshed_d.__dict__)`
  — refreshed_d is a fresh `ObservableDownloadItem` whose attributes
  (e.g. `url`, `eff_url`, `name`) come from extractor metadata.

Candidate test ideas:
- Confirm refresh path cannot inject new attributes onto the original
  item (both sides are model-controlled instances; no schema bypass).

Candidate status:
- Not a finding. Candidate requires reproduction.

---

## Subsystem: network utilities

Files inspected:
- `firedm/utils.py:set_curl_options:101-197`
- `firedm/utils.py:get_headers:199-263`
- `firedm/utils.py:download:266-346`
- `firedm/utils.py:simpledownload:349-XXXXX`
- `firedm/worker.py:set_options:177-210`
- `firedm/worker.py:write:331-373`

Trusted inputs:
- `config.http_headers`, `config.cookie_file_path`,
  `config.proxy`, `config.username`, `config.password`,
  `config.ignore_ssl_cert` (user-controlled by definition).

Untrusted or attacker-influenced inputs:
- Any URL passed by callers that originates from extractor metadata,
  redirect targets, m3u8 segment URIs, key URIs, thumbnail URLs.

Network inputs:
- HTTP/HTTPS responses (body, headers).

Filesystem inputs:
- `cookie_file_path` (read by libcurl COOKIEFILE).

Security boundary:
- network → filesystem (cookie file read is local), network →
  subprocess (none directly), URL → protocol handler.

Dangerous sinks:
- `pycurl.Curl().setopt(URL, ...)` (utils.py:242, 301; worker.py:186).
- `urllib.request.urlopen(url)` (utils.py:355) — only via
  `simpledownload`.

Existing validation:
- `is_allowed_network_url(url)` (utils.py:41-53) — `("http","https")`
  scheme allowlist used by `download` (utils.py:269-275) and by
  `download_thumbnail` (controller.py:181).
- `pycurl.PROTOCOLS = REDIR_PROTOCOLS = PROTO_HTTP|PROTO_HTTPS`
  (utils.py:156-158) applied to every Curl object via
  `set_curl_options`. Worker calls `set_curl_options` first then
  `setopt(URL,...)` (worker.py:184-186), so PROTOCOLS gate is active.
- `MAXREDIRS=10` (utils.py:149).

Missing or weak validation candidates:
- CAND-15: `simpledownload` uses stdlib `urllib.request.urlopen`,
  which still permits `file://`, `ftp://`. Static review shows the
  only callers are `scripts/appimage/*` and `scripts/exe_build/*`
  with hardcoded URLs — not reachable from the runtime app.

Candidate test ideas:
- Static-grep callers of `simpledownload` to confirm only build
  scripts call it; do not patch (out of runtime scope).
- Verify `worker.set_options` re-applies PROTOCOLS after `c.reset()`.

Candidate status:
- Not a finding. Candidate requires reproduction.

---

## Subsystem: video extractor flow

Files inspected:
- `firedm/video.py` (full).
- `firedm/extractor_adapter.py`
- `firedm/playlist_builder.py`, `firedm/playlist_entry.py`

Relevant entry points:
- `firedm/video.py:Video.__init__:155-200`
- `firedm/video.py:get_ytdl_options:77-135`
- `firedm/video.py:load_user_extractors:790-830`
- `firedm/video.py:url_to_playlist`, `process_video`,
  `get_media_info:1656+`

Trusted inputs:
- yt_dlp / youtube_dl Python modules (already imported via the
  package set in `requirements.txt`).

Untrusted or attacker-influenced inputs:
- Remote video metadata: title, formats, thumbnail, subtitles, key
  URIs, segment URLs.
- `<sett_folder>/extractors/*.py` — only consumed when
  `config.allow_user_extractors=True`.

Security boundary:
- Network → Python module execution (only via gated extractor loader).
- Network metadata → filesystem path (via `validate_file_name`).

Dangerous sinks:
- `import_file(fp, exec_module=True)` (video.py:811 → utils.py:1304).
- `os.path.join(folder, validate_file_name(name))` for output path.
- `download_thumbnail` (controller.py:164-189).

Existing validation:
- F-CRIT-1: `get_pkg_version` AST-parses (no exec).
- F-HIGH-6: `config.allow_user_extractors=False` default gates
  `load_user_extractors` (video.py:790-830).
- F-HIGH-5: `download_thumbnail` validates URL scheme.
- `validate_file_name` strips traversal-relevant separators.

Missing or weak validation candidates:
- CAND-04: `skd://` → `https://` URL substitution in
  MediaPlaylist (video.py:1539-1541, 1564-1566). Substitution
  produces an HTTPS URL that subsequently flows through the pycurl
  allowlist.

Candidate test ideas:
- Build a synthetic m3u8 with `URI="skd://attacker.example/path"`,
  parse via `MediaPlaylist`, assert the resulting key URL is
  `https://attacker.example/path` and is fetched only through the
  allowlist.

Candidate status:
- Not a finding. Candidate requires reproduction.

---

## Subsystem: HLS / playlist flow

Files inspected:
- `firedm/video.py:MediaPlaylist:1489-1654`
- `firedm/video.py:pre_process_hls:1000-1195`
- `firedm/video.py:post_process_hls:1198-1237`
- `firedm/video.py:download_m3u8:1279-1295`
- `firedm/video.py:parse_m3u8_line:1264-1276`
- `firedm/ffmpeg_commands.py:build_hls_process_command:53-68`

Trusted inputs:
- m3u8 parser logic.

Untrusted or attacker-influenced inputs:
- Remote m3u8 document content (segment URIs, key URIs, attributes).

Filesystem inputs:
- `d.temp_folder` (user-controlled root for download temp).

Security boundary:
- Network m3u8 → ffmpeg argv → filesystem write.

Dangerous sinks:
- ffmpeg invoked via `build_hls_process_command` argv.
- pycurl fetches per segment / key URI.

Existing validation:
- `MediaPlaylist.create_local_m3u8_doc` (video.py:1621-1629)
  rewrites segment and key URIs to local paths under `d.temp_folder`
  before the m3u8 is handed to ffmpeg. ffmpeg's
  `-protocol_whitelist "file,http,https,tcp,tls,crypto"` therefore
  only sees local paths the FireDM code generated.
- Segment downloads go through pycurl with PROTOCOLS allowlist.
- `_quote()` in ffmpeg_commands.py escapes embedded `"`.

Missing or weak validation candidates:
- CAND-02 (ffmpeg argv leading-dash filename) — m3u8 path uses
  absolute path on disk; argv element starts with drive letter
  on Windows, `/` on POSIX, so leading-dash is unreachable.
- CAND-08 (HLS protocol_whitelist `file`) — see existing validation
  above; the m3u8 ffmpeg reads is the *local* one with rewritten
  URIs.

Candidate test ideas:
- Synthetic m3u8 with `file:///etc/passwd` segment URI; confirm
  `create_local_m3u8_doc` substitutes the local segment name.
- Confirm `build_hls_process_command` argv does not contain a
  leading-dash filename for any pathological input that survives
  `validate_file_name`.

Candidate status:
- Not a finding. Candidate requires reproduction.

---

## Subsystem: ffmpeg and subprocess

Files inspected:
- `firedm/utils.py:run_command:508-584`
- `firedm/ffmpeg_service.py` (full)
- `firedm/tool_discovery.py` (full)
- `firedm/ffmpeg_commands.py` (full)
- `firedm/video.py:run_ffmpeg`/`merge_video_audio`/`post_process_hls`/
  `convert_audio`/`write_metadata`
- `firedm/dependency.py:install_missing_pkgs:30-51`

Trusted inputs:
- argv lists when callers pass them directly (ffmpeg_service.py:75,
  dependency.py:46-48, FireDM.py:46).

Untrusted or attacker-influenced inputs:
- ffmpeg path in `config.ffmpeg_actual_path` (user-set or persisted).
- `cmd` strings to `run_command` built from sanitized paths.
- per-item `on_completion_command` (already mitigated).

Security boundary:
- config → subprocess (ffmpeg path).
- network metadata → ffmpeg argv (mitigated by validate_file_name).

Dangerous sinks:
- `subprocess.Popen` (utils.py:549; video.py:724).
- `subprocess.run` (FireDM.py:46; dependency.py:51;
  ffmpeg_service.py:75).
- `os.startfile` (utils.py:710, 761).

Existing validation:
- `shell=False` forced (utils.py:526).
- Strings parsed via `shlex.split` to argv (utils.py:537).
- `_quote()` escapes embedded `"` and wraps argv elements
  (ffmpeg_commands.py:22-24).
- ffmpeg path from `resolve_binary_path`: saved_path → search_dirs →
  PATH lookup → Winget root.

Missing or weak validation candidates:
- CAND-01 (binary precedence in
  `tool_discovery.resolve_binary_path`): `search_dirs` traversed
  before `shutil.which`. Caller supplies
  `(config.current_directory, config.global_sett_folder)` —
  `current_directory` is the firedm package dir or frozen executable
  dir; `global_sett_folder` is `%APPDATA%\.firedm` (user-writable).
- CAND-03 (ffmpeg argv quote escape): verified `_quote()` escapes
  `"` correctly.

Candidate test ideas:
- Plant a fake `ffmpeg.exe` (stub Python file w/ `.exe` extension) in
  a synthetic global_sett_folder, run `resolve_binary_path` with that
  search_dirs, confirm fake takes precedence. Then evaluate whether
  attacker-write-to-APPDATA crosses a defended trust boundary.

Candidate status:
- Not a finding. Candidate requires reproduction.

---

## Subsystem: config and persisted state

Files inspected:
- `firedm/config.py`
- `firedm/setting.py`
- `firedm/downloaditem.py:save_progress_info:665-671`
- `firedm/downloaditem.py:load_progress_info:673-757`

Relevant entry points:
- `setting.load_setting:165-187`
- `setting.load_d_map:46-110`
- `setting.save_setting:190-204`
- `downloaditem.load_progress_info:673-757`

Trusted inputs:
- `config.settings_keys` (firedm/config.py:18-28).

Untrusted or attacker-influenced inputs:
- `<sett_folder>/setting.cfg`
- `<sett_folder>/downloads.dat`
- `<sett_folder>/thumbnails.dat`
- `<temp_folder>/progress_info.txt`

Security boundary:
- Disk file → object/global mutation.

Dangerous sinks:
- `config.__dict__.update(safe_settings)` (setting.py:187).
- `update_object(model.ObservableDownloadItem(), sanitized_dict)`
  (setting.py:74).
- `seg.__dict__.update(item)` (downloaditem.py:731, 750).

Existing validation:
- F-CRIT-3: `safe_settings` filtered against `config.settings_keys`.
- F-HIGH-4: `UNSAFE_DOWNLOAD_KEYS = ('on_completion_command',
  'shutdown_pc')` stripped before `update_object`.
- `update_object` (utils.py:598-610) uses `hasattr()` guard, so
  unknown keys cannot create new attributes on
  `ObservableDownloadItem`.

Missing or weak validation candidates:
- CAND-09: `ffmpeg_actual_path` is in `settings_keys`, so a
  poisoned setting.cfg could substitute a malicious binary path.
  Trust boundary: the user owns `setting.cfg`.
- CAND-13/CAND-16: `seg.__dict__.update(item)` — Segment fields
  poisoned via `progress_info.txt` could rewrite `name` (the
  on-disk segment file path). The file lives in the user's own
  download/temp folder (write access already implies user-trust
  compromise). After update, lines 734-739 re-write `tempfile`
  and `url`, but do not re-validate `name`.

Candidate test ideas:
- Poison setting.cfg with `ffmpeg_actual_path = "<temp>/evil.exe"`,
  confirm `setting.load_setting` accepts it. (Documenting the trust
  boundary.)
- Poison progress_info.txt with `seg.name="<absolute path
  outside temp_folder>"`, confirm it's accepted.

Candidate status:
- Not a finding. Candidate requires reproduction.

---

## Subsystem: update mechanism

Files inspected:
- `firedm/update.py`

Relevant entry points:
- `update.check_for_new_version:55-90`
- `update.get_pkg_latest_version:93-166`
- `update.update_pkg:187-294`
- `update.rollback_pkg:297+`

Trusted inputs:
- Hardcoded URLs:
  - `https://api.github.com/repos/GurucharanSavanth/FireDM/releases/latest`
  - `https://pypi.org/pypi/{pkg}/json`

Untrusted or attacker-influenced inputs:
- GitHub release JSON, PyPI JSON, downloaded wheel/zip/tar.

Security boundary:
- Network → filesystem (extract).
- Package metadata → version comparison.

Dangerous sinks:
- `safe_extract_tar`, `safe_extract_zip` (utils.py:1338-1355).
- `download(url, fp=z_fp)` for wheel/zip retrieval.

Existing validation:
- `packaging.version.parse` for version comparison.
- `safe_extract_*` containment + symlink/hardlink rejection.
- Source URLs hardcoded; no setting.cfg override of update URLs
  (verified: not in `settings_keys`).
- pycurl protocol allowlist applies.

Missing or weak validation candidates:
- CAND-06: no signature/hash verification on downloaded packages
  (matches stock pip trust model: HTTPS+CA only).

Candidate test ideas:
- Construct a synthetic wheel containing a `..` traversal entry,
  feed to `safe_extract_zip`; confirm rejection.

Candidate status:
- Not a finding. Candidate requires reproduction.

---

## Subsystem: tool discovery

Files inspected:
- `firedm/tool_discovery.py`
- `firedm/ffmpeg_service.py`
- callers: `firedm/controller.py:68-72`, `firedm/video.py:71-90`,
  `scripts/collect_runtime_diagnostics.py`

Relevant entry points:
- `tool_discovery.resolve_binary_path:43-74`
- `ffmpeg_service.locate_ffmpeg:53-89`
- `ffmpeg_service.resolve_ffmpeg_path:33-50`

Trusted inputs:
- `operating_system` discriminator from `platform.system()`.
- `path_lookup` injected by tests; defaults to `shutil.which`.

Untrusted or attacker-influenced inputs:
- `saved_path` from config (`config.ffmpeg_actual_path`).
- `search_dirs` items: `(config.current_directory,
  config.global_sett_folder)` per controller.py:70.
- Winget package root (`%LOCALAPPDATA%\Microsoft\WinGet\Packages`).

Security boundary:
- env/PATH → binary execution; APPDATA → binary execution.

Dangerous sinks:
- The returned path is later passed to ffmpeg via `subprocess.run`
  (`ffmpeg_service.locate_ffmpeg:83`) and to `run_command(... ffmpeg
  cmd)` for actual processing.

Existing validation:
- Order: saved_path (from config) → search_dirs → `shutil.which` →
  Winget. The last three are defenders against missing
  `saved_path`. None of them does signature verification.

Missing or weak validation candidates:
- CAND-01 (search_dirs precedence over `shutil.which`).

Candidate test ideas:
- See ffmpeg subsystem above.

Candidate status:
- Not a finding. Candidate requires reproduction.

---

## Subsystem: archive extraction

Files inspected:
- `firedm/utils.py:_archive_member_target:1317-1335`
- `firedm/utils.py:safe_extract_zip:1338-1344`
- `firedm/utils.py:safe_extract_tar:1346-1355`
- `firedm/update.py:234-238` (callers)

Trusted inputs:
- The base `extract_folder` chosen by FireDM.

Untrusted inputs:
- Archive member names (from any tar/zip downloaded by `update_pkg`).

Security boundary:
- archive → filesystem.

Dangerous sinks:
- `zipfile.ZipFile.extractall`, `tarfile.TarFile.extractall`.

Existing validation:
- `_archive_member_target` rejects empty names, absolute paths,
  Windows drive letters, and any name whose
  `os.path.commonpath([base,target])` is not `base`.
- `safe_extract_tar` rejects symlinks and hardlinks before
  extracting.

Missing or weak validation candidates:
- None that survive the existing checks. Edge case: alternate data
  stream-style names (`evil.txt:hidden.exe`) — the colon survives
  the sanitizer because `:` is not flagged by `_archive_member_target`,
  but the resulting target path stays under `extract_folder`.

Candidate test ideas:
- Synthetic zip with `..\..\evil.exe` → expect ValueError.
- Synthetic tar with symlink → expect ValueError.

Candidate status:
- Not a finding. Candidate requires reproduction.

---

## Subsystem: filesystem output path handling

Files inspected:
- `firedm/utils.py:validate_file_name:438-465`
- `firedm/utils.py:rename_file:492-505`
- `firedm/downloaditem.py:name`/`target_file`/`temp_folder`/`temp_file`
  properties (lines 395-417)
- `firedm/controller.py:rename:153-161`
- `firedm/controller.py:download_thumbnail:164-189`

Trusted inputs:
- `download_folder` chosen by user (config.download_folder default
  `~/Downloads`).

Untrusted inputs:
- Title/filename derived from extractor metadata.

Security boundary:
- Network metadata → filesystem path.

Dangerous sinks:
- `os.path.join(folder, name)` (downloaditem.py:411).
- File write inside the resulting path during segment download and
  final rename.

Existing validation:
- `validate_file_name` strips control chars, characters outside the
  BMP, plus `'`, `"`, and the punctuation class
  `~`` `` `#` `$` `&` `*` `()` `\` `|` `[]` `{}` `;` `<>` `/` `?` `!` `^` `,` `:`.
- 255-character truncation.

Missing or weak validation candidates:
- CAND-10: Windows reserved names (CON, PRN, AUX, NUL, LPT1-9,
  COM1-9) are not filtered. Impact: write fails on Windows (DoS,
  not security boundary).
- CAND-02: ffmpeg argv leading-dash via filename is mitigated by
  `os.path.join` producing an absolute path that begins with
  drive letter or `/`.

Candidate test ideas:
- `validate_file_name('CON.mp4')` → observe behavior.
- `os.path.join('C:/Users/Foo/Downloads', '-evil.mp4')` → assert
  argv element does not start with `-`.

Candidate status:
- Not a finding. Candidate requires reproduction.

---

## Subsystem: GUI open / open-folder behavior

Files inspected:
- `firedm/utils.py:open_file:697-728`
- `firedm/utils.py:open_folder:730-769`
- `firedm/tkview.py:url_watchdog` (clipboard) — inferred via the
  regex at 146 and event flow.

Trusted inputs:
- Path argument from FireDM-internal model fields.

Untrusted inputs:
- Clipboard text matched by
  `^(https?|ftps?|file)://`.

Security boundary:
- GUI → OS opener (file/URL).

Dangerous sinks:
- `os.startfile(fp)` (utils.py:710, 761).
- `subprocess.Popen(shlex.split(f'xdg-open "{path}"'))`
  (utils.py:722, 724, 766).
- `subprocess.Popen(shlex.split(f'explorer /select, "{file}"'))`
  (utils.py:759).

Existing validation:
- Path comes from sanitized `target_file`/`folder`.
- On Windows, `"` is illegal in NTFS paths (no embedded quote
  escape).
- `validate_file_name` strips `"`.

Missing or weak validation candidates:
- CAND-07: theoretical POSIX path with embedded `"` could break
  the `xdg-open "{path}"` quoting since `validate_file_name`
  strips `"` only from filenames; the *folder* could contain `"`
  on POSIX. Realistic only if the user typed `"` into the folder
  picker — same trust boundary.

Candidate test ideas:
- POSIX path with embedded `"` passed to `open_folder`; capture
  argv via `monkeypatch(subprocess.Popen)`; assert the argv split
  does not produce a shell escape.

Candidate status:
- Not a finding. Candidate requires reproduction.

---

## Subsystem: threading / concurrency

Files inspected:
- `firedm/controller.py:_observer:462-485`,
  `_download_q_handler:700-710`,
  `_scheduled_downloads_handler:712-723`,
  `_on_completion_watchdog:1546-1583`
- `firedm/brain.py:76-84` (daemon thread set)
- `firedm/utils.py:threaded` decorator (66-76)
- `firedm/model.py:_notify` (callback fan-out)

Trusted inputs:
- Internal state machine.

Untrusted inputs:
- None directly cross a security boundary in the threading layer.

Security boundary:
- Worker thread → GUI main thread (correctness, not confidentiality).

Dangerous sinks:
- Tk widget calls via `view.update_view` from the `_observer` daemon
  thread (correctness/crash risk, not security).

Missing or weak validation candidates:
- CAND-12: thread-safety of GUI updates. Out of audit scope (DoS /
  correctness, not security boundary).

Candidate status:
- Not a finding. Candidate requires reproduction.

---

## Subsystem: packaging / runtime resource lookup

Files inspected:
- `firedm/config.py:43,69-75`
- `firedm/app_paths.py` (full)
- `firedm/update.py:174,205`
- `scripts/firedm-win.spec` (PyInstaller spec)

Trusted inputs:
- `sys.executable`, `__file__`.

Untrusted inputs:
- Environment variables `APPDATA`, `LOCALAPPDATA`, `HOME`.

Security boundary:
- Environment → settings folder; environment → tool discovery.

Dangerous sinks:
- `sys.path.insert(0, current_directory)` (config.py:75).
- `sys.path.insert(0, os.path.dirname(current_directory))`
  (config.py:74).

Existing validation:
- `current_directory` is the firedm package dir or the frozen
  executable's directory — not the user's CWD.
- `app_paths.resolve_global_settings_dir` falls back through env
  vars in a controlled order.

Missing or weak validation candidates:
- CAND-05: sys.path injection via writable `current_directory`
  (only relevant if the FireDM install is in a user-writable
  location, which is the same trust boundary as code modification).

Candidate test ideas:
- Inspect `sys.path[:2]` after import; assert paths are absolute
  and within the FireDM install or package tree.

Candidate status:
- Not a finding. Candidate requires reproduction.

---

## Subsystem: test infrastructure

Files inspected:
- `tests/test_security.py` (existing 7 tests for F-CRIT-1..F-HIGH-6)
- `tests/test_ffmpeg_service.py`, `tests/test_extractor_service.py`,
  `tests/test_ffmpeg_pipeline.py`, `tests/test_packaged_diagnostics.py`
- `pyproject.toml [tool.pytest.ini_options]`

Trusted inputs:
- Pytest harness, repo fixtures.

Untrusted inputs:
- None (test fixtures are entirely synthetic and live in `tmp_path`).

Existing validation:
- Tests already use `tmp_path`/`monkeypatch`; no real network.
- `xfail_strict = true`.

Missing or weak validation candidates:
- Coverage gaps for: pycurl PROTOCOLS persistence after
  `Worker.reset()` (worker.py); `_archive_member_target` traversal
  reproduction; `safe_extract_tar` symlink rejection;
  `validate_file_name` quoting; `MediaPlaylist.create_local_m3u8_doc`
  rewriting.
- These are *test-coverage* gaps, not vulnerabilities. They can be
  added if a related candidate is admitted.

Candidate status:
- Not applicable (test code is not a security boundary).

---

## Mandatory Subsystems Confirmed Absent or Inapplicable

- "current working directory contents affecting executable lookup":
  `tool_discovery.resolve_binary_path` does **not** consult the OS CWD
  — only the explicit `search_dirs` it is given. Confirmed by reading
  tool_discovery.py:43-74.
- "169.254.169.254" (cloud metadata): no occurrence anywhere in the
  codebase.

---

## Candidate ID Index

| ID | Subsystem(s) | Title |
|----|--------------|-------|
| CAND-01 | tool discovery, ffmpeg | APPDATA-planted ffmpeg.exe pre-empts PATH |
| CAND-02 | filesystem path, HLS | ffmpeg argv leading-dash via filename |
| CAND-03 | ffmpeg | argv quote escape in `_quote()` |
| CAND-04 | extractor | `skd://` → `https://` URL substitution |
| CAND-05 | packaging | `sys.path.insert` of install dir |
| CAND-06 | update | PyPI/GitHub package no signature/hash verification |
| CAND-07 | GUI opener | POSIX path quote escape in `xdg-open` |
| CAND-08 | HLS | ffmpeg `-protocol_whitelist file,...` |
| CAND-09 | config | `ffmpeg_actual_path` poisoning via setting.cfg |
| CAND-10 | filesystem path | Windows reserved filename DoS |
| CAND-11 | HLS | unbounded m3u8 segment count DoS |
| CAND-12 | threading | Tk widget mutation from worker thread |
| CAND-13 | controller | `d.__dict__.update(refreshed_d.__dict__)` refresh path |
| CAND-14 | startup | `config.__dict__.update(sett)` from CLI Namespace |
| CAND-15 | network | `simpledownload` uses `urllib.request.urlopen` |
| CAND-16 | config | `seg.__dict__.update(item)` from `progress_info.txt` |
