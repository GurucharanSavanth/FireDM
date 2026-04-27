from __future__ import annotations

import argparse
from pathlib import Path

from common import CHECKSUMS_DIR, DIST_DIR, INSTALLERS_DIR, LICENSES_DIR, PORTABLE_DIR, ensure_dir, file_sha256


def publishable_files(root: Path) -> list[Path]:
    candidates = []
    for folder, patterns in (
        (INSTALLERS_DIR, ("*.exe", "*.manifest.json")),
        (PORTABLE_DIR, ("*.zip",)),
        (LICENSES_DIR, ("license-inventory.json",)),
    ):
        if not folder.is_dir():
            continue
        for pattern in patterns:
            candidates.extend(path for path in folder.glob(pattern) if path.is_file())

    for name in ("release-manifest.json", "release-body.md"):
        path = DIST_DIR / name
        if path.is_file():
            candidates.append(path)

    return sorted({path.resolve() for path in candidates if root == path.resolve() or root in path.resolve().parents})


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SHA256 checksums for release artifacts.")
    parser.add_argument("--root", default=str(DIST_DIR))
    args = parser.parse_args()
    root = Path(args.root).resolve()
    files = publishable_files(root)
    ensure_dir(CHECKSUMS_DIR)
    output = CHECKSUMS_DIR / "SHA256SUMS.txt"
    lines = [f"{file_sha256(path)}  {path.relative_to(root).as_posix()}" for path in files]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Checksums written: {output}")


if __name__ == "__main__":
    main()
