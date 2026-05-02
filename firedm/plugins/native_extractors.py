# FireDM Plugin System — Generated Implementation
# File: firedm/plugins/native_extractors.py
# Default State: DISABLED
# User Toggle: GUI → Settings → Plugin Manager
"""
Native Extractors Plugin
Direct site extractors for Twitter/X, Reddit, Vimeo — bypasses yt_dlp for
supported domains when possible.
Default OFF.
"""
import json
import os
import re
import urllib.request
from urllib.parse import urlparse

from .registry import PluginBase, PluginMeta, PluginRegistry
from .. import config
from ..utils import log

META = PluginMeta(
    name='native_extractors',
    version='1.0.0',
    author='FireDM',
    description='Direct extractors for Twitter/X, Reddit, Vimeo (no yt_dlp needed)',
    default_enabled=False,
)

# Twitter public bearer token (same one twitter.com web app uses)
_TWITTER_BEARER = (
    'AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D'
    '1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'
)

_DOMAIN_MAP = {}  # filled in NativeExtractorsPlugin.__init__


class NativeExtractorsPlugin(PluginBase):
    META = META

    def __init__(self):
        super().__init__()
        self._extractors = {
            'twitter.com': self._extract_twitter,
            'x.com': self._extract_twitter,
            'reddit.com': self._extract_reddit,
            'vimeo.com': self._extract_vimeo,
        }

    def on_download_start(self, d) -> bool:
        try:
            parsed = urlparse(getattr(d, 'url', ''))
        except Exception:
            return True

        domain = parsed.netloc.lower().lstrip('www.')
        extractor = self._extractors.get(domain)
        if not extractor:
            return True

        log(f'native_extractors: trying {domain}', log_level=2)
        try:
            info = extractor(d.url)
        except Exception as e:
            log(f'native_extractors: {domain} failed: {e}')
            return True  # fall through to yt_dlp

        if not info or not info.get('url'):
            return True

        d.url = info['url']
        d.eff_url = info['url']
        if info.get('title'):
            ext = info.get('ext', 'mp4')
            d.name = info['title'][:120] + '.' + ext
        d.type = config.MediaType.video
        d.resumable = True
        log(f'native_extractors: resolved {domain} → {info["url"][:80]}', log_level=2)
        return True

    # ----------------------------------------------------------------- Twitter

    def _extract_twitter(self, url: str) -> dict:
        tweet_id = re.search(r'(?:twitter|x)\.com/\w+/status/(\d+)', url)
        if not tweet_id:
            return {}

        guest_token = self._twitter_guest_token()
        if not guest_token:
            return {}

        tid = tweet_id.group(1)
        headers = {
            'Authorization': f'Bearer {_TWITTER_BEARER}',
            'x-guest-token': guest_token,
        }

        api_url = (
            f'https://api.twitter.com/graphql/-XypC2d5i5W7bBDl1J7W0A/'
            f'TweetResultByRestId?variables=%7B%22tweetId%22%3A%22{tid}%22%2C%22'
            f'withCommunity%22%3Afalse%2C%22includePromotedContent%22%3Afalse%2C%22'
            f'withVoice%22%3Afalse%7D'
        )

        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        legacy = (data.get('data', {})
                     .get('tweetResult', {})
                     .get('result', {})
                     .get('legacy', {}))
        media = (legacy.get('extended_entities', {})
                       .get('media', [{}])[0])

        variants = media.get('video_info', {}).get('variants', [])
        best = max(
            (v for v in variants if v.get('content_type') == 'video/mp4'),
            key=lambda v: v.get('bitrate', 0),
            default=None,
        )

        if best:
            title = re.sub(r'\s+', '_', legacy.get('full_text', 'twitter_video')[:60])
            return {'title': title, 'url': best['url'], 'ext': 'mp4'}
        return {}

    def _twitter_guest_token(self) -> str:
        req = urllib.request.Request(
            'https://api.twitter.com/1.1/guest/activate.json',
            headers={'Authorization': f'Bearer {_TWITTER_BEARER}'},
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return data.get('guest_token', '')

    # ------------------------------------------------------------------ Reddit

    def _extract_reddit(self, url: str) -> dict:
        json_url = url.rstrip('/') + '.json'
        req = urllib.request.Request(json_url, headers={
            'User-Agent': 'Mozilla/5.0 (FireDM native extractor)',
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        post = data[0]['data']['children'][0]['data']
        rvideo = post.get('media', {}).get('reddit_video', {})
        fallback = rvideo.get('fallback_url', '')
        if fallback:
            title = re.sub(r'\s+', '_', post.get('title', 'reddit_video')[:60])
            return {'title': title, 'url': fallback, 'ext': 'mp4'}
        return {}

    # ------------------------------------------------------------------- Vimeo

    def _extract_vimeo(self, url: str) -> dict:
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        req = urllib.request.Request(url, headers={'User-Agent': ua})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='replace')

        m = re.search(r'config_url\s*[=:]\s*"([^"]+)"', html)
        if not m:
            return {}

        config_url = m.group(1).replace('\\u0026', '&')
        req2 = urllib.request.Request(config_url, headers={'Referer': url, 'User-Agent': ua})
        with urllib.request.urlopen(req2, timeout=10) as resp:
            vdata = json.loads(resp.read())

        video_meta = vdata.get('video', {})
        files = vdata.get('request', {}).get('files', {}).get('progressive', [])
        if files:
            best = max(files, key=lambda x: x.get('width', 0))
            title = re.sub(r'\s+', '_', video_meta.get('title', 'vimeo_video')[:60])
            return {'title': title, 'url': best['url'], 'ext': 'mp4'}
        return {}


PluginRegistry.register(NativeExtractorsPlugin)
