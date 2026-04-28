# 11 Platform Review

Evidence labels: verified = command run; inferred = local-code reasoning.

## Windows
- verified host: Windows 10/11 x64, Python 3.10.11, PowerShell 5.1.
- verified `multiprocessing.connection.Listener` can create the local controller listener on this host.
- verified source help/import/native-host smoke.
- verified isolated PyInstaller build and packaged CLI/import smoke.
- inferred native messaging launcher handles paths with spaces by quoting each command part.

## Linux
- inferred Unix endpoint path uses tempdir socket path through `multiprocessing.connection`.
- inferred launcher is a POSIX shell script with `0700` chmod attempt.
- not verified on Linux in this pass.

## Cross-Platform Notes
- changed native endpoint cleanup only unlinks Unix socket paths, never Windows pipe names.
- changed package/source entry path supports `--native-host`.
- not verified: browser-native launch behavior on Chrome/Firefox/Edge on either platform.
