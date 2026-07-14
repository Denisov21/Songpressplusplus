# coding: utf-8

###############################################################
# Name:             Globals.py
# Purpose:     Hold global settings
# Author:         Luca Allulli (webmaster@roma21.it)
# Created:     2009-09-04
# Modified by: Denisov21 (https://github.com/Denisov21/Songpressplusplus)
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
#               Modifications copyright Denisov21
# License:     GNU GPL v2
##############################################################

import os.path
import sys
import shutil
from importlib.metadata import version, PackageNotFoundError

import wx


def _read_version():
    try:
        return version("songpressplusplus")
    except PackageNotFoundError:
        pass
    try:
        import tomllib
        _toml_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'pyproject.toml')
        with open(_toml_path, 'rb') as f:
            return tomllib.load(f)['project']['version']
    except Exception:
        pass
    return "dev"


def _read_name():
    try:
        from importlib.metadata import metadata
        return metadata("songpressplusplus")['Name']
    except Exception:
        pass
    try:
        import tomllib
        _toml_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'pyproject.toml')
        with open(_toml_path, 'rb') as f:
            return tomllib.load(f)['project']['name']
    except Exception:
        pass
    return "Songpress++"


class Globals(object):
    # Subfolders of templates/ that must always exist, both in the package
    # (global root) and in the user data dir (local root). Kept in sync with
    # MyPreferencesDialog._TEMPLATE_SUBDIRS: this is exactly the tree that the
    # "Open templates folder" button reveals to the user.
    #   fonts/      → custom fonts used by preview/export
    #   local_dir/  → skeleton copied into the data dir on first run
    #   slides/     → PowerPoint templates (.pptx)
    #   songs/      → song templates (.crd)
    #   themes/     → editor colour themes (.ini)
    TEMPLATE_SUBDIRS = ('fonts', 'local_dir', 'slides', 'songs', 'themes')

    def __init__(self):
        object.__init__(self)
        current_file = os.path.abspath(__file__)
        self.path = os.path.dirname(current_file)
        self.data_path = None

    def InitDataPath(self):
        sp = wx.StandardPaths.Get()
        portable_config = os.path.join(self.path, 'config.ini')
        if os.path.isfile(portable_config):
            # Monkey-patch StandardPaths instance so that portable config.ini is used
            def my_get(*args, **kwargs):
                return self.path
            sp.GetUserDataDir = my_get

        self.data_path = sp.GetUserDataDir()
        old_config = None
        if os.path.isfile(self.data_path):
            old_config = self.data_path + ".orig"
            shutil.move(self.data_path, old_config)
        if not os.path.exists(self.data_path):
            local_dir_src = os.path.join(self.path, 'templates', 'local_dir')
            if os.path.isdir(local_dir_src):
                shutil.copytree(local_dir_src, self.data_path)
            else:
                os.makedirs(self.data_path, exist_ok=True)
        if old_config is not None:
            # Preserve old config file, but don't use it
            shutil.move(old_config, os.path.join(self.data_path, "config.ini.orig"))

        # Ensure the user data dir always exposes every template subfolder, even
        # if templates/local_dir was incomplete or not shipped at all. Without
        # them ListLocalGlobalDir('templates/slides') would find nothing and the
        # "Open templates folder" button would show an incomplete tree.
        for sub in self.TEMPLATE_SUBDIRS:
            try:
                os.makedirs(os.path.join(self.data_path, 'templates', sub),
                            exist_ok=True)
            except OSError:
                pass  # read-only data dir: features degrade gracefully

    def AddPath(self, filename):
        return os.path.join(self.path, filename)

    def ListLocalGlobalDir(self, rel_path):
        """
        List both the local (data) and global (program) versions of a directory

        Missing or unreadable directories are silently skipped: on a system-wide
        installation (.deb) the data dir may not contain every subfolder yet, and
        os.listdir() would raise FileNotFoundError. Same tolerant behaviour as
        SongpressFrame._PopulateTemplateMenu().

        :param rel_path: relative path
        :return: list of absolute paths of files (global first, then local)
        """
        out = []
        for root in (self.path, self.data_path):
            if not root:
                continue  # data_path not initialised yet
            folder = os.path.join(root, rel_path)
            if not os.path.isdir(folder):
                continue
            try:
                for f in sorted(os.listdir(folder)):
                    out.append(os.path.join(folder, f))
            except OSError:
                pass  # unreadable directory: skip it
        return out

    languages = {
        'en': "English",
        'it': "Italiano",
    }

    translators = {
        'en': "Luca Allulli, Denisov21",
        'it': "Luca Allulli, Denisov21",
    }

    default_language = 'en'

    PROG_NAME = _read_name()
    VERSION = _read_version()
    BUG_REPORT_ADDRESS = ''
    YEAR = '2026'

glb = Globals()
