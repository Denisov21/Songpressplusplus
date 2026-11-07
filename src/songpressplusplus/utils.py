##############################################################
# Name:         utils.py
# Purpose:      Funzioni di utilità condivise di Songpress++:
#               - temp_dir        (cartella temporanea)
#               - undo_action     (operazione di annullamento atomica)
#               - set_pin_state   (icona del pulsante pin)
# Author:       Denisov21 (set_pin_state, pin_bitmap)
# Copyright:    Denisov21 © 2026
#               Basato su Songpress di Luca Allulli (https://www.skeed.it/songpress)
# License:      GNU GPL v2
##############################################################

from collections import defaultdict
from contextlib import contextmanager
import os
import tempfile
import logging
import shutil

import wx.stc


@contextmanager
def temp_dir(keep=False):
    """
    Context manager. Create and yield a temporary dir, and destroys it on exit
    """
    t = tempfile.mkdtemp()
    try:
        yield t
    finally:
        if keep:
            logging.info(f"Keeping temporary folder: {t}")
        else:
            shutil.rmtree(t)


_undo_action_in_progress = set()


@contextmanager
def undo_action(text: wx.stc.StyledTextCtrl):
    """
    Context manager. Handle an atomic undo operation on a StyledTextCtrl
    """
    nested = text in _undo_action_in_progress
    if not nested:
        text.BeginUndoAction()
        _undo_action_in_progress.add(text)
    try:
        yield
    finally:
        if not nested:
            text.EndUndoAction()
            _undo_action_in_progress.remove(text)


# ── Icona del pulsante «pin» (mantieni aperta la finestra) ───────────────────
# Si cerca in quest'ordine:
#   1. img/vector/pin_off.svg  /  img/vector/pin_on.svg    (vettoriale)
#   2. img/pin_off.png         /  img/pin_on.png           (bitmap)
#   3. emoji: 📌 (non fissato) / 📍 (fissato)
# «off» = finestra non fissata, «on» = finestra fissata.

PIN_EMOJI_OFF = u"\U0001F4CC"   # 📌
PIN_EMOJI_ON  = u"\U0001F4CD"   # 📍

_PIN_DEFAULT_SIZE = 18
_pin_cache = {}


def _pin_from_svg(path, size):
    """Bitmap rasterizzata da un SVG (wxPython >= 4.1.1), oppure None."""
    try:
        if not os.path.isfile(path):
            return None
        bundle = wx.BitmapBundle.FromSVGFile(path, wx.Size(size, size))
        if not bundle.IsOk():
            return None
        bmp = bundle.GetBitmap(wx.Size(size, size))
        return bmp if bmp.IsOk() else None
    except Exception:
        return None


def _pin_from_png(path, size):
    """Bitmap da un PNG, scalata a size x size se serve, oppure None."""
    try:
        if not os.path.isfile(path):
            return None
        img = wx.Image(path, wx.BITMAP_TYPE_PNG)
        if not img.IsOk():
            return None
        if img.GetWidth() != size or img.GetHeight() != size:
            img = img.Scale(size, size, wx.IMAGE_QUALITY_HIGH)
        bmp = wx.Bitmap(img)
        return bmp if bmp.IsOk() else None
    except Exception:
        return None


def pin_bitmap(on, size=_PIN_DEFAULT_SIZE):
    """Icona del pin (SVG, poi PNG). None se nessuno dei due file esiste."""
    key = (bool(on), size)
    if key in _pin_cache:
        return _pin_cache[key]
    from .Globals import glb   # import locale: evita dipendenze circolari
    name = 'pin_on' if on else 'pin_off'
    bmp = _pin_from_svg(glb.AddPath('img/vector/' + name + '.svg'), size)
    if bmp is None:
        bmp = _pin_from_png(glb.AddPath('img/' + name + '.png'), size)
    _pin_cache[key] = bmp
    return bmp


def set_pin_state(btn, on, size=_PIN_DEFAULT_SIZE):
    """Imposta l'aspetto del pulsante pin: icona se disponibile, altrimenti
    l'emoji. Da chiamare alla creazione e a ogni cambio di stato."""
    bmp = pin_bitmap(on, size)
    if bmp is not None:
        btn.SetLabel(u"")
        btn.SetBitmap(bmp)
    else:
        btn.SetBitmap(wx.NullBitmap)
        btn.SetLabel(PIN_EMOJI_ON if on else PIN_EMOJI_OFF)
