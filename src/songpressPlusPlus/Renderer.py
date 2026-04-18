###############################################################
# Name:             Renderer.py
# Purpose:     Render a song on a dc
# Author:         Luca Allulli (webmaster@roma21.it)
# Modified by:  Denisov21
# Created:     2009-02-21
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
#               Modifications copyright Denisov21
# License:     GNU GPL v2
##############################################################

import wx

from .SongDecorator import *
from .SongTokenizer import *
from .GuitarDiagramRenderer import draw_guitar_diagram_section
from .SongFormat import *
from .SongBoxes import *
from .Transpose import translateChord, autodetectNotation
from .EditDistance import minEditDist

_ = wx.GetTranslation


class BreakException(Exception):
    pass


class Renderer(object):
    def __init__(self, sf, sd=SongDecorator(), notations=[]):
        object.__init__(self)
        self.text = ""
        self.sd = sd
        self.dc = None
        # SongFormat
        self.starting_sf = sf
        self.sf = sf
        self.format = None
        self.currentBlock = None
        self.currentLine = None
        self.song = None
        self.notation = None
        self.notations = notations
        self.chordPatterns = []
        self.chordsBelow = False
        # 0 = non mostrare, 1 = "♩ = valore", 2 = "BPM: valore"
        self.tempoDisplay = 0
        # True = mostra nell'anteprima, False = solo metadato (non visualizzato)
        self.timeDisplay = True
        self.keyDisplay = True
        # Layout a colonne: numero di colonne (1 = nessuna divisione)
        # e altezza massima per colonna in pixel schermo (0 = auto/illimitata)
        self.columns = 1
        self.columnHeight = 0
        # Modalità di visualizzazione {start_of_grid}: 'pipe' | 'plain' | 'table'
        self.gridDisplayMode = 'pipe'
        # Contatori iniziali per la numerazione delle strofe:
        # permettono di continuare la numerazione tra segmenti {new_page}.
        self.initialVerseCount = 0
        self.initialLabelCount = 0
        self.initialChorusCount = 0

    def BeginBlock(self, type, label=None):
        self.EndBlock()
        if type == SongBlock.verse:
            self.song.verseCount += 1
            if label is None:
                self.song.labelCount += 1
            self.sf.AddVerse()
            self.format = self.sf.verse[-1]
        elif type == SongBlock.chorus:
            self.format = self.sf.chorus
            self.song.chorusCount += 1
        else:
            self.format = self.sf.title
        self.currentBlock = SongBlock(type, self.format)
        self.currentBlock.label = label
        self.currentBlock.verseNumber = self.song.verseCount
        self.currentBlock.verseLabelNumber = self.song.labelCount
        if getattr(self, '_next_page_break', False):
            self.currentBlock.pageBreakBefore = True
            self._next_page_break = False
        if getattr(self, '_next_column_break', False):
            self.currentBlock.columnBreakBefore = True
            self._next_column_break = False

    def EndBlock(self):
        if self.currentBlock is not None:
            self.EndLine()
            if self.sf.showChords == 1:
                current = self.currentBlock.chords
                found = False
                for p in self.chordPatterns:
                    led = len(p)
                    med = minEditDist(p, current)
                    if med < led and med < 4:
                        found = True
                        break
                if not found:
                    self.chordPatterns.append(current)
                else:
                    self.currentBlock.RemoveChordBoxes()
            self.song.AddBox(self.currentBlock)
            self.currentBlock = None

    def BeginVerse(self, label=None):
        if self.currentBlock == None:
            self.BeginBlock(SongBlock.verse, label)
            self.label = label

    def BeginChorus(self, label=None):
        self.BeginBlock(SongBlock.chorus, label)

    def ChorusVSkip(self):
        self.EndLine()
        self.BeginLine()
        self.EndLine()

    def BeginTab(self, label=None):
        """Apre un blocco {start_of_tab}: verse con font monospace e accordi soppressi."""
        lbl = label if (label and label.strip()) else _("Tab")
        self.BeginBlock(SongBlock.verse, lbl)
        self.currentBlock.is_tab = True
        # Salva il formato corrente e sostituisce il font con Courier New (monospace)
        self._tab_saved_face = self.sf.face
        self.sf.face = 'Courier New'
        self.format = ParagraphFormat(self.format)
        self.format.face = 'Courier New'

    def EndTab(self):
        """Chiude un blocco {end_of_tab} e ripristina il font."""
        state = self.GetState()
        if state == SongBlock.verse and getattr(self.currentBlock, 'is_tab', False):
            self.EndBlock()
        saved = getattr(self, '_tab_saved_face', None)
        if saved is not None:
            self.sf.face = saved
            self.format = ParagraphFormat(self.format)
            self.format.face = saved
            self._tab_saved_face = None

    def BeginGrid(self, label=None):
        """Apre un blocco {start_of_grid}: raccoglie le righe in self._grid_rows."""
        import re as _re
        # Chiude un eventuale blocco aperto
        self.EndBlock()
        # Etichetta predefinita: dalla preferenza, oppure "Grid" come fallback
        default_label = getattr(self, 'gridDefaultLabel', None) or _("Grid")
        # Estrai size=N, chordtopspacing=N, linespacing=N dalla stringa attributi
        raw = label or ''
        size_match = _re.search(r'\bsize\s*=\s*(\d+(?:[.,]\d{1,2})?)', raw)
        self._grid_size = float(size_match.group(1).replace(',', '.')) if size_match else 1.0
        cts_match = _re.search(r'\bchordtopspacing\s*=\s*(\d+)', raw, _re.IGNORECASE)
        self._grid_chordTopSpacing = int(cts_match.group(1)) if cts_match else None
        ls_match = _re.search(r'\blinespacing\s*=\s*(\d+)', raw, _re.IGNORECASE)
        self._grid_lineSpacing = int(ls_match.group(1)) if ls_match else None
        sd_match = _re.search(r'\bsizedir\s*=\s*(horizontal|vertical|both)\b', raw, _re.IGNORECASE)
        if sd_match:
            self._grid_sizeDir = sd_match.group(1).lower()
        else:
            # Fallback alla preferenza globale
            self._grid_sizeDir = getattr(self, 'gridSizeDir', 'both')
        # Rimuovi tutti i parametri key=value riconosciuti, il resto è l'etichetta
        clean_label = _re.sub(
            r'\b(?:size|chordtopspacing|linespacing)\s*=\s*\d+(?:[.,]\d{1,2})?'
            r'|\bsizedir\s*=\s*\w+',
            '', raw, flags=_re.IGNORECASE).strip()
        self._grid_label = clean_label if clean_label else default_label
        self._grid_rows = []   # list[list[str]] — celle per ogni riga

    def EndGrid(self):
        """Chiude il blocco grid e aggiunge un SongGridBox alla canzone."""
        rows = getattr(self, '_grid_rows', None)
        if rows is None:
            return
        mode = getattr(self, 'gridDisplayMode', 'pipe')
        font = self.format.wxFont
        chord_font  = self.format.chord.wxFont
        chord_color = self.format.chord.color
        label = getattr(self, '_grid_label', _("Grid"))
        box = SongGridBox(rows, display_mode=mode, font=font, label=label,
                          size=getattr(self, '_grid_size', 1),
                          chordTopSpacing=getattr(self, '_grid_chordTopSpacing', None),
                          lineSpacing=getattr(self, '_grid_lineSpacing', None),
                          sizeDir=getattr(self, '_grid_sizeDir', 'both'),
                          chord_font=chord_font,
                          chord_color=chord_color)
        box.pageBreakBefore = getattr(self, '_next_page_break', False)
        if box.pageBreakBefore:
            self._next_page_break = False
        box.columnBreakBefore = getattr(self, '_next_column_break', False)
        if box.columnBreakBefore:
            self._next_column_break = False
        self.song.AddBox(box)
        self._grid_rows = None
        self._grid_label = None

    def _ParseGridLine(self, l):
        """Estrae le celle da una riga del blocco grid.

        Regole di parsing:
            Formato pipe — | separa le battute:
                | Am | F | G |      → ['Am', 'F', 'G']
                | Am |   | G |      → ['Am', '', 'G']  (cella vuota = spazio)
                (spazio vuoto tra || = cella vuota che sposta gli accordi a destra)

            Solo spazi (nessun pipe):
                [C] [G] [Am] [F]  → ogni accordo = cella separata
        """
        import re as _re

        stripped = l.strip()
        if not stripped:
            return []

        def _clean_cell(s):
            """Normalizza spazi interni."""
            return ' '.join(s.split())

        # ── Formato pipe: | separa le battute ─────────────────────────
        if '|' in stripped:
            def replace_chord(m):
                return m.group(1)
            plain = _re.sub(r'\[([^\]]+)\]', replace_chord, stripped)
            parts = plain.split('|')
            # Rimuovi bordi vuoti (prima del primo | e dopo l'ultimo |)
            inner = parts[1:-1] if len(parts) >= 2 else parts
            if not inner:
                return []
            contents = [p.strip() for p in inner]
            widths   = [len(p)    for p in inner]
            # Larghezza minima di riferimento = parte non vuota più corta
            ref_widths = [w for w, c in zip(widths, contents) if c]
            min_w = min(ref_widths) if ref_widths else 1
            # Ogni parte occupa round(width/min_w) celle:
            # parte più larga = accordo preceduto da celle vuote
            result = []
            for w, c in zip(widths, contents):
                n_cells = max(1, round(w / min_w))
                result.extend([''  ] * (n_cells - 1))  # celle vuote extra
                result.append(c)                         # cella con accordo (o '')
            return result

        # ── Solo chord token separati da spazio: ogni accordo = cella ──
        chords = _re.findall(r'\[([^\]]+)\]', l)
        if chords:
            return chords

        # ── Testo puro: ogni parola = cella ───────────────────────────
        words = [_clean_cell(w) for w in stripped.split()]
        return [w for w in words if w]

    def RowSpacer(self):
        """Inserisce mezza riga vuota come blocco autonomo (comando {row} / {r})."""
        self.EndBlock()
        self.BeginBlock(SongBlock.verse, "")  # label "" = non numerato, nessuna etichetta
        self.BeginLine()
        # Crea un testo vuoto con font dimezzato per ottenere metà dell'altezza normale
        half_format = ParagraphFormat(self.sf)
        half_format.size = max(1, self.sf.size // 2)
        t = SongText(" ", half_format.wxFont, SongText.text, half_format.color)
        self.currentLine.AddBox(t)
        self.EndLine()
        self.EndBlock()

    def AddText(self, text, type=SongText.text):
        # Dentro un blocco {start_of_tab} gli accordi non vengono visualizzati:
        # il tab ASCII è già notazione completa, i chord marker sono ridondanti.
        if type == SongText.chord and self.currentBlock is not None and getattr(self.currentBlock, 'is_tab', False):
            return
        if(
            text.strip() != ''
            and type != SongText.title
            and type != SongText.subtitle
            and type != SongText.comment
            and self.currentBlock is not None
            and self.currentBlock.type == SongBlock.title
        ):
            self.EndBlock()
        if type == SongText.comment and self.currentBlock is None:
            self.BeginBlock(SongBlock.title)
            self.format = self.sf.title
        else:
            self.BeginVerse()
        self.BeginLine()
        if type == SongText.comment:
            text = "(" + text + ")"
            format = self.format.comment
        elif type == SongText.chord:
            format = self.format.chord
            if self.sf.showChords == 1:
                self.currentBlock.chords.append(translateChord(text, self.notation, self.notation))
        else:
            format = self.format
        t = SongText(text, format.wxFont, type, format.color)
        if type == SongText.chord and self._pending_duration:
            # Associa la durata in battiti all'accordo corrispondente per posizione
            # nella sequenza della direttiva {beats_time: ...}
            if self._duration_chord_idx < len(self._pending_duration):
                t.duration_beats = self._pending_duration[self._duration_chord_idx][1]
                self._duration_chord_idx += 1
                # Se abbiamo consumato tutti gli accordi, svuota la lista
                if self._duration_chord_idx >= len(self._pending_duration):
                    self._pending_duration = []
                    self._duration_chord_idx = 0
        if not type == SongText.chord or self.sf.showChords > 0:
            self.currentLine.AddBox(t)

    def AddTitle(self, title):
        if self.currentBlock is None or self.currentBlock.type != SongBlock.title:
            self.BeginBlock(SongBlock.title)
        self.format = self.sf.title
        self.AddText(title, SongText.title)

    def AddSubTitle(self, title):
        if self.currentBlock is None or self.currentBlock.type != SongBlock.title:
            self.BeginBlock(SongBlock.title)
        self.format = self.sf.subtitle
        self.AddText(title, SongText.subtitle)

    def BeginLine(self):
        if self.currentLine == None:
            if self.song.drawWholeSong or self.fromLine <= self.lineCount <= self.toLine:
                self.currentBlock.drawBlock = True
            self.currentLine = SongLine()

    def EndLine(self):
        if self.currentLine is not None:
            if len(self.currentLine.boxes) > 0 or self.currentBlock.type != SongBlock.title:
                self.currentBlock.AddBox(self.currentLine)
            self.currentLine = None

    def GetAttribute(self):
        try:
            tok = self.tkz.next()
            if tok.token != SongTokenizer.colonToken:
                self.tkz.Repeat()
                return None
            tok = self.tkz.next()
            if tok.token != SongTokenizer.attrToken:
                self.tkz.Repeat()
                return ''
            return tok.content
        except StopIteration:
            pass
        return None

    def GetState(self):
        return None if self.currentBlock == None else self.currentBlock.type

    def Render(self, text, dc, fromLine = -1, toLine = -1):
        self.text = text
        self.dc = dc
        self.verseNumber = 0
        self.format = self.starting_sf
        self.currentLine = None
        self.currentBlock = None
        self.lineCount = -1
        self.fromLine = fromLine
        self.toLine = toLine
        self.sf = SongFormat(self.starting_sf)
        self.song = SongSong(self.sf)
        self.song.verseCount = self.initialVerseCount
        self.song.labelCount = self.initialLabelCount
        self.song.chorusCount = self.initialChorusCount
        self.song.drawWholeSong = fromLine == -1
        self.song.chordsBelow = self.chordsBelow
        self.song.klavier_list = []  # accordi da mostrare come tastiere
        self.song.define_list  = []  # diagrammi chitarra da mostrare
        # Dizionario durate accordi dalla direttiva {beats_time: ACCORDO=battiti ...}
        # Attivo per la riga immediatamente successiva alla direttiva.
        self._pending_duration = []   # lista di (accordo, battiti) in ordine
        self._duration_chord_idx = 0  # indice accordo corrente nella riga

        self.song.columns = self.columns
        self.song.columnHeight = self.columnHeight
        self.song.timeDisplay = self.timeDisplay
        self.song.keyDisplay = self.keyDisplay
        self._next_page_break = False
        self._next_column_break = False
        if self.sf.showChords == 1:
            self.notation = autodetectNotation(text, self.notations)
            self.chordPatterns = []

        for l in self.text.splitlines():
            self.lineCount += 1
            state = self.GetState()

            # ── Blocco grid: raccoglie le righe in _grid_rows ─────────
            if getattr(self, '_grid_rows', None) is not None:
                stripped_l = l.strip()
                # {row} / {r} dentro il grid → riga vuota separatrice
                if stripped_l in ('{row}', '{r}'):
                    self._grid_rows.append([])   # lista vuota = riga vuota
                    continue
                # Le direttive {end_of_grid}, {eog} ecc. passano alla tokenizzazione normale
                if not (stripped_l.startswith('{') and stripped_l.endswith('}')):
                    cells = self._ParseGridLine(l)
                    if cells:
                        self._grid_rows.append(cells)
                    continue
            # ─────────────────────────────────────────────────────────

            self.tkz = SongTokenizer(l)
            empty = True
            for tok in self.tkz:
                state = self.GetState()
                t = tok.token
                if t == SongTokenizer.commentToken:
                    # Riga di commento (#...): ignorata interamente come se fosse vuota.
                    # Non si imposta empty=False, così il blocco corrente viene chiuso
                    # esattamente come farebbe una riga vuota.
                    break
                empty = False
                if t == SongTokenizer.normalToken:
                    self.AddText(tok.content)
                elif t == SongTokenizer.chordToken:
                    self.AddText(tok.content[1:], SongText.chord)
                elif t == SongTokenizer.commandToken:
                    cmd = tok.content.lower()
                    if cmd == 'soc' or cmd == 'start_of_chorus':
                        a = self.GetAttribute()
                        self.BeginChorus(a if (a and a.strip()) else None)
                    elif (cmd == 'eoc' or cmd == 'end_of_chorus') and state == SongBlock.chorus:
                        self.EndBlock()
                    # --- Nuovi comandi strutturati ---
                    elif cmd == 'start_verse':
                        # Strofa non numerata: passa label="" (non-None) così
                        # BeginBlock non incrementa labelCount e il decorator
                        # non visualizza nessuna etichetta numerica.
                        a = self.GetAttribute()
                        label = a if (a and a.strip()) else ""
                        self.BeginBlock(SongBlock.verse, label)
                    elif cmd == 'end_verse':
                        if state == SongBlock.verse:
                            self.EndBlock()
                    elif cmd == 'start_verse_num':
                        # Strofa numerata: passa label=None per l'auto-numerazione
                        a = self.GetAttribute()
                        self.BeginBlock(SongBlock.verse, a if (a and a.strip()) else None)
                    elif cmd == 'end_verse_num':
                        if state == SongBlock.verse:
                            self.EndBlock()
                    elif cmd == 'start_chorus':
                        a = self.GetAttribute()
                        self.BeginChorus(a if (a and a.strip()) else None)
                    elif cmd == 'end_chorus':
                        if state == SongBlock.chorus:
                            self.EndBlock()
                    elif cmd == 'start_chord':
                        # Introduzione accordi: etichetta fissa, non numerata
                        a = self.GetAttribute()
                        label = a if (a and a.strip()) else _("Intro")
                        self.BeginBlock(SongBlock.verse, label)
                    elif cmd == 'end_chord':
                        if state == SongBlock.verse:
                            self.EndBlock()
                    elif cmd == 'start_bridge':
                        # Inciso: etichetta fissa, non numerata
                        a = self.GetAttribute()
                        label = a.strip() if (a and a.strip()) else None
                        self.BeginBlock(SongBlock.verse, label)
                    elif cmd == 'end_bridge':
                        if state == SongBlock.verse:
                            self.EndBlock()
                    elif cmd == 'start_of_tab' or cmd == 'sot':
                        a = self.GetAttribute()
                        self.BeginTab(a)
                    elif cmd == 'end_of_tab' or cmd == 'eot':
                        self.EndTab()
                    elif cmd == 'start_of_grid' or cmd == 'sog' or cmd == 'grid':
                        a = self.GetAttribute()
                        self.BeginGrid(a)
                    elif cmd == 'end_of_grid' or cmd == 'eog':
                        self.EndGrid()
                    elif cmd == 'new_page' or cmd == 'np':
                        # Interruzione di pagina esplicita: chiudi il blocco corrente
                        # e segna il prossimo blocco con pageBreakBefore=True
                        self.EndBlock()
                        self._next_page_break = True
                    elif cmd == 'column_break' or cmd == 'colb':
                        # Interruzione di colonna esplicita: chiudi il blocco corrente
                        # e segna il prossimo blocco con columnBreakBefore=True
                        self.EndBlock()
                        self._next_column_break = True
                    elif cmd == 'row' or cmd == 'r':
                        # Riga vuota autonoma (spacer verticale senza testo né linee)
                        self.RowSpacer()
                    elif cmd == 'bar':
                        # {bar} dentro un blocco grid è già gestito come separatore
                        # di battuta nel parser di riga; fuori da una grid è ignorato.
                        pass
                    elif cmd == 'start_of_part' or cmd == 'sop':
                        # Sezione generica (ChordPro 6): trattata come strofa
                        # con etichetta opzionale; non numerata di default.
                        a = self.GetAttribute()
                        label = a.strip() if (a and a.strip()) else _("Part")
                        self.BeginBlock(SongBlock.verse, label)
                    elif cmd == 'end_of_part' or cmd == 'eop':
                        if state == SongBlock.verse:
                            self.EndBlock()
                    # Metadati estesi (ChordPro 6) — trattati come puri metadati:
                    # non visualizzati nell'anteprima, ignorati silenziosamente.
                    elif cmd in ('sorttitle', 'keywords', 'topic', 'collection',
                                 'language', 'pagetype', 'columns', 'meta',
                                 'transpose', 'duration'):
                        self.GetAttribute()   # consuma il token `:valore` senza usarlo
                    elif cmd == 'new_song':
                        # Inizio nuovo brano nello stesso documento:
                        # chiudi il blocco corrente e azzera i contatori
                        # di strofe e ritornelli così la numerazione riparte da 1.
                        self.EndBlock()
                        self.song.verseCount = 0
                        self.song.labelCount = 0
                        self.song.chorusCount = 0
                        self.sf.verse = []
                    # --- Fine nuovi comandi ---
                    elif cmd == 'c' or cmd == 'comment':
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            self.AddText(a, SongText.comment)
                    elif cmd == 'comment_italic' or cmd == 'ci':
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            t = self.AddText(a, SongText.comment)
                            if self.currentLine is not None and self.currentLine.boxes:
                                self.currentLine.boxes[-1].is_italic = True
                    elif cmd == 'comment_box' or cmd == 'cb':
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            self.AddText(a, SongText.comment)
                            if self.currentLine is not None and self.currentLine.boxes:
                                self.currentLine.boxes[-1].is_box = True
                    elif cmd == 't' or cmd == 'title':
                        a = self.GetAttribute()
                        if a is not None:
                            self.AddTitle(a)
                    elif cmd == 'st' or cmd == 'subtitle':
                        a = self.GetAttribute()
                        if a is not None:
                            self.AddSubTitle(a)
                    elif cmd == 'tempo':
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            if self.tempoDisplay == 0:
                                self.AddSubTitle('Tempo: %s' % a.strip())
                            elif self.tempoDisplay == 1:
                                self.AddSubTitle(u' = %s' % a.strip())
                                # Marca l'ultimo SongText aggiunto per disegnare la bitmap della nota
                                if self.currentLine is not None and self.currentLine.boxes:
                                    self.currentLine.boxes[-1].is_tempo_note = True
                            elif self.tempoDisplay == 2:
                                self.AddSubTitle('BPM: %s' % a.strip())
                            elif self.tempoDisplay == 3:
                                self.AddSubTitle(u' = %s' % a.strip())
                                if self.currentLine is not None and self.currentLine.boxes:
                                    self.currentLine.boxes[-1].is_tempo_metro = True
                            # tempoDisplay == -1 → metadato, non visualizzato
                    elif cmd == 'tempo_m':
                        # Minima (nota da mezzo) — img/minima_32x32.png
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            if self.tempoDisplay == 0:
                                self.AddSubTitle('Tempo: %s' % a.strip())
                            elif self.tempoDisplay == 1:
                                self.AddSubTitle(u' = %s' % a.strip())
                                if self.currentLine is not None and self.currentLine.boxes:
                                    self.currentLine.boxes[-1].is_tempo_half_note = True
                            elif self.tempoDisplay == 2:
                                self.AddSubTitle('BPM: %s' % a.strip())
                            elif self.tempoDisplay == 3:
                                self.AddSubTitle(u' = %s' % a.strip())
                                if self.currentLine is not None and self.currentLine.boxes:
                                    self.currentLine.boxes[-1].is_tempo_metro = True
                    elif cmd == 'tempo_s':
                        # Semiminima (nota da un quarto) — img/semiminima_32x32.png
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            if self.tempoDisplay == 0:
                                self.AddSubTitle('Tempo: %s' % a.strip())
                            elif self.tempoDisplay == 1:
                                self.AddSubTitle(u' = %s' % a.strip())
                                if self.currentLine is not None and self.currentLine.boxes:
                                    self.currentLine.boxes[-1].is_tempo_quarter_note = True
                            elif self.tempoDisplay == 2:
                                self.AddSubTitle('BPM: %s' % a.strip())
                            elif self.tempoDisplay == 3:
                                self.AddSubTitle(u' = %s' % a.strip())
                                if self.currentLine is not None and self.currentLine.boxes:
                                    self.currentLine.boxes[-1].is_tempo_metro = True
                    elif cmd == 'tempo_c':
                        # Croma (nota da un ottavo) — img/croma_32x32.png
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            if self.tempoDisplay == 0:
                                self.AddSubTitle('Tempo: %s' % a.strip())
                            elif self.tempoDisplay == 1:
                                self.AddSubTitle(u' = %s' % a.strip())
                                if self.currentLine is not None and self.currentLine.boxes:
                                    self.currentLine.boxes[-1].is_tempo_eighth_note = True
                            elif self.tempoDisplay == 2:
                                self.AddSubTitle('BPM: %s' % a.strip())
                            elif self.tempoDisplay == 3:
                                self.AddSubTitle(u' = %s' % a.strip())
                                if self.currentLine is not None and self.currentLine.boxes:
                                    self.currentLine.boxes[-1].is_tempo_metro = True
                    elif cmd == 'tempo_sp':
                        # Semiminima puntata — img/semiminima_punto_32x32.png
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            if self.tempoDisplay == 0:
                                self.AddSubTitle('Tempo: %s' % a.strip())
                            elif self.tempoDisplay == 1:
                                self.AddSubTitle(u' = %s' % a.strip())
                                if self.currentLine is not None and self.currentLine.boxes:
                                    self.currentLine.boxes[-1].is_tempo_dotted_quarter = True
                            elif self.tempoDisplay == 2:
                                self.AddSubTitle('BPM: %s' % a.strip())
                            elif self.tempoDisplay == 3:
                                self.AddSubTitle(u' = %s' % a.strip())
                                if self.currentLine is not None and self.currentLine.boxes:
                                    self.currentLine.boxes[-1].is_tempo_metro = True
                    elif cmd == 'tempo_cp':
                        # Croma puntata — img/croma_punto_32x32.png
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            if self.tempoDisplay == 0:
                                self.AddSubTitle('Tempo: %s' % a.strip())
                            elif self.tempoDisplay == 1:
                                self.AddSubTitle(u' = %s' % a.strip())
                                if self.currentLine is not None and self.currentLine.boxes:
                                    self.currentLine.boxes[-1].is_tempo_dotted_eighth = True
                            elif self.tempoDisplay == 2:
                                self.AddSubTitle('BPM: %s' % a.strip())
                            elif self.tempoDisplay == 3:
                                self.AddSubTitle(u' = %s' % a.strip())
                                if self.currentLine is not None and self.currentLine.boxes:
                                    self.currentLine.boxes[-1].is_tempo_metro = True
                    elif cmd == 'time':
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '' and self.timeDisplay:
                            self.AddSubTitle(a.strip())
                            if self.currentLine is not None and self.currentLine.boxes:
                                self.currentLine.boxes[-1].is_time_sig = True
                    elif cmd == 'key':
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '' and self.keyDisplay:
                            self.AddSubTitle(_(u'Key: %s') % a.strip())
                    elif cmd == 'capo':
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            self.AddSubTitle(_(u'Capo: %s') % a.strip())
                    elif cmd == 'artist':
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            self.AddSubTitle(a.strip())
                    elif cmd == 'composer':
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            self.AddSubTitle(a.strip())
                    elif cmd == 'lyricist':
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            self.AddSubTitle(_(u'Lyrics: %s') % a.strip())
                    elif cmd == 'arranger':
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            self.AddSubTitle(_(u'Arrangement: %s') % a.strip())
                    elif cmd == 'album':
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            self.AddSubTitle(_(u'Album: %s') % a.strip())
                    elif cmd == 'year':
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            self.AddSubTitle(a.strip())
                    elif cmd == 'copyright':
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            self.AddSubTitle(_(u'© %s') % a.strip())
                    elif cmd == 'verse':
                        self.BeginVerse(self.GetAttribute())
                    elif cmd == 'textsize':
                        try:
                            a = self.GetAttribute()
                            if a is None:
                                size = self.starting_sf.size
                            else:
                                a = a.strip()
                                try:
                                    if a.endswith("%"):
                                        perc = int(a[:-1])
                                        size = self.format.size * perc / 100
                                    else:
                                        size = int(a)
                                except TypeError:
                                    raise BreakException()
                                except ValueError:
                                    raise BreakException()
                            self.format = ParagraphFormat(self.format)
                            self.format.size = size
                            self.sf.size = size
                            self.sf.chorus.size = size
                            self.sf.title.size = size
                            self.sf.subtitle.size = size
                        except BreakException:
                            pass
                    elif cmd == 'textfont':
                        try:
                            face = self.GetAttribute()
                            if face is None:
                                face = self.starting_sf.face
                            else:
                                face = face.strip()
                            self.format = ParagraphFormat(self.format)
                            self.format.face = face
                            self.sf.face = face
                            self.sf.chorus.face = face
                            self.sf.title.face = face
                            self.sf.subtitle.face = face
                        except BreakException:
                            pass
                    elif cmd == 'textcolour':
                        try:
                            color = self.GetAttribute()
                            if color is None:
                                color = self.starting_sf.color
                            else:
                                color = color.strip()
                            self.format = ParagraphFormat(self.format)
                            self.format.color = color
                            self.sf.color = color
                            self.sf.chorus.color = color
                            self.sf.title.color = color
                            self.sf.subtitle.color = color
                        except BreakException:
                            pass
                    elif cmd == 'chordsize':
                        try:
                            a = self.GetAttribute()
                            if a is None:
                                size = self.starting_sf.chord.size
                            else:
                                a = a.strip()
                                try:
                                    if a.endswith("%"):
                                        perc = int(a[:-1])
                                        size = self.format.chord.size * perc / 100
                                    else:
                                        size = int(a)
                                except TypeError:
                                    raise BreakException()
                                except ValueError:
                                    raise BreakException()
                            self.format = ParagraphFormat(self.format)
                            self.format.chord.size = size
                            self.sf.chord.size = size
                            self.sf.chorus.chord.size = size
                        except BreakException:
                            pass
                    elif cmd == 'chordfont':
                        try:
                            face = self.GetAttribute()
                            if face is None:
                                face = self.starting_sf.chord.face
                            else:
                                face = face.strip()
                            self.format = ParagraphFormat(self.format)
                            self.format.chord.face = face
                            self.sf.chord.face = face
                            self.sf.chorus.chord.face = face
                        except BreakException:
                            pass
                    elif cmd == 'chordcolour':
                        try:
                            color = self.GetAttribute()
                            if color is None:
                                color = self.starting_sf.chord.color
                            else:
                                color = color.strip()
                            self.format = ParagraphFormat(self.format)
                            self.format.chord.color = color
                            self.sf.chord.color = color
                            self.sf.chorus.chord.color = color
                        except BreakException:
                            pass
                    elif cmd == 'chordtopspacing':
                        try:
                            a = self.GetAttribute()
                            if a is None:
                                spacing = self.starting_sf.chordTopSpacing
                            else:
                                a = a.strip()
                                try:
                                    spacing = int(a)
                                except (TypeError, ValueError):
                                    raise BreakException()
                            self.format = ParagraphFormat(self.format)
                            self.format.chordTopSpacing = spacing
                            self.sf.chordTopSpacing = spacing
                            self.sf.chorus.chordTopSpacing = spacing
                            for v in self.sf.verse:
                                v.chordTopSpacing = spacing
                        except BreakException:
                            pass
                    elif cmd == 'linespacing':
                        try:
                            a = self.GetAttribute()
                            if a is None:
                                spacing = self.starting_sf.lineSpacing
                            else:
                                a = a.strip()
                                try:
                                    spacing = int(a)
                                except (TypeError, ValueError):
                                    raise BreakException()
                            self.format = ParagraphFormat(self.format)
                            self.format.lineSpacing = spacing
                            self.sf.lineSpacing = spacing
                            self.sf.chorus.lineSpacing = spacing
                            for v in self.sf.verse:
                                v.lineSpacing = spacing
                        except BreakException:
                            pass
                    elif cmd == 'taste':
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            self.song.klavier_list.append(a.strip())
                    elif cmd == 'define':
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            self.song.define_list.append(a.strip())
                    elif cmd == 'fingering':
                        # Diteggiatura del primo accordo con numeri dita.
                        # Formato: {fingering: Am 1=Do 2=Mi 3=La}
                        # La stringa intera (accordo + mappa dita) va in klavier_list:
                        # il KlavierRenderer aggiornato la parsa e disegna i numeri.
                        a = self.GetAttribute()
                        if a is not None and a.strip() != '':
                            self.song.klavier_list.append(a.strip())
                    elif cmd == 'image':
                        a = self.GetAttribute()
                        if a is not None and a.strip():
                            box = self._ParseImageDirective(a.strip())
                            if box is not None:
                                self.EndBlock()
                                self.song.AddBox(box)
                    elif cmd == 'beats_time':
                        # Direttiva custom: {beats_time: DO=4 SOL=2 LA-=2 ...}
                        # Associa il numero di battiti a ciascun accordo della riga successiva.
                        a = self.GetAttribute()
                        if a is not None and a.strip():
                            dur = []
                            for token in a.strip().split():
                                if '=' in token:
                                    chord, _sep, beats = token.partition('=')
                                    try:
                                        dur.append((chord.strip().upper(), int(beats.strip())))
                                    except ValueError:
                                        pass
                            self._pending_duration = dur
                            self._duration_chord_idx = 0

            self.EndLine()
            if empty:
                if state in {SongBlock.verse, SongBlock.title}:
                    self.EndBlock()
                elif state == SongBlock.chorus:
                    self.ChorusVSkip()
        self.EndBlock()
        self._next_page_break = False  # ignora {new_page} finale senza blocco successivo
        self._next_column_break = False  # ignora {column_break} finale senza blocco successivo
        # Propaga la notazione rilevata al decorator per KlavierRenderer
        if hasattr(self.sd, 'notation'):
            self.sd.notation = self.notations
        # Propaga la dimensione icone tempo al decorator
        self.sd.tempoIconSize = getattr(self, 'tempoIconSize', None)
        w, h = self.sd.Draw(self.song, dc)
        self.dc = None
        # Raccoglie le posizioni Y (in pixel schermo) dei page break espliciti
        # (usato solo per debug/anteprima; la stampa usa _split_on_new_page)
        self.page_break_ys = []
        for block in self.song.boxes:
            if getattr(block, 'pageBreakBefore', False):
                by = self.song.marginTop + block.y
                self.page_break_ys.append(by)
        return w, h

    def SetDecorator(self, sd):
        self.sd = sd

    def SetChordsBelow(self, below):
        self.chordsBelow = below

    def _ParseImageDirective(self, arg):
        """Parsa l'argomento di {image: ...} e restituisce una SongImageBox o None.

        Formato atteso (spec ChordPro):
            filename.png [width=N] [height=N] [scale=N] [align=left|center|right] [border[=N]]

        Il filename e' il primo token prima delle opzioni key=value.
        """
        import shlex
        import os

        # Su Windows shlex.split in modalità posix interpreta i backslash
        # come escape, spezzando i percorsi. Usiamo posix=False e poi
        # rimuoviamo manualmente le virgolette esterne se presenti.
        try:
            lex = shlex.shlex(arg, posix=False)
            lex.whitespace_split = True
            lex.whitespace = ' \t'
            raw_parts = list(lex)
        except ValueError:
            raw_parts = arg.split()

        # Rimuovi virgolette esterne da ogni token (shlex posix=False le lascia)
        def _strip_quotes(s):
            if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
                return s[1:-1]
            return s

        parts = [_strip_quotes(p) for p in raw_parts]

        if not parts:
            return None

        path = parts[0]

        # Immagine embedded (data: URI base64): non serve risolvere il percorso.
        # Il campo path viene passato direttamente a SongImageBox, che lo decodifica
        # in un file temporaneo tramite resolve_path() al momento del rendering.
        if not path.startswith('data:'):
            # Risolvi il percorso rispetto alla directory del documento aperto, se disponibile
            if not os.path.isabs(path) and hasattr(self, '_document_dir') and self._document_dir:
                candidate = os.path.join(self._document_dir, path)
                if os.path.isfile(candidate):
                    path = candidate

        width = 0
        height = 0
        scale = 1.0
        align = 'center'
        border = 0

        for p in parts[1:]:
            if '=' in p:
                key, _, val = p.partition('=')
                key = key.strip().lower()
                has_percent = '%' in val
                val = val.strip().rstrip('%')
                try:
                    if key == 'width':
                        width = float(val)
                    elif key == 'height':
                        height = float(val)
                    elif key == 'scale':
                        v = float(val)
                        if has_percent:
                            v /= 100.0
                        scale = v
                    elif key == 'align':
                        if val.strip() in ('left', 'center', 'right'):
                            align = val.strip()
                    elif key == 'border':
                        border = float(val) if val else 1.0
                except (ValueError, TypeError):
                    pass
            else:
                p_low = p.lower()
                if p_low == 'center':
                    align = 'center'
                elif p_low == 'left':
                    align = 'left'
                elif p_low == 'right':
                    align = 'right'
                elif p_low == 'border':
                    border = 1.0

        return SongImageBox(path, width, height, scale, align, border)
