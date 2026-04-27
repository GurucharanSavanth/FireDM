from __future__ import annotations

import argparse
from pathlib import Path

from build_id import validate_build_id
from common import (
    CHECKSUMS_DIR,
    DIST_DIR,
    INSTALLERS_DIR,
    LICENSES_DIR,
    PORTABLE_DIR,
    checksum_file_name,
    ensure_dir,
    file_sha256,
    release_manifest_name,
    release_notes_name,
)


def publishable_files(root: Path, build_id: str) -> list[Path]:
    candidates = []
    for folder, patterns in (
        (INSTALLERS_DIR, (f"*{build_id}*.exe", f"*{build_id}*.manifest.json")),
        (PORTABLE_DIR, (f"*{build_id}*.zip",)),
        (LICENSES_DIR, (f"license-inventory_{build_id}.json",)),
    ):
        if not folder.is_dir():
            continue
        for pattern in patterns:
            candidates.extend(path for path in folder.glob(pattern) if path.is_file())

    for name in (release_manifest_name(build_id), release_notes_name(build_id)):
        path = DIST_DIR / name
        if path.is_file():
            candidates.append(path)

    return sorted({path.resolve() for path in candidates if root == path.resolve() or root in path.resolve().parents})


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SHA256 checksums for release artifacts.")
    parser.add_argument("--root", default=str(DIST_DIR))
    parser.add_argument("--build-id", required=True)
    args = parser.parse_args()
    if not validate_build_id(args.build_id):
        raise SystemExit(f"Invalid build ID: {args.build_id}")
    root = Path(args.root).resolve()
    files = publishable_files(root, args.build_id)
    ensure_dir(CHECKSUMS_DIR)
    output = CHECKSUMS_DIR / checksum_file_name(args.build_id)
    lines = [f"# build_id: {args.build_id}"]
    lines.extend(f"{file_sha256(path)}  {path.relative_to(root).as_posix()}" for path in files)
    text = "\n".join(lines) + "\n"
    output.write_text(text, encoding="utf-8")
    (CHECKSUMS_DIR / "SHA256SUMS.txt").write_text(text, encoding="utf-8")
    print(f"Checksums written: {output}")


if __name__ == "__main__":
    main()
