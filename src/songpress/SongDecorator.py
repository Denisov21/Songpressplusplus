###############################################################
# Name:             SongDecorator.py
# Purpose:     Base (and default) handlers for verse and chorus
# Author:         Luca Allulli (webmaster@roma21.it)
# Created:     2009-02-21
# Modified by:  Denisov21
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
#               Modifications copyright Denisov21
# License:     GNU GPL v2
##############################################################

from .SongFormat import *
from .SongBoxes import *
from .KlavierRenderer import draw_klavier_section
from .GuitarDiagramRenderer import draw_guitar_diagram_section
from .Globals import glb as _glb


class SongDecorator(object):
    def __init__(self):
        object.__init__(self)
        self.dc = None
        # Current y
        self.y = 0
        self.dc = None
        self.firstBlockOffsetY = 0
        self.lastBlockOffsetY = 0
        # SongBox
        self.s = None
        # Scale factor to compensate SetUserScale on DC (pen widths are scaled too)
        self.pen_scale = 1.0
        # Configurable line widths (logical pixels, compensated for DC scale)
        self.titleLineWidth = 4
        self.verseBoxWidth = 1
        # Whether to draw label rectangles (False when labelVerses is off)
        self.drawLabels = False
        # Whether to draw piano keyboard diagrams at end of song
        self.showKlavier = False
        # Whether to draw guitar chord diagrams at end of song
        self.showGuitarDiagrams = False
        # Notation object for chord parsing in KlavierRenderer
        self.notation = None
        # When True, suppress preview-only decorations (page/column break markers)
        self.exportMode = False
        # Granular control: show/hide page break and column break lines independently
        self.showPageBreakLines = True
        self.showColumnBreakLines = True
        # Colour for highlighted keys in klavier diagrams (wx.Colour or None = default red)
        self.klavierHighlightColor = None
        
    def SetMarginText(self, text):
        # Modify text margins
        pass
        
    def SetMarginChord(self, chord):
        # Modify chord margins
        pass
        
    def SetMarginLine(self, line):
        # Modify line margins
        pass

    def SetMarginBlock(self, block):
        # Modify line margins
        pass

    def SetMarginSong(self, song):
        # Modify line margins
        pass
        
    def LayoutComposeLine(self, line):
        # Pass 1: determine size of text
        chordMaxH = 0
        chordMaxTH = 0
        textMaxH = 0
        textMaxTH = 0
        chordsOnly = True
        hasChords = False
        for t in line.boxes:
            self.dc.SetFont(t.font)
            text = t.text
            t.w, t.h = self.dc.GetTextExtent(text)
            if getattr(t, 'is_time_sig', False):
                # Per la frazione musicale: larghezza = max(num, den), altezza = 2 * cifra
                parts = text.split('/')
                if len(parts) == 2:
                    nw, nh = self.dc.GetTextExtent(parts[0].strip())
                    dw, dh = self.dc.GetTextExtent(parts[1].strip())
                    t.w = max(nw, dw)
                    t.h = nh + dh
            if t.type == SongText.chord:
                hasChords = True
                self.SetMarginChord(t)
                chordMaxH = max(chordMaxH, t.h)
                chordMaxTH = max(chordMaxTH, t.GetTotalHeight())
                t.w += self.dc.GetTextExtent(" ")[0] / 2
            else:
                if text.strip() != '':
                    chordsOnly = False
                self.SetMarginText(t)
                textMaxH = max(textMaxH, t.h)
                textMaxTH = max(textMaxTH, t.GetTotalHeight())

        chordsBelow = self.s.chordsBelow

        if chordsOnly and hasChords:
            textMaxH = 0
            textMaxTH = 0
            line.textBaseline = chordMaxTH
            line.chordBaseline = chordMaxTH
        elif chordsOnly:  # Block without text or chords
            w, h = self.dc.GetTextExtent(' ')
            textMaxH = h
            textMaxTH = h
            line.textBaseline = h
            line.chordBaseline = chordMaxTH
        else:
            chord_top = line.parent.format.chordTopSpacing
            if chordsBelow:
                # Testo sopra, accordi sotto
                line.textBaseline = textMaxTH
                line.chordBaseline = (
                    textMaxTH
                    + textMaxH * (line.parent.format.textSpacing - 1)
                    + chord_top
                    + chordMaxTH
                )
            else:
                # Accordi sopra (comportamento originale)
                line.textBaseline = chord_top + chordMaxTH + chordMaxH * (line.parent.format.chordSpacing - 1) + textMaxTH
                line.chordBaseline = chordMaxTH + chord_top

        if chordsBelow and not (chordsOnly and hasChords) and not chordsOnly:
            line.h = (
                line.textBaseline
                + textMaxH * (line.parent.format.textSpacing - 1)
                + chord_top
                + chordMaxH * (line.parent.format.chordSpacing - 1)
                + chordMaxH
                + line.parent.format.lineSpacing
            )
        else:
            line.h = line.textBaseline + textMaxH * (line.parent.format.textSpacing - 1) + line.parent.format.lineSpacing

        # Pass 2: set layout
        x = 0
        chordX = 0
        for t in line.boxes:
            self.dc.SetFont(t.font)
            if t.type == SongText.chord:
                t.x = max(x, chordX)
                x = t.x
                chordX = x + t.GetTotalWidth()
                t.y = line.chordBaseline - t.GetTotalHeight()
            else:
                t.x = x
                x_chord = max(x, chordX)
                x = t.x + t.GetTotalWidth()
                t.y = line.textBaseline - t.GetTotalHeight()
                if t.text.strip() == '':
                    chordX = x_chord + t.GetTotalWidth()
            line.RelocateBox(t)
        self.SetMarginLine(line)
        
    def LayoutComposeBlock(self, block):
        y = 0
        for l in block.boxes:
            l.y = y
            y += l.GetTotalHeight()
            block.RelocateBox(l)
        self.SetMarginBlock(block)

    def LayoutComposeSong(self, song):
        columns = getattr(song, 'columns', 1)
        col_h_limit = getattr(song, 'columnHeight', 0)  # 0 = illimitata

        if columns <= 1:
            # Layout classico a colonna singola
            y = 0
            self.dc.SetFont(song.format.wxFont)
            for b in song.boxes:
                b.y = y
                b.x = 0
                y += b.GetTotalHeight() + b.GetLastLineTextHeight() * song.format.blockSpacing
                song.RelocateBox(b)
            self.SetMarginSong(song)
            return

        # --- Layout multi-colonna ---
        # Calcola larghezza massima dei blocchi per determinare la larghezza di colonna
        self.dc.SetFont(song.format.wxFont)
        max_block_w = max((b.GetTotalWidth() for b in song.boxes), default=0)
        gap = max(20, max_block_w // 10)  # spaziatura tra colonne

        col_idx = 0
        col_y = 0
        col_x = 0
        # Ricava la larghezza colonna dal DC se disponibile (per il clip corretto)
        # In stampa viene sovrascritta; nell'anteprima usa la larghezza naturale dei blocchi
        col_w = max_block_w

        for b in song.boxes:
            # {column_break} forza salto alla colonna successiva
            if getattr(b, 'columnBreakBefore', False) and col_idx < columns - 1:
                col_idx += 1
                col_x = col_idx * (col_w + gap)
                col_y = 0

            # Se abbiamo un'altezza limite e il blocco non ci sta, vai alla colonna successiva
            if col_h_limit > 0 and col_y > 0 and col_idx < columns - 1:
                if col_y + b.GetTotalHeight() > col_h_limit:
                    col_idx += 1
                    col_x = col_idx * (col_w + gap)
                    col_y = 0

            b.x = col_x
            b.y = col_y
            col_y += b.GetTotalHeight() + b.GetLastLineTextHeight() * song.format.blockSpacing
            song.RelocateBox(b)

        # Memorizza info colonne nel song per DrawBoxes
        song._col_w = col_w
        song._col_gap = gap
        song._num_cols_used = col_idx + 1
        self.SetMarginSong(song)

    def LayoutComposeImage(self, imgbox):
        """Calcola w e h finali di una SongImageBox in base alle sue opzioni."""
        if not imgbox.path:
            imgbox.w = 0
            imgbox.h = 0
            return
        try:
            img = wx.Image(imgbox.path)
            if not img.IsOk():
                imgbox.w = 0
                imgbox.h = 0
                return
            orig_w = img.GetWidth()
            orig_h = img.GetHeight()
        except Exception:
            imgbox.w = 0
            imgbox.h = 0
            return

        # Calcola dimensioni finali rispettando width/height/scale
        req_w = imgbox.img_width   # 0 = auto
        req_h = imgbox.img_height  # 0 = auto
        scale = imgbox.scale if imgbox.scale > 0 else 1.0

        if req_w > 0 and req_h > 0:
            final_w, final_h = int(req_w), int(req_h)
        elif req_w > 0:
            final_w = int(req_w)
            final_h = int(orig_h * final_w / orig_w) if orig_w else 0
        elif req_h > 0:
            final_h = int(req_h)
            final_w = int(orig_w * final_h / orig_h) if orig_h else 0
        else:
            final_w = int(orig_w * scale)
            final_h = int(orig_h * scale)

        imgbox.w = max(1, final_w)
        imgbox.h = max(1, final_h)
        # Salva le dimensioni calcolate per DrawBoxes
        imgbox._final_w = imgbox.w
        imgbox._final_h = imgbox.h

    def LayoutCompose(self):
        # Postorder layout composing
        for block in self.s.boxes:
            if isinstance(block, SongImageBox):
                self.LayoutComposeImage(block)
                continue
            for line in block.boxes:
                self.LayoutComposeLine(line)
        for block in self.s.boxes:
            if isinstance(block, SongImageBox):
                continue
            self.LayoutComposeBlock(block)
        self.LayoutComposeSong(self.s)
        
    def LayoutMoveBlock(self, block):
        # Move block within song
        pass
        
    def LayoutMoveLine(self, line):
        # Move line within block
        # If we need to, we can even move text and chords inside this line
        pass

    def LayoutMove(self):
        # Now that sizes are set, we can move elements inside each box if we need to
        for block in self.s.boxes:
            # Move block within song
            self.LayoutMoveBlock(block)
            for line in block.boxes:
                # Move line within block
                # If we need to, we can even move text and chords inside this line
                self.LayoutMoveLine(line)
                
    def PreDrawSong(self, song):
        pass
        
    def PreDrawBlock(self, block, bx, by):
        # bx, by: coordinates of top-left corner of drawable area
        # Disegna una linea tratteggiata se c'è un'interruzione di pagina prima di questo blocco
        if getattr(block, 'pageBreakBefore', False) and not self.exportMode and self.showPageBreakLines:
            # bx/by sono già le coordinate corrette nel DC (firstBlockOffsetY già sottratto
            # da DrawBoxes prima di chiamare PreDrawBlock)
            song_w = self.s.GetTotalWidth()
            x1 = int(self.s.marginLeft)
            x2 = int(self.s.marginLeft + max(song_w - self.s.marginLeft, 40))
            y  = max(0, int(by - 6))
            pen = wx.Pen(wx.Colour(100, 100, 220), 1, wx.PENSTYLE_SHORT_DASH)
            self.dc.SetPen(pen)
            self.dc.DrawLine(x1, y, x2, y)
            # Etichetta testuale centrata sulla linea
            self.dc.SetFont(wx.Font(7, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC,
                                    wx.FONTWEIGHT_NORMAL, False, "Arial"))
            self.dc.SetTextForeground(wx.Colour(100, 100, 220))
            label_txt = "———  interruzione di pagina  ———"
            lw, lh = self.dc.GetTextExtent(label_txt)
            tx = int(x1 + (x2 - x1 - lw) / 2)
            ty = max(0, int(y - lh))
            self.dc.DrawText(label_txt, tx, ty)
            self.dc.SetTextForeground(wx.BLACK)
        # Disegna rettangolo con linea sottile attorno all'etichetta della strofa
        if self.drawLabels and block.label is not None:
            self.dc.SetFont(block.format.wxFont)
            lw, lh = self.dc.GetTextExtent(block.label)
            padding = 3
            x = int(bx + block.marginLeft) - padding
            y = int(by + block.marginTop) - padding
            w = lw + padding * 2
            h = lh + padding * 2
            self.dc.SetPen(wx.Pen(block.format.color, max(1, int(self.verseBoxWidth / self.pen_scale)))) #stabilisce spessore bordo versetti
            self.dc.SetBrush(wx.TRANSPARENT_BRUSH)
            self.dc.DrawRectangle(x, y, w, h)
        
    def PreDrawLine(self, line, lx, ly):
        # lx, ly: coordinates of top-left corner of drawable area
        pass
        
    def PreDrawText(self, text, tx, ty):
        # tx, ty: coordinates of top-left corner of drawable area
        pass
        
    def DrawText(self, text, tx, ty):
        # tx, ty: coordinates of top-left corner of drawable area
        self.dc.SetFont(text.font)
        self.dc.SetTextForeground(text.color)
        if getattr(text, 'is_tempo_note', False):
            try:
                img = wx.Image(_glb.AddPath('img/tempo_note.png'))
                orig_h = img.GetHeight()
                orig_w = img.GetWidth()
                _icon_size = getattr(self, 'tempoIconSize', None)
                new_h = int(_icon_size) if _icon_size else int(text.h)
                new_w = int(orig_w * new_h / orig_h)
                img = img.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
                # Precomponi l'alpha su sfondo bianco: il PrinterDC su Windows
                # non gestisce la trasparenza nativa della PNG (appare come nero).
                if img.HasAlpha():
                    import array
                    a = array.array('B', img.GetAlphaBuffer())
                    rs = array.array('B', img.GetDataBuffer())
                    rb = bytearray(new_w * new_h * 3)
                    for i in range(new_w * new_h):
                        av = a[i] / 255.0
                        for c in range(3):
                            rb[i * 3 + c] = int(rs[i * 3 + c] * av + 255 * (1 - av))
                    white_bg = wx.Image(new_w, new_h)
                    white_bg.SetData(bytes(rb))
                    bmp = wx.Bitmap(white_bg)
                else:
                    bmp = wx.Bitmap(img)
                by = int(ty + text.marginTop)
                bx = int(tx + text.marginLeft)
                self.dc.DrawBitmap(bmp, bx, by, True)
                self.dc.DrawText(text.text, bx + new_w + 2, int(ty + text.marginTop))
                return
            except Exception:
                pass
        # --- Helper interno per disegnare icone nota con precomposizione alpha ---
        def _draw_tempo_icon(img_name):
            try:
                img = wx.Image(_glb.AddPath(img_name))
                orig_h = img.GetHeight()
                orig_w = img.GetWidth()
                _icon_size = getattr(self, 'tempoIconSize', None)
                new_h = int(_icon_size) if _icon_size else int(text.h)
                new_w = int(orig_w * new_h / orig_h)
                img = img.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
                if img.HasAlpha():
                    import array
                    a = array.array('B', img.GetAlphaBuffer())
                    rs = array.array('B', img.GetDataBuffer())
                    rb = bytearray(new_w * new_h * 3)
                    for i in range(new_w * new_h):
                        av = a[i] / 255.0
                        for c in range(3):
                            rb[i * 3 + c] = int(rs[i * 3 + c] * av + 255 * (1 - av))
                    white_bg = wx.Image(new_w, new_h)
                    white_bg.SetData(bytes(rb))
                    bmp = wx.Bitmap(white_bg)
                else:
                    bmp = wx.Bitmap(img)
                by = int(ty + text.marginTop)
                bx = int(tx + text.marginLeft)
                self.dc.DrawBitmap(bmp, bx, by, True)
                self.dc.DrawText(text.text, bx + new_w + 2, int(ty + text.marginTop))
                return True
            except Exception:
                return False
        if getattr(text, 'is_tempo_half_note', False):
            # {tempo_m:} — minima
            if _draw_tempo_icon('img/minima_32x32.png'):
                return
        if getattr(text, 'is_tempo_quarter_note', False):
            # {tempo_s:} — semiminima
            if _draw_tempo_icon('img/semiminima_32x32.png'):
                return
        if getattr(text, 'is_tempo_eighth_note', False):
            # {tempo_c:} — croma
            if _draw_tempo_icon('img/croma_32x32.png'):
                return
        if getattr(text, 'is_tempo_dotted_quarter', False):
            # {tempo_sp:} — semiminima puntata
            if _draw_tempo_icon('img/semiminima_punto_32x32.png'):
                return
        if getattr(text, 'is_tempo_dotted_eighth', False):
            # {tempo_cp:} — croma puntata
            if _draw_tempo_icon('img/croma_punto_32x32.png'):
                return
        if getattr(text, 'is_tempo_metro', False):
            # metronome display
            if _draw_tempo_icon('img/metronome.png'):
                return
        if getattr(text, 'is_time_sig', False):
            try:
                parts = text.text.split('/')
                if len(parts) == 2:
                    num, den = parts[0].strip(), parts[1].strip()
                    bx = int(tx + text.marginLeft)
                    by = int(ty + text.marginTop)
                    total_h = int(text.h)
                    half_h = total_h // 2
                    # Misura larghezza massima tra numeratore e denominatore
                    nw, nh = self.dc.GetTextExtent(num)
                    dw, dh = self.dc.GetTextExtent(den)
                    max_w = max(nw, dw)
                    # Disegna numeratore centrato in alto
                    self.dc.DrawText(num, bx + (max_w - nw) // 2, by)
                    # Linea orizzontale di separazione
                    pen = wx.Pen(text.color, max(1, int(1 / self.pen_scale)))
                    self.dc.SetPen(pen)
                    self.dc.DrawLine(bx, by + half_h, bx + max_w, by + half_h)
                    # Disegna denominatore centrato in basso
                    self.dc.DrawText(den, bx + (max_w - dw) // 2, by + half_h)
                    return
            except Exception:
                pass
        if getattr(text, 'is_italic', False):
            f = text.font
            italic_font = wx.Font(f.GetPointSize(), f.GetFamily(), wx.FONTSTYLE_ITALIC,
                                  f.GetWeight(), f.GetUnderlined(), f.GetFaceName())
            self.dc.SetFont(italic_font)
        self.dc.DrawText(text.text, int(tx + text.marginLeft), int(ty + text.marginTop))
        
    def PostDrawText(self, text, tx, ty):
        # tx, ty: coordinates of top-left corner of drawable area
        if text.type == SongText.title:
            self.dc.SetPen(wx.Pen(text.color, max(1, round(self.titleLineWidth / self.pen_scale)))) #stabilisce spessore linea titolo
            x1 = int(tx + text.marginLeft)
            x2 = int(tx + text.marginLeft + text.w)
            y = int(ty + text.marginTop + text.h)
            self.dc.DrawLine(x1, y, x2, y)
        if getattr(text, 'is_box', False):
            padding = 2
            x = int(tx + text.marginLeft) - padding
            y = int(ty + text.marginTop) - padding
            w = int(text.w) + padding * 2
            h = int(text.h) + padding * 2
            self.dc.SetPen(wx.Pen(text.color, max(1, int(1 / self.pen_scale))))
            self.dc.SetBrush(wx.TRANSPARENT_BRUSH)
            self.dc.DrawRectangle(x, y, w, h)
        
    def PostDrawLine(self, line, lx, ly):
        # lx, ly: coordinates of top-left corner of drawable area
        pass        
        
    def PostDrawBlock(self, block, bx, by):
        # bx, by: coordinates of top-left corner of drawable area
        pass
        
    def PostDrawSong(self, song):
        current_extra_h = 0

        if self.showKlavier:
            klavier_list = getattr(song, 'klavier_list', [])
            if klavier_list:
                start_x = int(song.marginLeft)
                start_y = int(song.marginTop + song.h) + 10
                base_font = song.format.wxFont
                h = draw_klavier_section(
                    self.dc, klavier_list, start_x, start_y,
                    base_font, self.pen_scale, self.notation,
                    self.klavierHighlightColor
                )
                current_extra_h += h + 20

        if self.showGuitarDiagrams:
            define_list = getattr(song, 'define_list', [])
            if define_list:
                start_x = int(song.marginLeft)
                start_y = int(song.marginTop + song.h + current_extra_h) + 10
                base_font = song.format.wxFont
                h = draw_guitar_diagram_section(
                    self.dc, define_list, start_x, start_y,
                    base_font, self.pen_scale,
                    self.klavierHighlightColor
                )
                current_extra_h += h + 20

        if current_extra_h:
            song.h += current_extra_h
        
    def DrawBoxes(self):
        if self.s.drawWholeSong:
            self.PreDrawSong(self.s)
            firstBlock = False
        else:
            firstBlock = True

        # Disegna linee di separazione tra colonne (solo in modalità anteprima intera, non in export)
        if self.s.drawWholeSong and getattr(self.s, 'columns', 1) > 1 and not self.exportMode and self.showColumnBreakLines:
            col_w   = getattr(self.s, '_col_w', 0)
            col_gap = getattr(self.s, '_col_gap', 20)
            n_cols  = getattr(self.s, '_num_cols_used', 1)
            song_h  = self.s.GetTotalHeight()
            for ci in range(1, n_cols):
                sep_x = int(self.s.marginLeft + ci * (col_w + col_gap) - col_gap // 2)
                sep_y1 = int(self.s.marginTop)
                sep_y2 = int(self.s.marginTop + song_h)
                pen = wx.Pen(wx.Colour(100, 100, 220), 1, wx.PENSTYLE_SHORT_DASH)
                self.dc.SetPen(pen)
                self.dc.DrawLine(sep_x, sep_y1, sep_x, sep_y2)
                # Etichetta
                self.dc.SetFont(wx.Font(7, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC,
                                        wx.FONTWEIGHT_NORMAL, False, "Arial"))
                self.dc.SetTextForeground(wx.Colour(100, 100, 220))
                lbl = "———  interruzione di colonna  ———"
                lw, lh = self.dc.GetTextExtent(lbl)
                self.dc.DrawText(lbl, sep_x - lw // 2, sep_y1)
                self.dc.SetTextForeground(wx.BLACK)

        for block in self.s.boxes:
            # --- Gestione SongImageBox ---
            if isinstance(block, SongImageBox):
                if not self.s.drawWholeSong:
                    continue  # le immagini si disegnano solo in modalita' intera
                self._DrawImageBox(block)
                continue

            block: SongBlock
            if block.drawBlock:
                if firstBlock:
                    firstBlock = False
                    self.firstBlockOffsetY = self.s.marginTop + block.y
                bx = self.s.marginLeft + block.x
                by = self.s.marginTop + block.y - self.firstBlockOffsetY
                # Maschera temporaneamente i flag di interruzione se la visualizzazione è disabilitata
                saved_page  = block.__dict__.get('pageBreakBefore', False)
                saved_col   = block.__dict__.get('columnBreakBefore', False)
                if not (self.exportMode is False and self.showPageBreakLines):
                    block.pageBreakBefore = False
                if not (self.exportMode is False and self.showColumnBreakLines):
                    block.columnBreakBefore = False
                self.PreDrawBlock(block, bx, by)
                block.pageBreakBefore   = saved_page
                block.columnBreakBefore = saved_col
                for line in block.boxes:
                    lx = bx + block.marginLeft + line.x
                    ly = by + block.marginTop + line.y
                    self.PreDrawLine(line, lx, ly)
                    for text in line.boxes:
                        tx = lx + line.marginLeft + text.x
                        ty = ly + line.marginTop + text.y
                        self.PreDrawText(text, tx, ty)
                        self.DrawText(text, tx, ty)
                        self.PostDrawText(text, tx, ty)
                self.lastBlockOffsetY = by + block.GetTotalHeight()
                self.PostDrawBlock(block, bx, by)
        if self.s.drawWholeSong:
            self.PostDrawSong(self.s)
        
    def _DrawImageBox(self, imgbox):
        """Disegna una SongImageBox sul DC corrente."""
        if not imgbox.path or not getattr(imgbox, '_final_w', 0) or not getattr(imgbox, '_final_h', 0):
            return
        try:
            img = wx.Image(imgbox.path)
            if not img.IsOk():
                return
            final_w = imgbox._final_w
            final_h = imgbox._final_h
            img = img.Scale(final_w, final_h, wx.IMAGE_QUALITY_HIGH)

            # Precomponi alpha su sfondo bianco (compatibilita' PrinterDC su Windows)
            if img.HasAlpha():
                import array
                a = array.array('B', img.GetAlphaBuffer())
                rs = array.array('B', img.GetDataBuffer())
                rb = bytearray(final_w * final_h * 3)
                for i in range(final_w * final_h):
                    av = a[i] / 255.0
                    for c in range(3):
                        rb[i * 3 + c] = int(rs[i * 3 + c] * av + 255 * (1 - av))
                white_bg = wx.Image(final_w, final_h)
                white_bg.SetData(bytes(rb))
                bmp = wx.Bitmap(white_bg)
            else:
                bmp = wx.Bitmap(img)

            # Calcola x in base ad align e larghezza disponibile
            available_w = self.s.GetTotalWidth() - self.s.marginLeft - self.s.marginRight
            if imgbox.align == 'left':
                bx = int(self.s.marginLeft)
            elif imgbox.align == 'right':
                bx = int(self.s.marginLeft + max(0, available_w - final_w))
            else:  # center
                bx = int(self.s.marginLeft + max(0, (available_w - final_w) // 2))

            by = int(self.s.marginTop + imgbox.y)
            self.dc.DrawBitmap(bmp, bx, by, False)

            # Bordo opzionale
            if imgbox.border > 0:
                pen = wx.Pen(wx.BLACK, max(1, int(imgbox.border / self.pen_scale)))
                self.dc.SetPen(pen)
                self.dc.SetBrush(wx.TRANSPARENT_BRUSH)
                self.dc.DrawRectangle(bx, by, final_w, final_h)
        except Exception:
            pass

    def InitDraw(self):
        pass
        
    def Draw(self, s: SongSong, dc):
        self.s = s
        self.dc = dc
        # Auto-detect DC user scale to compensate pen widths
        sx, sy = dc.GetUserScale()
        self.pen_scale = sx if sx > 0 else 1.0
        self.InitDraw()
        self.LayoutCompose()
        self.LayoutMove()
        self.DrawBoxes()
        self.dc = None
        if self.s.drawWholeSong:
            h = self.s.GetTotalHeight()
        else:
            h = self.lastBlockOffsetY
        # In modalità multi-colonna la larghezza totale comprende tutte le colonne
        if getattr(self.s, 'columns', 1) > 1 and hasattr(self.s, '_col_w'):
            n_cols = getattr(self.s, '_num_cols_used', 1)
            total_w = self.s.marginLeft + n_cols * self.s._col_w + (n_cols - 1) * self.s._col_gap + self.s.marginLeft
        else:
            total_w = self.s.GetTotalWidth()
        return total_w, h
