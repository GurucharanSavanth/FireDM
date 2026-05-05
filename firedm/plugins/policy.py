"""Release and UI policy for shipped plugins."""

from __future__ import annotations

BLOCKED_PLUGIN_REASONS: dict[str, str] = {
    "drm_decryption": (
        "blocked by security policy: DRM bypass, protected-media "
        "circumvention, license-server access, and media-key extraction are not supported"
    ),
    "anti_detection": (
        "blocked until TLS/proxy/header impersonation behavior is validated and "
        "represented as truthful, user-controlled settings"
    ),
    "browser_integration": (
        "blocked until native-host origin provisioning and authentication are "
        "release-validated with a real browser connector"
    ),
    "native_extractors": (
        "blocked until site-specific extractor behavior and embedded public API "
        "token use are covered by release tests"
    ),
    "post_processing": (
        "blocked until antivirus/extract/convert substeps use argv-safe command "
        "execution, path validation, and explicit per-step UI controls"
    ),
    "protocol_expansion": (
        "blocked until partial FTP/WebDAV/SFTP/magnet/IPFS/data handlers are split "
        "or fully validated with dependency and RPC safety tests"
    ),
}


def blocked_plugin_reason(plugin_id: str) -> str:
    """Return blocking reason for a shipped plugin ID, or empty string."""

    return BLOCKED_PLUGIN_REASONS.get(plugin_id, "")


def is_blocked_plugin(plugin_id: str) -> bool:
    """True when a plugin must not be loadable/selectable."""

    return bool(blocked_plugin_reason(plugin_id))


__all__ = ["BLOCKED_PLUGIN_REASONS", "blocked_plugin_reason", "is_blocked_plugin"]
