# Security Boundaries

## Hard No Implementation Areas
- prohibited: DRM bypass.
- prohibited: protected-media circumvention.
- prohibited: Widevine, PlayReady, FairPlay, or license-server bypass.
- prohibited: media-key extraction.
- prohibited: browser credential theft.
- prohibited: silent cookie harvesting.
- prohibited: arbitrary local file reads.
- prohibited: public local API binding by default.
- prohibited: shell execution by default.
- prohibited: path traversal.
- prohibited: writing outside configured download root unless explicitly configured safe.
- prohibited: unsafe deserialization.
- prohibited: execution from saved state.
- prohibited: leaking tokens, cookies, authorization headers, proxy passwords, browser-cookie data, or local API tokens.

## Browser Integration Rules
- observed: `firedm/plugins/browser_integration.py` is disabled by default.
- observed: Controller native message handling rejects non-HTTP download and stream URLs.
- required: Browser integration must require explicit user enablement.
- required: Native/browser handoff must use existing controller and queue paths.
- required: Do not duplicate download engine logic in browser code.
- required: Do not collect cookies silently.
- required: Do not accept unsafe schemes such as local file, FTP, SMB, gopher, telnet, or TFTP.

## Local API Rules
- required: Bind local-only by default.
- required: Never bind all interfaces by default.
- required: Use random local token or authkey.
- required: Require token/authkey for mutating endpoints.
- required: Validate payload shape and maximum size.
- required: Reject unsafe schemes.
- required: Redact secrets from logs.

## Cookie/Header Handling Rules
- observed: `Controller._coerce_native_headers()` drops authorization, proxy-authorization, cookie, and set-cookie headers.
- required: Never log raw cookies or auth headers.
- required: Never persist browser cookies unless user explicitly selects a cookie file.
- required: Treat proxy credentials as secrets.
- required: Pass only validated safe headers from browser/native handoff into download paths.

## Diagnostics Redaction Rules
- observed: `pipeline_logger.py` redacts credential-bearing URL query and fragment parameters.
- required: Redact cookies.
- required: Redact Set-Cookie.
- required: Redact Authorization.
- required: Redact Proxy-Authorization.
- required: Redact bearer tokens.
- required: Redact local API tokens.
- required: Redact passwords.
- required: Redact proxy credentials.
- required: Redact browser-cookie data.
- required: Avoid arbitrary local file inclusion in diagnostics.
- required: Mark diagnostic artifacts as safe or unsafe before sharing.
- required: Auxiliary downloads or diagnostics that buffer responses in memory must enforce a clear size cap.

## Completion Action Rules
- observed: `setting.load_d_map()` drops unsafe persisted completion-action keys.
- required: Completion commands must never execute from restored saved state.
- required: User-triggered completion commands need explicit current-session opt-in.
- required: Do not add silent shutdown, script, or shell actions.

## Path Safety Rules
- observed: `utils.safe_extract_zip()` and `utils.safe_extract_tar()` validate archive member targets and reject tar links.
- required: Use `pathlib` where practical for new code.
- required: Keep final paths under configured download root unless an explicit safe override exists.
- required: Reject traversal.
- required: Sanitize Windows reserved names.
- required: Preserve Linux case-sensitive behavior.
- required: Validate archive extraction paths before writing.

## Subprocess Rules
- observed: `FireDM.open_config_editor()` uses argv list and `shell=False`.
- observed: `ffmpeg_service.py` probes tools with argv lists.
- observed: Some legacy ffmpeg paths still build string commands before `utils.run_command()` forces `shell=False`.
- required: No `shell=True` unless explicitly justified and reviewed.
- required: Prefer argv lists.
- required: Never interpolate URLs, filenames, headers, cookies, metadata, or user input into shell strings.
- required: Paths containing quotes, spaces, or platform-specific separators must be handled as argv elements, not shell-quoted strings.
- required: Trusted script execution must be opt-in and restricted to configured trusted directories.
- required: Redact secrets from printed command lines.

## Packaging Secret Rules
- observed: code-signing docs state no signing certificate or private key is present in this checkout.
- required: Do not write signing secrets to docs, logs, manifests, or generated release notes.
- required: Do not print PFX passwords, API tokens, or CI tokens.
- required: Stable public builds must not claim signing unless validation artifacts prove it.

## Review Checklist
- Check URL scheme allowlists.
- Check path joins and extraction paths.
- Check subprocess command construction.
- Check saved-state deserialization.
- Check cookie/header handling.
- Check diagnostics redaction.
- Check local API bind/auth defaults.
- Check plugin default-disabled behavior.
- Check package artifact paths and signing secret handling.
