"""
    FireDM

    multi-connections internet download manager, based on "LibCurl", and "youtube_dl".

    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.
"""

import json
import os
from datetime import datetime, timezone

from . import config, model
from .app_paths import choose_settings_dir, resolve_global_settings_dir
from .utils import log, update_object


def get_global_sett_folder():
    """return a proper global setting folder"""
    return os.fspath(
        resolve_global_settings_dir(
            config.APP_NAME,
            config.operating_system,
            current_directory=config.current_directory,
        )
    )


config.global_sett_folder = get_global_sett_folder()


def locate_setting_folder():
    """check local folder and global setting folder for setting.cfg file"""
    setting_folder = choose_settings_dir(config.current_directory, config.global_sett_folder)

    if os.fspath(setting_folder) != config.current_directory:
        log("No enough permission to store setting at local folder:", config.current_directory)
        log('Global setting folder will be selected:', config.global_sett_folder)

    return os.fspath(setting_folder)


config.sett_folder = locate_setting_folder()


def _quarantine_invalid_json_file(file):
    """Preserve malformed JSON before the app writes replacement defaults."""
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup_file = f'{file}.invalid-{timestamp}'
    try:
        os.replace(file, backup_file)
        log('Invalid JSON config preserved at:', backup_file)
    except OSError as e:
        log('Could not preserve invalid JSON config:', e)


def load_d_map():
    """create and return a dictionary of 'uid: DownloadItem objects' based on data extracted from 'downloads.dat' file

    """
    d_map = {}

    try:

        log('Load previous download items from', config.sett_folder)

        # get data
        file = os.path.join(config.sett_folder, 'downloads.dat')
        with open(file) as f:
            # expecting a list of dictionaries
            data = json.load(f)

        # SECURITY: refuse to restore attributes that, when paired with the
        # status machine, give the disk file ACE / privilege escalation.
        # `on_completion_command` is invoked via run_command() in
        # `controller._post_download()`; `shutdown_pc` triggers a system
        # shutdown without confirmation. Neither is part of the persisted
        # `saved_properties` schema -- a hostile downloads.dat that adds them
        # is the attack vector. See tests/test_security.py F-HIGH-4.
        UNSAFE_DOWNLOAD_KEYS = ('on_completion_command', 'shutdown_pc')

        # converting data to a map of uid: ObservableDownloadItem() objects
        for uid, d_dict in data.items():  # {'uid': d_dict, 'uid2': d_dict2, ...}
            sanitized_dict = {k: v for k, v in d_dict.items() if k not in UNSAFE_DOWNLOAD_KEYS}
            d = update_object(model.ObservableDownloadItem(), sanitized_dict)
            if d:  # if update_object() returned an updated object not None
                d.uid = uid
                d_map[uid] = d

        # get thumbnails
        file = os.path.join(config.sett_folder, 'thumbnails.dat')
        with open(file) as f:
            # expecting a list of dictionaries
            thumbnails = json.load(f)

        # clean d_map and load thumbnails
        for d in d_map.values():
            d.live_connections = 0

            # for compatibility, after change status value, will correct old stored status values
            valid_values = [x for x in vars(config.Status).values() if isinstance(x, str)]
            for x in valid_values:
                if d.status.lower() == x.lower():
                    d.status = x

            if d.status not in (config.Status.completed, config.Status.scheduled, config.Status.error):
                d.status = config.Status.cancelled

            # use encode() to convert base64 string to byte, however it does work without it, will keep it to be safe
            d.thumbnail = thumbnails.get(d.uid, '').encode()

            # update progress info
            d.load_progress_info()

    except Exception as e:
        log(f'load_d_map()>: {e}')
        return {}

    if not isinstance(d_map, dict):
        return {}
    return d_map


def save_d_map(d_map):
    try:
        data = {}  # dictionary, key=d.uid, value=ObservableDownloadItem
        thumbnails = {}  # dictionary, key=d.uid, value=base64 binary string for thumbnail
        for uid, d in d_map.items():
            d_dict = {key: d.__dict__.get(key) for key in d.saved_properties}
            data[uid] = d_dict

            # thumbnails
            if d.thumbnail:
                # convert base64 byte to string is required because json can't handle byte objects
                thumbnails[d.uid] = d.thumbnail.decode("utf-8")

        # store d_map in downloads.cfg file
        downloads_fp = os.path.join(config.sett_folder, 'downloads.dat')
        with open(downloads_fp, 'w') as f:
            try:
                json.dump(data, f, indent=4)
            except Exception as e:
                print('error save d_list:', e)

        # store thumbnails in thumbnails.cfg file
        thumbnails_fp = os.path.join(config.sett_folder, 'thumbnails.dat')
        with open(thumbnails_fp, 'w') as f:
            try:
                json.dump(thumbnails, f)
            except Exception as e:
                print('error save thumbnails file:', e)

        log('downloads items list saved in:', downloads_fp, log_level=2)
    except Exception as e:
        log('save_d_map()> ', e)


def get_user_settings():
    settings = {}
    file = os.path.join(config.sett_folder, 'setting.cfg')
    try:
        # log('Load user setting from', config.sett_folder)
        with open(file) as f:
            settings = json.load(f)

    except FileNotFoundError:
        log('setting.cfg not found')
    except json.JSONDecodeError as e:
        log('load_setting()> invalid setting.cfg JSON:', e)
        _quarantine_invalid_json_file(file)
    except Exception as e:
        log('load_setting()> ', e)

    if not isinstance(settings, dict):
        return {}
    return settings


def load_setting():

    # log('Load Application setting from', config.sett_folder)
    settings = get_user_settings()

    # SECURITY: filter against the declared schema so a poisoned setting.cfg
    # cannot inject NEW attributes into config (e.g. a `log_popup_callback`
    # function reference) or override trusted constants such as APP_URL /
    # LATEST_RELEASE_URL / FFMPEG_DOWNLOAD_HELP_URL. Only keys explicitly
    # declared by `config.settings_keys` are accepted on disk.
    # See tests/test_security.py F-CRIT-3.
    allowed_keys = set(config.settings_keys)
    safe_settings = {k: v for k, v in settings.items() if k in allowed_keys}
    dropped = [k for k in settings if k not in allowed_keys]
    if dropped:
        log(
            'load_setting()> ignoring unknown / unsafe keys in setting.cfg:',
            dropped,
            log_level=2,
        )

    # update config module
    config.__dict__.update(safe_settings)

    # Plugin loading is deferred to Controller init so registry imports do not
    # run during settings deserialization.
    config.plugin_states = settings.get('plugin_states', {})
    if not isinstance(config.plugin_states, dict):
        config.plugin_states = {}
    if not isinstance(config.plugin_dir, str):
        config.plugin_dir = ''
    config.allow_user_plugins = bool(config.allow_user_plugins)


def save_setting():
    # web authentication
    if not config.remember_web_auth:
        config.username = ''
        config.password = ''

    settings = {key: config.__dict__.get(key) for key in config.settings_keys}

    try:
        file = os.path.join(config.sett_folder, 'setting.cfg')
        with open(file, 'w') as f:
            json.dump(settings, f, indent=4)
            log('settings saved in:', file)
    except Exception as e:
        log('save_setting() > error', e)
