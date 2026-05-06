"""Release and UI policy for shipped plugins.

Two tiers:

PERMANENTLY_BLOCKED  — hard gates that cannot be overridden by any user toggle.
                       Used exclusively for features that carry irreversible legal
                       or safety implications (DRM circumvention, etc.).

USER_OVERRIDABLE_BLOCKED — advisory blocks for engineering-incomplete features.
                           The user may enable these via Advanced → Plugins after
                           acknowledging the risk, but they are OFF by default.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Tier 1 — PERMANENT.  No user toggle exists or will ever exist.
# ---------------------------------------------------------------------------
PERMANENTLY_BLOCKED: dict[str, str] = {
    "drm_decryption": (
        "permanently blocked by legal policy: DRM bypass, protected-media "
        "circumvention, license-server access, and media-key extraction are "
        "prohibited under DMCA §1201, EU EUCD, and equivalent statutes. "
        "No user-sovereignty override applies — see USER_SOVEREIGNTY_POLICY.md §8."
    ),
}

# ---------------------------------------------------------------------------
# Tier 2 — USER-OVERRIDABLE.  Blocked by default for safety/completeness;
# user may enable each via config.enable_plugin_<id> after acknowledgment.
# ---------------------------------------------------------------------------
USER_OVERRIDABLE_BLOCKED: dict[str, str] = {
    "anti_detection": (
        "off by default: TLS/proxy/header impersonation has not been "
        "release-validated as truthful, user-controlled behavior. "
        "Enable via Advanced → Plugins → Anti-Detection."
    ),
    "browser_integration": (
        "off by default: native-host origin provisioning and authentication "
        "require OS-level manifest installation not yet automated. "
        "Enable via Advanced → Plugins → Browser Integration."
    ),
    "native_extractors": (
        "off by default: site-specific extractors embed public API tokens whose "
        "behavior is not covered by release tests. "
        "Enable via Advanced → Plugins → Native Extractors."
    ),
    # post_processing was unblocked 2026-05-05; entry removed.
    "protocol_expansion": (
        "off by default: FTP/WebDAV/SFTP/Magnet/IPFS handlers are partial; "
        "RPC and dependency safety tests are incomplete. "
        "Enable via Advanced → Plugins → Protocol Expansion."
    ),
}

# Combined view for code that does not need to distinguish tiers.
BLOCKED_PLUGIN_REASONS: dict[str, str] = {
    **PERMANENTLY_BLOCKED,
    **USER_OVERRIDABLE_BLOCKED,
}


def blocked_plugin_reason(plugin_id: str) -> str:
    """Return blocking reason string, or empty string if plugin is not blocked.

    Respects user override for USER_OVERRIDABLE_BLOCKED plugins when the
    corresponding enable_plugin_<id> config toggle is True AND the master
    advanced_features_enabled gate is also True.
    """
    if plugin_id in PERMANENTLY_BLOCKED:
        return PERMANENTLY_BLOCKED[plugin_id]

    if plugin_id in USER_OVERRIDABLE_BLOCKED:
        try:
            from .. import config
            if (
                getattr(config, 'advanced_features_enabled', False)
                and getattr(config, f'enable_plugin_{plugin_id}', False)
            ):
                return ''  # user has explicitly enabled this plugin
        except Exception:
            pass
        return USER_OVERRIDABLE_BLOCKED[plugin_id]

    return ''


def is_blocked_plugin(plugin_id: str) -> bool:
    """True when the plugin must not be loaded."""
    return bool(blocked_plugin_reason(plugin_id))


def is_permanently_blocked(plugin_id: str) -> bool:
    """True only for tier-1 plugins that cannot be user-enabled."""
    return plugin_id in PERMANENTLY_BLOCKED


__all__ = [
    "PERMANENTLY_BLOCKED",
    "USER_OVERRIDABLE_BLOCKED",
    "BLOCKED_PLUGIN_REASONS",
    "blocked_plugin_reason",
    "is_blocked_plugin",
    "is_permanently_blocked",
]
