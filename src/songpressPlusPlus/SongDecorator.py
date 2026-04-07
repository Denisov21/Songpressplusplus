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
from .MusicalSymbolDialog import get_smp_faces as _get_smp_faces


def _has_smp(s: str) -> bool:
    """True se la stringa contiene almeno un carattere SMP (codepoint > U+FFFF).
    I simboli musicali Unicode (U+1D100-U+1D1FF) cadono in questo range e
    non vengono resi da GDI classico: servono GDI+ / GraphicsContext.
    """
    return any(ord(c) > 0xFFFF for c in s)


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
            # GDI restituisce 0x0 per caratteri SMP: rimisura con GDI+ se necessario
            if t.w == 0 and _has_smp(text):
                t.w, t.h = self._GetTextExtentSMP(text)
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
        # ── Blocco grid in modalità table: ridimensiona all'altezza reale ──
        if getattr(block, 'is_grid', False):
            grid_rows = getattr(block, 'grid_rows', [])
            if grid_rows and self.dc is not None:
                self.dc.SetFont(block.format.wxFont)
                _, char_h = self.dc.GetTextExtent('Mg')
                pad_y = 4
                cell_h = char_h + pad_y * 2
                n_rows = len(grid_rows)
                table_h = n_rows * (cell_h + 1)
                if table_h > block.h:
                    block.h = table_h

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

    def LayoutComposeGrid(self, gridbox):
        """Calcola w, h, cell_w, cell_h di un SongGridBox."""
        if not gridbox.rows or gridbox.font is None:
            gridbox.w = 0
            gridbox.h = 0
            return
        # Misura il testo delle celle usando il DC corrente
        old_font = self.dc.GetFont()
        self.dc.SetFont(gridbox.font)
        # Larghezza cella = max del testo più lungo + padding
        _size    = max(1, getattr(gridbox, 'size', 1))
        _sizeDir = getattr(gridbox, 'sizeDir', 'both')
        _sx = _size if _sizeDir in ('both', 'horizontal') else 1.0
        _sy = _size if _sizeDir in ('both', 'vertical')   else 1.0
        pad_x = 8 * _sx   # px padding orizzontale per lato
        pad_y = 4 * _sy   # px padding verticale per lato
        max_text_w = 0
        max_text_h = 0
        for row in gridbox.rows:
            for cell in row:
                tw, th = self.dc.GetTextExtent(cell if cell else ' ')
                max_text_w = max(max_text_w, tw)
                max_text_h = max(max_text_h, th)
        # Misura offset orizzontale e altezza etichetta — stessi parametri di StandardVerseNumbers
        baseW, baseH = self.dc.GetTextExtent("0")
        leftMargin    = 0.5
        leftPadding   = 0.25
        rightPadding  = 0.25
        rightMargin   = 0.5
        topPadding    = 0.1
        bottomPadding = 0.1
        # Offset x del testo della griglia = stessa posizione del testo nei blocchi normali
        # (equivalente a block.marginLeft in SetMarginBlock per i verse)
        text_x_offset = int(baseW * (leftMargin + leftPadding + rightMargin + rightPadding))
        gridbox._text_x_offset = text_x_offset
        label_h = 0
        if gridbox.label:
            _, lh = self.dc.GetTextExtent(gridbox.label)
            label_h = int(lh + baseH * (topPadding + bottomPadding)) + 4  # gap sotto
        gridbox._label_h = label_h
        self.dc.SetFont(old_font)
        cell_w   = int(max_text_w + pad_x * 2)
        cell_h   = int(max_text_h + pad_y * 2)
        spacer_h = cell_h // 2
        col_count = max((len(row) for row in gridbox.rows), default=1)
        row_top    = int(gridbox.chordTopSpacing) if gridbox.chordTopSpacing is not None else 0
        row_bottom = int(gridbox.lineSpacing)     if gridbox.lineSpacing     is not None else 0
        row_h      = cell_h + row_top + row_bottom
        gridbox.cell_w   = cell_w
        gridbox.cell_h   = cell_h
        gridbox.row_h    = row_h
        gridbox.row_top  = row_top
        gridbox.spacer_h = spacer_h
        gridbox.col_count = col_count
        gridbox._pad_x   = int(pad_x)
        gridbox._pad_y   = int(pad_y)
        gridbox._label_h = label_h
        gridbox.w = cell_w * col_count
        # Altezza totale: etichetta + righe normali + spacer per righe vuote
        total_h = label_h
        for row in gridbox.rows:
            total_h += spacer_h if not row else row_h
        gridbox.h = total_h
    def LayoutCompose(self):
        # Postorder layout composing
        for block in self.s.boxes:
            if isinstance(block, SongImageBox):
                self.LayoutComposeImage(block)
                continue
            if isinstance(block, SongGridBox):
                self.LayoutComposeGrid(block)
                continue
            for line in block.boxes:
                self.LayoutComposeLine(line)
        for block in self.s.boxes:
            if isinstance(block, (SongImageBox, SongGridBox)):
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
            if _draw_tempo_icon('img/metronomeWindows.png'):
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
        # Caratteri SMP (U+10000+, es. blocco Musical Symbols U+1D100-U+1D1FF):
        # GDI non fa font-fallback → switcha su GDI+ via GraphicsContext solo per loro.
        if _has_smp(text.text):
            self._DrawTextSMP(text.text, int(tx + text.marginLeft), int(ty + text.marginTop))
        else:
            self.dc.DrawText(text.text, int(tx + text.marginLeft), int(ty + text.marginTop))
        
    # ------------------------------------------------------------------ #
    # Supporto simboli Unicode SMP (U+10000+, es. Musical Symbols)       #
    # GDI non ha font-fallback: per questi caratteri usiamo GDI+ con     #
    # un font che ha copertura SMP (FreeSerif > Segoe UI Symbol).        #
    # ------------------------------------------------------------------ #

    def _smp_gc_font(self, gc, base_font, color):
        """Crea un wx.GraphicsFont con copertura SMP a partire da base_font.
        Itera su tutti i font caricati dalla cartella fonts/ (via get_smp_faces()),
        più il font di sistema come ultimo fallback.
        La dimensione viene scalata per pen_scale (zoom DC) perché GraphicsContext
        non eredita SetUserScale del DC padre.
        """
        # pen_scale = fattore zoom del DC (es. 1.5 con zoom al 150%)
        # Il GC ignora SetUserScale → moltiplichiamo la dimensione del font
        scale = getattr(self, 'pen_scale', 1.0)
        pt = max(1, round(base_font.GetPointSize() * scale))
        # Lista dinamica: tutti i font caricati da fonts/ + font corrente come
        # ultimo fallback (mostra rettangoli per glifi mancanti ma non crasha)
        faces = list(_get_smp_faces()) + [base_font.GetFaceName()]
        for face in faces:
            if not face:
                continue
            candidate = wx.Font(
                pt, wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,
                faceName=face,
            )
            if candidate.IsOk():
                return gc.CreateFont(candidate, color)
        return gc.CreateFont(base_font, color)

    def _GetTextExtentSMP(self, s: str):
        """Misura *s* con GDI+ usando un font con copertura SMP.
        GDI restituisce 0x0 per caratteri SMP → rimisura con GraphicsContext.
        Il risultato viene diviso per pen_scale per tornare in coordinate DC logiche.
        """
        scale = getattr(self, 'pen_scale', 1.0)
        try:
            gc = wx.GraphicsContext.Create(self.dc)
            if gc is None:
                return self.dc.GetTextExtent(s)
            gc.SetFont(self._smp_gc_font(gc, self.dc.GetFont(), self.dc.GetTextForeground()))
            w, h = gc.GetTextExtent(s)
            if w < 1:
                cw, ch = self.dc.GetTextExtent('M')
                # dc.GetTextExtent tiene già conto di pen_scale; niente divisione
                return cw * max(1, len(s)), ch
            # gc misura in pixel fisici (senza scala DC) → dividiamo per scale
            return int(w / scale), int(h / scale)
        except Exception:
            cw, ch = self.dc.GetTextExtent('M')
            return cw * max(1, len(s)), ch

    def _DrawTextSMP(self, s: str, x: int, y: int):
        """Disegna *s* con GDI+ usando un font con copertura SMP (FreeSerif).
        Chiamato solo quando *s* contiene caratteri U+10000+.
        Le coordinate x, y sono in spazio DC (con scala); il GC non eredita
        SetUserScale, quindi le moltiplichiamo per pen_scale prima di passarle al GC.
        """
        scale = getattr(self, 'pen_scale', 1.0)
        try:
            gc = wx.GraphicsContext.Create(self.dc)
            if gc is None:
                self.dc.DrawText(s, x, y)
                return
            gc.SetFont(self._smp_gc_font(gc, self.dc.GetFont(), self.dc.GetTextForeground()))
            # Converti coordinate da spazio DC logico a pixel fisici
            gc.DrawText(s, x * scale, y * scale)
        except Exception:
            self.dc.DrawText(s, x, y)

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
        # ── Tabella griglia accordi (modalità 'table') ────────────────
        if not getattr(block, 'is_grid', False):
            return
        grid_rows = getattr(block, 'grid_rows', [])
        if not grid_rows:
            return
        # Determina larghezza massima cella misurando il testo
        self.dc.SetFont(block.format.wxFont)
        pad_x = 8   # padding orizzontale interno cella (px)
        pad_y = 4   # padding verticale interno cella (px)
        _, char_h = self.dc.GetTextExtent('Mg')
        # Calcola la larghezza massima tra tutte le celle di tutte le righe
        max_cell_w = 0
        for row in grid_rows:
            for cell in row:
                cw, _ = self.dc.GetTextExtent(cell)
                max_cell_w = max(max_cell_w, cw)
        cell_w = max_cell_w + pad_x * 2
        cell_h = char_h + pad_y * 2

        # Colore bordo tabella
        border_pen = wx.Pen(wx.Colour(80, 80, 80), max(1, int(1 / self.pen_scale)))
        fill_brush = wx.Brush(wx.Colour(240, 240, 255))  # sfondo cella: azzurro chiaro
        self.dc.SetBrush(fill_brush)

        # Posizione di partenza: inizio del contenuto del blocco
        start_x = int(bx + block.marginLeft)
        start_y = int(by + block.marginTop)

        # Disegna riga per riga
        for row_idx, row in enumerate(grid_rows):
            row_y = start_y + row_idx * (cell_h + 1)
            for col_idx, cell_text in enumerate(row):
                cx = start_x + col_idx * (cell_w + 1)
                cy = row_y
                # Disegna la cella
                self.dc.SetPen(border_pen)
                self.dc.SetBrush(fill_brush)
                self.dc.DrawRectangle(cx, cy, cell_w, cell_h)
                # Testo centrato nella cella
                tw, _ = self.dc.GetTextExtent(cell_text)
                tx = cx + (cell_w - tw) // 2
                ty = cy + pad_y
                self.dc.SetTextForeground(block.format.color)
                self.dc.DrawText(cell_text, tx, ty)
        
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

            # --- Gestione SongGridBox ---
            if isinstance(block, SongGridBox):
                if not self.s.drawWholeSong:
                    continue
                self._DrawGridBox(block)
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

    def _DrawGridBox(self, gridbox):
        """Disegna un SongGridBox sul DC corrente.

        Modalità:
            'table' -- cella con bordi wx reali (DrawRectangle)
            'pipe'  -- testo con separatori | allineati
            'plain' -- testo spaziato senza separatori
        """
        if not gridbox.rows or gridbox.w == 0:
            return

        # bx del gridbox allineato al testo dei blocchi normali:
        # i blocchi normali hanno marginLeft = (leftMargin+leftPadding+rightMargin+rightPadding)*baseW
        # Il testo inizia a marginLeft + block.marginLeft.
        # Per il gridbox usiamo lo stesso punto di partenza del testo (senza calcolare baseW qui
        # perché non abbiamo ancora impostato il font) — usiamo gridbox._text_offset se disponibile,
        # altrimenti marginLeft puro (verrà corretto da LayoutComposeGrid se necessario).
        bx = int(self.s.marginLeft + getattr(gridbox, '_text_x_offset', 0) + gridbox.x)
        label_h = getattr(gridbox, '_label_h', 0)
        by = int(self.s.marginTop + gridbox.y) + label_h

        mode = gridbox.display_mode
        font = gridbox.font
        if font is None:
            return

        old_font = self.dc.GetFont()

        # ── Etichetta stile identico a StandardVerseNumbers (verse) ──
        # Posizione, colori e dimensioni identici a PreDrawBlock per i verse
        if self.drawLabels and gridbox.label:
            self.dc.SetFont(font)
            baseW, baseH = self.dc.GetTextExtent("0")
            lw, lh = self.dc.GetTextExtent(gridbox.label)
            # Stessi parametri di StandardVerseNumbers.Format
            leftMargin    = 0.5
            leftPadding   = 0.25
            rightPadding  = 0.25
            topPadding    = 0.1
            bottomPadding = 0.1
            # rx allineato come i blocchi normali:
            # nei blocchi normali bx = marginLeft + block.x + block.marginLeft
            # block.marginLeft include già leftMargin+leftPadding*baseW (da SetMarginBlock)
            # Per il gridbox usiamo direttamente marginLeft come punto di riferimento
            rx = int(self.s.marginLeft + leftMargin * baseW)
            tx = rx + baseW * leftPadding
            ty = int(self.s.marginTop + gridbox.y)
            ry = int(ty - topPadding * baseH)
            rw = int(lw + baseW * (leftPadding + rightPadding))
            rh = int(lh + baseH * (topPadding + bottomPadding))
            wxGrey  = wx.Colour(200, 200, 200)
            wxBlack = wx.Colour(0, 0, 0)
            # Step 1: fill sfondo grigio
            self.dc.SetBrush(wx.Brush(wxGrey, wx.SOLID))
            self.dc.SetPen(wx.TRANSPARENT_PEN)
            self.dc.DrawRectangle(rx, ry, rw, rh)
            # Step 2: bordo nero
            pen_w = max(1, round(getattr(self, 'verseBoxWidth', 1) / self.pen_scale))
            self.dc.SetPen(wx.Pen(wxBlack, pen_w))
            self.dc.SetBrush(wx.TRANSPARENT_BRUSH)
            self.dc.DrawRectangle(rx, ry, rw, rh)
            # Step 3: testo nero
            self.dc.SetTextForeground(wxBlack)
            self.dc.SetBackgroundMode(wx.TRANSPARENT)
            self.dc.DrawText(gridbox.label, int(tx), int(ty))
            self.dc.SetTextForeground(wx.BLACK)

        self.dc.SetFont(font)

        cell_w  = gridbox.cell_w
        cell_h  = gridbox.cell_h
        row_h   = getattr(gridbox, 'row_h',  cell_h)   # cell_h + top + bottom spacing
        row_top = getattr(gridbox, 'row_top', 0)        # offset y per chordTopSpacing
        pad_x   = getattr(gridbox, '_pad_x', 6)
        pad_y   = getattr(gridbox, '_pad_y', 3)

        # Font e colore per il testo delle celle (accordi)
        _chord_font  = getattr(gridbox, 'chord_font',  None) or font
        _chord_color = getattr(gridbox, 'chord_color', None) or wx.Colour(255, 0, 0)

        if mode == 'table':
            pen = wx.Pen(wx.Colour(80, 80, 80), max(1, int(1 / self.pen_scale)))
            self.dc.SetPen(pen)
            self.dc.SetBrush(wx.TRANSPARENT_BRUSH)
            spacer_h = getattr(gridbox, 'spacer_h', max(4, cell_h // 2))
            cy = by
            for row in gridbox.rows:
                if not row:
                    cy += spacer_h
                    continue
                for ci, cell in enumerate(row):
                    cx = bx + ci * cell_w
                    self.dc.SetFont(font)
                    self.dc.SetTextForeground(wx.BLACK)
                    self.dc.DrawRectangle(cx, cy + row_top, cell_w, cell_h)
                    if cell:
                        self.dc.SetFont(_chord_font)
                        self.dc.SetTextForeground(_chord_color)
                        tw, th = self.dc.GetTextExtent(cell)
                        tx = cx + (cell_w - tw) // 2
                        ty = cy + row_top + (cell_h - th) // 2
                        self.dc.DrawText(cell, tx, ty)
                cy += row_h

        else:
            spacer_h = getattr(gridbox, 'spacer_h', max(4, cell_h // 2))
            cy = by
            for row in gridbox.rows:
                if not row:
                    cy += spacer_h
                    continue
                for ci, cell in enumerate(row):
                    cx = bx + ci * cell_w
                    if mode == 'pipe':
                        # Separatore | con font/colore normale
                        self.dc.SetFont(font)
                        self.dc.SetTextForeground(wx.BLACK)
                        self.dc.DrawText('|', cx, cy + row_top + pad_y)
                        if cell:
                            self.dc.SetFont(_chord_font)
                            self.dc.SetTextForeground(_chord_color)
                            self.dc.DrawText(cell, cx + pad_x, cy + row_top + pad_y)
                    else:  # plain
                        if cell:
                            self.dc.SetFont(_chord_font)
                            self.dc.SetTextForeground(_chord_color)
                            self.dc.DrawText(cell, cx + pad_x, cy + row_top + pad_y)
                # Chiudi l'ultima | in modalità pipe
                if mode == 'pipe' and row:
                    self.dc.SetFont(font)
                    self.dc.SetTextForeground(wx.BLACK)
                    self.dc.DrawText('|', bx + len(row) * cell_w, cy + row_top + pad_y)
                cy += row_h

        self.dc.SetFont(old_font)

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
