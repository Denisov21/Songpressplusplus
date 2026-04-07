###############################################################
# Name:             i18n.py
# Purpose:     Support internationalization
# Author:         Luca Allulli (webmaster@roma21.it)
# Modified by:  Denisov21
# Created:     2009-01-11
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
#               Modifications copyright Denisov21
# License:     GNU GPL v2
###############################################################

import inspect
import os
import locale

from .Globals import *


# 2-character language code of current language
current_language = None
# wxPython wx.Locale object for current language
mylocale = None
# 2-character language code of default language, set during init
defaultLang = None
# Array mapping 2-character language codes of languages supported by Songpress
# to language names. To be set during init phase, by calling init function
supportedLangs = None


"""
Client shall:
1. Call `init`
2. Call either `setLang` (if a langugage is chosen by the user)
   or `setSystemLang`
"""


def init(default_lang, supported_langs):
    global defaultLang
    global supportedLangs
    defaultLang = default_lang
    supportedLangs = supported_langs


import gettext as gettext_module
_ = lambda x: x


def setLang(l):
    global current_language, mylocale, _
    current_language = l
    langid = wx.Locale.FindLanguageInfo(l).Language
    mylocale = wx.Locale(langid)
    localedir = os.path.join(glb.path, "locale")
    xrc_localedir = os.path.join(glb.path, "xrc", "locale")
    mylocale.AddCatalogLookupPathPrefix(localedir)
    mylocale.AddCatalogLookupPathPrefix(xrc_localedir)
    mylocale.AddCatalog('songpress')
    lc_messages_dir = os.path.join(localedir, l, "LC_MESSAGES")
    if os.path.isdir(lc_messages_dir):
        for f in os.listdir(lc_messages_dir):
            fn, ext = os.path.splitext(f)
            if ext.lower() == '.mo' and fn != 'songpress':
                mylocale.AddCatalog(fn)
    for f in os.listdir(glb.path):
        fn, ext = os.path.splitext(f)
        if ext.lower() == '.pot':
            mylocale.AddCatalog(fn)
    # Override _ with gettext so all modules get actual translations.
    # Scansiona automaticamente tutti i .mo in LC_MESSAGES e li concatena.
    import builtins
    lc_messages_dir = os.path.join(localedir, l, "LC_MESSAGES")
    catalog_names = []
    if os.path.isdir(lc_messages_dir):
        for f in os.listdir(lc_messages_dir):
            fn, ext = os.path.splitext(f)
            if ext.lower() == '.mo':
                catalog_names.append(fn)
    for name in ('songpress', 'SongpressFrame'):
        if name not in catalog_names:
            catalog_names.append(name)
    combined = None
    for name in catalog_names:
        try:
            t = gettext_module.translation(name, localedir, languages=[l])
            if combined is None:
                combined = t
            else:
                combined.add_fallback(t)
        except FileNotFoundError:
            pass
    if combined is not None:
        _ = combined.gettext
        builtins._ = _


def getLang():
    return current_language


def setSystemLang():
    l = locale.getdefaultlocale()
    if l is not None and l[0][:2] in supportedLangs:
        setLang(l[0][:2])
    else:
        setLang(defaultLang)


def localizeXrc(filename):
    abs_filename = glb.AddPath(filename)
    if current_language != defaultLang:
        d, domain_full = os.path.split(filename)
        base, ext = os.path.splitext(domain_full)
        # Look for a language-specific XRC file, e.g. "songpress.it.xrc"
        # alongside the original file (using the absolute path directory).
        abs_dir = os.path.dirname(abs_filename)
        localized_filename = os.path.join(abs_dir, f"{base}_{current_language}{ext}")
        if os.path.isfile(localized_filename):
            abs_filename = localized_filename
    res = wx.xrc.XmlResource()
    res.Load(abs_filename)
    return res
