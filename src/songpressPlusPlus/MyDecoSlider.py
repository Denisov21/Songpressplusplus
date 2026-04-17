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


# Colori della barra (modificabili)
BAR_COLOUR_FULL  = wx.Colour(41, 128, 185)   # blu pieno (valore alto)
BAR_COLOUR_EMPTY = wx.Colour(200, 220, 240)  # azzurro chiaro (valore basso / sfondo barra)
BAR_COLOUR_BG    = wx.Colour(230, 235, 240)  # sfondo pannello
BAR_HEIGHT       = 8    # px – altezza della barra
BAR_RADIUS       = 4    # px – arrotondamento angoli
TICK_COLOUR      = wx.Colour(150, 170, 190)  # colore dei segni di graduazione
TICK_HEIGHT      = 4    # px – altezza dei tick
LABEL_COLOUR     = wx.Colour(120, 140, 160)  # colore etichette Facile/Difficile
LABEL_FONT_SIZE  = 8                          # pt


class MyDecoSlider(DecoSlider):
    def __init__(self, parent):
        DecoSlider.__init__(self, parent)
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
