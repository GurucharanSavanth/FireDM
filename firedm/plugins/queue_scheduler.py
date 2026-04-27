# FireDM Plugin System — Generated Implementation
# File: firedm/plugins/queue_scheduler.py
# Default State: DISABLED
# User Toggle: GUI → Settings → Plugin Manager
"""Queue and scheduler plugin."""

import os
import time
import threading
from datetime import datetime

from .registry import PluginBase, PluginMeta, PluginRegistry
from .. import config
from ..utils import log

META = PluginMeta(
    name='queue_scheduler',
    version='1.0.0',
    author='FireDM',
    description='Priority queue, categories, bandwidth shaping, time-based scheduling',
    default_enabled=False,
)

_DEFAULT_CATEGORIES = {
    'Videos': {'max_concurrent': 2, 'speed_limit': 0},
    'Audio': {'max_concurrent': 2, 'speed_limit': 0},
    'Documents': {'max_concurrent': 3, 'speed_limit': 0},
    'Compressed': {'max_concurrent': 2, 'speed_limit': 0},
    'General': {'max_concurrent': 3, 'speed_limit': 0},
}

_EXT_CATEGORY = {
    '.mp4': 'Videos', '.mkv': 'Videos', '.avi': 'Videos', '.mov': 'Videos', '.webm': 'Videos',
    '.mp3': 'Audio', '.aac': 'Audio', '.wav': 'Audio', '.flac': 'Audio', '.ogg': 'Audio',
    '.pdf': 'Documents', '.doc': 'Documents', '.docx': 'Documents',
    '.zip': 'Compressed', '.rar': 'Compressed', '.7z': 'Compressed', '.tar': 'Compressed',
}


class QueueSchedulerPlugin(PluginBase):
    META = META

    def __init__(self):
        super().__init__()
        # (uid, priority, category, scheduled_datetime_or_None)
        self._queue = []
        self._queue_lock = threading.Lock()
        self._active_uids = set()
        self._active_categories = {}
        self.categories = dict(_DEFAULT_CATEGORIES)
        # [(start_time, end_time, allowed_categories_list)]
        self.time_rules = []
        self._scheduler_thread = None
        self._running = False

    def on_load(self) -> bool:
        self._running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop, daemon=True, name='firedm-scheduler'
        )
        self._scheduler_thread.start()
        return True

    def on_unload(self) -> bool:
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=3)
        return True

    def on_download_start(self, d) -> bool:
        uid = getattr(d, 'uid', None)
        if uid is None:
            return True

        category = self._categorize(d)
        cat_cfg = self.categories.get(category, self.categories['General'])
        max_concurrent = cat_cfg.get('max_concurrent', 3)

        with self._queue_lock:
            active_in_cat = sum(1 for c in self._active_categories.values() if c == category)

            total_active = len(self._active_uids)
            global_limit = config.max_concurrent_downloads

            can_start = (
                uid in self._active_uids or  # already tracked
                (total_active < global_limit and active_in_cat < max_concurrent)
            )

            if can_start:
                self._active_uids.add(uid)
                self._active_categories[uid] = category
                return True

            # Queue it
            sched_dt = getattr(d, '_sched_dt', None)
            d._plugin_queued = True
            self._queue.append((uid, 5, category, sched_dt))
            self._queue.sort(key=lambda x: (-x[1], x[3] or datetime.max))

        log(f'queue_scheduler: queued {getattr(d, "name", uid)} [{category}]', log_level=2)
        d.status = config.Status.pending
        return False  # block immediate start

    def on_download_complete(self, d) -> bool:
        uid = getattr(d, 'uid', None)
        if uid:
            with self._queue_lock:
                self._active_uids.discard(uid)
                self._active_categories.pop(uid, None)
        return True

    # ------------------------------------------------------------ scheduler loop

    def _scheduler_loop(self):
        while self._running:
            try:
                self._tick()
            except Exception as e:
                log(f'queue_scheduler: tick error: {e}')
            time.sleep(5)

    def _tick(self):
        now = datetime.now()
        now_time = now.time()
        allowed_cats = self._allowed_categories(now_time)

        with self._queue_lock:
            remaining = []
            for item in self._queue:
                uid, priority, category, sched_dt = item

                if sched_dt and now < sched_dt:
                    remaining.append(item)
                    continue

                if allowed_cats is not None and category not in allowed_cats:
                    remaining.append(item)
                    continue

                cat_cfg = self.categories.get(category, self.categories['General'])
                max_concurrent = cat_cfg.get('max_concurrent', 3)
                active_in_cat = sum(1 for c in self._active_categories.values() if c == category)
                total_active = len(self._active_uids)

                if total_active >= config.max_concurrent_downloads or active_in_cat >= max_concurrent:
                    remaining.append(item)
                    continue

                if self._start_download(uid):
                    self._active_uids.add(uid)
                    self._active_categories[uid] = category
                    log(f'queue_scheduler: started uid={uid} [{category}]', log_level=2)
                else:
                    remaining.append(item)

            self._queue = remaining

    def _start_download(self, uid: str) -> bool:
        from ..controller import Controller
        ctrl = Controller._instance
        if ctrl is None:
            return False
        return ctrl._start_queued_download(uid)

    def _allowed_categories(self, now_time) -> list:
        for start, end, cats in self.time_rules:
            if start <= now_time <= end:
                return cats
        return None  # no restriction

    @staticmethod
    def _categorize(d) -> str:
        ext = getattr(d, 'extension', '').lower()
        return _EXT_CATEGORY.get(ext, 'General')


PluginRegistry.register(QueueSchedulerPlugin)
