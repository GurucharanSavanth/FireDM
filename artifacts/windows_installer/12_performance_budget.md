# 12 Performance Budget

Evidence labels: measured, blocked, inferred.

## Measured In This Pass
- measured: x64 payload contains 1168 files and 69,734,739 bytes.
- measured: `firedm.exe --help` against the x64 one-dir payload took 356.1728 ms, 317.9462 ms, and 306.6594 ms in three local samples.
- measured: installer `--help` took 1173.8911 ms and 995.8756 ms in two local samples.

## Budget Direction
- inferred: installed-tree one-dir runtime remains preferred over one-file app runtime because it avoids app extraction on every launch.
- inferred: installer one-file extraction cost is acceptable because it runs during install/repair/uninstall, not every app launch.

## Blocked Measurements
- blocked: GUI cold launch, GUI warm launch, GUI idle memory, active download memory, CPU during downloads, and FFmpeg post-processing CPU were not measured in this pass.
- required future action: run a GUI/performance scenario with a controlled download target and explicit process sampling before claiming resource budgets.

