# coding: utf-8

import sys
import os
import os.path
import platform
from cx_Freeze import setup, Executable


def _get_files(d):
    out = []
    parent, nd = os.path.split(d)
    n = len(parent)
    for dirpath, dirnames, filenames in os.walk(d):
        base = dirpath[n:]
        for f in filenames:
            out.append(os.path.join(base, f))
    return out


def get_files(dirs):
    """
    Get list of file paths included in dirs.

    dirs is a list of paths.

    Returned paths are relative to dir's parent.
    """
    out = []
    for d in dirs:
        out.extend(_get_files(d))
    return out


include_files = [(x, x) for x in get_files(['help', 'img', 'locale', 'templates', 'xrc'])]

options = {
    'build_exe': {
        'include_files': include_files,
        'include_msvcr': True,
        'packages': [
            "multiprocessing",
            "idna.idnadata",
            "ssl",
            "wx",
            "requests",
            "reportlab",
            "pptx",
            "pyshortcuts",
        ],
        'excludes': ["numpy", "tkinter"],
    }
}

# Workaround for cx_Freeze + requests su Windows (OpenSSL DLL)
# https://github.com/anthony-tuininga/cx_Freeze/issues/437
PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
if sys.platform == "win32":
    for dll in ('libcrypto-1_1.dll', 'libssl-1_1.dll'):
        dll_path = os.path.join(PYTHON_INSTALL_DIR, 'DLLs', dll)
        if os.path.exists(dll_path):
            options['build_exe']['include_files'].append(dll_path)

base = "Win32GUI" if sys.platform == "win32" else None


def build(version):
    setup(
        name="Songpress++",
        version=version,
        description="Songpress++ - Il Canzonatore",
        options=options,
        executables=[Executable(
            "main.py",
            base=base,
            target_name='Songpress++' if platform.system() == 'Linux' else "Songpress++.exe",
            icon='songpressplusplus.ico',
        )]
    )


if __name__ == '__main__':
    import Globals
    build(Globals.glb.VERSION)
