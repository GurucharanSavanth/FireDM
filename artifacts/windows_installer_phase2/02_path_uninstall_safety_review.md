# 02 Path Uninstall Safety Review

Evidence labels: observed, changed, verified.

## Previous Risk
- observed: the first-pass `safe_rmtree()` checked only path depth. A custom `--install-dir` could point at an unmanaged non-empty directory and be removed during install replacement or uninstall.

## Changes
- changed: `assert_safe_root()` rejects drive roots, shallow roots, Windows directory, Program Files root, user profile root, temp root, and the repository root itself.
- changed: `assert_can_replace_install_dir()` allows replacement only for empty directories or installer-owned directories with matching state metadata.
- changed: `assert_can_uninstall_dir()` requires installer-owned state before uninstall removes an install tree.
- changed: safe ZIP extraction still rejects traversal, and extraction destination must pass safe-root checks.
- changed: payload ZIP SHA256 is checked against installer manifest and every ZIP member CRC is tested before extraction.

## Regression Tests
- verified: `tests/release/test_installer_bootstrap_paths.py` covers traversal rejection, checksum mismatch, valid payload verification, unmanaged replace refusal, installer-owned replace, unmanaged uninstall refusal, log path validation, process-local launcher environment, and shortcut paths via mocks.

## Runtime Validation
- verified: isolated installer validation installs only to a temp install root and removes only that generated root during uninstall.
