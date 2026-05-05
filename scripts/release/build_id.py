from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DIST_DIR = REPO_ROOT / "dist"
BUILD_ID_RE = re.compile(r"(?<!\d)(?P<date>\d{8})_V(?P<index>[1-9]\d*)(?!\d)")
TAG_PREFIX = "build-"


@dataclass(frozen=True)
class BuildIdParts:
    date: str
    index: int


@dataclass(frozen=True)
class BuildIdSelection:
    build_id: str
    date: str
    index: int
    tag: str
    release_name: str
    source_date_mode: str
    discovered_existing_ids: list[str]
    collision_status: str


def parse_build_id(value: str) -> BuildIdParts:
    match = BUILD_ID_RE.fullmatch(value.strip())
    if not match:
        raise ValueError(f"Invalid build ID {value!r}; expected YYYYMMDD_VN")
    date = match.group("date")
    index = int(match.group("index"))
    validate_date(date)
    return BuildIdParts(date=date, index=index)


def validate_date(value: str) -> None:
    try:
        parsed = datetime.strptime(value, "%Y%m%d")
    except ValueError as exc:
        raise ValueError(f"Invalid build date {value!r}; expected YYYYMMDD") from exc
    if parsed.strftime("%Y%m%d") != value:
        raise ValueError(f"Invalid build date {value!r}; expected YYYYMMDD")


def format_build_id(date: str, index: int) -> str:
    validate_date(date)
    if index < 1:
        raise ValueError("Build ID index must be >= 1")
    return f"{date}_V{index}"


def validate_build_id(value: str) -> bool:
    try:
        parse_build_id(value)
    except ValueError:
        return False
    return True


def build_tag_name(build_id: str) -> str:
    parse_build_id(build_id)
    return f"{TAG_PREFIX}{build_id}"


def build_release_name(build_id: str) -> str:
    parse_build_id(build_id)
    return f"FireDM {build_id}"


def today_build_date() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d")


def extract_build_ids(text: str) -> set[str]:
    ids: set[str] = set()
    for match in BUILD_ID_RE.finditer(text):
        build_id = f"{match.group('date')}_V{match.group('index')}"
        if validate_build_id(build_id):
            ids.add(build_id)
    return ids


