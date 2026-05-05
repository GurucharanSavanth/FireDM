# FireDM Plugin System — Generated Implementation
# File: firedm/plugins/post_processing.py
# Default State: DISABLED
# User Toggle: GUI → Settings → Plugin Manager
"""
Post-Processing Plugin
Runs configurable steps after a download completes:
  antivirus, auto-extract, file organise, format convert, duplicate check.
Each step is individually togglable via `enabled_steps`.
Default OFF.
"""
import contextlib
import hashlib
import json
import os

from .. import config
from ..utils import delete_file, log, rename_file, run_command, safe_extract_tar, safe_extract_zip
from .registry import PluginBase, PluginMeta, PluginRegistry

META = PluginMeta(
    name='post_processing',
    version='1.0.0',
    author='FireDM',
    description='AV scan, auto-extract, organise, convert, duplicate detection',
    default_enabled=False,
)


class PostProcessingPlugin(PluginBase):
    META = META

    def __init__(self):
        super().__init__()
        # User toggles individual steps; all off by default
        self.enabled_steps = set()

    def on_download_complete(self, d) -> bool:
        step_map = {
            'antivirus': self._scan_antivirus,
            'extract': self._auto_extract,
            'organize': self._organize_file,
            'convert': self._convert_format,
            'duplicate': self._check_duplicate,
        }
        for step_name, handler in step_map.items():
            if step_name not in self.enabled_steps:
                continue
            try:
                if not handler(d):
                    log(f'post_processing: step "{step_name}" failed for {getattr(d, "name", "?")}')
                    return False
            except Exception as e:
                log(f'post_processing: step "{step_name}" error: {e}')
        return True

    # ----------------------------------------------------------------- ClamAV

    def _scan_antivirus(self, d) -> bool:
        target = getattr(d, 'target_file', '')
        if not target or not os.path.isfile(target):
            return True

        clamscan = (r'C:\Program Files\ClamAV\clamscan.exe'
                    if config.operating_system == 'Windows'
                    else '/usr/bin/clamscan')
        if not os.path.isfile(clamscan):
            log('post_processing: ClamAV not found, skipping AV scan')
            return True

        error, output = run_command(f'"{clamscan}" --no-summary "{target}"', verbose=False)
        if 'Infected files: 0' in output:
            log(f'post_processing: AV clean: {d.name}', log_level=2)
            return True

        log(f'post_processing: ANTIVIRUS ALERT for {d.name}:\n{output}')
        quarantine = os.path.join(config.sett_folder, 'quarantine')
        os.makedirs(quarantine, exist_ok=True)
        try:
            rename_file(target, os.path.join(quarantine, d.name))
        except Exception as e:
            log(f'post_processing: quarantine move failed: {e}')
        return False

    # ----------------------------------------------------------------- Extract

    def _auto_extract(self, d) -> bool:
        target = getattr(d, 'target_file', '')
        if not target or not os.path.isfile(target):
            return True

        ext = os.path.splitext(target)[1].lower()
        if ext not in ('.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'):
            return True

        extract_dir = os.path.splitext(target)[0]
        os.makedirs(extract_dir, exist_ok=True)

        try:
            if ext == '.zip':
                import zipfile
                with zipfile.ZipFile(target, 'r') as z:
                    safe_extract_zip(z, extract_dir)
            elif ext in ('.tar', '.gz', '.bz2'):
                import tarfile
                with tarfile.open(target, 'r:*') as t:
                    safe_extract_tar(t, extract_dir)
            elif ext == '.rar':
                run_command(f'unrar x "{target}" "{extract_dir}/"', verbose=False)
            elif ext == '.7z':
                run_command(f'7z x "{target}" -o"{extract_dir}"', verbose=False)

            log(f'post_processing: extracted {d.name} → {extract_dir}', log_level=2)
        except Exception as e:
            log(f'post_processing: extract error: {e}')
        return True

    # ---------------------------------------------------------------- Organize

    def _organize_file(self, d) -> bool:
        target = getattr(d, 'target_file', '')
        if not target or not os.path.isfile(target):
            return True

        ext = os.path.splitext(target)[1].lower()
        if ext in ('.mp4', '.mkv', '.avi', '.mov', '.webm'):
            category = 'Videos'
        elif ext in ('.mp3', '.aac', '.wav', '.flac', '.opus', '.ogg'):
            category = 'Audio'
        elif ext in ('.zip', '.rar', '.7z', '.tar', '.gz'):
            category = 'Compressed'
        elif ext in ('.pdf', '.doc', '.docx', '.xls', '.xlsx'):
            category = 'Documents'
        else:
            category = 'General'

        cat_folder = os.path.join(config.download_folder, category)
        os.makedirs(cat_folder, exist_ok=True)

        dest = os.path.join(cat_folder, os.path.basename(target))
        if dest != target:
            try:
                rename_file(target, dest)
                d.folder = cat_folder
                log(f'post_processing: organized {d.name} → {category}', log_level=2)
            except Exception as e:
                log(f'post_processing: organize failed: {e}')
        return True

    # ----------------------------------------------------------------- Convert

    def _convert_format(self, d) -> bool:
        target = getattr(d, 'target_file', '')
        target_ext = getattr(d, '_target_ext', None)
        if not target or not target_ext or not os.path.isfile(target):
            return True

        if os.path.splitext(target)[1].lower() == target_ext:
            return True

        ffmpeg = config.ffmpeg_actual_path
        if not ffmpeg:
            return True

        output = os.path.splitext(target)[0] + target_ext
        error, _ = run_command(f'"{ffmpeg}" -y -i "{target}" "{output}"', verbose=True)
        if not error and os.path.isfile(output):
            delete_file(target)
            log(f'post_processing: converted {d.name} → {target_ext}', log_level=2)
        return True

    # -------------------------------------------------------------- Duplicates

    def _check_duplicate(self, d) -> bool:
        target = getattr(d, 'target_file', '')
        if not target or not os.path.isfile(target):
            return True

        db_path = os.path.join(config.sett_folder, 'file_hash_db.json')
        db = {}
        if os.path.isfile(db_path):
            try:
                with open(db_path) as f:
                    db = json.load(f)
            except Exception:
                db = {}

        if getattr(d, 'type', '') == config.MediaType.video:
            file_hash = self._perceptual_hash(d, target)
        else:
            file_hash = self._md5(target)

        if not file_hash:
            return True

        uid = getattr(d, 'uid', str(target))
        if file_hash in db.values() and db.get(uid) != file_hash:
            log(f'post_processing: duplicate detected: {d.name}')

        db[uid] = file_hash
        try:
            with open(db_path, 'w') as f:
                json.dump(db, f)
        except Exception as e:
            log(f'post_processing: hash db write error: {e}')
        return True

    def _md5(self, path: str) -> str:
        m = hashlib.md5()
        try:
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    m.update(chunk)
            return m.hexdigest()
        except Exception as e:
            log(f'post_processing: md5 error: {e}')
            return ''

    def _perceptual_hash(self, d, target: str) -> str:
        try:
            import imagehash
            from PIL import Image

            ffmpeg = config.ffmpeg_actual_path
            if not ffmpeg:
                return self._md5(target)

            frame = os.path.join(getattr(d, 'temp_folder', config.download_folder), '_phash_frame.jpg')
            err, _ = run_command(f'"{ffmpeg}" -y -ss 00:00:01 -i "{target}" -vframes 1 "{frame}"', verbose=False)
            if not err and os.path.isfile(frame):
                h = str(imagehash.phash(Image.open(frame)))
                with contextlib.suppress(Exception):
                    os.unlink(frame)
                return h
        except ImportError:
            pass
        return self._md5(target)


PluginRegistry.register(PostProcessingPlugin)
