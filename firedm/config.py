"""FireDM: multi-connections internet download manager.

Based on "LibCurl", "yt_dlp", and Tkinter.

:copyright: (c) 2019-2021 by Mahmoud Elshahat.
:license: GNU LGPLv3, see LICENSE for more details.
"""

from __future__ import annotations

import logging
import os
import platform
import sys
from pathlib import Path
from queue import Queue
from typing import Any, Dict, List, Optional, Tuple

from .version import __version__

logger = logging.getLogger(__name__)

# Settings parameters to be saved on disk
settings_keys: List[str] = [
    'active_video_extractor', 'auto_rename', 'autoscroll_download_tab', 'check_for_update', 'checksum', 'current_theme',
    'custom_user_agent', 'disable_log_popups', 'ditem_show_top', 'download_folder', 'download_thumbnail',
    'enable_proxy', 'enable_systray', 'gui_font', 'ibus_workaround', 'ignore_ssl_cert',
    'keep_temp', 'last_update_check', 'log_level', 'max_concurrent_downloads', 'remember_web_auth', 'use_web_auth',
    'username', 'password', 'max_connections', 'minimize_to_systray', 'monitor_clipboard', 'on_download_notification',
    'proxy', 'recent_folders', 'refresh_url_retries', 'scrollbar_width', 'speed_limit', 'update_frequency',
    'playlist_autonum_options', 'use_server_timestamp', 'window_size', 'write_metadata', 'view_mode', 'temp_folder',
    'window_maximized', 'force_window_maximize', 'd_preview', 'updater_version', 'media_presets',
    'video_title_template', 'ffmpeg_actual_path', 'allow_user_extractors',
    'plugin_states', 'plugin_dir', 'allow_user_plugins',
]

# ----------------------------------------------------------------------------------------General ----------------------
# CONSTANTS
APP_NAME = 'FireDM'
APP_VERSION = __version__
APP_TITLE = f'{APP_NAME} version {APP_VERSION} .. an open source download manager'

# minimum segment size used in auto-segmentation process, refer to brain.py>thread_manager.
SEGMENT_SIZE = 1024 * 100  # 100 KB

APP_URL = 'https://github.com/GurucharanSavanth/FireDM'
LATEST_RELEASE_URL = 'https://github.com/GurucharanSavanth/FireDM/releases/latest'
FFMPEG_DOWNLOAD_HELP_URL = 'https://ffmpeg.org/download.html'

FROZEN = getattr(sys, "frozen", False)  # check if app is being compiled by cx_freeze

operating_system = platform.system()  # current operating system  ('Windows', 'Linux', 'Darwin')

# Example output: Os: Linux - Platform: Linux-5.11.0-7614-generic-x86_64-with-glibc2.32 - Machine: x86_64
operating_system_info = f"Os: {platform.system()} - Platform: {platform.platform()} - Machine: {platform.machine()}"

try:
    import distro

    # Example output: Distribution: ('Pop!_OS', '20.10', 'groovy')
    operating_system_info += f"\nDistribution: {distro.linux_distribution(full_distribution_name=True)}"
except (ImportError, AttributeError) as e:
    logger.debug(f"Could not get Linux distribution info: {e}")

# release type
isappimage = False  # will be set to True by AppImage run script
appimage_update_folder = None  # will be set by AppImage run script

# application exit flag
shutdown = False

on_download_notification = True  # show notify message when done downloading

# Filesystem options
# Current folders
if hasattr(sys, 'frozen'):  # Application frozen by cx_freeze
    current_directory: Path = Path(sys.executable).parent
else:
    current_directory = Path(__file__).resolve().parent

sys.path.insert(0, str(current_directory.parent))
sys.path.insert(0, str(current_directory))

sett_folder: Optional[Path] = None
global_sett_folder: Optional[Path] = None
download_folder: Path = Path.home() / 'Downloads'
recent_folders: List[Path] = []

auto_rename: bool = False  # Auto rename file if one exists at download folder
checksum: bool = False  # Calculate checksums for completed files (MD5, SHA256)
playlist_autonum_options: Dict[str, bool] = {
    'enable': True,
    'reverse': False,
    'zeropadding': True,
}

# Video file title template
# ref: https://github.com/ytdl-org/youtube-dl#output-template
video_title_template: str = ''  # '%(title)s'

temp_folder: str = ''

# Network Options
proxy: str = ''  # Example: 127.0.0.1:8080
enable_proxy: bool = False

# Authentication Options
use_web_auth: bool = False
remember_web_auth: bool = False
username: str = ''
password: str = ''

