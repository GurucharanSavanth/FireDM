"""Plugin manifest discovery for release build + UI surfaces.

This module reads the existing PluginRegistry and produces a release-safe
view of plugin metadata that the canonical Windows build script can fold
into manifest.json and the modern GUI can render in the Plugins panel.

The manifest never enables a plugin and never imports GUI toolkits.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .policy import blocked_plugin_reason, is_permanently_blocked
from .registry import PluginMeta, PluginRegistry

logger = logging.getLogger(__name__)

PLUGIN_STATUS_AVAILABLE: str = "available"
PLUGIN_STATUS_DISABLED: str = "disabled"
PLUGIN_STATUS_BLOCKED: str = "blocked"
PLUGIN_STATUS_PLANNED: str = "planned"
PLUGIN_STATUS_DEPRECATED: str = "deprecated"

_VALID_STATUSES: frozenset[str] = frozenset(
    (
        PLUGIN_STATUS_AVAILABLE,
        PLUGIN_STATUS_DISABLED,
        PLUGIN_STATUS_BLOCKED,
        PLUGIN_STATUS_PLANNED,
        PLUGIN_STATUS_DEPRECATED,
    )
)


@dataclass(frozen=True)
class PluginManifestEntry:
    """Single entry for a plugin/engine adapter, suitable for release manifest."""

    plugin_id: str
    display_name: str
    version: str
    status: str
    description: str = ""
    author: str = ""
    capabilities: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    default_enabled: bool = False
    enabled: bool = False
    loaded: bool = False
    blocked_reason: str = ""
    # True  → user can enable via Advanced panel (USER_OVERRIDABLE_BLOCKED tier)
    # False → permanently blocked; no user toggle exists (PERMANENTLY_BLOCKED tier)
    user_overridable: bool = False

    def __post_init__(self) -> None:
        if not self.plugin_id:
            raise ValueError("plugin_id must be non-empty")
        if not self.display_name:
            raise ValueError("display_name must be non-empty")
        if self.status not in _VALID_STATUSES:
            raise ValueError(f"invalid plugin status: {self.status}")
        if self.status == PLUGIN_STATUS_BLOCKED and not self.blocked_reason:
            raise ValueError("blocked plugin requires blocked_reason")


@dataclass(frozen=True)
class PluginManifestSection:
    """Release manifest section: included, blocked, planned plugins."""

    included: tuple[PluginManifestEntry, ...] = ()
    blocked: tuple[PluginManifestEntry, ...] = ()
    planned: tuple[PluginManifestEntry, ...] = ()
    discovery_warnings: tuple[str, ...] = ()

    def to_serializable(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "included": [_entry_to_dict(entry) for entry in self.included],
            "blocked": [_entry_to_dict(entry) for entry in self.blocked],
            "planned": [_entry_to_dict(entry) for entry in self.planned],
            "discovery_warnings": list(self.discovery_warnings),
        }

    @property
    def all_entries(self) -> tuple[PluginManifestEntry, ...]:
        return self.included + self.blocked + self.planned


def _entry_to_dict(entry: PluginManifestEntry) -> dict[str, Any]:
    """Convert a manifest entry to a serializable dictionary."""
    return {
        "plugin_id": entry.plugin_id,
        "display_name": entry.display_name,
        "version": entry.version,
        "status": entry.status,
        "description": entry.description,
        "author": entry.author,
        "capabilities": list(entry.capabilities),
        "dependencies": list(entry.dependencies),
        "conflicts": list(entry.conflicts),
        "default_enabled": entry.default_enabled,
        "enabled": entry.enabled,
        "loaded": entry.loaded,
        "blocked_reason": entry.blocked_reason,
        "user_overridable": entry.user_overridable,
    }


def entry_from_meta(
    meta: PluginMeta,
    *,
    status: str = PLUGIN_STATUS_DISABLED,
    blocked_reason: str = "",
    user_overridable: bool = False,
) -> PluginManifestEntry:
    """Build a manifest entry from a PluginMeta record."""
    return PluginManifestEntry(
        plugin_id=meta.name,
        display_name=meta.name,
        version=str(meta.version or "0.0.0"),
        status=status,
        description=str(meta.description or ""),
        author=str(meta.author or ""),
        dependencies=tuple(meta.dependencies or ()),
        conflicts=tuple(meta.conflicts or ()),
        default_enabled=bool(meta.default_enabled),
        enabled=bool(meta.enabled),
        loaded=bool(meta.loaded),
        blocked_reason=blocked_reason,
        user_overridable=user_overridable,
    )


def discover_plugin_manifest(
    *,
    scan: bool = True,
    blocked_overrides: Iterable[tuple[str, str]] = (),
) -> PluginManifestSection:
    """Inspect the PluginRegistry and return a release-safe manifest section.

    Args:
        scan: If True, call PluginRegistry.scan_plugins(). Disable for unit
              tests that want to control the registry directly.
        blocked_overrides: Iterable of (plugin_id, reason) pairs for entries
                          that must be classified as blocked even if registered.

    Returns:
        PluginManifestSection with included, blocked, and planned plugins.
    """
    warnings: list[str] = []
    if scan:
        try:
            PluginRegistry.scan_plugins()
        except Exception as exc:  # pragma: no cover - defensive
            warnings.append(f"plugin scan failed: {exc!r}")

    blocked_map = {plugin_id: reason for plugin_id, reason in blocked_overrides}
    metas = PluginRegistry.get_plugin_list()

    included: list[PluginManifestEntry] = []
    blocked: list[PluginManifestEntry] = []

    for meta in metas:
        reason = blocked_map.get(meta.name) or blocked_plugin_reason(meta.name)
        if reason:
            # user_overridable=True only for USER_OVERRIDABLE_BLOCKED tier;
            # PERMANENTLY_BLOCKED plugins (e.g. drm_decryption) are never overridable.
            overridable = not is_permanently_blocked(meta.name)
            blocked.append(entry_from_meta(
                meta,
                status=PLUGIN_STATUS_BLOCKED,
                blocked_reason=reason,
                user_overridable=overridable,
            ))
            continue

        status = PLUGIN_STATUS_AVAILABLE if meta.loaded else PLUGIN_STATUS_DISABLED
        included.append(entry_from_meta(meta, status=status))

    return PluginManifestSection(
        included=tuple(included),
        blocked=tuple(blocked),
        planned=(),
        discovery_warnings=tuple(warnings),
    )


def render_text_summary(section: PluginManifestSection) -> str:
    """Generate single-line-per-entry text summary for build.log/manifest preview."""
    lines: list[str] = []
    for entry in section.included:
        lines.append(f"included {entry.plugin_id} v{entry.version} [{entry.status}]")
    for entry in section.blocked:
        lines.append(f"blocked  {entry.plugin_id} v{entry.version} reason={entry.blocked_reason}")
    for entry in section.planned:
        lines.append(f"planned  {entry.plugin_id} v{entry.version}")
    for warn in section.discovery_warnings:
        lines.append(f"warning  {warn}")
    if not lines:
        lines.append("no plugins discovered")
    return "\n".join(lines)


__all__ = [
    "PLUGIN_STATUS_AVAILABLE",
    "PLUGIN_STATUS_BLOCKED",
    "PLUGIN_STATUS_DEPRECATED",
    "PLUGIN_STATUS_DISABLED",
    "PLUGIN_STATUS_PLANNED",
    "PluginManifestEntry",
    "PluginManifestSection",
    "discover_plugin_manifest",
    "entry_from_meta",
    "render_text_summary",
]
