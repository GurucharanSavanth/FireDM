# FireDM Plugin System - Generated Implementation
# File: firedm/plugins/drm_decryption.py
# Default State: DISABLED
"""Unsupported DRM-decryption plugin placeholder.

FireDM does not implement DRM bypass, protected-media circumvention,
license-server access, media-key extraction, or ClearKey/Widevine/PlayReady/
FairPlay decryption. The placeholder remains only so old settings that mention
`drm_decryption` fail closed instead of importing an active decryptor.
"""

from ..utils import log
from .registry import PluginBase, PluginMeta, PluginRegistry

META = PluginMeta(
    name="drm_decryption",
    version="1.0.0",
    author="FireDM",
    description="Unsupported: DRM/protected-media decryption is not implemented",
    default_enabled=False,
)


class DRMDecryptionPlugin(PluginBase):
    META = META

    def on_load(self) -> bool:
        log("drm_decryption: unsupported; protected-media decryption is not available")
        return False


PluginRegistry.register(DRMDecryptionPlugin)
