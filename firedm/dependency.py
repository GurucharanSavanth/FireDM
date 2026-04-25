#!/usr/bin/env python
"""
    FireDM

    multi-connections internet download manager, based on "LibCurl", and "yt_dlp".

    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.
"""

# The purpose of this module is checking and auto installing dependencies
import importlib.util
import subprocess
import sys

# add the required packages here without any version numbers
requirements = ['plyer', 'certifi', 'yt_dlp', 'pycurl', 'PIL', 'pystray', 'awesometkinter']
pip_names = {
    'PIL': 'pillow',
    'yt_dlp': 'yt-dlp[default]',
}


def is_venv():
    """check if running inside virtual environment
    there is no 100% working method to tell, but we can check for both real_prefix and base_prefix"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)


def install_missing_pkgs():

    # list of dependency
    missing_pkgs = [pkg for pkg in requirements if importlib.util.find_spec(pkg) is None]

    if missing_pkgs:
        print('required pkgs: ', requirements)
        print('missing pkgs: ', missing_pkgs)

        for pkg in missing_pkgs:
            pkg = pip_names.get(pkg, pkg)

            # using "--user" flag is safer also avoid the need for admin privilege , but it fails inside venv, where pip
            # will install packages normally to user folder but venv still can't see those packages

            if is_venv():
                cmd = [sys.executable, "-m", "pip", "install", '--upgrade', pkg]  # no --user flag
            else:
                cmd = [sys.executable, "-m", "pip", "install", '--user', '--upgrade', pkg]

            print('running command:', ' '.join(cmd))
            subprocess.run(cmd, shell=False)


