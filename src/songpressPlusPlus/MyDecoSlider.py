###############################################################
# Name:             MyDecoSlider.py
# Purpose:     Slider with a decorated range indicator
# Author:         Luca Allulli (webmaster@roma21.it)
# Modified by:  Denis
# Created:     2010-06-02
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
#               Modifications copyright Denis
# License:     GNU GPL v2
##############################################################

import wx

from .DecoSlider import *

_ = wx.GetTranslation


# Colori della barra (modificabili).
# Definiti come tuple RGB per evitare la creazione di wx.Colour prima che
# wx.App esista (causa crash su macOS e certi Linux).
# Usare _c() per ottenere il wx.Colour corrispondente al momento del disegno.
_BAR_COLOUR_FULL_RGB  = (41, 128, 185)    # blu pieno (valore alto)
_BAR_COLOUR_EMPTY_RGB = (200, 220, 240)   # azzurro chiaro (valore basso / sfondo barra)
_BAR_COLOUR_BG_RGB    = (230, 235, 240)   # sfondo pannello
_TICK_COLOUR_RGB      = (150, 170, 190)   # colore dei segni di graduazione
_LABEL_COLOUR_RGB     = (120, 140, 160)   # colore etichette Facile/Difficile

def _c(rgb):
    """Restituisce un wx.Colour dalla tripla RGB. Chiamato solo a runtime."""
    return wx.Colour(*rgb)

# Alias pubblici per compatibilità con codice esterno che modifica BAR_COLOUR_FULL
# (es. MyPreferencesDialog._apply_deco_bar_colour). Vengono letti come wx.Colour
# tramite _c() internamente, ma possono essere sovrascritti con wx.Colour direttamente.
BAR_COLOUR_FULL  = None   # inizializzato a runtime da _get_bar_colour_full()
BAR_COLOUR_EMPTY = None
BAR_COLOUR_BG    = None
TICK_COLOUR      = None
LABEL_COLOUR     = None

def _ensure_colours():
    """Inizializza i wx.Colour globali la prima volta che servono (dopo wx.App)."""
    global BAR_COLOUR_FULL, BAR_COLOUR_EMPTY, BAR_COLOUR_BG, TICK_COLOUR, LABEL_COLOUR
    if BAR_COLOUR_FULL is None:
        BAR_COLOUR_FULL  = _c(_BAR_COLOUR_FULL_RGB)
        BAR_COLOUR_EMPTY = _c(_BAR_COLOUR_EMPTY_RGB)
        BAR_COLOUR_BG    = _c(_BAR_COLOUR_BG_RGB)
        TICK_COLOUR      = _c(_TICK_COLOUR_RGB)
        LABEL_COLOUR     = _c(_LABEL_COLOUR_RGB)

BAR_HEIGHT       = 8    # px – altezza della barra
BAR_RADIUS       = 4    # px – arrotondamento angoli
LABEL_FONT_SIZE  = 8    # pt
TICK_HEIGHT      = 4    # px – altezza dei tick


class MyDecoSlider(DecoSlider):
    def __init__(self, parent):
        DecoSlider.__init__(self, parent)
        _ensure_colours()
        # Altezza minima aumentata per ospitare le etichette Easy/Difficult
        self.panel.SetMinSize(wx.Size(-1, 36))
        # Adattiamo il colore di sfondo del panel al nuovo stile
        self.panel.SetBackgroundColour(BAR_COLOUR_BG)
        # Aggiorna il pannello ad ogni movimento del cursore
        self.slider.Bind(wx.EVT_SLIDER, self.OnSliderChanged)

    def OnSliderChanged(self, event):
        self.panel.Refresh()
        event.Skip()

    def OnPaint(self, event):
        _ensure_colours()
        dc = wx.PaintDC(self.panel)
        w, h = dc.GetSize()

        # --- sfondo ---
        dc.SetBackground(wx.Brush(BAR_COLOUR_BG, wx.SOLID))
        dc.Clear()

        # --- etichette tradotte ---
        lbl_easy = _("Easy")
        lbl_hard = _("Difficult")
        lbl_font = wx.Font(LABEL_FONT_SIZE, wx.FONTFAMILY_DEFAULT,
                           wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        dc.SetFont(lbl_font)
        dc.SetTextForeground(LABEL_COLOUR)
        easy_w, lbl_h = dc.GetTextExtent(lbl_easy)
        hard_w, _lh   = dc.GetTextExtent(lbl_hard)

        # --- geometria: barra sopra, etichette sotto ---
        margin     = 8
        bar_w      = max(w - 2 * margin, 1)
        bar_area_h = h - lbl_h - 2
        bar_y      = max((bar_area_h - BAR_HEIGHT) // 2, 0)
        lbl_y      = bar_area_h + 2

        # --- parametri slider ---
        val   = self.slider.GetValue()
        mn    = self.slider.GetMin()
        mx    = self.slider.GetMax()
        ratio = (val - mn) / max(mx - mn, 1)

        # Usiamo GraphicsContext per avere angoli arrotondati nativi
        gc = wx.GraphicsContext.Create(dc)
        if gc is None:
            self._paint_fallback(dc, ratio, margin, bar_w, bar_y)
            dc.DrawText(lbl_easy, margin, lbl_y)
            dc.DrawText(lbl_hard, w - margin - hard_w, lbl_y)
            return

        # --- barra di sfondo (vuota) ---
        gc.SetBrush(gc.CreateBrush(wx.Brush(BAR_COLOUR_EMPTY, wx.SOLID)))
        gc.SetPen(wx.NullPen)
        gc.DrawRoundedRectangle(margin, bar_y, bar_w, BAR_HEIGHT, BAR_RADIUS)

        # --- barra riempita (valore corrente) ---
        filled_w = max(int(bar_w * ratio), BAR_RADIUS * 2 if ratio > 0 else 0)
        if filled_w > 0:
            gc.SetBrush(gc.CreateBrush(wx.Brush(BAR_COLOUR_FULL, wx.SOLID)))
            gc.DrawRoundedRectangle(margin, bar_y, filled_w, BAR_HEIGHT, BAR_RADIUS)

        # --- tick marks (uno per ogni step) ---
        steps = mx - mn
        if steps > 1:
            pen = wx.Pen(TICK_COLOUR, 1, wx.PENSTYLE_SOLID)
            gc.SetPen(pen)
            tick_y_top = bar_y + BAR_HEIGHT + 2
            tick_y_bot = tick_y_top + TICK_HEIGHT
            for i in range(steps + 1):
                tx = margin + int(bar_w * i / steps)
                gc.StrokeLine(tx, tick_y_top, tx, tick_y_bot)

        # --- etichette (disegnate con dc, non gc) ---
        dc.DrawText(lbl_easy, margin, lbl_y)
        dc.DrawText(lbl_hard, w - margin - hard_w, lbl_y)

    def _paint_fallback(self, dc, ratio, margin, bar_w, bar_y):
        """Disegno semplificato senza GraphicsContext (sistemi molto datati)."""
        dc.SetPen(wx.NullPen)
        dc.SetBrush(wx.Brush(BAR_COLOUR_EMPTY, wx.SOLID))
        dc.DrawRectangle(margin, bar_y, bar_w, BAR_HEIGHT)
        filled_w = max(int(bar_w * ratio), 0)
        if filled_w > 0:
            dc.SetBrush(wx.Brush(BAR_COLOUR_FULL, wx.SOLID))
            dc.DrawRectangle(margin, bar_y, filled_w, BAR_HEIGHT)

    def OnSize(self, event):
        self.panel.Refresh()
        event.Skip()
