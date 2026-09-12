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

import wx
from .SongFormat import *
from .SongBoxes import *
from .KlavierRenderer import draw_klavier_section, start_note_to_semitone
from .GuitarDiagramRenderer import draw_guitar_diagram_section
from .Globals import glb as _glb
from .MusicalSymbolDialog import get_smp_faces as _get_smp_faces


def _has_smp(s: str) -> bool:
    """True se la stringa contiene almeno un carattere SMP (codepoint > U+FFFF).
    I simboli musicali Unicode (U+1D100-U+1D1FF) cadono in questo range e
    non vengono resi da GDI classico: servono GDI+ / GraphicsContext.
    """
    return any(ord(c) > 0xFFFF for c in s)


def _smp_runs(s: str):
    """Genera coppie (substring, is_smp) per run consecutivi di caratteri con
    o senza codepoint SMP (> U+FFFF), così da poter disegnare/misurare ogni
    tratto col font corretto: il font del brano per il testo normale, il font
    con copertura SMP (FreeSerif) solo per il simbolo musicale.
    Es.: "\U0001D13D  Per nutrirci di " ->
         [("\U0001D13D", True), ("  Per nutrirci di ", False)]
    """
    if not s:
        return
    cur = [s[0]]
    cur_smp = ord(s[0]) > 0xFFFF
    for ch in s[1:]:
        smp = ord(ch) > 0xFFFF
        if smp == cur_smp:
            cur.append(ch)
        else:
            yield ''.join(cur), cur_smp
            cur = [ch]
            cur_smp = smp
    yield ''.join(cur), cur_smp


