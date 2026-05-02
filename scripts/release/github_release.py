from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from build_id import build_release_name, build_tag_name, validate_build_id
from common import DIST_DIR, file_sha256, git_value, release_manifest_name


@dataclass(frozen=True)
class ReleasePlan:
    build_id: str
    tag: str
    title: str
    channel: str
    draft: bool
    prerelease: bool
    notes: Path
    artifacts: list[Path]
    command: list[str]


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"Release manifest missing: {path}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Release manifest is not valid JSON: {path}") from exc
    build_id = manifest.get("build_id")
    if not isinstance(build_id, str) or not validate_build_id(build_id):
        raise SystemExit("Release manifest missing valid build_id")
    return manifest


def dist_root_for_manifest(path: Path) -> Path:
    if path.parent.name == "dist":
        return path.parent
    return DIST_DIR


def resolve_dist_path(dist_root: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        raise SystemExit(f"Manifest contains absolute local path: {value}")
    resolved = (dist_root / candidate).resolve()
    root = dist_root.resolve()
    if resolved != root and root not in resolved.parents:
        raise SystemExit(f"Manifest path escapes dist: {value}")
    return resolved


def verify_manifest_artifacts(manifest: dict[str, Any], manifest_path: Path) -> list[Path]:
    build_id = manifest["build_id"]
    dist_root = dist_root_for_manifest(manifest_path)
    artifacts: list[Path] = []
    for artifact in manifest.get("artifacts", []):
        if not isinstance(artifact, dict):
            raise SystemExit("Manifest artifact entry is not an object")
        rel = artifact.get("path")
        expected_sha = artifact.get("sha256")
        if not isinstance(rel, str) or not rel:
            raise SystemExit("Manifest artifact missing path")
        if build_id not in Path(rel).name:
            raise SystemExit(f"Refusing stale artifact without build ID {build_id}: {rel}")
        path = resolve_dist_path(dist_root, rel)
        if not path.is_file():
            raise SystemExit(f"Manifest artifact missing: {path}")
        actual_sha = file_sha256(path)
        if expected_sha and actual_sha != expected_sha:
            raise SystemExit(f"Checksum mismatch for {rel}: expected {expected_sha}, got {actual_sha}")
        artifacts.append(path)
    if not artifacts:
        raise SystemExit("Release manifest has no artifacts")
    return artifacts


def verify_checksums(manifest: dict[str, Any], manifest_path: Path) -> Path:
    build_id = manifest["build_id"]
    checksums_rel = manifest.get("checksumsPath")
    if not isinstance(checksums_rel, str) or not checksums_rel:
        raise SystemExit("Release manifest missing checksumsPath")
    dist_root = dist_root_for_manifest(manifest_path)
    checksums = resolve_dist_path(dist_root, checksums_rel)
    if build_id not in checksums.name:
        raise SystemExit(f"Checksum file name does not include build ID {build_id}: {checksums.name}")
    if not checksums.is_file():
        raise SystemExit(f"Checksum file missing: {checksums}")
    allowed_targets = {
        str(item.get("path"))
        for item in manifest.get("artifacts", [])
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    canonical_manifest = release_manifest_name(build_id)
    allowed_targets.add(canonical_manifest)
    seen_build_id = False
    for raw_line in checksums.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            if line == f"# build_id: {build_id}":
                seen_build_id = True
            continue
        try:
            expected_sha, rel = line.split(None, 1)
        except ValueError as exc:
            raise SystemExit(f"Malformed checksum line: {raw_line}") from exc
        target = resolve_dist_path(dist_root, rel.strip())
        if not target.is_file():
            raise SystemExit(f"Checksum target missing: {rel}")
        actual_sha = file_sha256(target)
        if actual_sha != expected_sha:
            raise SystemExit(f"Checksum mismatch for {rel}: expected {expected_sha}, got {actual_sha}")
        if build_id not in Path(rel).name:
            raise SystemExit(f"Checksum target missing build ID {build_id}: {rel}")
        normalized_rel = Path(rel).as_posix()
        if normalized_rel not in allowed_targets:
            raise SystemExit(f"Checksum target is not listed in release manifest: {rel}")
    if not seen_build_id:
        raise SystemExit(f"Checksum file missing build_id header: {build_id}")
    return checksums


def enforce_release_policy(manifest: dict[str, Any], *, allow_dirty: bool) -> None:
    channel = str(manifest.get("channel", "dev"))
    if channel == "stable":
        if manifest.get("workingTreeDirty") and not allow_dirty:
            raise SystemExit("Stable release requires a clean build working tree. Use --allow-dirty only for audited exceptions.")
        if git_value(["status", "--short"]) and not allow_dirty:
            raise SystemExit("Stable release requires clean current working tree. Use --allow-dirty only for audited exceptions.")
        validation = manifest.get("validation", {})
        platforms = manifest.get("platforms")
        if platforms and "windows" in platforms:
            installer_records = [item for item in manifest.get("artifacts", []) if item.get("kind") == "installer"]
            if not installer_records or not all(item.get("signed") is True for item in installer_records):
                raise SystemExit("Stable release requires signed installer artifacts.")
            if validation.get("payload") and validation.get("payload") != "passed":
                raise SystemExit("Stable release requires passed payload validation in manifest.")
            if validation.get("installer") and validation.get("installer") != "passed":
                raise SystemExit("Stable release requires passed installer validation in manifest.")
        elif not platforms:
            if validation.get("payload") != "passed" or validation.get("installer") != "passed":
                raise SystemExit("Stable release requires passed payload and installer validation in manifest.")
            installer_records = [item for item in manifest.get("artifacts", []) if item.get("kind") == "installer"]
            if not installer_records or not all(item.get("signed") is True for item in installer_records):
                raise SystemExit("Stable release requires signed installer artifacts.")


def default_notes_path(manifest: dict[str, Any], manifest_path: Path) -> Path:
    dist_root = dist_root_for_manifest(manifest_path)
    release_notes = [item for item in manifest.get("artifacts", []) if item.get("kind") == "releaseNotes"]
    if release_notes:
        rel = release_notes[0].get("path")
        if isinstance(rel, str):
            return resolve_dist_path(dist_root, rel)
    return dist_root / "release-body.md"


def build_plan(
    manifest_path: Path,
    *,
    notes: Path | None = None,
    draft: bool = True,
    prerelease: bool | None = None,
    allow_dirty: bool = False,
    repo: str | None = None,
) -> ReleasePlan:
    manifest = load_manifest(manifest_path)
    enforce_release_policy(manifest, allow_dirty=allow_dirty)
    artifacts = verify_manifest_artifacts(manifest, manifest_path)
    checksums = verify_checksums(manifest, manifest_path)
    build_id = manifest["build_id"]
    dist_root = dist_root_for_manifest(manifest_path)
    canonical_manifest = dist_root / release_manifest_name(build_id)
    if canonical_manifest.is_file():
        manifest_upload = canonical_manifest
    elif build_id in manifest_path.name:
        manifest_upload = manifest_path
    else:
        raise SystemExit(f"Canonical build-ID manifest missing: {canonical_manifest}")
    upload_paths = [*artifacts, checksums, manifest_upload]
    channel = str(manifest.get("channel", "dev"))
    tag = str(manifest.get("tag_name") or build_tag_name(build_id))
    title = str(manifest.get("release_name") or build_release_name(build_id))
    notes_path = notes.resolve() if notes else default_notes_path(manifest, manifest_path)
    if not notes_path.is_file():
        raise SystemExit(f"Release notes missing: {notes_path}")
    release_is_prerelease = channel in {"dev", "beta"} if prerelease is None else prerelease
    command = ["gh", "release", "create", tag]
    command.extend(str(path) for path in upload_paths)
    command.extend(["--title", title, "--notes-file", str(notes_path)])
    if draft:
        command.append("--draft")
    if release_is_prerelease:
        command.append("--prerelease")
    if repo:
        command.extend(["--repo", repo])
    return ReleasePlan(
        build_id=build_id,
        tag=tag,
        title=title,
        channel=channel,
        draft=draft,
        prerelease=release_is_prerelease,
        notes=notes_path,
        artifacts=upload_paths,
        command=command,
    )


def print_plan(plan: ReleasePlan, *, publish: bool) -> None:
    mode = "publish" if publish else "dry-run"
    print(f"mode: {mode}")
    print(f"build_id: {plan.build_id}")
    print(f"tag: {plan.tag}")
    print(f"title: {plan.title}")
    print(f"channel: {plan.channel}")
    print(f"draft: {str(plan.draft).lower()}")
    print(f"prerelease: {str(plan.prerelease).lower()}")
    print(f"notes: {plan.notes}")
    print("artifacts:")
    for artifact in plan.artifacts:
        print(f"  - {artifact}")
    print("command:")
    print(" ".join(plan.command))


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or dry-run a FireDM GitHub draft release.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--notes")
    parser.add_argument("--repo")
    parser.add_argument("--publish", action="store_true", help="Actually create the GitHub release with gh.")
    parser.add_argument("--dry-run", action="store_true", help="Print the release plan without publishing. Default.")
    parser.add_argument("--draft", dest="draft", action="store_true", default=True)
    parser.add_argument("--no-draft", dest="draft", action="store_false")
    parser.add_argument("--prerelease", dest="prerelease", action="store_true")
    parser.add_argument("--no-prerelease", dest="prerelease", action="store_false")
    parser.set_defaults(prerelease=None)
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    notes = Path(args.notes).resolve() if args.notes else None
    plan = build_plan(
        manifest_path,
        notes=notes,
        draft=args.draft,
        prerelease=args.prerelease,
        allow_dirty=args.allow_dirty,
        repo=args.repo,
    )
    print_plan(plan, publish=args.publish)
    if not args.publish:
        return
    if not shutil.which("gh"):
        raise SystemExit("GitHub CLI not found; cannot publish.")
    result = subprocess.run(plan.command, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
