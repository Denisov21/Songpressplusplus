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


# ── Icone dei pulsanti (SVG, poi PNG) ────────────────────────────────────────
# Ogni icona si cerca in quest'ordine:
#   1. img/vector/<nome>.svg     (vettoriale)
#   2. img/<nome>.png            (bitmap, di norma 16x16)
# Se nessuno dei due esiste icon_bitmap() restituisce None e il chiamante
# ripiega sul testo (o sull'emoji, per il pin).

_ICON_DEFAULT_SIZE = 16
_icon_cache = {}


def _icon_from_svg(path, size):
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


def _icon_from_png(path, size):
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


def icon_bitmap(name, size=_ICON_DEFAULT_SIZE):
    """Icona `name` come wx.Bitmap: prima img/vector/<name>.svg, poi
    img/<name>.png. None se nessuno dei due file esiste o è leggibile."""
    key = (name, size)
    if key in _icon_cache:
        return _icon_cache[key]
    from .Globals import glb   # import locale: evita dipendenze circolari
    bmp = _icon_from_svg(glb.AddPath('img/vector/' + name + '.svg'), size)
    if bmp is None:
        bmp = _icon_from_png(glb.AddPath('img/' + name + '.png'), size)
    _icon_cache[key] = bmp
    return bmp


# ── Pulsante «pin» (mantieni aperta la finestra) ─────────────────────────────
# Icone: pin_off / pin_on (vedi icon_bitmap); se mancano, le emoji 📌 / 📍.
# «off» = finestra non fissata, «on» = finestra fissata.

PIN_EMOJI_OFF = u"\U0001F4CC"   # 📌
PIN_EMOJI_ON  = u"\U0001F4CD"   # 📍

_PIN_DEFAULT_SIZE = 18


def pin_bitmap(on, size=_PIN_DEFAULT_SIZE):
    """Icona del pin (SVG, poi PNG). None se nessuno dei due file esiste."""
    return icon_bitmap('pin_on' if on else 'pin_off', size)


def _set_button_icon(btn, bmp):
    """Mostra `bmp` come unica icona del pulsante (senza testo).

    Ritorna True se ci riesce, False altrimenti. Su alcune versioni di wxGTK
    (Linux) SetBitmap() su un pulsante senza testo fa scattare l'asserzione
    «must have image widget» (wxAssertionError) e, non gestita, fa chiudere la
    finestra Opzioni: in quel caso il chiamante ripiega sul testo.
    """
    try:
        btn.SetLabel(u"")
        btn.SetBitmap(bmp)
        return True
    except Exception:
        return False


def safe_set_bitmap(btn, bmp, position=None):
    """btn.SetBitmap(bmp) (+ SetBitmapPosition) che non solleva eccezioni.

    Ritorna True se l'icona e' stata impostata. Su wxGTK alcuni pulsanti
    (quelli standard dell'anteprima di stampa, quelli senza testo) rifiutano
    SetBitmap con l'asserzione «must have image widget»: in quel caso il
    pulsante resta com'e' (senza icona) invece di far crashare la finestra.
    """
    try:
        btn.SetBitmap(bmp)
        if position is not None:
            btn.SetBitmapPosition(position)
        return True
    except Exception:
        return False


def _clear_button_icon(btn):
    """Toglie l'icona dal pulsante, senza mai sollevare eccezioni."""
    try:
        btn.SetBitmap(wx.NullBitmap)
    except Exception:
        pass


def set_pin_state(btn, on, size=_PIN_DEFAULT_SIZE):
    """Imposta l'aspetto del pulsante pin: icona se disponibile (e se il
    sistema la accetta), altrimenti l'emoji. Da chiamare alla creazione e a
    ogni cambio di stato."""
    bmp = pin_bitmap(on, size)
    if bmp is not None and _set_button_icon(btn, bmp):
        return
    _clear_button_icon(btn)
    btn.SetLabel(PIN_EMOJI_ON if on else PIN_EMOJI_OFF)


# ── Pulsante «Schermo intero / Ripristina» delle finestre guida ──────────────

def setup_maximize_button(dlg, btn, label_full, label_restore,
                          size=_ICON_DEFAULT_SIZE):
    """Configura `btn` come interruttore massimizza/ripristina di `dlg`.

    Mostra le icone maximize_page (finestra normale) e reduce (finestra
    massimizzata) con il testo come suggerimento (tooltip). Se manca anche una
    sola delle due icone (né SVG né PNG) ripiega sul testo, come prima, con la
    larghezza fissata al più lungo dei due.
    """
    bmp_full = icon_bitmap('maximize_page', size)
    bmp_rest = icon_bitmap('reduce', size)
    use_icons = bmp_full is not None and bmp_rest is not None

    def _show(maximized):
        nonlocal use_icons
        text = label_restore if maximized else label_full
        btn.SetToolTip(text)
        if use_icons and _set_button_icon(btn, bmp_rest if maximized else bmp_full):
            return
        # Niente icone (file mancanti o rifiutate da wxGTK): si usa il testo,
        # e _fix_size() dimensiona il pulsante di conseguenza.
        use_icons = False
        _clear_button_icon(btn)
        btn.SetLabel(text)

    def _on_toggle(e):
        if dlg.IsMaximized():
            dlg.Restore()
            _show(False)
        else:
            dlg.Maximize()
            _show(True)

    def _fix_size():
        best = btn.GetBestSize()
        if use_icons:
            # Pulsante grande quanto l'icona (più un piccolo margine): la
            # larghezza NON si ricava da GetBestSize(), che può essere ancora
            # quella calcolata con il testo («Schermo intero»). L'altezza resta
            # quella degli altri pulsanti della barra.
            w = size + 12
            h = max(best.height, size + 8)
            btn.SetMinSize(wx.Size(w, h))
            btn.SetSize(wx.Size(w, h))
        else:
            dc = wx.ClientDC(btn)
            dc.SetFont(btn.GetFont())
            w1 = dc.GetTextExtent(label_full)[0]
            w2 = dc.GetTextExtent(label_restore)[0]
            cur_tw = dc.GetTextExtent(btn.GetLabel())[0]
            padding = best.width - cur_tw
            btn.SetMinSize(wx.Size(max(w1, w2) + max(padding, 20), best.height))
        sizer = btn.GetContainingSizer()
        if sizer is not None:
            sizer.Layout()
        parent = btn.GetParent()
        if parent is not None:
            parent.Layout()

    _show(False)
    btn.Bind(wx.EVT_BUTTON, _on_toggle)
    wx.CallAfter(_fix_size)
