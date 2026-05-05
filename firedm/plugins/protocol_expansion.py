# FireDM Plugin System — Generated Implementation
# File: firedm/plugins/protocol_expansion.py
# Default State: DISABLED
# User Toggle: GUI → Settings → Plugin Manager
"""Protocol expansion plugin."""

import json
import os
import subprocess
import threading
import time
import urllib.request
from urllib.parse import parse_qs, unquote_plus, urlparse

from .. import config
from ..downloaditem import Segment
from ..utils import get_range_list, log, validate_file_name
from .registry import PluginBase, PluginMeta, PluginRegistry

META = PluginMeta(
    name='protocol_expansion',
    version='1.0.0',
    author='FireDM',
    description='FTP/FTPS, SFTP, WebDAV, Magnet, IPFS, Data URI support',
    default_enabled=False,
)


class ProtocolExpansionPlugin(PluginBase):
    META = META

    def __init__(self):
        super().__init__()
        self._handlers = {
            'ftp': self._handle_ftp,
            'ftps': self._handle_ftp,
            'sftp': self._handle_sftp,
            'webdav': self._handle_webdav,
            'webdavs': self._handle_webdav,
            'magnet': self._handle_magnet,
            'ipfs': self._handle_ipfs,
            'data': self._handle_data,
        }

    def on_download_start(self, d) -> bool:
        url = getattr(d, 'url', '')
        try:
            scheme = urlparse(url).scheme.lower()
        except Exception:
            return True

        if scheme in ('http', 'https', ''):
            return True

        handler = self._handlers.get(scheme)
        if not handler:
            log(f'protocol_expansion: unsupported scheme "{scheme}"')
            return True  # let FireDM fail gracefully

        log(f'protocol_expansion: handling {scheme}://', log_level=2)
        return handler(d)

    # --------------------------------------------------------------------- FTP

    def _handle_ftp(self, d) -> bool:
        try:
            from ftplib import FTP, FTP_TLS
            parsed = urlparse(d.url)
            use_tls = parsed.scheme == 'ftps'
            ftp = FTP_TLS() if use_tls else FTP()
            ftp.connect(parsed.hostname, parsed.port or 21, timeout=30)
            ftp.login(parsed.username or 'anonymous', parsed.password or '')
            if use_tls:
                ftp.prot_p()
            size = ftp.size(parsed.path) or 0
            ftp.quit()

            d.size = size
            d.resumable = size > 0
            d.type = config.MediaType.general
            d.eff_url = d.url
            d.segments = [Segment(
                name=os.path.join(d.temp_folder, '0'),
                num=0, range=[0, size - 1] if size else None, size=size,
                url=d.url, tempfile=d.temp_file,
                media_type=config.MediaType.general, d=d,
            )]
            d._protocol_handler = parsed.scheme
            d._plugin_segments_ready = True
            d.http_headers = getattr(d, 'http_headers', {})
            return True
        except Exception as e:
            log(f'protocol_expansion: FTP error: {e}')
            return False

    # -------------------------------------------------------------------- SFTP

    def _handle_sftp(self, d) -> bool:
        try:
            import paramiko
            parsed = urlparse(d.url)
            transport = paramiko.Transport((parsed.hostname, parsed.port or 22))
            transport.connect(username=parsed.username or '', password=parsed.password or '')
            sftp = paramiko.SFTPClient.from_transport(transport)
            size = sftp.stat(parsed.path).st_size
            sftp.close()
            transport.close()

            d.size = size
            d.resumable = True
            d.type = config.MediaType.general
            d.eff_url = d.url
            d.segments = [Segment(
                name=os.path.join(d.temp_folder, '0'),
                num=0, range=[0, size - 1], size=size,
                url=d.url, tempfile=d.temp_file,
                media_type=config.MediaType.general, d=d,
            )]
            d._protocol_handler = 'sftp'
            d._plugin_segments_ready = True
            return True
        except ImportError:
            log('protocol_expansion: paramiko not installed (pip install paramiko)')
            return False
        except Exception as e:
            log(f'protocol_expansion: SFTP error: {e}')
            return False

    # ------------------------------------------------------------------ WebDAV

    def _handle_webdav(self, d) -> bool:
        try:
            import urllib.request
            parsed = urlparse(d.url)
            http_scheme = 'https' if parsed.scheme == 'webdavs' else 'http'
            http_url = parsed._replace(scheme=http_scheme).geturl()
            req = urllib.request.Request(http_url, method='HEAD')
            with urllib.request.urlopen(req, timeout=15) as resp:
                size = int(resp.headers.get('Content-Length', 0))
                accept_ranges = resp.headers.get('Accept-Ranges', '').lower()
                resumable = accept_ranges not in ('', 'none')

            d.size = size
            d.resumable = resumable
            d.type = config.MediaType.general
            d.eff_url = http_url

            if resumable and size:
                ranges = get_range_list(size, config.SEGMENT_SIZE)
                d.segments = [
                    Segment(
                        name=os.path.join(d.temp_folder, str(i)),
                        num=i, range=r, size=r[1] - r[0] + 1 if r else 0,
                        url=http_url, tempfile=d.temp_file,
                        media_type=config.MediaType.general, d=d,
                    )
                    for i, r in enumerate(ranges)
                ]
            else:
                d.segments = [Segment(
                    name=os.path.join(d.temp_folder, '0'),
                    num=0, range=None, size=size,
                    url=http_url, tempfile=d.temp_file,
                    media_type=config.MediaType.general, d=d,
                )]
            d._protocol_handler = parsed.scheme
            d._plugin_segments_ready = True
            return True
        except Exception as e:
            log(f'protocol_expansion: WebDAV error: {e}')
            return False

    # ------------------------------------------------------------------ Magnet

    def _handle_magnet(self, d) -> bool:
        return self._magnet(d)

    def _magnet(self, d):
        """Spawn aria2c for magnet links, monitor via RPC."""
        aria2c = self._find_aria2c()
        if not aria2c:
            log('aria2c not found for magnet links')
            return False

        rpc_port = 6800

        try:
            req = urllib.request.Request(
                f'http://localhost:{rpc_port}/jsonrpc',
                data=json.dumps({
                    'jsonrpc': '2.0',
                    'id': '1',
                    'method': 'aria2.tellActive'
                }).encode(),
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(req, timeout=2)
        except Exception:
            daemon_cmd = [
                aria2c, '--enable-rpc', f'--rpc-listen-port={rpc_port}',
                '--rpc-allow-origin-all', '--rpc-listen-all=false',
                '--seed-time=0', '--dir=' + d.temp_folder,
                '--daemon'
            ]
            subprocess.Popen(daemon_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)

        req = urllib.request.Request(
            f'http://localhost:{rpc_port}/jsonrpc',
            data=json.dumps({
                'jsonrpc': '2.0',
                'id': '1',
                'method': 'aria2.addUri',
                'params': [[d.url], {'dir': d.temp_folder}]
            }).encode(),
            headers={'Content-Type': 'application/json'}
        )

        try:
            resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read())
            gid = result['result']

            d._aria2c_gid = gid
            d._aria2c_port = rpc_port
            d._protocol_handler = 'magnet'
            d._plugin_queued = True
            d.status = config.Status.pending
            d.type = config.MediaType.general
            d.resumable = False
            if not getattr(d, 'name', ''):
                d.name = self._magnet_display_name(d.url)

            threading.Thread(target=self._monitor_aria2c, args=(d,), daemon=True).start()
            return True

        except Exception as e:
            log('aria2c addUri failed:', e)
            return False

    @staticmethod
    def _magnet_display_name(url):
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        display_names = params.get('dn') or []
        if display_names:
            return validate_file_name(unquote_plus(display_names[0]))
        return validate_file_name('magnet-download')

    def _monitor_aria2c(self, d):
        """Poll aria2c until download completes, then integrate into FireDM."""
        while True:
            try:
                req = urllib.request.Request(
                    f'http://localhost:{d._aria2c_port}/jsonrpc',
                    data=json.dumps({
                        'jsonrpc': '2.0',
                        'id': '1',
                        'method': 'aria2.tellStatus',
                        'params': [d._aria2c_gid]
                    }).encode(),
                    headers={'Content-Type': 'application/json'}
                )
                resp = urllib.request.urlopen(req, timeout=10)
                status = json.loads(resp.read())['result']

                if status['status'] == 'complete':
                    files = status.get('files', [])
                    if files:
                        completed_path = files[0]['path']
                        from ..utils import rename_file
                        rename_file(completed_path, d.target_file)
                        d._plugin_completed = True
                        d.status = config.Status.completed
                        self._notify_controller_complete(d)
                    break
                elif status['status'] in ('error', 'removed'):
                    d.status = config.Status.error
                    self._notify_controller_complete(d)
                    break

                completed = int(status.get('completedLength', 0))
                total = int(status.get('totalLength', 1))
                d.size = total
                d.current_size = completed
                d.down_bytes = completed

                time.sleep(2)

            except Exception as e:
                log('aria2c monitor error:', e)
                break

    @staticmethod
    def _notify_controller_complete(d):
        try:
            from ..controller import Controller

            ctrl = Controller._instance
            if ctrl is None:
                return
            ctrl.report_d(d)
            if d.status == config.Status.completed:
                ctrl._post_download(d)
            ctrl.save_d_map()
        except Exception as e:
            log('aria2c controller notify error:', e)

    def _find_aria2c(self):
        """Find aria2c binary in PATH or config."""
        candidates = ['aria2c.exe'] if config.operating_system == 'Windows' else ['aria2c']

        for cmd in candidates:
            try:
                subprocess.run([cmd, '--version'], capture_output=True, check=True)
                return cmd
            except Exception:
                continue

        override = getattr(config, 'aria2c_path', '')
        if override and os.path.isfile(override):
            return override

        return None

    # -------------------------------------------------------------------- IPFS

    def _handle_ipfs(self, d) -> bool:
        try:
            import urllib.request
            parsed = urlparse(d.url)
            cid = parsed.netloc or parsed.path.lstrip('/')
            if not cid:
                return False

            local_url = f'http://127.0.0.1:8080/ipfs/{cid}'
            try:
                req = urllib.request.Request(local_url, method='HEAD')
                with urllib.request.urlopen(req, timeout=5):
                    d.url = local_url
            except Exception:
                d.url = f'https://ipfs.io/ipfs/{cid}'

            d.eff_url = d.url
            log(f'protocol_expansion: IPFS resolved to {d.url}', log_level=2)
            return True  # now treat as HTTP
        except Exception as e:
            log(f'protocol_expansion: IPFS error: {e}')
            return False

    # ---------------------------------------------------------------- Data URI

    def _handle_data(self, d) -> bool:
        try:
            from urllib.parse import unquote
            raw = d.url
            if ',' not in raw:
                return False

            header, data = raw.split(',', 1)
            is_base64 = ';base64' in header

            if is_base64:
                import base64
                content = base64.b64decode(data)
            else:
                content = unquote(data).encode('utf-8')

            os.makedirs(d.temp_folder, exist_ok=True)
            with open(d.temp_file, 'wb') as f:
                f.write(content)

            if not getattr(d, 'name', ''):
                d.name = validate_file_name('data-uri-download.bin')
            d.type = config.MediaType.general
            d.size = len(content)
            d.status = config.Status.completed
            d._plugin_completed = True
            d._plugin_completed_file = d.temp_file
            return True
        except Exception as e:
            log(f'protocol_expansion: data URI error: {e}')
            return False


PluginRegistry.register(ProtocolExpansionPlugin)