# Video Options
# youtube-dl abort flag, used by decorated YoutubeDl.urlopen()
ytdl_abort: bool = False
video_extractors_list: List[str] = ['youtube_dl', 'yt_dlp']
active_video_extractor: str = 'yt_dlp'

ffmpeg_actual_path: str = ''
ffmpeg_version: str = ''
ffmpeg_download_folder: Optional[Path] = sett_folder

# Media presets
media_presets: Dict[str, str] = {
    'video_ext': 'mp4',
    'video_quality': 'best',
    'dash_audio': 'best',
    'audio_ext': 'mp3',
    'audio_quality': 'best'
}

# SECURITY: load_user_extractors() executes every .py in user-writable
# extractors folder. Default OFF so a dropped file doesn't grant ACE on
# next FireDM launch. See tests/test_security.py F-HIGH-6.
allow_user_extractors: bool = False

# Plugin system — all plugins default OFF; user enables via GUI toggle
plugin_states: Dict[str, bool] = {}  # {plugin_name: bool}, persisted in setting.cfg
plugin_dir: str = ''  # Path to custom user plugin directory
allow_user_plugins: bool = False  # SECURITY: loading user plugins = importlib exec

# Video qualities
vq: Dict[int, str] = {
    4320: '4320p-8K',
    2160: '2160p-4K',
    1440: '1440p-HD',
    1080: '1080-HD',
    720: '720p',
    480: '480p',
    360: '360p',
    240: '240p',
    144: '144p',
}
standard_video_qualities: List[int] = list(vq.keys())
video_quality_choices: List[str] = ['best'] + list(vq.values()) + ['lowest']
video_ext_choices: Tuple[str, ...] = ('mp4', 'webm', '3gp')
dash_audio_choices: Tuple[str, ...] = ('best', 'lowest')
audio_ext_choices: Tuple[str, ...] = ('mp3', 'aac', 'wav', 'm4a', 'opus', 'flac', 'ogg', 'webm')
audio_quality_choices: Tuple[str, ...] = ('best', 'lowest')

# Workarounds
ibus_workaround: bool = False  # Issue #256
ignore_ssl_cert: bool = False  # Ignore SSL certificate validation

# Random user agent will be used later if no custom user agent set
DEFAULT_USER_AGENT: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3721.3'
custom_user_agent: Optional[str] = None
http_headers: Dict[str, str] = {
    'User-Agent': custom_user_agent or DEFAULT_USER_AGENT,
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-us,en;q=0.5',
}

use_referer: bool = False
referer_url: str = ''  # Referer website URL
use_cookies: bool = False
cookie_file_path: str = ''

# Post-processing Options
download_thumbnail: bool = False
write_metadata: bool = False  # Write metadata to video file
shutdown_pc: bool = False
on_completion_command: str = ''
on_completion_exit: bool = False
use_server_timestamp: bool = False  # Write 'last modified' timestamp to downloaded file

# Application Update Options
# Set this flag to True to disable update feature completely
disable_update_feature: bool = False

check_for_update: bool = not disable_update_feature
update_frequency: int = 7  # Days
last_update_check: Optional[Tuple[int, int, int]] = None  # Date format (year, month, day)
updater_version: str = ''  # Application version that did last update check

youtube_dl_version: Optional[str] = None
yt_dlp_version: Optional[str] = None
atk_version: Optional[str] = None  # awesometkinter

# Downloader Options
refresh_url_retries: int = 1  # Retries to refresh expired URL, zero to disable
speed_limit: int = 0  # Bytes, zero = no limit
max_concurrent_downloads: int = 3
max_connections: int = 10
max_seg_retries: int = 10  # Maximum download retries for a segment

# Debugging Options
keep_temp: bool = False  # Keep temp files/folders after download for debugging

max_log_size: int = 1024 * 1024 * 5  # 5 MB
log_level: int = 2  # standard=1, verbose=2, debug=3

# Log callbacks executed when calling log function
# Callback and popup accept 3 positional args: log_callback(start, text, end)
log_callbacks: List[Any] = []
log_popup_callback: Optional[Any] = None
test_mode: bool = False

# GUI Options
DEFAULT_THEME: str = 'Orange_Black'
current_theme: str = DEFAULT_THEME
gui_font: Dict[str, Any] = {}
gui_font_size_default: int = 10
gui_font_size_range: range = range(6, 26)

scrollbar_width_default: int = 10
scrollbar_width: int = scrollbar_width_default
scrollbar_width_range: range = range(1, 51)
monitor_clipboard: bool = True
autoscroll_download_tab: bool = False
ditem_show_top: bool = True

# Systray disabled by default (doesn't work on most OS except Windows)
enable_systray: bool = True if operating_system == 'Windows' else False
minimize_to_systray: bool = False

