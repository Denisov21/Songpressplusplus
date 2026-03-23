###############################################################
# Name:             PreviewCanvas.py
# Purpose:     Window containing preview
# Author:         Luca Allulli (webmaster@roma21.it)
# Modified by:  Denisov21
# Created:     2009-02-21
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
#               Modifications copyright Denisov21
# License:     GNU GPL v2
###############################################################

import platform

import wx
import wx.adv

from .Renderer import *


_ = wx.GetTranslation


class PreviewCanvas(object):
    def __init__(self, parent, sf, notations, sd=SongDecorator(), embedded=False):
        object.__init__(self)
        self.main_panel = wx.Window(parent)
        bSizer = wx.BoxSizer(wx.VERTICAL)
        parent = self.main_panel
        if not embedded:
            self.link = wx.adv.HyperlinkCtrl(parent, 0, _("Copy formatted song to clipboard"), '')
            tt = wx.ToolTip(_("Copy formatted song to clipboard, so that it can be pasted in any program and printed"))
            self.link.SetToolTip(tt)
            bSizer.Add(self.link, 0, wx.EXPAND)
        self.panel = wx.ScrolledWindow(parent, style=wx.BORDER_DOUBLE)
        self.panel.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.pixedScrolled = 10
        self.panel.SetScrollbars(self.pixedScrolled, self.pixedScrolled, 0, 0)
        self.panel.Bind(wx.EVT_PAINT, self.OnPaint, self.panel)
        self.panel.SetBackgroundColour(wx.WHITE)
        self.text = ""
        bSizer.Add(self.panel, 1, wx.EXPAND)
        #SongFormat
        self.renderer = Renderer(sf, sd, notations)
        self.main_panel.SetSizer(bSizer)
        self.main_panel.Layout()
        # Flags per le linee di interruzione (persistenti anche al cambio decorator)
        self._showPageBreakLines = True
        self._showColumnBreakLines = True


    def OnPaint(self, e):
        #print("OnPaint")
        dc = wx.AutoBufferedPaintDC(self.panel)
        self.panel.PrepareDC(dc)
        dc.SetBackground(wx.WHITE_BRUSH)
        dc.Clear()
        w, h = self.renderer.Render(self.text, dc)
        self.panel.SetVirtualSize(wx.Size(int(w), int(h)))
        

    def Refresh(self, text):
        self.text = text
        # Abilita automaticamente il layout a 2 colonne se il testo contiene {column_break}
        import re
        has_col_break = bool(re.search(r'\{\s*(?:column_break|colb)\s*\}', text, re.IGNORECASE))
        self.renderer.columns = 2 if has_col_break else 1
        self.renderer.columnHeight = 0
        # Riapplica sempre i flag al decorator corrente (sopravvive a SetDecorator)
        self.renderer.sd.showPageBreakLines = self._showPageBreakLines
        self.renderer.sd.showColumnBreakLines = self._showColumnBreakLines
        self.panel.Refresh()

    def SetColumns(self, columns):
        """Imposta il numero di colonne per il layout dell'anteprima."""
        self.renderer.columns = columns
        self.renderer.columnHeight = 0

    def SetDecorator(self, sd):
        self.renderer.SetDecorator(sd)
        # Riapplica i flag al nuovo decorator
        sd.showPageBreakLines = self._showPageBreakLines
        sd.showColumnBreakLines = self._showColumnBreakLines

    def SetLineWidths(self, titleLineWidth, verseBoxWidth):
        self.renderer.sd.titleLineWidth = titleLineWidth
        self.renderer.sd.verseBoxWidth = verseBoxWidth

    def SetChordsBelow(self, below):
        self.renderer.SetChordsBelow(below)

    def SetShowPageBreakLines(self, show):
        """Mostra o nasconde la linea blu di interruzione di pagina nell'anteprima."""
        self._showPageBreakLines = show
        self.renderer.sd.showPageBreakLines = show

    def SetShowColumnBreakLines(self, show):
        """Mostra o nasconde la linea blu di interruzione di colonna nell'anteprima."""
        self._showColumnBreakLines = show
        self.renderer.sd.showColumnBreakLines = show

    def SetTempoDisplay(self, tempoDisplay):
        self.renderer.tempoDisplay = tempoDisplay

    def SetTempoIconSize(self, size):
        """Imposta la dimensione in pixel delle icone {tempo_*} (16, 24 o 32)."""
        self.renderer.tempoIconSize = size

    def SetTimeDisplay(self, show):
        self.renderer.timeDisplay = show

    def SetKeyDisplay(self, show):
        self.renderer.keyDisplay = show
