###############################################################
# Name:             Watermark.py
# Purpose:          Filigrana (watermark) per stampa ed esportazione
# Author:           Denisov21
# License:          GNU GPL v2
###############################################################
#
# Disegna una filigrana diagonale su un qualsiasi wx.DC.
# Funziona su tutti i backend usati da Songpress++:
#   - wx.MemoryDC   (export PNG)
#   - wx.SVGFileDC  (export SVG, copy-as-image)
#   - wx.PostScriptDC (export EPS)
#   - wx.MetafileDC (export EMF, copy-as-image su Windows)
#   - wx.PrinterDC / Printout DC (stampa)
#
# La trasparenza NON e' usata con GraphicsContext (non supportato da
# SVGFileDC/PostScriptDC): viene invece SIMULATA fondendo il colore verso
# il bianco del foglio in base alla percentuale di opacita'. Cosi'
# DrawRotatedText funziona identico su ogni DC.
#
###############################################################

import math
import wx

_ = wx.GetTranslation


# Valori di default (usati anche da SongpressFrame per inizializzare le pref)
DEFAULTS = {
    'enabled':    False,
    'text':       'DRAFT',
    'opacity':    12,          # 2..100  (percentuale di "intensita'": alto = piu' scuro)
    'angle':      45,          # -90..90 gradi
    'sizePct':    100,         # 20..300 scala della dimensione carattere
    'tile':       False,       # False = una filigrana centrata; True = ripetuta a mosaico
    'colourHex':  '#000000',
    'showInPreview': True,     # True = mostra la filigrana anche nell'anteprima Songpress
}


def _blend_toward_white(hex_str, opacity_pct):
    """Fonde `hex_str` verso il bianco secondo l'opacita' (2..100 -> 0.02..1.0).

    Simula la trasparenza su DC che non supportano l'alpha (SVG, PostScript).
    Il foglio e' bianco in stampa e in tutti gli export, quindi il risultato
    e' visivamente corretto.
    """
    try:
        r = int(hex_str[1:3], 16)
        g = int(hex_str[3:5], 16)
        b = int(hex_str[5:7], 16)
    except (ValueError, IndexError, TypeError):
        r, g, b = 0, 0, 0
    a = max(2, min(100, int(opacity_pct))) / 100.0
    R = int(round(255 * (1 - a) + r * a))
    G = int(round(255 * (1 - a) + g * a))
    B = int(round(255 * (1 - a) + b * a))
    return wx.Colour(R, G, B)


def _make_font(point_size):
    ps = max(6, int(point_size))
    return wx.Font(ps, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                   wx.FONTWEIGHT_BOLD, False)


def _fit_font(dc, text, target_width, size_pct):
    """Trova una dimensione carattere per cui il testo largo ~ target_width."""
    probe = 100
    dc.SetFont(_make_font(probe))
    tw, th = dc.GetTextExtent(text or ' ')
    if tw < 1:
        tw = 1
    size = probe * (target_width / tw)
    size = size * (max(20, min(300, int(size_pct))) / 100.0)
    font = _make_font(size)
    dc.SetFont(font)
    return dc.GetTextExtent(text or ' ')


def draw_watermark(dc, w, h, cfg):
    """Disegna la filigrana su `dc` entro l'area (w x h).

    `cfg` e' un dict con le chiavi di DEFAULTS. Se il testo e' vuoto non fa
    nulla. Da chiamare PRIMA di renderizzare il brano, cosi' la filigrana
    finisce dietro al testo e non lo oscura.
    """
    if w <= 1 or h <= 1:
        return
    text = (cfg.get('text') or '').strip()
    if not text:
        return

    angle_deg = float(cfg.get('angle', 45))
    colour = _blend_toward_white(cfg.get('colourHex', '#000000'),
                                 cfg.get('opacity', 12))

    dc.SetTextForeground(colour)

    diag = math.hypot(w, h)

    if cfg.get('tile', False):
        _draw_tiled(dc, w, h, text, angle_deg, cfg.get('sizePct', 100), diag)
    else:
        _draw_centered(dc, w, h, text, angle_deg, cfg.get('sizePct', 100), diag)


def _draw_centered(dc, w, h, text, angle_deg, size_pct, diag):
    target = diag * 0.72
    tw, th = _fit_font(dc, text, target, size_pct)

    theta = math.radians(angle_deg)
    cos, sin = math.cos(theta), math.sin(theta)
    cx, cy = w / 2.0, h / 2.0

    # DrawRotatedText ancora al top-left e ruota in senso antiorario attorno
    # a quel punto. Ricaviamo l'ancora affinche' il centro del testo cada al
    # centro dell'area.
    x = cx - (tw / 2.0) * cos - (th / 2.0) * sin
    y = cy + (tw / 2.0) * sin - (th / 2.0) * cos
    dc.DrawRotatedText(text, int(round(x)), int(round(y)), angle_deg)