class SongDecorator(object):
    def __init__(self):
        object.__init__(self)
        self.dc = None
        # Current y
        self.y = 0
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
        # Colour for finger number labels on klavier keys (wx.Colour or None = auto contrast)
        self.fingerNumColor = None
        # Nota del primo tasto (a sinistra) dei diagrammi klavier.
        # Accetta un intero semitono (0=DO) oppure un nome di nota ("SI", "B"...).
        # Solo i tasti bianchi (DO RE MI FA SOL LA SI) sono validi; qualsiasi
        # altro valore ripiega su DO. Nota: solo DO e FA mostrano tutti e 5 i
        # tasti neri; le altre note ne mostrano 4 (la finestra di 7 bianchi
        # taglia un tasto nero).
        self.klavierStartNote = 0
        # Whether to show beat count above chords ({beats_time} directive)
        self.showDurationBeats = True
        # Modalità visualizzazione battiti: 'number' | 'dots' | 'both'
        self.durationBeatsMode = 'number'
        # Parola da evidenziare nel preview (stringa cerca/trova, '' = nessuna)
        self.find_word   = ''
        self.find_flags  = 0   # stessi flag usati da wx.stc FindText
        self.find_colour = wx.Colour(255, 220, 0)  # colore evidenziazione (modificabile)
        
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
        
    # ── Battiti sopra l'accordo ({beats_time: ...}) ────────────────────────────
    # Routine unica condivisa da:
    #   - LayoutComposeLine / PostDrawLine  (righe normali, blocchi verse:
    #     include {start_chord} e {start_bridge}, che sono blocchi verse)
    #   - LayoutComposeGrid / _DrawGridBox  (celle dei blocchi {start_of_grid})

    def _BeatsApexFont(self, base_font):
        """Font dell'apice (numero battiti) derivato dal font dell'accordo."""
        size_pct  = getattr(self, 'durationBeatsSizePct', 60)
        is_bold   = getattr(self, 'durationBeatsBold', False)
        apex_size = max(5, int(base_font.GetPointSize() * size_pct / 100))
        return wx.Font(
            apex_size,
            base_font.GetFamily(),
            base_font.GetStyle(),
            wx.FONTWEIGHT_BOLD if is_bold else wx.FONTWEIGHT_NORMAL,
            False,
            base_font.GetFaceName(),
        )

    def _BeatsApexHeight(self, base_font):
        """Altezza (px) da riservare sopra l'accordo per numero/puntini.

        Ritorna 0 se la visualizzazione dei battiti è disattivata.
        NOTA: altera il font del DC — il chiamante deve ripristinarlo.
        """
        if not getattr(self, 'showDurationBeats', True):
            return 0
        mode      = getattr(self, 'durationBeatsMode', 'number')
        apex_font = self._BeatsApexFont(base_font)
        apex_size = apex_font.GetPointSize()
        self.dc.SetFont(apex_font)
        if mode in ('number', 'both'):
            _lw, lh = self.dc.GetTextExtent('0')
            dot_extra = 0
            if mode == 'both':
                dot_r     = max(1, int(apex_size * 0.30))
                dot_extra = dot_r * 2 + 2
            return lh + dot_extra + 1
        elif mode == 'dots':
            dot_r = max(1, int(apex_size * 0.30))
            return dot_r * 2 + 2
        return 0

    def _DrawBeatsApex(self, beats, chord_left, chord_w, chord_top, base_font):
        """Disegna numero e/o puntini dei battiti sopra un accordo.

        chord_left/chord_w/chord_top sono in coordinate assolute del DC.
        NOTA: altera font, colore, pen e brush del DC — il chiamante ripristina.
        """
        if beats is None or beats < 1:
            return
        if not getattr(self, 'showDurationBeats', True):
            return

        mode       = getattr(self, 'durationBeatsMode', 'number')
        colour_hex = getattr(self, 'durationBeatsColourHex', '#6464C8')
        try:
            colour = wx.Colour(colour_hex)
        except Exception:
            colour = wx.Colour(100, 100, 200)

        apex_font = self._BeatsApexFont(base_font)
        apex_size = apex_font.GetPointSize()
        chord_right = int(chord_left + chord_w)
        self.dc.SetFont(apex_font)
        self.dc.SetTextForeground(colour)
        self.dc.SetBackgroundMode(wx.TRANSPARENT)

        # ── Modalità NUMERO ──────────────────────────────────────
        if mode in ('number', 'both'):
            label = str(beats)
            lw, lh = self.dc.GetTextExtent(label)
            align = getattr(self, 'durationBeatsAlign', 'right')
            if align == 'left':
                ax = int(chord_left)
            elif align == 'center':
                ax = int(chord_left) + (int(chord_w) - lw) // 2
            else:
                ax = chord_right - lw
            ay = int(chord_top) - lh - 1
            self.dc.DrawText(label, ax, ay)

        # ── Modalità PUNTINI ─────────────────────────────────────
        if mode in ('dots', 'both'):
            dot_r = max(1, int(apex_size * 0.30))
            self.dc.SetFont(apex_font)
            _mw, mh = self.dc.GetTextExtent('0')
            if mode == 'both':
                # Sopra il numero: numero a (chord_top - mh - 1), puntini più in alto
                dot_y = int(chord_top) - mh - 1 - dot_r - 2
            else:
                dot_y = int(chord_top) - dot_r - 2
            box_w = max(int(chord_w), dot_r * 3 * beats)
            self.dc.SetPen(wx.TRANSPARENT_PEN)
            self.dc.SetBrush(wx.Brush(colour, wx.SOLID))
            for i in range(beats):
                frac  = (i + 0.5) / beats
                dot_x = int(chord_left) + int(box_w * frac)
                self.dc.DrawCircle(dot_x, dot_y, dot_r)
            self.dc.SetBrush(wx.NullBrush)
            self.dc.SetPen(wx.NullPen)

    def _DrawCellBeats(self, cell, beats, cell_text_left, cell_text_top, chord_font):
        """Disegna i battiti sopra OGNI accordo contenuto in una cella di griglia.

        cell            -- testo della cella (può contenere più accordi: 'DO SOL')
        beats           -- lista di battiti allineata a cell.split() (int o None)
        cell_text_left  -- x del primo carattere del testo della cella (assoluto)
        cell_text_top   -- y del bordo superiore del testo della cella (assoluto)
        """
        if not cell or not beats:
            return
        tokens = cell.split()
        for k, tok in enumerate(tokens):
            b = beats[k] if k < len(beats) else None
            if not b:
                continue
            # Offset x del token: larghezza del prefisso (token precedenti + spazi)
            self.dc.SetFont(chord_font)
            prefix = u' '.join(tokens[:k])
            if prefix:
                prefix += u' '
            pw, _ph = self.dc.GetTextExtent(prefix) if prefix else (0, 0)
            tw, _th = self.dc.GetTextExtent(tok)
            self._DrawBeatsApex(b, cell_text_left + pw, tw, cell_text_top, chord_font)

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
            # Box che contiene caratteri SMP: misura ogni run col suo font
            # (testo normale col font del brano, simbolo con FreeSerif) e somma
            # le larghezze. Così la larghezza riservata combacia con ciò che
            # _DrawMixed disegnerà e il token successivo non si sovrappone.
            if _has_smp(text):
                t.w, t.h = self._MeasureMixed(text)
            else:
                t.w, t.h = self.dc.GetTextExtent(text)
            if getattr(t, 'is_time_sig', False):
                # Per la frazione musicale: larghezza = max(num, den),
                # altezza = cifra_sopra + gap + 1px linea + gap + cifra_sotto
                parts = text.split('/')
                if len(parts) == 2:
                    nw, nh = self.dc.GetTextExtent(parts[0].strip())
                    dw, dh = self.dc.GetTextExtent(parts[1].strip())
                    gap = max(2, nh // 4)
                    t.w = max(nw, dw)
                    t.h = nh + gap + 1 + gap + dh
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

        # ── Spazio extra per i numeri/puntini beats sopra gli accordi ──────────
        # PostDrawLine disegna i battiti a (chord_top - apex_h - 1), cioè sopra
        # l'area già allocata per gli accordi. Se showDurationBeats è attivo e la
        # riga contiene almeno un accordo con duration_beats > 0, aggiungiamo
        # quell'altezza al chord_top effettivo così il layout riserva lo spazio
        # corretto e la linea di interruzione di pagina viene posizionata bene.
        beatsExtraH = 0
        if hasChords and getattr(self, 'showDurationBeats', True):
            for t in line.boxes:
                if t.type != SongText.chord:
                    continue
                if getattr(t, 'duration_beats', 0) < 1:
                    continue
                beatsExtraH = max(beatsExtraH, self._BeatsApexHeight(t.font))
            # Ripristina font per il Pass 2
            if line.boxes:
                self.dc.SetFont(line.boxes[0].font)

        # ── Modalità linespacing "rel" ({linespacing: N rel}) ─────────────────
        # Quando attiva, i beats_time NON contribuiscono all'altezza né al passo
        # di riga: PostDrawLine li disegna comunque appena sopra l'accordo, ma
        # finiscono dentro lo spazio del linespacing invece di aggiungersi. In
        # pratica gli N px sono misurati dalla riga accordi alla riga di testo,
        # escludendo la banda dei beats.
        if beatsExtraH and getattr(line.parent.format, 'lineSpacingRel', False):
            beatsExtraH = 0
        # ────────────────────────────────────────────────────────────────────────

        chordsBelow = self.s.chordsBelow

        if chordsOnly and hasChords:
            textMaxH = 0
            textMaxTH = 0
            line.textBaseline = chordMaxTH + beatsExtraH
            line.chordBaseline = chordMaxTH + beatsExtraH
        elif chordsOnly:  # Block without text or chords
            w, h = self.dc.GetTextExtent(' ')
            textMaxH = h
            textMaxTH = h
            line.textBaseline = h
            line.chordBaseline = chordMaxTH
        else:
            chord_top = line.parent.format.chordTopSpacing + beatsExtraH
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
            last_line_h = b.GetLastLineTextHeight() if hasattr(b, 'GetLastLineTextHeight') else 0
            col_y += b.GetTotalHeight() + last_line_h * song.format.blockSpacing
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
            img = wx.Image(imgbox.resolve_path())
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
        # ── Spazio extra sopra le celle per i battiti ({beats_time: ...}) ──
        # Stessa routine usata dalle righe normali (_BeatsApexHeight), così i
        # numerini/puntini nella griglia hanno identico aspetto e ingombro.
        beats_h = 0
        if gridbox.HasBeats():
            _beats_base_font = getattr(gridbox, 'chord_font', None) or gridbox.font
            beats_h = self._BeatsApexHeight(_beats_base_font)
            self.dc.SetFont(gridbox.font)   # _BeatsApexHeight altera il font del DC
        gridbox.beats_h = beats_h
        row_h      = cell_h + row_top + row_bottom + beats_h
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
            if isinstance(block, (SongImageBox, SongGridBox)):
                continue
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
        fw = self.find_word
        if not fw or not text.text:
            return
        import wx.stc as _stc
        match_case = bool(self.find_flags & _stc.STC_FIND_MATCHCASE)
        haystack = text.text if match_case else text.text.lower()
        needle   = fw        if match_case else fw.lower()
        if needle not in haystack:
            return
        self.dc.SetFont(text.font)
        self.dc.SetPen(wx.TRANSPARENT_PEN)
        self.dc.SetBrush(wx.Brush(self.find_colour, wx.SOLID))
        bx = int(tx + text.marginLeft)
        by = int(ty + text.marginTop)
        bh = int(text.h)
        nd_len = len(needle)
        start  = 0
        while True:
            idx = haystack.find(needle, start)
            if idx == -1:
                break
            prefix_w, _ = self.dc.GetTextExtent(text.text[:idx])
            match_w,  _ = self.dc.GetTextExtent(text.text[idx:idx + nd_len])
            self.dc.DrawRectangle(bx + prefix_w - 1, by, match_w + 2, bh)
            start = idx + nd_len

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
                    _bg = getattr(self, "bgColour", None)
                    _bgr = (_bg.Red(), _bg.Green(), _bg.Blue()) if _bg else (255, 255, 255)
                    _tc = getattr(self, 'tempoIconColour', None)
                    _tint = (_tc.Red(), _tc.Green(), _tc.Blue()) if _tc else None
                    a = array.array('B', img.GetAlphaBuffer())
                    rs = array.array('B', img.GetDataBuffer())
                    rb = bytearray(new_w * new_h * 3)
                    for i in range(new_w * new_h):
                        av = a[i] / 255.0
                        for c in range(3):
                            _src = _tint[c] if _tint else rs[i * 3 + c]
                            rb[i * 3 + c] = int(_src * av + _bgr[c] * (1 - av))
                    bg_img = wx.Image(new_w, new_h)
                    bg_img.SetData(bytes(rb))
                    bmp = wx.Bitmap(bg_img)
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
                    _bg = getattr(self, 'bgColour', None)
                    _bgr = (_bg.Red(), _bg.Green(), _bg.Blue()) if _bg else (255, 255, 255)
                    _tc = getattr(self, 'tempoIconColour', None)
                    _tint = (_tc.Red(), _tc.Green(), _tc.Blue()) if _tc else None
                    a = array.array('B', img.GetAlphaBuffer())
                    rs = array.array('B', img.GetDataBuffer())
                    rb = bytearray(new_w * new_h * 3)
                    for i in range(new_w * new_h):
                        av = a[i] / 255.0
                        for c in range(3):
                            _src = _tint[c] if _tint else rs[i * 3 + c]
                            rb[i * 3 + c] = int(_src * av + _bgr[c] * (1 - av))
                    bg_img = wx.Image(new_w, new_h)
                    bg_img.SetData(bytes(rb))
                    bmp = wx.Bitmap(bg_img)
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
                    # Misura larghezza e altezza di numeratore e denominatore
                    nw, nh = self.dc.GetTextExtent(num)
                    dw, dh = self.dc.GetTextExtent(den)
                    max_w = max(nw, dw)
                    # Gap verticale tra testo e linea di separazione (in px)
                    gap = max(2, nh // 4)
                    line_y = by + nh + gap
                    # Disegna numeratore centrato in alto
                    self.dc.DrawText(num, bx + (max_w - nw) // 2, by)
                    # Linea orizzontale di separazione
                    pen = wx.Pen(text.color, max(1, int(1 / self.pen_scale)))
                    self.dc.SetPen(pen)
                    self.dc.DrawLine(bx, line_y, bx + max_w, line_y)
                    # Disegna denominatore centrato in basso, dopo il gap
                    self.dc.DrawText(den, bx + (max_w - dw) // 2, line_y + gap)
                    return
            except Exception:
                pass
        if getattr(text, 'is_italic', False):
            f = text.font
            italic_font = wx.Font(f.GetPointSize(), f.GetFamily(), wx.FONTSTYLE_ITALIC,
                                  f.GetWeight(), f.GetUnderlined(), f.GetFaceName())
            self.dc.SetFont(italic_font)
        # Caratteri SMP (U+10000+, es. blocco Musical Symbols U+1D100-U+1D1FF):
        # GDI/Cairo non fanno font-fallback → per i soli run SMP passiamo a GDI+
        # via GraphicsContext con FreeSerif, mentre il testo normale resta col
        # font del brano. Così cambia carattere solo il simbolo, non tutta la riga.
        if _has_smp(text.text):
            self._DrawMixed(text.text, int(tx + text.marginLeft), int(ty + text.marginTop))
        else:
            self.dc.DrawText(text.text, int(tx + text.marginLeft), int(ty + text.marginTop))
        
    # ------------------------------------------------------------------ #
    # Supporto simboli Unicode SMP (U+10000+, es. Musical Symbols)       #
    # GDI non ha font-fallback: per questi caratteri usiamo GDI+ con     #
    # un font che ha copertura SMP (FreeSerif > Segoe UI Symbol).        #
    # ------------------------------------------------------------------ #

    def _smp_gc_font_at(self, gc, pt: int, color):
        """Crea un wx.GraphicsFont con copertura SMP alla dimensione *pt* (in
        pixel device). Itera sui font caricati da fonts/ (get_smp_faces()) più il
        face del brano come ultimo fallback. Usato sia dal DC su schermo sia dal
        MemoryDC offscreen del percorso bitmap (stampa)."""
        faces = list(_get_smp_faces()) + [self.dc.GetFont().GetFaceName()]
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
        return gc.CreateFont(self.dc.GetFont(), color)

    def _smp_gc_font(self, gc, base_font, color):
        """Compat: dimensione = pt del font base * pen_scale (zoom/stampa)."""
        scale = getattr(self, 'pen_scale', 1.0)
        pt = max(1, int(round(base_font.GetPointSize() * scale)))
        return self._smp_gc_font_at(gc, pt, color)

    def _smp_measure_device(self, s: str, pt: int, color):
        """Misura *s* con un GraphicsContext su un MemoryDC (sempre disponibile,
        anche quando GraphicsContext.Create(self.dc) fallisce su un DC di
        stampa). Ritorna la misura in PIXEL DEVICE alla dimensione *pt*."""
        bmp = wx.Bitmap(1, 1, 32)
        mdc = wx.MemoryDC(bmp)
        try:
            gc = wx.GraphicsContext.Create(mdc)
            if gc is None:
                cw, ch = mdc.GetTextExtent('M')
                return float(cw * max(1, len(s))), float(ch)
            gc.SetFont(self._smp_gc_font_at(gc, pt, color))
            return gc.GetTextExtent(s)
        finally:
            mdc.SelectObject(wx.NullBitmap)

    def _smp_measure_device_pair(self, s: str, pt: int, color):
        """Misura, nello STESSO GraphicsContext offscreen e alla stessa
        dimensione *pt*, sia la stringa SMP sia un riferimento ('Mg') col font
        del brano. Ritorna ((smp_w, smp_h), ref_h_gc).

        FIX Linux — dimensione SMP non fisica in stampa
        ────────────────────────────────────────────────
        La dimensione ASSOLUTA misurata dal GC dipende dal DPI con cui il GC
        converte i point in pixel: GDI+ (Windows) usa ~96 dpi, Cairo (Linux)
        ~72 dpi. Il vecchio codice faceva `th / scale` assumendo che il DPI del
        GC coincidesse con quello del DC: vero su Windows, falso su Linux, dove
        il glifo SMP usciva ~25% più piccolo e non seguiva {textsize:N} sul
        foglio.

        La misura del RIFERIMENTO ('Mg') col font del brano, fatta nello stesso
        GC e allo stesso pt, permette al chiamante di convertire la misura SMP
        da device-GC a logico-DC tramite un RAPPORTO (glifo/testo), che è
        indipendente dal DPI. Il fattore DPI si semplifica: su Windows il
        risultato resta identico a prima, su Linux viene corretto."""
        bmp = wx.Bitmap(1, 1, 32)
        mdc = wx.MemoryDC(bmp)
        try:
            gc = wx.GraphicsContext.Create(mdc)
            if gc is None:
                cw, ch = mdc.GetTextExtent('M')
                ch = float(ch) if ch else 1.0
                return (float(cw * max(1, len(s))), ch), ch
            # Run SMP con font a copertura SMP (FreeSerif) a dimensione pt.
            gc.SetFont(self._smp_gc_font_at(gc, pt, color))
            smp_w, smp_h = gc.GetTextExtent(s)
            # Riferimento: font del brano alla STESSA dimensione pt (stesso
            # percorso point-size di _smp_gc_font_at), stesso GC.
            try:
                ref_font = wx.Font(self.dc.GetFont())
                ref_font.SetPointSize(pt)
                gc.SetFont(gc.CreateFont(ref_font, color))
                _rw, ref_h = gc.GetTextExtent('Mg')
            except Exception:
                ref_h = 0
            if not ref_h or ref_h < 1:
                ref_h = smp_h if smp_h and smp_h >= 1 else 1.0
            return (smp_w, smp_h), float(ref_h)
        finally:
            mdc.SelectObject(wx.NullBitmap)

    def _MeasureMixed(self, s: str):
        """Larghezza/altezza di *s* misurando ogni run col font giusto:
        il font del brano per il testo normale, FreeSerif (via GDI+) per i run
        SMP. La larghezza totale è la somma dei run, l'altezza è il massimo.
        Deve restare coerente con _DrawMixed, altrimenti il token successivo
        si sovrappone (era la causa dell'overlap, amplificata dallo zoom).
        """
        total_w = 0
        max_h = 0
        for run, is_smp in _smp_runs(s):
            if is_smp:
                w, h = self._GetTextExtentSMP(run)
                # Riserva lo spazio dell'abbassamento (vedi _DrawMixed), così il
                # glifo spostato in basso non invade la riga successiva.
                h += int(round(h * getattr(self, 'smp_valign_frac', self._SMP_VALIGN_FRAC)))
            else:
                w, h = self.dc.GetTextExtent(run)
            total_w += w
            max_h = max(max_h, h)
        if max_h == 0:
            _w, max_h = self.dc.GetTextExtent('Mg')
        return total_w, max_h

    # Abbassamento del glifo SMP come frazione della sua altezza. Il simbolo,
    # ancorato in alto, risulta troppo in alto rispetto alle lettere. Il valore
    # utente (spin in Opzioni) è un "livello" su scala compressa: 0 = punto
    # grezzo, ~ALIGNED_PCT allinea il glifo alla riga di testo.
    #   frazione effettiva = livello * (ALIGNED_FRAC / ALIGNED_PCT)
    _SMP_ALIGN_ALIGNED_PCT  = 5       # valore utente che allinea il glifo
    _SMP_ALIGN_ALIGNED_FRAC = 0.22    # abbassamento (frazione altezza) che allinea
    _SMP_VALIGN_FRAC = _SMP_ALIGN_ALIGNED_FRAC   # fallback se Config non è disponibile
    _SMP_VALIGN_CFG_PATH = '/Rendering'
    # Livello utente (0 = grezzo). Chiave separata dalla vecchia 'smp_valign_pct'
    # (valore assoluto, semantica diversa): non va riletta qui.
    _SMP_VALIGN_CFG_KEY  = 'smp_valign_offset_pct'

    def _read_smp_valign_frac(self):
        """Frazione di abbassamento a partire dal livello utente su scala compressa.
        0 = punto grezzo (nessun abbassamento); ~5 allinea il glifo alla riga;
        valori più alti lo abbassano ancora. Ripiega sull'allineamento se Config
        non è disponibile. Ripristina sempre il path di Config, risultato in 0..1."""
        frac = 0.0
        try:
            cfg = wx.Config.Get()
            old = cfg.GetPath()
            try:
                cfg.SetPath(self._SMP_VALIGN_CFG_PATH)
                off = cfg.ReadInt(self._SMP_VALIGN_CFG_KEY, self._SMP_ALIGN_ALIGNED_PCT)
            finally:
                cfg.SetPath(old)
            frac = max(0.0, min(1.0,
                       off * (self._SMP_ALIGN_ALIGNED_FRAC / self._SMP_ALIGN_ALIGNED_PCT)))
        except Exception:
            pass
        return frac

    def _DrawMixed(self, s: str, x: int, y: int):
        """Disegna *s* avanzando in orizzontale, un run alla volta: il testo
        normale col font già impostato sul DC, i run SMP con FreeSerif.
        Le larghezze usate per avanzare sono le stesse di _MeasureMixed.
        Il solo run SMP viene abbassato di _SMP_VALIGN_FRAC * altezza per
        allinearsi meglio alla riga di testo (vedi immagine: il simbolo stava
        troppo in alto)."""
        cx = x
        for run, is_smp in _smp_runs(s):
            if is_smp:
                w, h = self._GetTextExtentSMP(run)
                dy = int(round(h * getattr(self, 'smp_valign_frac', self._SMP_VALIGN_FRAC)))
                self._DrawTextSMP(run, int(cx), int(y + dy))
            else:
                self.dc.DrawText(run, int(cx), y)
                w, _h = self.dc.GetTextExtent(run)
            cx += w

    def _GetTextExtentSMP(self, s: str):
        """Misura *s* (che contiene caratteri SMP) in coordinate logiche del DC.

        Misuriamo con un MemoryDC offscreen (dove GraphicsContext è sempre
        disponibile, a differenza dei DC di stampa) alla dimensione device
        pt = pointSize*scale.

        FIX Linux — dimensione SMP non fisica in stampa
        ────────────────────────────────────────────────
        Il vecchio `th / scale` assumeva che il DPI del GraphicsContext (usato
        per misurare il glifo) coincidesse con quello del DC. Su Windows (GDI+
        ~96dpi) è vero; su Linux (Cairo ~72dpi) no, quindi il glifo SMP usciva
        ~25% più piccolo e NON seguiva {textsize:N} sul foglio.

        Ora ancoriamo l'altezza logica del glifo all'altezza LOGICA che il DC dà
        al font del brano (quella che occupa il testo normale sulla stessa
        riga): il glifo SMP risulta così alto quanto il testo su OGNI
        piattaforma, e scala fisicamente con {textsize:N}. La conversione
        device-GC → logico-DC passa dal rapporto misurato tra riferimento nel DC
        e riferimento nel GC (stesso font, stesso pt) → il DPI si semplifica e su
        Windows il risultato è identico a prima (conv = 1/scale).
        """
        scale = getattr(self, 'pen_scale', 1.0)
        base_font = self.dc.GetFont()
        color = self.dc.GetTextForeground()
        pt = max(1, int(round(base_font.GetPointSize() * scale)))

        (tw, th), ref_h_gc = self._smp_measure_device_pair(s, pt, color)
        if tw < 1 or th < 1:
            cw, ch = self.dc.GetTextExtent('M')
            return cw * max(1, len(s)), ch

        # Altezza logica del font del brano nel DC (ciò che occupa il testo
        # normale). 'Mg' come nel riferimento del GC → il fattore di line-height
        # si semplifica nel rapporto.
        _rw, dc_ref_h = self.dc.GetTextExtent('Mg')
        if ref_h_gc >= 1 and dc_ref_h >= 1:
            conv = dc_ref_h / ref_h_gc      # device-GC → logico-DC (DPI-safe)
        else:
            conv = 1.0 / scale if scale else 1.0   # fallback = vecchio comportamento

        return max(1, int(round(tw * conv))), max(1, int(round(th * conv)))

    def _DrawTextSMP(self, s: str, x: int, y: int):
        """Disegna *s* con un font a copertura SMP (FreeSerif).
        Chiamato solo per i run che contengono caratteri U+10000+.

        Due percorsi, scelti dal flag `smp_via_bitmap`:

        • Anteprima live a schermo (flag False): GraphicsContext direttamente sul
          DC. Azzeriamo UserScale prima di creare il GC così wxMSW (che non
          eredita la scala) e wxGTK/Cairo (che la eredita) si comportano allo
          stesso modo; poi applichiamo noi `scale`. Resta nitido a ogni zoom.

        • Stampa / esporta PDF (flag True, impostato dal printout): sul PrinterDC
          di Windows il GraphicsContext rende i glifi SMP come garbage (giganti o
          spezzati) e dc.DrawText mostra il .notdef. L'unico metodo affidabile su
          quel DC è quello già usato per le icone di tempo: rasterizzare il glifo
          su una bitmap (dove il GC funziona sempre) e blittarla con DrawBitmap,
          supportato da qualunque DC. Lo stesso percorso vale per l'anteprima di
          stampa, così anteprima e carta coincidono.
        """
        if getattr(self, 'smp_via_bitmap', False):
            self._DrawTextSMP_bitmap(s, x, y)
            return

        # Anteprima live.
        # Su wxGTK creare un GraphicsContext IN-PLACE sul DC a schermo e togglare
        # UserScale corrompe la matrice cairo condivisa: a zoom != 100% il testo
        # disegnato DOPO il glifo SMP risulta deformato. Evitiamo del tutto il GC
        # in-place passando dal percorso a bitmap (GC costruito su un MemoryDC
        # separato, poi StretchBlit): non tocca il contesto cairo del DC.
        #
        # ATTENZIONE (bug zoom Linux): a zoom != 100% lo StretchBlit "logico"
        # (dest in coordinate logiche, lasciando che sia il DC a scalarle con
        # UserScale) su wxGTK/Cairo NON è affidabile — a seconda della versione
        # la scala sul rettangolo di destinazione viene ignorata o applicata due
        # volte, e il glifo SMP finisce fuori posto / di dimensione sbagliata
        # (il "pasticcio" segnalato quando si cambia lo zoom). Per l'anteprima
        # live passiamo quindi device_res=True: il blit avviene in coordinate
        # DEVICE con UserScale azzerato solo attorno alla StretchBlit (nessun
        # GraphicsContext coinvolto → la matrice cairo non viene toccata), così
        # il risultato è corretto a QUALSIASI zoom, indipendentemente da come
        # wxGTK interpreti la scala nel blit.
        # Su wxMSW/macOS il GC in-place funziona ed è nitido a ogni zoom: lo
        # teniamo per non cambiare un comportamento già corretto lì.
        if wx.Platform == '__WXGTK__':
            self._DrawTextSMP_bitmap(s, x, y, device_res=True)
            return

        scale = getattr(self, 'pen_scale', 1.0)
        old_sx, old_sy = self.dc.GetUserScale()
        try:
            self.dc.SetUserScale(1.0, 1.0)
            gc = wx.GraphicsContext.Create(self.dc)
            if gc is None:
                raise RuntimeError("GraphicsContext non disponibile sul DC")
            gc.SetFont(self._smp_gc_font(gc, self.dc.GetFont(), self.dc.GetTextForeground()))
            gc.DrawText(s, x * scale, y * scale)
            return
        except Exception:
            pass
        finally:
            self.dc.SetUserScale(old_sx, old_sy)
        # Rete di sicurezza: se il GC diretto non è disponibile, usa la bitmap.
        self._DrawTextSMP_bitmap(s, x, y)

    # Cache condivise per la rasterizzazione FreeType/Pillow dei glifi SMP.
    #   _smp_pil_font_cache: {px: ImageFont}          (font per dimensione)
    #   _smp_pil_cache:      {(s, px, (r,g,b)): Image} (glifo RGBA renderizzato)
    _smp_pil_font_cache = {}
    _smp_pil_cache = {}

    def _smp_pil_font(self, px: int):
        """ImageFont FreeType per FreeSerif.ttf alla dimensione *px* (pixel).

        FreeType legge il file font direttamente, senza passare dal font-matching
        di GDI/GDI+ (che su Windows ignora i font privati). Ritorna None se Pillow
        o il file font non sono disponibili → il chiamante ripiega su GDI+.
        Il risultato è in cache per dimensione.
        """
        cache = SongDecorator._smp_pil_font_cache
        if px in cache:
            return cache[px]
        font = None
        try:
            from PIL import ImageFont
            # Path confermato: template/fonts/FreeSerif.ttf. Provo qualche
            # candidato e uso il primo che carica, così un layout diverso nei
            # pacchetti (AppImage/.deb) non rompe il caricamento.
            for rel in ('templates/fonts/FreeSerif.ttf',
                        'template/fonts/FreeSerif.ttf',
                        'fonts/FreeSerif.ttf'):
                try:
                    font = ImageFont.truetype(_glb.AddPath(rel), px)
                    break
                except Exception:
                    continue
        except Exception:
            font = None
        cache[px] = font
        return font

    def _render_smp_bitmap(self, s: str, px: int, color, bg):
        """Rasterizza *s* (glifo/i SMP) da FreeSerif.ttf con FreeType/Pillow e
        ritorna (wx.Bitmap 24bit, w, h) già composto sullo sfondo *bg*.

        Perché non lasciarlo a GDI+: la FreeSerif del progetto è un font privato
        e su Windows GDI+ non lo risolve in fase di stampa → .notdef → glifo
        assente sul foglio. Qui rasterizziamo noi dal .ttf: identico su Windows e
        Linux, e la stampante riceve solo pixel (come le icone di tempo PNG).

        Il glifo RGBA (colore + alpha) è in cache per (s, px, colore); la
        composizione su *bg* — che varia poco ed è economica — è rifatta a ogni
        chiamata così un cambio di colore pagina non invalida la cache del glifo.

        Ritorna None se Pillow/il font non sono disponibili.
        """
        font = self._smp_pil_font(px)
        if font is None:
            return None
        try:
            from PIL import Image, ImageDraw
            r, g, b = color.Red(), color.Green(), color.Blue()
            key = (s, px, (r, g, b))
            glyph = SongDecorator._smp_pil_cache.get(key)
            if glyph is None:
                ascent, descent = font.getmetrics()
                try:
                    adv = int(round(font.getlength(s)))
                except Exception:
                    adv = 0
                bbox = font.getbbox(s)            # (l, t, r, b)
                gw = max(1, adv, int(bbox[2]))
                gh = max(1, ascent + descent)
                glyph = Image.new('RGBA', (gw, gh), (r, g, b, 0))
                draw = ImageDraw.Draw(glyph)
                # Anchor top-left (default di Pillow): il top del glifo cade a
                # y=0, coerente con DC.DrawText che posiziona dal suo angolo
                # alto-sinistro → il glifo si allinea al resto del testo.
                draw.text((0, 0), s, font=font, fill=(r, g, b, 255))
                SongDecorator._smp_pil_cache[key] = glyph
            w, h = glyph.size
            # Composita su sfondo opaco: la stampa Windows non gestisce l'alpha,
            # quindi consegniamo un bitmap 24 bit già appiattito su *bg*.
            flat = Image.new('RGB', (w, h), (bg.Red(), bg.Green(), bg.Blue()))
            flat.paste(glyph, (0, 0), glyph)      # usa l'alpha del glifo da maschera
            wx_img = wx.Image(w, h)
            wx_img.SetData(flat.tobytes())
            return wx.Bitmap(wx_img), w, h
        except Exception:
            return None

    def _screen_content_scale(self):
        """Fattore di scala HiDPI del DC di destinazione (1.0 se non HiDPI o non
        interrogabile). Su wxGTK/Wayland un monitor a 150/200% restituisce >1:
        serve a rasterizzare la sorgente SMP abbastanza grande da non risultare
        sgranata dopo l'upscale del backend. Interrogato in modo difensivo perché
        GetContentScaleFactor non è esposto da tutte le versioni/tipi di DC; in
        caso di dubbio torna 1.0 e il pavimento ss=2 dell'anteprima copre comunque
        lo scarto di risoluzione."""
        dc = getattr(self, 'dc', None)
        if dc is None:
            return 1.0
        getf = getattr(dc, 'GetContentScaleFactor', None)
        if callable(getf):
            try:
                v = float(getf())
                if v and v > 0:
                    return v
            except Exception:
                pass
        return 1.0

    # Sovracampionamento del glifo SMP in anteprima (SOLO wxGTK/Linux). Valore
    # utente 1..4 salvato in wx.Config da MyPreferencesDialog; è il fattore
    # MINIMO di sovracampionamento della sorgente (1 = nessuno → possibile
    # sgranatura, 3 = consigliato/default, 4 = massimo). Stesso path/chiave usati
    # da Preferences._Save/_LoadSmpOversample.
    _SMP_OVERSAMPLE_CFG_PATH = '/Rendering'
    _SMP_OVERSAMPLE_CFG_KEY  = 'smp_oversample'
    _SMP_OVERSAMPLE_DEFAULT  = 3
    _SMP_OVERSAMPLE_MIN      = 1
    _SMP_OVERSAMPLE_MAX      = 4

    def _read_smp_oversample(self):
        """Pavimento di sovracampionamento SMP scelto dall'utente (1..4).
        Riletto a ogni render (come l'abbassamento) così un cambio in Preferenze
        si riflette subito in anteprima. Ripiega sul default se Config manca."""
        val = self._SMP_OVERSAMPLE_DEFAULT
        try:
            cfg = wx.Config.Get()
            old = cfg.GetPath()
            try:
                cfg.SetPath(self._SMP_OVERSAMPLE_CFG_PATH)
                val = cfg.ReadInt(self._SMP_OVERSAMPLE_CFG_KEY,
                                  self._SMP_OVERSAMPLE_DEFAULT)
            finally:
                cfg.SetPath(old)
        except Exception:
            pass
        return max(self._SMP_OVERSAMPLE_MIN, min(int(val), self._SMP_OVERSAMPLE_MAX))

    def _DrawTextSMP_bitmap(self, s: str, x: int, y: int, device_res=None):
        """Rasterizza il glifo SMP su una bitmap e la blitta sul DC corrente.
        Usato per la stampa, l'anteprima di stampa e, su wxGTK, anche per
        l'anteprima live (vedi _DrawTextSMP).

        La bitmap è a 24 bit (niente alpha): un tentativo con bitmap a 32 bit
        risultava trasparente sul PrinterDC di Windows (il glifo «non appariva»).
        Lo sfondo è riempito col colore di pagina, come la pre-composizione delle
        icone di tempo.

        Blit UNICO per tutti i casi: la sorgente è renderizzata a risoluzione
        DEVICE (pt*scale, nitida) e posata con StretchBlit in un rettangolo di
        destinazione in coordinate LOGICHE (la dimensione del glifo dal layout).
        È il DC a scalare dest→device: così il glifo segue la dimensione del
        testo (quindi {textsize:N}) su carta come in anteprima, resta nitido, e
        non serve toccare UserScale (azzerarlo nascondeva il glifo in anteprima).

        `device_res` sceglie il ramo di blit finale:
        • None/False (stampa, anteprima di stampa, rete di sicurezza): dest in
          coordinate LOGICHE → il DC scala con UserScale, così il glifo segue
          {textsize:N} sul foglio.
        • True (anteprima live wxGTK): dest in coordinate DEVICE con UserScale
          azzerato solo attorno alla StretchBlit → il glifo è corretto a ogni
          zoom anche dove wxGTK non onora la scala nel blit (vedi _DrawTextSMP).
        """
        scale = getattr(self, 'pen_scale', 1.0)
        base_font = self.dc.GetFont()
        color = self.dc.GetTextForeground()

        # In ENTRAMBI i casi la sorgente è renderizzata a risoluzione DEVICE
        # (pt*scale): così resta nitida sia su carta sia in anteprima.
        #
        # FIX Linux — glifo SMP sgranato in anteprima
        # ───────────────────────────────────────────
        # Su wxMSW/macOS l'anteprima disegna il glifo SMP come VETTORE
        # (GraphicsContext in-place, vedi _DrawTextSMP): sempre nitido. Su wxGTK
        # invece passiamo per questa bitmap (device_res=True) e la StretchBlit la
        # deposita in un rettangolo di destinazione la cui impronta FISICA è più
        # grande dei pixel della sorgente, per due motivi che si sommano:
        #   1) Pillow/FreeType rasterizza a `pt` PIXEL (~72 dpi), mentre il DC
        #      dimensiona il testo in unità logiche ~96 dpi → la destinazione è
        #      ~1.3× la sorgente anche a zoom 100% su monitor normale;
        #   2) su HiDPI (KDE/Wayland a 150/200%) il backing store ha
        #      content-scale× pixel fisici in più, che il blit deve ancora
        #      risalire.
        # In entrambi i casi la sorgente viene INGRANDITA dal blit → sgranatura.
        # Rimedio: sovracampioniamo SOLO la sorgente dell'anteprima (il rettangolo
        # di destinazione — quindi dimensione e posizione — resta identico): la
        # rasterizziamo a `pt*ss` e lasciamo che StretchBlit la RIDUCA sull'impronta
        # fisica reale → nitida. `ss` è un PAVIMENTO scelto dall'utente in
        # Preferenze (simbolo SMP, solo Linux; default 3): copre lo scarto 72/96
        # dpi ed è alzato dall'HiDPI quando serve. Il cap evita bitmap enormi.
        # Stampa e anteprima di stampa (device_res falso) NON sono toccate.
        ss = 1.0
        if device_res:
            floor = float(getattr(self, 'smp_oversample', self._SMP_OVERSAMPLE_DEFAULT))
            ss = max(floor, self._screen_content_scale())
            ss = min(ss, float(self._SMP_OVERSAMPLE_MAX))
        pt = max(1, int(round(base_font.GetPointSize() * scale * ss)))

        bg = getattr(self, 'bgColour', None) or wx.WHITE

        # ── Sorgente PRIMARIA: rasterizzazione da FreeSerif.ttf con FreeType ──
        # Il glifo SMP viene dalla FreeSerif bundled del progetto. Su Windows
        # GDI+ NON vede i font privati (aggiunti a runtime con AddFontResourceEx):
        # in stampa il match FreeSerif fallisce, disegna .notdef e sul foglio il
        # glifo sparisce. FreeType (via Pillow) legge il .ttf direttamente dal
        # file, in-process, indipendente da GDI/GDI+/driver — come le icone di
        # tempo (PNG): la stampante riceve solo pixel controllati da noi.
        _pil = self._render_smp_bitmap(s, pt, color, bg)
        if _pil is not None:
            bmp, w, h = _pil
        else:
            # ── Fallback: percorso storico GDI+ (se Pillow/il font mancano) ──
            tw, th = self._smp_measure_device(s, pt, color)
            w = max(1, int(tw + 0.999))
            h = max(1, int(th + 0.999))
            bmp = wx.Bitmap(w, h, 24)   # 24 bit: niente alpha → sempre visibile
            mdc = wx.MemoryDC(bmp)
            mdc.SetBackground(wx.Brush(bg))
            mdc.Clear()
            gc = wx.GraphicsContext.Create(mdc)
            if gc is None:
                mdc.SelectObject(wx.NullBitmap)
                self.dc.DrawText(s, int(x), int(y))
                return
            gc.SetFont(self._smp_gc_font_at(gc, pt, color))
            gc.DrawText(s, 0, 0)
            # GDI+ trasferisce sul DIB solo al flush/distruzione del GC: va
            # eliminato PRIMA di deselezionare il bitmap e di blittarlo, altrimenti
            # il glifo resta nel Graphics non-flushato e il bitmap è vuoto.
            gc.Flush()
            del gc
            mdc.SelectObject(wx.NullBitmap)
            del mdc

        # Blit UNIFICATO (stampa reale, PDF e anteprima di stampa):
        # StretchBlit della sorgente ad alta risoluzione (device-res) in un
        # rettangolo di destinazione in coordinate LOGICHE della dimensione del
        # glifo (lw, lh dallo stesso _GetTextExtentSMP usato dal layout). È il DC
        # a scalare dest→device con la propria trasformazione.
        #   • Resta NITIDO: la sorgente è a risoluzione device, StretchBlit la
        #     ricampiona ~1:1 sul footprint device del glifo.
        #   • Traccia la DIMENSIONE: dest in unità logiche ∝ textsize → il DC lo
        #     scala come il resto del testo. Il vecchio DrawBitmap a coordinate
        #     device (blit 1:1 in pixel nativi) NON seguiva textsize su carta:
        #     il glifo restava della stessa dimensione a ogni {textsize:N}.
        #   • Non tocca UserScale, così vale identico anche in anteprima (dove
        #     azzerarlo nascondeva il glifo).
        lw, lh = self._GetTextExtentSMP(s)
        lw = max(1, int(lw))
        lh = max(1, int(lh))
        src = wx.MemoryDC(bmp)
        try:
            if device_res:
                # ── Anteprima live wxGTK: blit in coordinate DEVICE ──
                # Convertiamo noi la destinazione logica (x, y, lw, lh) in pixel
                # device usando l'UserScale corrente, poi azzeriamo UserScale
                # SOLO attorno alla StretchBlit. Con scala 1.0 il DC non ri-scala
                # il rettangolo di destinazione (la DeviceOrigin — scroll+margine
                # — resta invariata e viene comunque applicata), quindi:
                #   • se wxGTK IGNORA la scala nel blit → corretto (già in device);
                #   • se la applica DUE volte → non accade più (scala = 1.0);
                #   • se la applica una volta sola → corretto.
                # In tutti i casi il glifo, renderizzato a risoluzione device
                # (w×h), viene posato ~1:1 sul suo footprint device (dw×dh) alla
                # posizione giusta, nitido e nel punto esatto a ogni zoom.
                # Nessun GraphicsContext sul DC a schermo → la matrice cairo
                # condivisa non viene toccata: il testo disegnato DOPO il glifo
                # non risulta più deformato.
                old_sx, old_sy = self.dc.GetUserScale()
                dx = int(round(x * old_sx))
                dy = int(round(y * old_sy))
                dw = max(1, int(round(lw * old_sx)))
                dh = max(1, int(round(lh * old_sy)))
                self.dc.SetUserScale(1.0, 1.0)
                try:
                    self.dc.StretchBlit(dx, dy, dw, dh, src, 0, 0, w, h)
                finally:
                    self.dc.SetUserScale(old_sx, old_sy)
            else:
                # Percorso stampa / anteprima di stampa: dest in coordinate
                # LOGICHE, lasciando che sia il PrinterDC (UserScale tipicamente
                # 1.0) a scalare → il glifo segue {textsize:N} sul foglio.
                self.dc.StretchBlit(int(x), int(y), lw, lh, src, 0, 0, w, h)
        finally:
            src.SelectObject(wx.NullBitmap)

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
        # ── Numero/puntini battiti sopra ogni accordo ({beats_time: ...}) ─
        if not getattr(self, 'showDurationBeats', True):
            return

        # Costruisce la sequenza completa dei box della riga in ordine di x
        all_boxes = sorted(line.boxes, key=lambda t: t.x)

        for text in all_boxes:
            if text.type != SongText.chord:
                continue
            beats = getattr(text, 'duration_beats', 0)
            if beats < 1:
                continue

            chord_left = int(lx + line.marginLeft + text.x + text.marginLeft)
            chord_top  = int(ly + line.marginTop + text.y + text.marginTop)

            self._DrawBeatsApex(beats, chord_left, int(text.w), chord_top, text.font)

            # Ripristina font e colore
            self.dc.SetFont(text.font)
            self.dc.SetTextForeground(text.color)


    def PostDrawBlock(self, block, bx, by):
        # bx, by: coordinates of top-left corner of drawable area
        # ── Tabella griglia accordi (modalità 'table') ────────────────
        # La griglia è già stata disegnata interamente da _DrawGridBox
        # (chiamato da DrawBoxes per i SongGridBox). PostDrawBlock gestisce
        # solo i SongBlock ordinari: se is_grid è True usciamo subito per
        # evitare un secondo rendering sovrapposto.
        if getattr(block, 'is_grid', False):
            return
        
    def PostDrawSong(self, song):
        current_extra_h = 0
        self._klavier_extra_w = 0  # larghezza aggiuntiva oltre il testo (usata da Draw())
        # Larghezza utile disponibile per il klavier (da marginLeft alla fine del testo)
        content_w = song.GetTotalWidth() - int(song.marginLeft)

        if self.showKlavier:
            klavier_list = getattr(song, 'klavier_list', [])
            if klavier_list:
                start_x = int(song.marginLeft)
                start_y = int(song.marginTop + song.h) + 10
                base_font = song.format.wxFont
                h, used_w = draw_klavier_section(
                    self.dc, klavier_list, start_x, start_y,
                    base_font, self.pen_scale, self.notation,
                    self.klavierHighlightColor,
                    finger_num_color=self.fingerNumColor,
                    content_w=content_w,
                    start_note=start_note_to_semitone(self.klavierStartNote),
                )
                current_extra_h += h + 20
                # Se il klavier è più largo del testo, memorizza la larghezza extra
                klavier_total_w = start_x + used_w
                if klavier_total_w > song.GetTotalWidth():
                    self._klavier_extra_w = klavier_total_w - song.GetTotalWidth()

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
                    self.PostDrawLine(line, lx, ly)
                self.lastBlockOffsetY = by + block.GetTotalHeight()
                self.PostDrawBlock(block, bx, by)
        if self.s.drawWholeSong:
            self.PostDrawSong(self.s)
        
    def _DrawImageBox(self, imgbox):
        """Disegna una SongImageBox sul DC corrente."""
        if not imgbox.path or not getattr(imgbox, '_final_w', 0) or not getattr(imgbox, '_final_h', 0):
            return
        try:
            img = wx.Image(imgbox.resolve_path())
            if not img.IsOk():
                return
            final_w = imgbox._final_w
            final_h = imgbox._final_h
            img = img.Scale(final_w, final_h, wx.IMAGE_QUALITY_HIGH)

            # Precomponi alpha su sfondo bianco (compatibilita' PrinterDC su Windows)
            if img.HasAlpha():
                import array
                _bg = getattr(self, 'bgColour', None)
                _bgr = (_bg.Red(), _bg.Green(), _bg.Blue()) if _bg else (255, 255, 255)
                a = array.array('B', img.GetAlphaBuffer())
                rs = array.array('B', img.GetDataBuffer())
                rb = bytearray(final_w * final_h * 3)
                for i in range(final_w * final_h):
                    av = a[i] / 255.0
                    for c in range(3):
                        rb[i * 3 + c] = int(rs[i * 3 + c] * av + _bgr[c] * (1 - av))
                bg_img = wx.Image(final_w, final_h)
                bg_img.SetData(bytes(rb))
                bmp = wx.Bitmap(bg_img)
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
        # Posizione, colori e dimensioni identici a PreDrawBlock per i verse.
        # L'etichetta del grid è sempre visibile, indipendentemente da drawLabels
        # (che controlla solo i numeri di strofa, non le etichette dei blocchi grid).
        if gridbox.label:
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

        # Offset verticale effettivo del contenuto della cella: allo spazio
        # chordTopSpacing si somma quello riservato ai battiti (0 se assenti).
        beats_h  = getattr(gridbox, 'beats_h', 0)
        row_top += beats_h

        if mode == 'table':
            pen = wx.Pen(wx.Colour(80, 80, 80), max(1, int(1 / self.pen_scale)))
            self.dc.SetPen(pen)
            self.dc.SetBrush(wx.TRANSPARENT_BRUSH)
            spacer_h = getattr(gridbox, 'spacer_h', max(4, cell_h // 2))
            cy = by
            for ri, row in enumerate(gridbox.rows):
                if not row:
                    cy += spacer_h
                    continue
                for ci, cell in enumerate(row):
                    cx = bx + ci * cell_w
                    self.dc.SetFont(font)
                    self.dc.SetTextForeground(wx.BLACK)
                    self.dc.SetPen(pen)
                    self.dc.SetBrush(wx.TRANSPARENT_BRUSH)
                    self.dc.DrawRectangle(cx, cy + row_top, cell_w, cell_h)
                    if cell:
                        self.dc.SetFont(_chord_font)
                        self.dc.SetTextForeground(_chord_color)
                        tw, th = self.dc.GetTextExtent(cell)
                        tx = cx + (cell_w - tw) // 2
                        ty = cy + row_top + (cell_h - th) // 2
                        self.dc.DrawText(cell, tx, ty)
                        # Battiti sopra ciascun accordo della cella
                        beats = gridbox.GetBeats(ri, ci)
                        if beats:
                            self._DrawCellBeats(cell, beats, tx,
                                                cy + row_top, _chord_font)
                cy += row_h

        else:
            spacer_h = getattr(gridbox, 'spacer_h', max(4, cell_h // 2))
            cy = by
            for ri, row in enumerate(gridbox.rows):
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
                        beats = gridbox.GetBeats(ri, ci)
                        if beats:
                            self._DrawCellBeats(cell, beats, cx + pad_x,
                                                cy + row_top + pad_y, _chord_font)
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
        # Abbassamento verticale del simbolo SMP: valore utente salvato in
        # wx.Config (scritto dalla finestra Simboli musicali). Ricaricato a ogni
        # render così un cambio dell'impostazione si riflette subito in anteprima.
        self.smp_valign_frac = self._read_smp_valign_frac()
        self.smp_oversample = self._read_smp_oversample()
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
        # Se il klavier è più largo del testo, aumenta total_w di conseguenza
        # così PreviewCanvas imposterà una virtual size sufficiente a mostrarlo tutto.
        total_w += getattr(self, '_klavier_extra_w', 0)
        return total_w, h
