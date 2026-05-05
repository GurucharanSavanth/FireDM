# FireDM Plugin System — Generated Implementation
# File: firedm/plugins/anti_detection.py
# Default State: DISABLED
# User Toggle: GUI → Settings → Plugin Manager
"""
Anti-Detection Plugin
Rotates TLS fingerprint (via curl-impersonate), HTTP headers, and proxy per download.
Default OFF.
"""
import os
import random
import shutil

from .. import config
from ..utils import log
from .registry import PluginBase, PluginMeta, PluginRegistry

META = PluginMeta(
    name='anti_detection',
    version='1.0.0',
    author='FireDM',
    description='TLS fingerprint (curl-impersonate), header rotation, proxy chain per download',
    default_enabled=False,
)

_CURL_IMPERSONATE_PROFILES = [
    'chrome116', 'chrome119', 'chrome120',
    'safari15_3', 'safari15_5',
    'firefox109', 'firefox117'
]

_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
]

_SEC_CH_UA = [
    '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    '"Not.A/Brand";v="8", "Chromium";v="124", "Google Chrome";v="124"',
]


class AntiDetectionPlugin(PluginBase):
    META = META

    def on_download_start(self, d) -> bool:
        ua = random.choice(_USER_AGENTS)
        sec = random.choice(_SEC_CH_UA)

        headers = getattr(d, 'http_headers', None)
        if not isinstance(headers, dict):
            headers = {}
            d.http_headers = headers

        headers.update({
            'User-Agent': ua,
            'sec-ch-ua': sec,
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })

        # Rotate proxy from chain if configured
        proxy_chain = getattr(config, 'proxy_chain', None)
        if proxy_chain and isinstance(proxy_chain, (list, tuple)) and proxy_chain:
            config.proxy = random.choice(proxy_chain)
            config.enable_proxy = True

        if self._curl_impersonate_available():
            d._use_curl_impersonate = True
            d._curl_impersonate_profile = random.choice(_CURL_IMPERSONATE_PROFILES)

        log(f'anti_detection: fingerprint rotated for {getattr(d, "name", "?")}', log_level=2)
        return True

    def _curl_impersonate_available(self):
        """Check if curl-impersonate binary exists."""
        binary = getattr(config, 'curl_impersonate_path', '')
        if binary and os.path.isfile(binary):
            return True
        return shutil.which('curl_chrome116') is not None

    def _get_curl_impersonate_cmd(self, d, seg):
        """Build curl-impersonate command for segment download."""
        profile = getattr(d, '_curl_impersonate_profile', 'chrome116')
        binary = getattr(config, 'curl_impersonate_path', '') or f'curl_{profile}'

        cmd = [binary]

        for k, v in (getattr(d, 'http_headers', {}) or {}).items():
            cmd.extend(['-H', f'{k}: {v}'])

        if getattr(seg, 'range', None):
            cmd.extend(['-r', f'{seg.range[0]}-{seg.range[1]}'])

        cmd.extend(['-o', seg.name])
        cmd.append(seg.url)

        return cmd


PluginRegistry.register(AntiDetectionPlugin)
