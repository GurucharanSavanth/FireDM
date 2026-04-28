# 10 Security Review

Evidence labels: changed = modified by this pass; verified = tested; inferred = code reasoning.

## Native Messaging
- changed: controller endpoint no longer opens by default.
- changed: endpoint opens only when `browser_integration` is enabled.
- changed: controller transport uses `multiprocessing.connection` authkey from repo/user settings secret.
- changed: native message size capped at 1 MiB.
- changed: native message handler accepts only `download` and `capture_stream`.
- changed: non-http(s) URLs are rejected before download handoff.
- changed: `Authorization`, `Proxy-Authorization`, `Cookie`, `Set-Cookie`, malformed headers, and non-string-like header values are stripped.
- verified: browser integration tests and security tests pass.

## DRM/Protected Media
- changed: active ClearKey/AES decrypt behavior removed.
- changed: `drm_decryption` plugin fails closed and exposes no decrypt/fetch APIs.
- verified: DRM placeholder tests pass; full pytest no longer needs `cryptography`.

## Subprocess/Path
- changed: native host no longer uses stdout logger.
- observed: post-processing plugin still builds command strings for optional disabled steps; deferred because not in active default path.
- observed: legacy AppImage/exe scripts still contain `shell=True`; historical reference scripts, not current release path.

## Remaining Security Risks
- inferred: same-user processes with access to the settings secret can authenticate to the local endpoint; stronger OS ACL/token isolation is future work.
- inferred: real browser extension origin behavior not verified; default allowed origin remains placeholder until a real extension ID exists.
- inferred: optional native extractor/anti-detection plugins remain default-off and need separate policy review before release enablement.
