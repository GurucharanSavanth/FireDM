# 08 Universal Bootstrapper Status

Evidence labels: observed, blocked.

## Status
- blocked: universal bootstrapper was not implemented.

## Reason
- observed: only one architecture payload exists: `dist/payloads/win-x64/FireDM`.
- observed: release scripts reject `x86` and `arm64`.
- blocked: a universal bootstrapper must select between at least two validated payloads or it risks pretending architecture support that does not exist.

## Safe Current Artifact
- observed: current installer is architecture-specific: `FireDM_Setup_2022.2.5_dev_win_x64.exe`.

## Next Gate
- blocked: implement universal bootstrapper only after x86 and/or ARM64 payloads are built, checksummed, and validated.
