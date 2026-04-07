###############################################################
# Name:             StandardVerseNumbers.py
# Purpose:     Decorator that adds verse numbering
# Author:         Luca Allulli (webmaster@roma21.it)
# Modified by:  Denisov21
# Created:     2009-03-14
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
# Copyright: Modifications © 2026 Denisov21
# License:     GNU GPL v2
##############################################################

from ..SongDecorator import *
from ..SongFormat import *
import wx

class Format(FontFormat):
    def __init__(self, sf, chorusLabel):
        FontFormat.__init__(self)
        self.face = sf.face
        self.size = sf.size
        self.bold = sf.bold
        self.italic = sf.italic
        self.underline = sf.underline
        self.leftMargin = 0.5
        self.rightMargin = 0.5
        self.leftPadding = 0.25
        self.rightPadding = 0.25
        self.topPadding = 0.1
        self.bottomPadding = 0.1
        self.chorus = FontFormat()
        self.chorus.face = sf.chorus.face
        self.chorus.size = sf.chorus.size
        self.chorus.bold = sf.chorus.bold
        self.chorus.italic = sf.chorus.italic
        self.chorus.underline = sf.chorus.underline
        self.chorus.label = chorusLabel

    def SetChorusLabel(self, label):
        self.chorus.label = label

    def GetChorusLabel(self):
        return self.chorus.label


class Decorator(SongDecorator):
    def __init__(self, format):
        SongDecorator.__init__(self)
        self.format = format
        self.drawLabels = True

    wxBlack = wx.Colour(0, 0, 0)
    wxWhite = wx.Colour(255, 255, 255)
    wxGrey = wx.Colour(200, 200, 200)

    def SetMarginBlock(self, block):
        font = block.format.wxFont
        self.dc.SetFont(font)
        baseWidth, baseHeight = self.dc.GetTextExtent("0")
        if block.type == block.verse:
            # Nessun margine per blocchi che contengono solo commenti {c:}
            all_texts = [t for line in block.boxes for t in line.boxes]
            if all_texts and all(t.type == SongText.comment for t in all_texts):
                block.SetMargin(0, 0, 0, 0)
                return
            text = block.label if block.label is not None else ''
            text_spacer = text if text != '' else str(self.s.labelCount)
            w, h = self.dc.GetTextExtent(text_spacer)
            w += baseWidth * (
                self.format.leftMargin + self.format.leftPadding + self.format.rightMargin + self.format.rightPadding
            )
        elif block.type == block.title:
            w = 0
        else:
            if block.label is not None:
                text = block.label
            else:
                text = self.format.chorus.label
            w, h = self.dc.GetTextExtent(text)
            w += baseWidth * (
                self.format.leftMargin + self.format.leftPadding + self.format.rightMargin + self.format.rightPadding
            )
        block.SetMargin(0, 0, 0, w)

    def PreDrawBlock(self, block, bx, by):
        # Disegna solo la linea di interruzione pagina dal parent, NON il rettangolo label
        if getattr(block, 'pageBreakBefore', False):
            song_w = self.s.GetTotalWidth()
            x1 = int(self.s.marginLeft)
            x2 = int(self.s.marginLeft + max(song_w - self.s.marginLeft, 40))
            y  = max(0, int(by - 6))
            pen = wx.Pen(wx.Colour(100, 100, 220), 1, wx.PENSTYLE_SHORT_DASH)
            self.dc.SetPen(pen)
            self.dc.DrawLine(x1, y, x2, y)
            self.dc.SetFont(wx.Font(7, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC,
                                    wx.FONTWEIGHT_NORMAL, False, "Arial"))
            self.dc.SetTextForeground(wx.Colour(100, 100, 220))
            label_txt = "———  interruzione di pagina  ———"
            lw, lh = self.dc.GetTextExtent(label_txt)
            tx = int(x1 + (x2 - x1 - lw) / 2)
            ty = max(0, int(y - lh))
            self.dc.DrawText(label_txt, tx, ty)
            self.dc.SetTextForeground(wx.BLACK)

        if block.type != block.title and len(block.boxes) > 0:
            # Non mostrare numero se il blocco contiene solo commenti {c:}
            if block.type == block.verse:
                all_texts = [t for line in block.boxes for t in line.boxes]
                if all_texts and all(t.type == SongText.comment for t in all_texts):
                    return
            font = block.format.wxFont
            self.dc.SetFont(font)
            baseWidth, baseHeight = self.dc.GetTextExtent("0")
            if block.type == block.verse:
                background = self.wxGrey
                foreground = self.wxBlack
                if block.label is not None:
                    text = block.label
                    text_spacer = text
                    if text == '':
                        text_spacer = str(self.s.labelCount)
                else:
                    text = str(block.verseLabelNumber)
                    text_spacer = str(self.s.labelCount)
                w, h = self.dc.GetTextExtent(text_spacer)
            else:
                background = self.wxBlack
                foreground = self.wxWhite
                if block.label is not None:
                    text = block.label
                else:
                    text = self.format.chorus.label
                w, h = self.dc.GetTextExtent(text)
            if text != '':
                realW, realH = self.dc.GetTextExtent(text)
                rx = bx + self.format.leftMargin * baseWidth
                tx = (rx
                    + baseWidth * self.format.leftPadding
                    + 0.5 * (w - realW))
                ty = by + block.boxes[0].textBaseline + block.marginTop - h
                ry = ty - self.format.topPadding * baseHeight
                rw = int(w + baseWidth * (self.format.leftPadding + self.format.rightPadding))
                rh = int(h + baseHeight * (self.format.topPadding + self.format.bottomPadding))
                # Step 1: fill background
                self.dc.SetBrush(wx.Brush(background, wx.SOLID))
                self.dc.SetPen(wx.TRANSPARENT_PEN)
                self.dc.DrawRectangle(int(rx), int(ry), rw, rh)
                # Step 2: border con spessore configurabile
                pen_w = max(1, round(self.verseBoxWidth / self.pen_scale))
                self.dc.SetPen(wx.Pen(foreground, pen_w))
                self.dc.SetBrush(wx.TRANSPARENT_BRUSH)
                self.dc.DrawRectangle(int(rx), int(ry), rw, rh)
                # Step 3: testo
                self.dc.SetTextForeground(foreground)
                self.dc.SetBackgroundMode(wx.TRANSPARENT)
                self.dc.DrawText(text, int(tx), int(ty))
                self.dc.SetTextForeground(self.wxBlack)