def _draw_tiled(dc, w, h, text, angle_deg, size_pct, diag):
    # In modalita' mosaico usiamo un carattere piu' piccolo e ripetiamo.
    target = diag * 0.28
    tw, th = _fit_font(dc, text, target, size_pct)

    theta = math.radians(angle_deg)
    cos, sin = math.cos(theta), math.sin(theta)

    step_x = max(tw, th) + int(diag * 0.10)
    step_y = max(th * 3, int(diag * 0.16))

    # Copriamo un'area piu' ampia dell'output cosi' la rotazione non lascia
    # angoli vuoti.
    y = -step_y
    row = 0
    while y < h + step_y:
        offset = (step_x // 2) if (row % 2) else 0
        x = -step_x + offset
        while x < w + step_x:
            ax = x - (tw / 2.0) * cos - (th / 2.0) * sin
            ay = y + (tw / 2.0) * sin - (th / 2.0) * cos
            dc.DrawRotatedText(text, int(round(ax)), int(round(ay)), angle_deg)
            x += step_x
        y += step_y
        row += 1


# ---------------------------------------------------------------------------
# Dialogo di configurazione
# ---------------------------------------------------------------------------

class WatermarkDialog(wx.Dialog):
    """Dialogo per aggiungere/rimuovere e configurare la filigrana."""

    def __init__(self, parent, cfg):
        super().__init__(parent, title=_("Watermark"),
                         style=wx.DEFAULT_DIALOG_STYLE)
        self._cfg = dict(DEFAULTS)
        self._cfg.update(cfg or {})

        pad = 8
        main = wx.BoxSizer(wx.VERTICAL)

        # Abilita filigrana
        self.chkEnabled = wx.CheckBox(self, label=_("Enable watermark"))
        self.chkEnabled.SetValue(bool(self._cfg['enabled']))
        main.Add(self.chkEnabled, 0, wx.ALL, pad)

        # Mostra anche nell'anteprima Songpress (stampa/export non ne dipendono)
        self.chkPreview = wx.CheckBox(self, label=_("Show in Songpress preview++"))
        self.chkPreview.SetValue(bool(self._cfg.get('showInPreview', True)))
        main.Add(self.chkPreview, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, pad)

        grid = wx.FlexGridSizer(0, 2, pad, pad)
        grid.AddGrowableCol(1, 1)

        # Testo
        grid.Add(wx.StaticText(self, label=_("Text:")),
                 0, wx.ALIGN_CENTER_VERTICAL)
        self.txtText = wx.TextCtrl(self, value=str(self._cfg['text']),
                                   size=(220, -1))
        grid.Add(self.txtText, 1, wx.EXPAND)

        # Opacita'
        grid.Add(wx.StaticText(self, label=_("Opacity (%):")),
                 0, wx.ALIGN_CENTER_VERTICAL)
        self.spinOpacity = wx.SpinCtrl(self, min=2, max=100,
                                       initial=int(self._cfg['opacity']))
        grid.Add(self.spinOpacity, 0)

        # Angolo
        grid.Add(wx.StaticText(self, label=_("Angle (\u00b0):")),
                 0, wx.ALIGN_CENTER_VERTICAL)
        self.spinAngle = wx.SpinCtrl(self, min=-90, max=90,
                                     initial=int(self._cfg['angle']))
        grid.Add(self.spinAngle, 0)

        # Dimensione
        grid.Add(wx.StaticText(self, label=_("Size (%):")),
                 0, wx.ALIGN_CENTER_VERTICAL)
        self.spinSize = wx.SpinCtrl(self, min=20, max=300,
                                    initial=int(self._cfg['sizePct']))
        grid.Add(self.spinSize, 0)

        # Colore
        grid.Add(wx.StaticText(self, label=_("Colour:")),
                 0, wx.ALIGN_CENTER_VERTICAL)
        self.colourPicker = wx.ColourPickerCtrl(
            self, colour=wx.Colour(self._cfg['colourHex']))
        grid.Add(self.colourPicker, 0)

        main.Add(grid, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, pad)

        # Mosaico
        self.chkTile = wx.CheckBox(self, label=_("Tile (repeat over the page)"))
        self.chkTile.SetValue(bool(self._cfg['tile']))
        main.Add(self.chkTile, 0, wx.ALL, pad)

        # Nota
        note = wx.StaticText(
            self,
            label=_("The watermark is always applied in print and in exported\n"
                    "files (PNG, SVG, EMF, EPS, PDF). Enable \"Show in Songpress\n"
                    "preview++\" to see it in the editor too. It is drawn behind\n"
                    "the song, so it never covers the text."))
        note.SetForegroundColour(wx.Colour(110, 110, 110))
        main.Add(note, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, pad)

        # Pulsanti
        btns = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        main.Add(btns, 0, wx.EXPAND | wx.ALL, pad)

        self.SetSizerAndFit(main)

        self.chkEnabled.Bind(wx.EVT_CHECKBOX, self._on_toggle)
        self._on_toggle(None)

    def _on_toggle(self, evt):
        on = self.chkEnabled.GetValue()
        for w in (self.chkPreview, self.txtText, self.spinOpacity, self.spinAngle,
                  self.spinSize, self.colourPicker, self.chkTile):
            w.Enable(on)

    def GetConfig(self):
        col = self.colourPicker.GetColour()
        return {
            'enabled':   self.chkEnabled.GetValue(),
            'text':      self.txtText.GetValue(),
            'opacity':   self.spinOpacity.GetValue(),
            'angle':     self.spinAngle.GetValue(),
            'sizePct':   self.spinSize.GetValue(),
            'tile':      self.chkTile.GetValue(),
            'colourHex': '#%02X%02X%02X' % (col.Red(), col.Green(), col.Blue()),
            'showInPreview': self.chkPreview.GetValue(),
        }
