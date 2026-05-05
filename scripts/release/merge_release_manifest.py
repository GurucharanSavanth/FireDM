"""Merge per-platform FireDM release manifests into one cross-platform manifest.

Inputs:
  --windows-manifest  path/to/FireDM_release_manifest_<BUILD>_windows.json
  --linux-manifest    path/to/FireDM_release_manifest_<BUILD>_linux.json
  --output            path/to/FireDM_release_manifest_<BUILD>.json
  --build-id          YYYYMMDD_VN  (asserted against every input manifest)

Both inputs must agree on build_id, product version, channel, tag, and
release name. The merged manifest captures every artifact, the union of
validation results, and known blocked lanes for both platforms.

The merged checksum file is generated separately by ``generate_checksums.py``
after this script runs.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_id import build_release_name, build_tag_name, validate_build_id
from common import DIST_DIR, file_sha256


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"Per-platform manifest missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Per-platform manifest is not valid JSON: {path}") from exc


def assert_consistency(manifests: dict[str, dict[str, Any]], build_id: str) -> None:
    expected = {"build_id": build_id}
    references: dict[str, set] = {"version": set(), "channel": set(), "tag_name": set(), "release_name": set()}
    for label, manifest in manifests.items():
        if manifest.get("build_id") != build_id and manifest.get("build_code") != build_id:
            raise SystemExit(f"{label} manifest build_id mismatch: {manifest.get('build_id')!r} vs {build_id!r}")
        for key in references:
            value = manifest.get(key)
            if value is not None:
                references[key].add(value)
    for key, values in references.items():
        if len(values) > 1:
            raise SystemExit(f"Per-platform manifests disagree on {key}: {sorted(values)}")


def merge_artifacts(manifests: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    seen = {}
    merged: list[dict[str, Any]] = []
    for label, manifest in manifests.items():
        for artifact in manifest.get("artifacts", []):
            if not isinstance(artifact, dict):
                continue
            key = (artifact.get("kind"), artifact.get("path"))
            if key in seen:
                continue
            entry = dict(artifact)
            entry.setdefault("platform", label)
            seen[key] = True
            merged.append(entry)
    return merged


def merge_validation(manifests: dict[str, dict[str, Any]]) -> dict[str, str]:
    summary: dict[str, str] = {}
    for label, manifest in manifests.items():
        validation = manifest.get("validation") or {}
        for key, value in validation.items():
            scoped_key = key
            summary[scoped_key] = str(value)
    return summary


def merge_blocked(manifests: dict[str, dict[str, Any]]) -> dict[str, str]:
    blocked: dict[str, str] = {}
    for manifest in manifests.values():
        for source in (manifest.get("blockedArtifacts") or {}, manifest.get("blocked") or {}):
            if isinstance(source, dict):
                for key, value in source.items():
                    if key not in blocked:
                        blocked[key] = str(value)
    return blocked


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge per-platform FireDM release manifests.")
    parser.add_argument("--windows-manifest")
    parser.add_argument("--linux-manifest")
    parser.add_argument("--output")
    parser.add_argument("--build-id", required=True)
    parser.add_argument("--workflow", default="local")
    args = parser.parse_args()

    if not validate_build_id(args.build_id):
        raise SystemExit(f"Invalid build id: {args.build_id}")

    manifests: dict[str, dict[str, Any]] = {}
    if args.windows_manifest:
        manifests["windows"] = load_manifest(Path(args.windows_manifest).resolve())
    if args.linux_manifest:
        manifests["linux"] = load_manifest(Path(args.linux_manifest).resolve())
    if not manifests:
        raise SystemExit("Pass at least one of --windows-manifest or --linux-manifest")

    assert_consistency(manifests, args.build_id)

    primary = next(iter(manifests.values()))
    product_version = primary.get("version")
    channel = primary.get("channel")
    tag_name = primary.get("tag_name") or build_tag_name(args.build_id)
    release_name = primary.get("release_name") or build_release_name(args.build_id)

    output_path = Path(args.output).resolve() if args.output else DIST_DIR / f"FireDM_release_manifest_{args.build_id}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    merged: dict[str, Any] = {
        "schema": 2,
        "version": product_version,
        "build_id": args.build_id,
        "build_code": args.build_id,
        "build_date": primary.get("build_date"),
        "build_index": primary.get("build_index"),
        "tag_name": tag_name,
        "release_name": release_name,
        "channel": channel,
        "platforms": sorted(manifests.keys()),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generated_by_workflow": args.workflow,
        "perPlatformManifests": {label: manifest for label, manifest in manifests.items()},
        "artifacts": merge_artifacts(manifests),
        "validation": merge_validation(manifests),
        "blocked": merge_blocked(manifests),
        "ffmpegPolicy": "not bundled; detected as optional external tool",
        "compatibilityAliases": {
            "releaseManifest": "release-manifest.json",
            "checksums": "checksums/SHA256SUMS.txt",
        },
    }

    if "windows" in manifests:
        windows = manifests["windows"]
        merged["windowsManifestPath"] = str(Path(args.windows_manifest).name)
        merged.setdefault("legacyArtifacts", windows.get("legacyArtifacts", {}))
    if "linux" in manifests:
        merged["linuxManifestPath"] = str(Path(args.linux_manifest).name)

    checksums_rel = primary.get("checksumsPath")
    if not checksums_rel:
        for manifest in manifests.values():
            if manifest.get("checksumsPath"):
                checksums_rel = manifest["checksumsPath"]
                break
    if not checksums_rel:
        checksums_rel = f"checksums/SHA256SUMS_{args.build_id}.txt"
    merged["checksumsPath"] = checksums_rel

    output_path.write_text(json.dumps(merged, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    legacy = output_path.parent / "release-manifest.json"
    legacy.write_text(output_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Merged release manifest: {output_path}")


if __name__ == "__main__":
    main()
