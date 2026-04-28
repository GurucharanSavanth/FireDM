# Code Signing

Status: optional hook implemented, actual signing blocked until certificate/tooling is configured.

No certificate, private key, `signtool.exe` path, timestamp server, or CI secret configuration is present in this checkout.

## Build Environment Variables

`scripts/release/build_installer.py` supports these variables:

- `FIREDM_SIGNTOOL`: path or command name for `signtool.exe`
- `FIREDM_SIGN_CERT_SHA1`: certificate thumbprint in the Windows certificate store
- `FIREDM_SIGN_PFX`: path to a PFX file
- `FIREDM_SIGN_PFX_PASSWORD`: PFX password; never print or commit
- `FIREDM_SIGN_TIMESTAMP_URL`: RFC 3161 timestamp URL
- `FIREDM_REQUIRE_SIGNING=1`: fail the installer build if signing is not configured

The build script redacts the PFX password from printed command lines and runs
`signtool verify /pa /v` after signing.

Unsigned artifact implications:
- Windows SmartScreen and AV products may warn on first-run installer artifacts.
- Release notes must mark installer artifacts unsigned.
- Maintainers should sign both installer EXE and, if possible, packaged application EXEs before public release.
- `scripts/release/github_release.py` refuses stable releases when installer
  artifacts are unsigned.
- `.github/workflows/draft-release.yml` sets `FIREDM_REQUIRE_SIGNING=1` for
  build-ID tag runs and stable manual runs.

Required future inputs:
- code signing certificate
- secure private-key storage
- timestamp server URL
- `signtool.exe` availability in CI/local build host
- verification command after signing

Do not commit certificates or private keys.