def git_values(args: list[str]) -> list[str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def discover_local_artifact_build_ids(dist_dir: Path = DIST_DIR) -> set[str]:
    ids: set[str] = set()
    if not dist_dir.exists():
        return ids
    for path in dist_dir.rglob("*"):
        ids.update(extract_build_ids(path.name))
        if path.is_file() and path.suffix.lower() == ".json" and "manifest" in path.name.lower():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                continue
            build_id = payload.get("build_id") or payload.get("buildId")
            if isinstance(build_id, str) and validate_build_id(build_id):
                ids.add(build_id)
    return ids


def discover_local_tag_build_ids() -> set[str]:
    ids: set[str] = set()
    for tag in git_values(["tag", "--list", f"{TAG_PREFIX}*"]):
        if tag.startswith(TAG_PREFIX):
            ids.update(extract_build_ids(tag.removeprefix(TAG_PREFIX)))
    return ids


def discover_remote_tag_build_ids(remote: str = "origin") -> set[str]:
    ids: set[str] = set()
    for ref in git_values(["ls-remote", "--tags", "--refs", remote, f"refs/tags/{TAG_PREFIX}*"]):
        ids.update(extract_build_ids(ref))
    return ids


def discover_github_release_build_ids() -> set[str]:
    if not shutil.which("gh"):
        return set()
    try:
        result = subprocess.run(
            ["gh", "release", "list", "--limit", "200", "--json", "tagName,name"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return set()
    if result.returncode != 0:
        return set()
    try:
        releases = json.loads(result.stdout)
    except json.JSONDecodeError:
        return set()
    ids: set[str] = set()
    for release in releases:
        if isinstance(release, dict):
            ids.update(extract_build_ids(str(release.get("tagName", ""))))
            ids.update(extract_build_ids(str(release.get("name", ""))))
    return ids


def discover_existing_build_ids(
    *,
    dist_dir: Path = DIST_DIR,
    include_local_artifacts: bool = True,
    include_local_tags: bool = True,
    include_remote_tags: bool = False,
    include_github_releases: bool = False,
) -> set[str]:
    ids: set[str] = set()
    if include_local_artifacts:
        ids.update(discover_local_artifact_build_ids(dist_dir))
    if include_local_tags:
        ids.update(discover_local_tag_build_ids())
    if include_remote_tags:
        ids.update(discover_remote_tag_build_ids())
    if include_github_releases:
        ids.update(discover_github_release_build_ids())
    return ids


def next_build_id(date: str, sources: Iterable[str]) -> str:
    validate_date(date)
    max_index = 0
    for build_id in sources:
        parts = parse_build_id(build_id)
        if parts.date == date:
            max_index = max(max_index, parts.index)
    return format_build_id(date, max_index + 1)


def select_build_id(
    *,
    date: str | None = None,
    build_id: str | None = None,
    allow_overwrite: bool = False,
    include_remote_tags: bool = False,
    include_github_releases: bool = False,
    dist_dir: Path = DIST_DIR,
) -> BuildIdSelection:
    discovered = discover_existing_build_ids(
        dist_dir=dist_dir,
        include_remote_tags=include_remote_tags,
        include_github_releases=include_github_releases,
    )
    source_date_mode = "override" if date else "local"
    if build_id:
        parts = parse_build_id(build_id)
        if date and parts.date != date:
            raise ValueError(f"--build-id date {parts.date} does not match --date {date}")
        if build_id in discovered and not allow_overwrite:
            raise ValueError(f"Build ID already exists: {build_id}. Use --allow-overwrite for explicit rebuilds.")
        selected = build_id
        collision_status = "overwrite-allowed" if build_id in discovered else "explicit-no-collision"
    else:
        build_date = date or today_build_date()
        validate_date(build_date)
        selected = next_build_id(build_date, discovered)
        parts = parse_build_id(selected)
        collision_status = "generated-next"
    parts = parse_build_id(selected)
    return BuildIdSelection(
        build_id=selected,
        date=parts.date,
        index=parts.index,
        tag=build_tag_name(selected),
        release_name=build_release_name(selected),
        source_date_mode=source_date_mode,
        discovered_existing_ids=sorted(discovered),
        collision_status=collision_status,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and validate FireDM build IDs.")
    parser.add_argument("--date", help="Override build date as YYYYMMDD.")
    parser.add_argument("--build-id", help="Explicit build ID for rebuild/release use.")
    parser.add_argument("--allow-overwrite", action="store_true")
    parser.add_argument("--include-remote-tags", action="store_true")
    parser.add_argument("--include-github-releases", action="store_true")
    parser.add_argument("--print-next", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    if args.validate:
        if not args.build_id:
            parser.error("--validate requires --build-id")
        parts = parse_build_id(args.build_id)
        payload = {
            "build_id": args.build_id,
            "date": parts.date,
            "index": parts.index,
            "tag": build_tag_name(args.build_id),
            "release_name": build_release_name(args.build_id),
            "valid": True,
        }
        print(json.dumps(payload, indent=2) if args.json_output else "valid")
        return

    if args.print_next:
        selection = select_build_id(
            date=args.date,
            build_id=args.build_id,
            allow_overwrite=args.allow_overwrite,
            include_remote_tags=args.include_remote_tags,
            include_github_releases=args.include_github_releases,
        )
        if args.json_output:
            print(json.dumps(asdict(selection), indent=2))
        else:
            print(selection.build_id)
        return

    parser.error("No action requested. Use --print-next or --validate.")


if __name__ == "__main__":
    main()