DEFAULT_WINDOW_SIZE: Tuple[int, int] = (925, 500)  # width, height in pixels
window_size: Tuple[int, int] = DEFAULT_WINDOW_SIZE
window_maximized: bool = False
force_window_maximize: bool = False

BULK: str = 'Bulk'
COMPACT: str = 'Compact'
MIX: str = 'Mix'
DEFAULT_VIEW_MODE: str = MIX
view_mode: str = DEFAULT_VIEW_MODE
view_mode_choices: Tuple[str, ...] = (COMPACT, BULK, MIX)
view_filter: str = 'ALL'  # Show all
d_preview: bool = False  # Preview for download items

# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

# Queues
error_q: Queue[Any] = Queue()  # Used by workers to report server connection errors
jobs_q: Queue[Any] = Queue()  # Required for failed worker jobs


class Status:
    """Status enumeration for download items."""

    downloading: str = 'Downloading'
    cancelled: str = 'Paused'
    completed: str = 'Completed'
    pending: str = 'Pending'
    processing: str = 'Processing'  # FFmpeg operations
    error: str = 'Failed'
    scheduled: str = 'Scheduled'
    refreshing_url: str = 'Refreshing url'
    active_states: Tuple[str, ...] = (downloading, processing, refreshing_url)
    all_states: Tuple[str, ...] = (downloading, cancelled, completed, pending, processing, error, scheduled, refreshing_url)


view_filter_map: Dict[str, Tuple[str, ...]] = {
    'ALL': Status.all_states,
    'Selected': (),
    'Active': Status.active_states,
    'Uncompleted': tuple(s for s in Status.all_states if s != Status.completed)
}

for status in [x for x in Status.all_states if x not in Status.active_states]:
    view_filter_map[status] = (status,)


class MediaType:
    """Media type enumeration."""

    general: str = 'general'
    video: str = 'video'
    audio: str = 'audio'
    key: str = 'key'


# Popup windows for user responses
disable_log_popups: bool = False

popups: Dict[int, Dict[str, Any]] = {
    1: {
        'tag': 'html contents',
        'description': 'Show "Contents might be an html web page warning".',
        'body': 'Contents might be a web page / html, Download anyway?',
        'options': ['Ok', 'Cancel'],
        'default': 'Ok',
        'show': True
    },
    2: {
        'tag': 'ffmpeg',
        'description': 'Prompt for ffmpeg install help if not found on Windows.',
        'body': 'FFMPEG is missing! Install ffmpeg or add ffmpeg.exe to the app folder, PATH, or Winget package folder.',
        'options': ['Open Help', 'Cancel'],
        'default': 'Open Help',
        'show': True
    },
    4: {
        'tag': 'overwrite file',
        'description': 'Ask what to do if same file already exist on disk.',
        'body': 'File with the same name already exist on disk',
        'options': ['Overwrite', 'Rename', 'Cancel'],
        'default': 'Rename',
        'show': True
    },
    5: {
        'tag': 'non-resumable',
        'description': 'Show "Non-resumable downloads warning".',
        'body': (
            'Warning!\n'
            'This remote server does not support chunk downloading.\n'
            'If download stops, resume will not be available and the file will be downloaded from the beginning.\n'
            'Are you sure you want to continue?'
        ),
        'options': ['Yes', 'Cancel'],
        'default': 'Yes',
        'show': True
    },
    6: {
        'tag': 'ssl-warning',
        'description': 'Show warning when disabling SSL verification.',
        'body': (
            'WARNING: Disabling SSL certificate verification could allow hackers to perform '
            'man-in-the-middle attacks and make communication insecure.\n\n'
            'Are you sure?'
        ),
        'options': ['Yes', 'Cancel'],
        'default': 'Yes',
        'show': True
    },
    7: {
        'tag': 'delete-item',
        'description': 'Confirm when deleting an item from download list.',
        'body': 'Remove item(s) from the list?',
        'options': ['Yes', 'Cancel'],
        'default': 'Yes',
        'show': True
    },
}

for k in popups.keys():
    var_name = f'popup_{k}'
    globals()[var_name] = True if k in (2, 4, 6, 7) else False
    settings_keys.append(var_name)


def get_popup(k: int) -> Dict[str, Any]:
    """Get popup configuration by key.

    Args:
        k: Popup key identifier.

    Returns:
        Popup configuration dictionary.
    """
    item = popups[k]
    item['show'] = globals()[f'popup_{k}']
    return item


def enable_popup(k: int, value: bool) -> None:
    """Enable or disable a popup.

    Args:
        k: Popup key identifier.
        value: True to enable, False to disable.
    """
    globals()[f'popup_{k}'] = value

# disable some popups
