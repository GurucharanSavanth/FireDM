"""
    FireDM

    multi-connections internet download manager, based on "pyCuRL/curl", and "youtube_dl""

    :copyright: (c) 2019-2021 by Mahmoud Elshahat.
    :license: GNU LGPLv3, see LICENSE for more details.

    Module description:
        build an executable (exe) for windows using cx_freeze
        you should execute this module from command line using: "python cx_setup.py build" on windows only.
"""

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from cx_Freeze import Executable, setup

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

APP_NAME = 'FireDM'

# to run setup.py directly
if len(sys.argv) == 1:
    sys.argv.append("build")

# get current directory
fp = Path(__file__).resolve()
current_folder = fp.parent

logger.info('cx_setup.py ....................................................................................')

project_folder = current_folder.parent.parent
build_folder = current_folder
app_folder = build_folder / APP_NAME
icon_path = project_folder / 'icons' / '48_32_16.ico'  # best use size 48, and must be an "ico" format
version_fp = project_folder / 'firedm' / 'version.py'
requirements_fp = project_folder / 'requirements.txt'
main_script_path = project_folder / 'firedm.py'

sys.path.insert(0, str(project_folder))  # for imports to work
from firedm.utils import simpledownload, delete_folder, create_folder

# create build folder
create_folder(str(build_folder))

# get version
version_module: Dict[str, Any] = {}
with open(version_fp, encoding='utf-8') as f:
    exec(f.read(), version_module)  # then we can use it as: version_module['__version__']
    version = version_module['__version__']


# get required packages
with open(requirements_fp, encoding='utf-8') as f:
    packages: List[str] = [line.strip().split(' ')[0] for line in f.readlines() if line.strip()] + ['firedm']

# clean names
packages = [pkg.replace(';', '') for pkg in packages]

# filter some packages
for pkg in ['distro', 'Pillow']:
    if pkg in packages:
        packages.remove(pkg)

# add keyring to packages
packages.append('keyring')

logger.info(f'packages: {packages}')

includes = []
include_files = []
excludes = ['numpy', 'test', 'setuptools', 'unittest']

cmd_target_name = f'{APP_NAME.lower()}.exe'
gui_target_name = f'{APP_NAME}-GUI.exe'

executables = [
    Executable(main_script_path, base='Console', target_name=cmd_target_name),
    Executable(main_script_path, base='Win32GUI', target_name=gui_target_name, icon=icon_path),
]

setup(

    version=version,
    description=f"{APP_NAME} Download Manager",
    author="Mahmoud Elshahat",
    name=APP_NAME,

    options={"build_exe": {
        "includes": includes,
        'include_files': include_files,
        "excludes": excludes,
        "packages": packages,
        'build_exe': app_folder,
        'include_msvcr': True,
    }
    },

    executables=executables
)

# Post processing

# there is a bug in python3.6 where tkinter name is "Tkinter" with capital T, will rename it.
try:
    print('-' * 50)
    print('rename Tkinter to tkinter')
    os.rename(f'{app_folder}/lib/Tkinter', f'{app_folder}/lib/tkinter')
except Exception as e:
    print(e)

# manually remove excluded libraries if found
for lib_name in excludes:
    folder = f'{app_folder}/lib/{lib_name}'
    delete_folder(folder, verbose=True)

# ffmpeg
ffmpeg_path = os.path.join(current_folder, 'ffmpeg.exe')
if not os.path.isfile(os.path.join(app_folder, 'ffmpeg.exe')):
    if not os.path.isfile(ffmpeg_path):
        # download from github
        ffmpeg_url = 'https://github.com/firedm/FireDM/releases/download/extra/ffmpeg_32bit.exe'
        simpledownload(ffmpeg_url, fp=ffmpeg_path)
    shutil.copy(ffmpeg_path, os.path.join(app_folder, 'ffmpeg.exe'))


# write resource fields for exe files ----------------------------------------------------------------------------------
# install pe-tools  https://github.com/avast/pe_tools
cmd = f'{sys.executable} -m pip install pe_tools'
subprocess.run(cmd, shell=True)

for fname in (cmd_target_name, gui_target_name):
    fp = os.path.join(app_folder, fname)
    info = {
        'Comments': 'https://github.com/firedm/FireDM',
        'CompanyName': 'FireDM',
        'FileDescription': 'FireDM download manager',
        'FileVersion': version,
        'InternalName': fname,
        'LegalCopyright': '2019-2021 by Mahmoud Elshahat',
        'LegalTrademarks': 'FireDM',
        'OriginalFilename': fname,
        'ProductName': 'FireDM',
        'ProductVersion': version,
        'legalcopyright': 'copyright(c) 2019-2021 by Mahmoud Elshahat'
    }

    param = ' -V '.join([f'"{k}={v}"' for k, v in info.items()])
    cmd = f'peresed -V {param} {fp}'
    subprocess.run(cmd, shell=True)

# create zip file
output_filename = f'{APP_NAME}_{version}'
print(f'prepare final zip filename: {output_filename}.zip')
fname = shutil.make_archive(output_filename, 'zip', base_dir=APP_NAME)


print('Done .....')
