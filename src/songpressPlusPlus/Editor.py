###############################################################
# Name:             Editor.py
# Purpose:     Subclass of StyledTextCtrl providing songpress
#            editor: loading, saving and syntax hilighting
# Author:         Luca Allulli (webmaster@roma21.it)
# Modified by:  Denisov21
# Created:     2009-01-16
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
#               Modifications copyright Denisov21
# License:     GNU GPL v2
##############################################################

# Crea ContexMenu e icone!


import codecs

from wx.stc import *
import wx.lib, wx.lib.newevent

from .SDIMainFrame import *
from .SongTokenizer import *
from . import Transpose
from .utils import undo_action

_ = wx.GetTranslation

EventTextChanged, EVT_TEXT_CHANGED = wx.lib.newevent.NewEvent()


def get_text_from_clipboard():
    """
    Return text in clipboard, or None
    """
    if wx.TheClipboard.IsOpened():
        return None
    wx.TheClipboard.Open()
    do = wx.TextDataObject()
    if not wx.TheClipboard.GetData(do):
        return None
    wx.TheClipboard.Close()
    return do.GetText()


class Editor(StyledTextCtrl):
    def __init__(self, spframe, interactive=True, frame=None):
        self.frame = spframe.frame if frame is None else frame
        StyledTextCtrl.__init__(self, self.frame)
        self.spframe = spframe
        self.interactive = interactive
        if self.interactive:
            self.lastPos = 0
            self.frame.Bind(EVT_STC_CHANGE, self.OnTextChange, self)
            self.frame.Bind(EVT_STC_UPDATEUI, self.OnUpdateUI, self)
            self.Bind(EVT_STC_DOUBLECLICK, self.OnDoubleClick, self)
            self.Bind(wx.EVT_CHAR, self.OnChar, self)
            # self.Bind(EVT_STC_CLIPBOARD_COPY, self.frame.OnCopy, self)
            self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu, self)
            self.UsePopUp(0)  # disabilita il menu nativo di Scintilla
            self.autoChangeMode = False
            self._multi_cursor_enabled = False
            self.Bind(wx.EVT_LEFT_DOWN, self.OnEditorLeftDown)
            self.Bind(wx.EVT_KEY_DOWN, self.OnEditorKeyDown)
        self.frame.Bind(EVT_STC_STYLENEEDED, self.OnStyleNeeded, self)
        self.STC_STYLE_NORMAL = 11
        self.STC_STYLE_CHORD = 12
        self.STC_STYLE_COMMAND = 13
        self.STC_STYLE_ATTR = 14
        self.STC_STYLE_CHORUS = 15
        self.STC_STYLE_COMMENT = 16
        self.STC_STYLE_TAB_GRID = 17
        # UTF-8: necessario per visualizzare correttamente i caratteri multibyte (simboli musicali SMP)
        self.SetCodePage(STC_CP_UTF8)
        # DirectWrite abilita il font-fallback automatico sui glifi SMP (U+1D100 ecc.) su Windows.
        # Su altri OS viene ignorato silenziosamente.
        try:
            self.SetTechnology(STC_TECHNOLOGY_DIRECTWRITE)
        except AttributeError:
            pass  # costante non disponibile in versioni vecchie di wxPython
        self.SetFont("Lucida Console", 12)
        self.SetLexer(STC_LEX_CONTAINER)
        self.StyleSetForeground(self.STC_STYLE_NORMAL, wx.Colour(0, 0, 0))
        self.StyleSetForeground(self.STC_STYLE_CHORUS, wx.Colour(0, 0, 0))
        self.StyleSetForeground(self.STC_STYLE_CHORD, wx.Colour(255, 0, 0))
        self.StyleSetForeground(self.STC_STYLE_COMMAND, wx.Colour(0, 0, 255))
        self.StyleSetForeground(self.STC_STYLE_ATTR, wx.Colour(0, 128, 0))
        self.StyleSetForeground(self.STC_STYLE_COMMENT, wx.Colour(128, 128, 128))
        self.StyleSetForeground(self.STC_STYLE_TAB_GRID, wx.Colour(139, 90, 0))
        self.StyleSetItalic(self.STC_STYLE_TAB_GRID, True)
        self.StyleSetBold(self.STC_STYLE_CHORUS, True)
        #Dummy "token": we artificially replace every normalToken into a chorusToken when we are
        #inside chorus.  Then, we can associate the chorus style in self.tokenStyle dictionary.
        self.chorusToken = 'chorusToken'
        # Dummy token for content inside {start_of_tab}/{start_of_grid} blocks.
        self.tabGridToken = 'tabGridToken'
        self.tokenStyle = {
            SongTokenizer.openCurlyToken: self.STC_STYLE_COMMAND,
            SongTokenizer.closeCurlyToken: self.STC_STYLE_COMMAND,
            SongTokenizer.normalToken: self.STC_STYLE_NORMAL,
            SongTokenizer.commandToken: self.STC_STYLE_COMMAND,
            SongTokenizer.attrToken: self.STC_STYLE_ATTR,
            SongTokenizer.chordToken: self.STC_STYLE_CHORD,
            SongTokenizer.closeChordToken: self.STC_STYLE_CHORD,
            SongTokenizer.colonToken: self.STC_STYLE_COMMAND,
            SongTokenizer.commentToken: self.STC_STYLE_COMMENT,
            self.chorusToken: self.STC_STYLE_CHORUS,
            self.tabGridToken: self.STC_STYLE_TAB_GRID,
        }
        #self.chorus[i] == True iff, at the end of line i, we are still in chorus (i.e. bold) mode
        self.chorus = []
        # self.in_tab_grid[i] == True iff, at the end of line i, we are inside a tab/grid block
        self.in_tab_grid = []

    def SetFont(self, face, size):
        font = wx.Font(
            size,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL,
            faceName = face
        )
        self.StyleSetFont(STC_STYLE_DEFAULT, font)
        #I don't know why, but the following line is necessary in order to make
        #the font bold
        self.StyleSetFont(self.STC_STYLE_CHORUS, font)
        self.StyleSetFont(self.STC_STYLE_TAB_GRID, font)
        # Riapplica il colore di selezione dopo ogni cambio di stile
        sel_hex = getattr(getattr(self, 'spframe', None), 'pref', None)
        if sel_hex is not None:
            sel_hex = getattr(sel_hex, 'selColourHex', None)
        if sel_hex:
            self.SetSelColour(sel_hex)

    def SetBgColour(self, hex_str):
        """Imposta il colore di sfondo dell'editor su tutti gli stili STC."""
        try:
            h = hex_str.strip().lstrip('#')
            c = wx.Colour(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)) if len(h) == 6 else wx.Colour(255, 255, 255)
        except Exception:
            c = wx.Colour(255, 255, 255)

        # 1. Sfondo wx nativo del controllo (aree non coperte da testo)
        self.SetBackgroundColour(c)

        # 2. STC_STYLE_DEFAULT (32) — stile base
        self.StyleSetBackground(STC_STYLE_DEFAULT, c)

        # 3. Tutti gli stili custom (11-16) + stili STC di sistema
        for style_id in (
            0,
            self.STC_STYLE_NORMAL,
            self.STC_STYLE_CHORD,
            self.STC_STYLE_COMMAND,
            self.STC_STYLE_ATTR,
            self.STC_STYLE_CHORUS,
            self.STC_STYLE_COMMENT,
            self.STC_STYLE_TAB_GRID,
            STC_STYLE_LINENUMBER,
            STC_STYLE_BRACELIGHT,
            STC_STYLE_BRACEBAD,
            STC_STYLE_CONTROLCHAR,
            STC_STYLE_INDENTGUIDE,
        ):
            self.StyleSetBackground(style_id, c)

        # 4. Forza il ridisegno completo
        self.Colourise(0, -1)
        self.Refresh()

    def SetSelColour(self, hex_str):
        """Imposta il colore di sfondo della selezione del testo."""
        try:
            h = hex_str.strip().lstrip('#')
            c = wx.Colour(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)) if len(h) == 6 else wx.Colour(51, 153, 255)
        except Exception:
            c = wx.Colour(51, 153, 255)
        self.SetSelBackground(True, c)
        # Calcola luminosità per scegliere automaticamente bianco o nero come colore testo
        luminance = 0.299 * c.Red() + 0.587 * c.Green() + 0.114 * c.Blue()
        fg = wx.Colour(0, 0, 0) if luminance > 128 else wx.Colour(255, 255, 255)
        self.SetSelForeground(True, fg)

    def SetSyntaxColour(self, style_id, hex_str):
        """Imposta il colore foreground di uno stile STC tramite hex string."""
        try:
            h = hex_str.strip().lstrip('#')
            c = wx.Colour(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)) if len(h) == 6 else wx.Colour(0, 0, 0)
        except Exception:
            c = wx.Colour(0, 0, 0)
        self.StyleSetForeground(style_id, c)
        self.Colourise(0, -1)
        self.Refresh()

    # --- Find highlight (indicatore STC n. 8, sfondo giallo) ---------------

    FIND_INDICATOR = 8
    # Colore evidenziazione trova — modificabile dall'utente (default giallo)
    find_highlight_colour = wx.Colour(255, 220, 0)

    def SetFindHighlight(self, word, flags=0):
        """Evidenzia tutte le occorrenze di *word* con il colore scelto dall'utente."""
        self.ClearFindHighlight()
        if not word:
            return
        self.IndicatorSetStyle(self.FIND_INDICATOR, wx.stc.STC_INDIC_ROUNDBOX)
        self.IndicatorSetForeground(self.FIND_INDICATOR, self.find_highlight_colour)
        self.IndicatorSetAlpha(self.FIND_INDICATOR, 80)
        self.IndicatorSetOutlineAlpha(self.FIND_INDICATOR, 200)
        self.IndicatorSetUnder(self.FIND_INDICATOR, True)
        self.SetIndicatorCurrent(self.FIND_INDICATOR)
        total = self.GetLength()
        p = 0
        while True:
            result = self.FindText(p, total, word, flags)
            pos = result[0] if isinstance(result, tuple) else result
            if pos == -1:
                break
            # len in bytes UTF-8 per IndicatorFillRange
            byte_len = len(word.encode('utf-8'))
            self.IndicatorFillRange(pos, byte_len)
            p = pos + max(1, byte_len)

    def ClearFindHighlight(self):
        """Rimuove tutte le evidenziazioni del trova."""
        self.SetIndicatorCurrent(self.FIND_INDICATOR)
        self.IndicatorClearRange(0, self.GetLength())

    def SetFindHighlightColour(self, colour):
        """Aggiorna il colore e ridisegna tutte le occorrenze già evidenziate."""
        self.find_highlight_colour = colour
        # Aggiorna lo stile dell'indicatore
        self.IndicatorSetStyle(self.FIND_INDICATOR, wx.stc.STC_INDIC_ROUNDBOX)
        self.IndicatorSetForeground(self.FIND_INDICATOR, colour)
        self.IndicatorSetAlpha(self.FIND_INDICATOR, 80)
        self.IndicatorSetOutlineAlpha(self.FIND_INDICATOR, 200)
        self.IndicatorSetUnder(self.FIND_INDICATOR, True)
        # Scintilla non aggiorna i fill esistenti al cambio colore:
        # bisogna cancellare e riscrivere gli indicatori già presenti.
        # Troviamo tutte le posizioni con indicatore attivo e le rifacciamo.
        self.SetIndicatorCurrent(self.FIND_INDICATOR)
        total = self.GetLength()
        pos = 0
        while pos < total:
            # Salta le posizioni senza indicatore
            if not (self.IndicatorValueAt(self.FIND_INDICATOR, pos)):
                pos = self.IndicatorEnd(self.FIND_INDICATOR, pos)
                if pos <= 0:
                    break
                continue
            # Trovato inizio di un run con indicatore attivo
            start = pos
            end   = self.IndicatorEnd(self.FIND_INDICATOR, pos)
            if end <= start:
                break
            # Cancella e riscrive lo stesso range con il nuovo colore
            self.IndicatorClearRange(start, end - start)
            self.IndicatorFillRange(start,  end - start)
            pos = end

    # -----------------------------------------------------------------------

    # --- Duration dots (indicatore STC n. 9) --------------------------------
    # Mostra puntini nell'editor tra accordi con {duration} quando la modalità
    # è 'dots' o 'both'. I puntini sono applicati sul testo normale tra ] e [.

    DOTS_INDICATOR = 9

    def SetDurationDots(self, text, mode):
        """Aggiorna i puntini di durata nell'editor.

        *text*: testo completo del documento.
        *mode*: 'number' (nessun punto), 'dots' o 'both'.
        """
        self.ClearDurationDots()
        if mode not in ('dots', 'both'):
            return
        self.IndicatorSetStyle(self.DOTS_INDICATOR, wx.stc.STC_INDIC_DOTS)
        self.IndicatorSetForeground(self.DOTS_INDICATOR, wx.Colour(100, 100, 200))
        self.IndicatorSetUnder(self.DOTS_INDICATOR, True)
        self.SetIndicatorCurrent(self.DOTS_INDICATOR)
        import re as _re
        # Cerca righe con accordi precedute da {duration: ...}
        lines = text.splitlines(keepends=True)
        byte_offset = 0
        duration_pending = False
        duration_map = {}   # accordo_idx -> battiti sulla prossima riga
        for line in lines:
            stripped = line.strip()
            # Direttiva {duration: ...}
            if stripped.lower().startswith('{duration:') and stripped.endswith('}'):
                duration_pending = True
                byte_offset += len(line.encode('utf-8'))
                continue
            if duration_pending:
                duration_pending = False
                # Trova tutti gli accordi [X] nella riga e il testo tra essi
                # Disegna i puntini sul testo normale tra ] e il prossimo [
                tokens = list(_re.finditer(r'\[([^\]]+)\]', line))
                for i, m in enumerate(tokens):
                    chord_end_byte = byte_offset + len(line[:m.end()].encode('utf-8'))
                    if i + 1 < len(tokens):
                        next_start_byte = byte_offset + len(line[:tokens[i+1].start()].encode('utf-8'))
                        span = next_start_byte - chord_end_byte
                        if span > 0:
                            self.IndicatorFillRange(chord_end_byte, span)
            byte_offset += len(line.encode('utf-8'))

    def ClearDurationDots(self):
        """Rimuove i puntini di durata dall'editor."""
        self.SetIndicatorCurrent(self.DOTS_INDICATOR)
        self.IndicatorClearRange(0, self.GetLength())

    # -----------------------------------------------------------------------

    def New(self):
        self.ClearAll()

    def Open(self):
        self.ClearAll()
        self.LoadFile(self.spframe.document)

    def Save(self):
        #self.SaveFile(self.spframe.document)
        t = self.GetText()
        f = codecs.open(self.spframe.document, 'w', 'utf-8')
        f.write(t)
        f.close()

    def GetTextOrSelection(self):
        start, end = self.GetSelection()
        if start == end:
            return self.GetText()
        return self.GetSelectedText()

    def ReplaceTextOrSelection(self, text):
        start, end = self.GetSelection()
        if start == end:
            self.SetText(text)
        else:
            self.ReplaceSelection(text)

    def GetChordUnderCursor(self, position=None):
        """Return info about chord under cursor, or None

        If `position` is specified, use it instead of the cursor position.

        Return a 3-tuple: (begin, end, chord)
            begin: position before open bracket
            end: position after close bracket
            chord: chord, without brackets
        """
        if position is None:
            pos, dummy = self.GetSelection()
        else:
            pos = position
        char = ""
        if position is None and self.GetSelectedText().find('[') != -1:
            start = pos
            while char != '[':
                next = self.PositionAfter(start)
                char = self.GetTextRange(start, next)
                start = next
            start = self.PositionBefore(start)
        else:
            start = self.PositionBefore(pos)
            while start >= 0 and char != '[' and char != '\n' and char != ']':
                char = self.GetTextRange(start, self.PositionAfter(start))
                if start == 0:
                    start = -1
                else:
                    start = self.PositionBefore(start)
            if start >= 0:
                start = self.PositionAfter(start)
            else:
                start = 0
        if char == '[':
            end = self.PositionBefore(pos)
            l = self.GetLength()
            while end < l and char != ']' and char != '\n':
                char = self.GetTextRange(end, self.PositionAfter(end))
                end = self.PositionAfter(end)
            if char == ']':
                return (start, end, self.GetTextRange(self.PositionAfter(start), self.PositionBefore(end)))
        return None

    def SelectNextChord(self):
        dummy, pos = self.GetSelection()
        n = self.GetLength()
        c = ''
        while pos < n:
            while pos < n and c != '[':
                c = self.GetTextRange(pos, self.PositionAfter(pos))
                pos = self.PositionAfter(pos)
            if c == '[':
                start = pos
                while pos < n and c != ']' and c != '\n':
                    c = self.GetTextRange(pos, self.PositionAfter(pos))
                    pos = self.PositionAfter(pos)
                if c == ']':
                    self.SetSelection(self.PositionBefore(start), pos)
                    return True
        return False

    def SelectPreviousChord(self):
        pos, dummy = self.GetSelection()
        c = ''
        done = False
        while not done:
            while not done and c != ']':
                c = self.GetTextRange(pos, self.PositionAfter(pos))
                if pos <= 0:
                    done = True
                else:
                    pos = self.PositionBefore(pos)
            if c == ']':
                end = pos
                while not done and c != '[' and c != '\n':
                    c = self.GetTextRange(pos, self.PositionAfter(pos))
                    if pos <= 0:
                        pos = -1
                        done = True
                    else:
                        pos = self.PositionBefore(pos)
                if pos == -1:
                    pos = 0
                else:
                    pos = self.PositionAfter(pos)
                if c == '[':
                    self.SetSelection(pos, self.PositionAfter(self.PositionAfter(end)))
                    return True
        return False

    def RemoveChordsInSelection(self):
        self.ReplaceSelection(Transpose.removeChords(self.GetSelectedText()))
        
    def CopyOnlyText(self):
        text = Transpose.removeChordPro(self.GetSelectedText())
        c = wx.TheClipboard
        if c.Open():
            c.SetData(wx.TextDataObject(text))
            c.Close()

    def OnTextChange(self, evt):
        if self.interactive:
            self.spframe.SetModified()
            self.spframe.TextUpdated()
            if not self.autoChangeMode:
                currentPos = self.GetCurrentPos()
                if currentPos - self.lastPos > 2:
                    evt = EventTextChanged(lastPos=self.lastPos, currentPos=currentPos)
                    wx.PostEvent(self.frame, evt)

    def OnUpdateUI(self, evt):
        self.lastPos = self.GetCurrentPos()
        evt.Skip(False)

    def OnDoubleClick(self, evt):
        t = self.GetChordUnderCursor()
        if t is not None:
            self.SetSelection(t[0], t[1])
        evt.Skip()

    def OnChar(self, evt):
        t = self.GetSelectedText()
        if t != '' and t[0] == '[' and t[-1] == ']':
            c = evt.GetKeyCode()
            if (c >= 65 and c <= 90) or (c >= 97 and c <= 122):
                s, e = self.GetSelection()
                self.SetSelection(self.PositionAfter(s), self.PositionBefore(e))

        evt.Skip()

    def AutoChangeMode(self, acm):
        self.autoChangeMode = acm
        
    def PasteChords(self):
        src = get_text_from_clipboard()
        if src is None:
            return
        with undo_action(self):
            start, end = self.GetSelection()
            if start == end:
                l = self.LineFromPosition(start)
                end = self.PositionFromLine(l + len(src.splitlines()))
                if end == -1:
                    end = self.GetLength()
                else:
                    end = self.PositionBefore(end)
            prev = self.PositionBefore(end)
            while end > start and self.GetCharAt(prev) in [10, 13]:
                end = prev
                prev = self.PositionBefore(end)
            self.SetSelection(start, end)
            sel = self.GetSelectedText()
            if sel == "":
                sel = " "
            self.ReplaceSelection(Transpose.pasteChords(src, sel))

    def ApplyMultiCursor(self, enabled):
        """Abilita o disabilita il multicursore. Chiamare dopo ogni cambio preferenza."""
        self._multi_cursor_enabled = enabled
        self.SetMultipleSelection(enabled)
        self.SetAdditionalSelectionTyping(enabled)
        self.SetMultiPaste(STC_MULTIPASTE_EACH if enabled else STC_MULTIPASTE_ONCE)
        self.SetAdditionalCaretsVisible(enabled)

    def OnEditorLeftDown(self, evt):
        if self._multi_cursor_enabled and evt.AltDown():
            pos = self.PositionFromPoint(evt.GetPosition())
            if pos != STC_INVALID_POSITION:
                self.AddSelection(pos, pos)
            # Non propagare: il click nativo resetterebbe le selezioni
            return
        if self._multi_cursor_enabled and self.GetSelections() > 1:
            # Click normale: resetta a selezione singola sul cursore principale
            caret = self.GetSelectionNCaret(self.GetMainSelection())
            anchor = self.GetSelectionNAnchor(self.GetMainSelection())
            self.SetSelection(anchor, caret)
        evt.Skip()

    def OnEditorKeyDown(self, evt):
        # Spazio dentro {start_of_grid} → inserisce pipe e sposta il cursore nella cella vuota.
        # Intercettato in KEY_DOWN (prima che STC scriva il carattere).
        if evt.GetKeyCode() == wx.WXK_SPACE and not evt.ControlDown() and not evt.AltDown():
            pref = getattr(self.spframe, 'pref', None)
            space_as_pipe = getattr(pref, 'gridSpaceAsPipe', True)
            if space_as_pipe and self.spframe._GetGridContext() is not None:
                self.spframe._MoveGridCellRight()
                return   # non propagare: lo spazio non deve essere inserito nell'STC

        if (self._multi_cursor_enabled
                and evt.ControlDown()
                and not evt.AltDown()
                and evt.GetKeyCode() == ord('D')):
            self._SelectNextOccurrence()
            return
        evt.Skip()

    def _SelectNextOccurrence(self):
        """Aggiunge una selezione sulla prossima occorrenza del testo selezionato (Ctrl+D)."""
        n = self.GetSelections()
        idx = self.GetMainSelection()
        s = self.GetSelectionNStart(idx)
        e = self.GetSelectionNEnd(idx)
        if s == e:
            return
        word = self.GetTextRange(s, e)
        last_e = max(self.GetSelectionNEnd(i) for i in range(n))
        found = self.FindText(last_e, self.GetLength(), word, 0)[0]
        if found == -1:
            found = self.FindText(0, s, word, 0)[0]
        if found != -1:
            self.AddSelection(found + len(word), found)
            self.SetMainSelection(self.GetSelections() - 1)

    def OnContextMenu(self, evt):
        menu = wx.Menu()

        def add_item(label, handler, art_id=None, png_path=None, enabled=True):
            item = wx.MenuItem(menu, wx.ID_ANY, label)
            bmp = wx.NullBitmap
            if png_path:
                b = wx.Bitmap(png_path, wx.BITMAP_TYPE_PNG)
                if b.IsOk():
                    bmp = b
            elif art_id is not None:
                b = wx.ArtProvider.GetBitmap(art_id, wx.ART_MENU, (16, 16))
                if b.IsOk():
                    bmp = b
            if bmp.IsOk():
                item.SetBitmap(bmp)
            menu.Append(item)
            item.Enable(enabled)
            menu.Bind(wx.EVT_MENU, handler, item)

        import os
        _img_dir = os.path.join(os.path.dirname(__file__), 'img')
        img = lambda name: os.path.join(_img_dir, name)

        # Recupera le preferenze di visibilità (default True se non presenti)
        pref = getattr(self.spframe, 'pref', None)
        def cm_pref(name):
            if pref is None:
                return True
            return getattr(pref, name, True)

        has_selection = self.GetSelectedText() != ''
        can_paste = wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT))
        can_undo = self.CanUndo()
        can_redo = self.CanRedo()

        # --- Gruppo Cronologia ---
        show_undo = cm_pref('cmUndo')
        show_redo = cm_pref('cmRedo')
        if show_undo:
            add_item(_("&Undo"), lambda e: self.Undo(), png_path=img('undo.png'), enabled=can_undo)
        if show_redo:
            add_item(_("&Redo"), lambda e: self.Redo(), png_path=img('redo.png'), enabled=can_redo)
        if show_undo or show_redo:
            menu.AppendSeparator()

        # --- Gruppo Modifica ---
        show_cut    = cm_pref('cmCut')
        show_copy   = cm_pref('cmCopy')
        show_paste  = cm_pref('cmPaste')
        show_delete = cm_pref('cmDelete')
        if show_cut:
            add_item(_("Cu&t"),    lambda e: self.Cut(),                png_path=img('cut.png'),    enabled=has_selection)
        if show_copy:
            add_item(_("&Copy"),   lambda e: self.Copy(),               png_path=img('copy.png'),   enabled=has_selection)
        if show_paste:
            add_item(_("&Paste"),  lambda e: self.Paste(),              png_path=img('paste.png'),  enabled=can_paste)
        if show_delete:
            def _do_delete(e):
                if cm_pref('cmConfirmDelete'):
                    if wx.MessageBox(
                        _("Delete the selected text?"),
                        _("Songpress++"),
                        wx.YES_NO | wx.ICON_QUESTION
                    ) != wx.YES:
                        return
                self.ReplaceSelection('')
            add_item(_("&Delete"), _do_delete, png_path=img('delete.png'), enabled=has_selection)
        if show_cut or show_copy or show_paste or show_delete:
            menu.AppendSeparator()

        # --- Gruppo Azioni speciali ---
        show_paste_chords         = cm_pref('cmPasteChords')
        show_copy_text_only       = cm_pref('cmCopyTextOnly')
        show_propagate_verse      = cm_pref('cmPropagateVerseChords')
        show_propagate_chorus     = cm_pref('cmPropagateChorusChords')
        if show_paste_chords:
            add_item(_("Paste &chords"),            lambda e: self.PasteChords(),                              png_path=img('pasteChords.png'), enabled=can_paste)
        if show_propagate_verse:
            add_item(_("Propagate &verse chords"),  lambda e: self.spframe.OnPropagateVerseChords(e))
        if show_propagate_chorus:
            add_item(_("Propagate c&horus chords"), lambda e: self.spframe.OnPropagateChorusChords(e))
        if show_copy_text_only:
            add_item(_("Copy &text only"),          lambda e: self.CopyOnlyText(),                             png_path=img('copy.png'),        enabled=has_selection)
        if show_paste_chords or show_copy_text_only or show_propagate_verse or show_propagate_chorus:
            menu.AppendSeparator()

        # --- Gruppo Selezione ---
        if cm_pref('cmSelectAll'):
            add_item(_("Select &all"), lambda e: self.SelectAll(), png_path=img('selectAll.png'))

        # Rimuove eventuali separatori finali ridondanti
        count = menu.GetMenuItemCount()
        if count > 0:
            last = menu.FindItemByPosition(count - 1)
            if last and last.IsSeparator():
                menu.Remove(last)

        if menu.GetMenuItemCount() > 0:
            self.PopupMenu(menu)
        menu.Destroy()

    def OnStyleNeeded(self, evt):
        end = evt.GetPosition()
        pos = self.GetEndStyled()
        ln = self.LineFromPosition(pos)
        start = self.PositionFromLine(ln)
        if ln > 0 and len(self.chorus) > ln-1:
            bold = self.chorus[ln-1]
        else:
            bold = False
        if ln > 0 and len(self.in_tab_grid) > ln-1:
            in_tg = self.in_tab_grid[ln-1]
        else:
            in_tg = False
        #changedBold is True iff self.chorus has changed for the current line, and thus we need
        #to process (at least) another line
        changedBold = False
        lc = self.GetLineCount()

        # Comandi di apertura/chiusura blocchi tab e grid (tutte le varianti ChordPro)
        _SOT = frozenset(['SOT', 'START_OF_TAB'])
        _EOT = frozenset(['EOT', 'END_OF_TAB'])
        _SOG = frozenset(['SOG', 'START_OF_GRID', 'GRID'])
        _EOG = frozenset(['EOG', 'END_OF_GRID'])

        while (changedBold and ln < lc) or start < end:
            self.StartStyling(start)
            l = self.GetLine(ln)
            tkz = SongTokenizer(l)
            for tok in tkz:
                n = len(tok.content.encode('utf-8'))
                t = tok.token
                if in_tg and t == SongTokenizer.normalToken:
                    t = self.tabGridToken
                elif bold and t == SongTokenizer.normalToken:
                    t = self.chorusToken
                self.SetStyling(n, self.tokenStyle[t])
                if t == SongTokenizer.commandToken:
                    cmd = tok.content.upper()
                    if cmd == 'SOC' or cmd == 'START_OF_CHORUS':
                        bold = True
                    elif cmd == 'EOC' or cmd == 'END_OF_CHORUS':
                        bold = False
                    elif cmd in _SOT or cmd in _SOG:
                        in_tg = True
                    elif cmd in _EOT or cmd in _EOG:
                        in_tg = False
            if len(self.chorus) > ln:
                changedBold = self.chorus[ln] != bold
                self.chorus[ln] = bold
            else:
                self.chorus.append(bold)
                changedBold = False
            if len(self.in_tab_grid) > ln:
                if self.in_tab_grid[ln] != in_tg:
                    changedBold = True
                self.in_tab_grid[ln] = in_tg
            else:
                self.in_tab_grid.append(in_tg)
            ln = ln + 1
            start = self.PositionFromLine(ln)


