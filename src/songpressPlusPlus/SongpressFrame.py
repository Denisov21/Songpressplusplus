###############################################################
# Name:             SongpressFrame.py
# Purpose:     Main frame for Songpress++
# Author:         Luca Allulli (webmaster@roma21.it)
# Modified by:  Denisov21
# Created:     2009-01-16
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
# Copyright: Modifications © 2026 Denisov21
# License:     GNU GPL v2
##############################################################

##############################################################
#Note: wx.FontDialog è un wrapper del dialog nativo di Windows, e SetTitle()
#potrebbe non funzionare su tutte le versioni di wxPython/Windows
#perché il titolo viene gestito dal sistema. 
#Però funziona bene Windows 11 e wxFormBuilder 4.2.1!
###############################################################


import subprocess
import sys
import os
import os.path
import platform

# import wx.aui as aui
import wx.adv
from wx import xrc

from .Editor import *
from .PreviewCanvas import *
from .Renderer import *
from .FontComboBox import FontComboBox
from .FontFaceDialog import FontFaceDialog
from .MyPreferencesDialog import MyPreferencesDialog
from .HTML import HtmlExporter, TabExporter
from . import PdfExporter
from . import SongbookExporter
from .MyTransposeDialog import *
from .MyNotationDialog import *
from .MyNormalizeDialog import *
from .MyListDialog import MyListDialog
from .Globals import glb
from .Preferences import Preferences
from . import i18n
from .utils import temp_dir, undo_action
from .SyntaxChecker import check as syntax_check
from .SyntaxCheckerDialog import SyntaxCheckerDialog, EVT_SYNTAX_GOTO
from .MusicalSymbolDialog import MusicalSymbolDialog
from . import KlavierRenderer

_ = wx.GetTranslation


if platform.system() == 'Windows':
    import wx.msw


class SongpressFindReplaceDialog(object):
    """Dialogo Trova/Sostituisci unificato con due tab (Trova e Sostituisci)."""

    def __init__(self, owner, replace=False):
        object.__init__(self)
        self.owner = owner
        self.replace = replace

        self.dialog = wx.Dialog(
            owner.frame, title=_(u"Find / Replace"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP
        )

        init_find = self.owner.text.GetSelectedText() or ''

        outer = wx.BoxSizer(wx.VERTICAL)

        # ── Notebook ──────────────────────────────────────────────────
        self.notebook = wx.Notebook(self.dialog)

        # ── Tab 1: Trova ──────────────────────────────────────────────
        pg_find = wx.Panel(self.notebook)
        sz_find = wx.BoxSizer(wx.VERTICAL)

        row_f = wx.BoxSizer(wx.HORIZONTAL)
        row_f.Add(wx.StaticText(pg_find, label=_(u"Find:")),
                  0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        self.txtFind = wx.ComboBox(pg_find, value=init_find,
                                   size=(240, -1), style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)
        row_f.Add(self.txtFind, 1, wx.EXPAND)
        sz_find.Add(row_f, 0, wx.EXPAND | wx.ALL, 8)

        mid_f = wx.BoxSizer(wx.HORIZONTAL)
        opts_f = wx.BoxSizer(wx.VERTICAL)
        self.cbWholeWord = wx.CheckBox(pg_find, label=_(u"Whole words only"))
        self.cbMatchCase = wx.CheckBox(pg_find, label=_(u"Match case"))
        self.cbRegex     = wx.CheckBox(pg_find, label=_(u"Regular expressions"))
        opts_f.Add(self.cbWholeWord, 0, wx.BOTTOM, 4)
        opts_f.Add(self.cbMatchCase, 0, wx.BOTTOM, 4)
        opts_f.Add(self.cbRegex,    0)
        mid_f.Add(opts_f, 0, wx.RIGHT, 20)
        dir_box = wx.StaticBoxSizer(
            wx.StaticBox(pg_find, label=_(u"Direction")), wx.HORIZONTAL)
        self.rbUp   = wx.RadioButton(pg_find, label=_(u"Up"), style=wx.RB_GROUP)
        self.rbDown = wx.RadioButton(pg_find, label=_(u"Down"))
        self.rbDown.SetValue(True)
        dir_box.Add(self.rbUp,   0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        dir_box.Add(self.rbDown, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        mid_f.Add(dir_box, 0)
        sz_find.Add(mid_f, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        pg_find.SetSizer(sz_find)
        self.notebook.AddPage(pg_find, _(u"Find"))

        # ── Tab 2: Sostituisci ────────────────────────────────────────
        pg_repl = wx.Panel(self.notebook)
        sz_repl = wx.BoxSizer(wx.VERTICAL)
        lbl_w = 110

        row_rf = wx.BoxSizer(wx.HORIZONTAL)
        row_rf.Add(wx.StaticText(pg_repl, label=_(u"Find:"),
                   size=(lbl_w, -1)), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        self.txtFindR = wx.ComboBox(pg_repl, value=init_find,
                                    size=(240, -1), style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)
        row_rf.Add(self.txtFindR, 1, wx.EXPAND)
        sz_repl.Add(row_rf, 0, wx.EXPAND | wx.ALL, 8)

        row_rr = wx.BoxSizer(wx.HORIZONTAL)
        row_rr.Add(wx.StaticText(pg_repl, label=_(u"Replace with:"),
                   size=(lbl_w, -1)), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        self.txtReplace = wx.ComboBox(pg_repl, size=(240, -1),
                                      style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)
        row_rr.Add(self.txtReplace, 1, wx.EXPAND)
        sz_repl.Add(row_rr, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        mid_r = wx.BoxSizer(wx.HORIZONTAL)
        opts_r = wx.BoxSizer(wx.VERTICAL)
        self.cbWholeWordR  = wx.CheckBox(pg_repl, label=_(u"Whole words only"))
        self.cbMatchCaseR  = wx.CheckBox(pg_repl, label=_(u"Match case"))
        self.cbRegexR      = wx.CheckBox(pg_repl, label=_(u"Regular expressions"))
        self.cbWrapAround  = wx.CheckBox(pg_repl, label=_(u"Silent wrap-around"))
        opts_r.Add(self.cbWholeWordR,  0, wx.BOTTOM, 4)
        opts_r.Add(self.cbMatchCaseR,  0, wx.BOTTOM, 4)
        opts_r.Add(self.cbRegexR,      0, wx.BOTTOM, 4)
        opts_r.Add(self.cbWrapAround,  0)
        mid_r.Add(opts_r, 0, wx.RIGHT, 20)
        dir_box_r = wx.StaticBoxSizer(
            wx.StaticBox(pg_repl, label=_(u"Direction")), wx.HORIZONTAL)
        self.rbUpR   = wx.RadioButton(pg_repl, label=_(u"Up"),   style=wx.RB_GROUP)
        self.rbDownR = wx.RadioButton(pg_repl, label=_(u"Down"))
        self.rbDownR.SetValue(True)
        dir_box_r.Add(self.rbUpR,   0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        dir_box_r.Add(self.rbDownR, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        mid_r.Add(dir_box_r, 0, wx.ALIGN_TOP)
        sz_repl.Add(mid_r, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        pg_repl.SetSizer(sz_repl)
        self.notebook.AddPage(pg_repl, _(u"Replace"))

        # ── Bottoni colonna verticale a destra ───────────────────────
        self.btnFindNext   = wx.Button(self.dialog, label=_(u"Find next"))
        self.btnReplace    = wx.Button(self.dialog, label=_(u"Replace"))
        self.btnReplaceAll = wx.Button(self.dialog, label=_(u"Replace all"))
        self.btnCount      = wx.Button(self.dialog, label=_(u"Count matches"))
        self.btnCancel     = wx.Button(self.dialog, wx.ID_ANY, _(u"Close"))
        self.btnFindNext.SetDefault()

        btn_col = wx.BoxSizer(wx.VERTICAL)
        btn_col.Add(self.btnFindNext,   0, wx.EXPAND | wx.BOTTOM, 4)
        btn_col.Add(self.btnReplace,    0, wx.EXPAND | wx.BOTTOM, 4)
        btn_col.Add(self.btnReplaceAll, 0, wx.EXPAND | wx.BOTTOM, 4)
        btn_col.Add(self.btnCount,      0, wx.EXPAND | wx.BOTTOM, 4)
        btn_col.AddStretchSpacer()
        btn_col.Add(self.btnCancel,     0, wx.EXPAND)

        # ── Notebook + bottoni affiancati ────────────────────────────
        nb_and_btns = wx.BoxSizer(wx.HORIZONTAL)

        # Notebook con etichetta count sotto
        left_col = wx.BoxSizer(wx.VERTICAL)
        left_col.Add(self.notebook, 1, wx.EXPAND)
        self.lblCount = wx.StaticText(self.dialog, label=u"")
        self.lblCount.SetForegroundColour(wx.Colour(0, 100, 180))
        left_col.Add(self.lblCount, 0, wx.LEFT | wx.TOP, 4)

        nb_and_btns.Add(left_col,  1, wx.EXPAND | wx.ALL, 6)
        nb_and_btns.Add(btn_col,   0, wx.EXPAND | wx.TOP | wx.RIGHT | wx.BOTTOM, 8)

        outer.Add(nb_and_btns, 1, wx.EXPAND)

        # ── Riga inferiore: scope evidenziazione + colore ─────────────
        bottom_row = wx.BoxSizer(wx.HORIZONTAL)

        # Radio: solo editor / editor + preview
        hl_scope_box = wx.StaticBoxSizer(
            wx.StaticBox(self.dialog, label=_(u"Highlight")), wx.HORIZONTAL)
        self.rbHlEditor  = wx.RadioButton(self.dialog,
                                          label=_(u"Editor only"),
                                          style=wx.RB_GROUP)
        self.rbHlBoth    = wx.RadioButton(self.dialog,
                                          label=_(u"Editor + Preview"))
        self.rbHlBoth.SetValue(True)
        hl_scope_box.Add(self.rbHlEditor, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        hl_scope_box.Add(self.rbHlBoth,   0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        bottom_row.Add(hl_scope_box, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)

        # Colore evidenziazione: pulsante Pick + Default + swatch
        hl_col_box = wx.StaticBoxSizer(
            wx.StaticBox(self.dialog, label=_(u"Highlight colour")), wx.HORIZONTAL)
        self.btnHlColour   = wx.Button(self.dialog, label=_(u"Pick\u2026"))
        self.btnHlDefault  = wx.Button(self.dialog, label=_(u"Default"))
        self._hl_colour  = self._load_find_colour()
        self.swatchHl    = wx.Panel(self.dialog, size=(24, 24),
                                    style=wx.BORDER_SIMPLE)
        self.swatchHl.SetBackgroundColour(self._hl_colour)
        hl_col_box.Add(self.btnHlColour,  0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        hl_col_box.Add(self.btnHlDefault, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        hl_col_box.Add(self.swatchHl,     0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        bottom_row.Add(hl_col_box, 0, wx.ALIGN_CENTER_VERTICAL)

        outer.Add(bottom_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.dialog.SetSizerAndFit(outer)
        self.dialog.CentreOnParent()

        # Seleziona la tab giusta
        self.notebook.SetSelection(1 if replace else 0)
        self._UpdateButtons()

        # ── Bind ─────────────────────────────────────────────────────
        self.btnFindNext.Bind(wx.EVT_BUTTON,    self._OnFindNext)
        self.btnReplace.Bind(wx.EVT_BUTTON,     self._OnReplace)
        self.btnReplaceAll.Bind(wx.EVT_BUTTON,  self._OnReplaceAll)
        self.btnCount.Bind(wx.EVT_BUTTON,       self._OnCount)
        self.btnCancel.Bind(wx.EVT_BUTTON,      self._OnCancel)
        self.txtFind.Bind(wx.EVT_TEXT_ENTER,    self._OnFindNext)
        self.txtFind.Bind(wx.EVT_TEXT,          self._OnFindTextChanged)
        self.txtFind.Bind(wx.EVT_TEXT,          self._SyncFindText)
        self.txtFindR.Bind(wx.EVT_TEXT_ENTER,   self._OnFindNext)
        self.txtFindR.Bind(wx.EVT_TEXT,         self._OnFindTextChanged)
        self.txtFindR.Bind(wx.EVT_TEXT,         self._SyncFindTextR)
        self.txtReplace.Bind(wx.EVT_TEXT_ENTER, self._OnReplace)
        self.cbWholeWord.Bind(wx.EVT_CHECKBOX,  self._SyncCheckboxes)
        self.cbMatchCase.Bind(wx.EVT_CHECKBOX,  self._SyncCheckboxes)
        self.cbRegex.Bind(wx.EVT_CHECKBOX,      self._SyncCheckboxes)
        self.cbWholeWordR.Bind(wx.EVT_CHECKBOX, self._SyncCheckboxes)
        self.cbMatchCaseR.Bind(wx.EVT_CHECKBOX, self._SyncCheckboxes)
        self.cbRegexR.Bind(wx.EVT_CHECKBOX,     self._SyncCheckboxes)
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._OnTabChanged)
        self.dialog.Bind(wx.EVT_CLOSE,      self._OnClose)
        self.dialog.Bind(wx.EVT_CHAR_HOOK,  self._OnCharHook)
        self.btnHlColour.Bind(wx.EVT_BUTTON,  self._OnPickHlColour)
        self.btnHlDefault.Bind(wx.EVT_BUTTON, self._OnDefaultHlColour)

        # Applica il colore caricato subito all'apertura
        self._apply_hl_colour(self._hl_colour)

        self.dialog.Show()
        self._FocusFindField()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _IsReplaceTab(self):
        return self.notebook.GetSelection() == 1

    def _ActiveFindCtrl(self):
        return self.txtFindR if self._IsReplaceTab() else self.txtFind

    def _FocusFindField(self):
        ctrl = self._ActiveFindCtrl()
        ctrl.SetFocus()
        ctrl.SetInsertionPointEnd()

    def _UpdateButtons(self):
        on_replace = self._IsReplaceTab()
        self.btnReplace.Show(on_replace)
        self.btnReplaceAll.Show(on_replace)
        self.dialog.Layout()
        self.dialog.Fit()

    def _SyncCheckboxes(self, evt):
        if getattr(self, '_syncing', False):
            evt.Skip()
            return
        self._syncing = True
        try:
            src = evt.GetEventObject()
            v = src.GetValue()
            if src in (self.cbWholeWord, self.cbWholeWordR):
                self.cbWholeWord.SetValue(v)
                self.cbWholeWordR.SetValue(v)
            elif src in (self.cbMatchCase, self.cbMatchCaseR):
                self.cbMatchCase.SetValue(v)
                self.cbMatchCaseR.SetValue(v)
            elif src in (self.cbRegex, self.cbRegexR):
                self.cbRegex.SetValue(v)
                self.cbRegexR.SetValue(v)
        finally:
            self._syncing = False
        evt.Skip()

    def _SyncFindText(self, evt):
        v = self.txtFind.GetValue()
        if self.txtFindR.GetValue() != v:
            self.txtFindR.ChangeValue(v)
        evt.Skip()

    def _SyncFindTextR(self, evt):
        v = self.txtFindR.GetValue()
        if self.txtFind.GetValue() != v:
            self.txtFind.ChangeValue(v)
        evt.Skip()

    def _OnTabChanged(self, evt):
        self._UpdateButtons()
        wx.CallAfter(self._FocusFindField)
        evt.Skip()

    def _OnFindTextChanged(self, evt):
        self.lblCount.SetLabel(u"")
        evt.Skip()

    def _OnCharHook(self, evt):
        if evt.GetKeyCode() == wx.WXK_ESCAPE:
            self._OnCancel(evt)
        else:
            evt.Skip()

    def _get_flags(self):
        flags = 0
        if self.cbWholeWord.GetValue():
            flags |= wx.stc.STC_FIND_WHOLEWORD
        if self.cbMatchCase.GetValue():
            flags |= wx.stc.STC_FIND_MATCHCASE
        if self.cbRegex.GetValue():
            flags |= wx.stc.STC_FIND_REGEXP
        return flags

    def _get_down(self):
        if self._IsReplaceTab():
            return self.rbDownR.GetValue()
        return self.rbDown.GetValue()

    _MAX_HISTORY = 10

    def _AddToHistory(self, combo, value):
        """Aggiunge value allo storico del ComboBox (max 10, senza duplicati)."""
        if not value:
            return
        items = list(combo.GetItems())
        if value in items:
            items.remove(value)
        items.insert(0, value)
        items = items[:self._MAX_HISTORY]
        combo.SetItems(items)
        combo.SetValue(value)

    # ------------------------------------------------------------------
    # Azioni
    # ------------------------------------------------------------------

    def _OnFindNext(self, evt, silent_wrap=False):
        st = self._ActiveFindCtrl().GetValue()
        if not st:
            return
        flags = self._get_flags()
        down  = self._get_down()
        self.owner._lastFindSt    = st
        self.owner._lastFindFlags = flags
        self.owner._lastFindDown  = down
        self._AddToHistory(self.txtFind,  st)
        self._AddToHistory(self.txtFindR, st)
        text = self.owner.text
        if down:
            s, e = text.GetSelection()
            text.SetSelection(e, e)
            from_start = s == 0
            text.SearchAnchor()
            p = text.SearchNext(flags, st)
        else:
            s, e = text.GetSelection()
            text.SetSelection(s, s)
            from_start = s == text.GetLength()
            text.SearchAnchor()
            p = text.SearchPrev(flags, st)
        if p != -1:
            text.SetSelection(p, p + len(st))
            self.lblCount.SetLabel(u"")
            self.lblCount.SetForegroundColour(wx.Colour(0, 100, 180))
            # Evidenzia nell'editor sempre; nel preview solo se rbHlBoth è attivo
            self.owner.text.SetFindHighlight(st, flags)
            if self.rbHlBoth.GetValue():
                self.owner.previewCanvas.SetFindWord(st, flags)
            else:
                self.owner.previewCanvas.ClearFindWord()
        else:
            if not from_start:
                if down:
                    wherefrom, where, newStart = _(u"Reached the end"), _(u"beginning"), 0
                else:
                    wherefrom, where, newStart = _(u"Reached the beginning"), _(u"end"), text.GetLength()
                wrap_msg = _(u"%s of the song, restarting search from the %s") % (wherefrom, where)
                do_wrap = silent_wrap or self.cbWrapAround.GetValue()
                if do_wrap:
                    text.SetSelection(newStart, newStart)
                    self._OnFindNext(evt, silent_wrap=True)
                else:
                    d = wx.MessageDialog(
                        self.dialog,
                        wrap_msg,
                        self.owner.appName, wx.OK | wx.CANCEL | wx.ICON_INFORMATION
                    )
                    if d.ShowModal() == wx.ID_OK:
                        text.SetSelection(newStart, newStart)
                        self._OnFindNext(evt, silent_wrap=True)
            else:
                # Messaggio inline invece di MessageDialog modale
                self.lblCount.SetLabel(_(u"The specified text was not found"))
                self.lblCount.SetForegroundColour(wx.Colour(180, 0, 0))
                self.dialog.Layout()
                self.dialog.Fit()


    def _OnCount(self, evt):
        st = self._ActiveFindCtrl().GetValue()
        if not st:
            self.lblCount.SetLabel(u"")
            return
        flags = self._get_flags()
        text  = self.owner.text
        total = text.GetLength()
        count = 0
        p = 0
        while True:
            result = text.FindText(p, total, st, flags)
            pos = result[0] if isinstance(result, tuple) else result
            if pos == -1:
                break
            count += 1
            p = pos + max(1, len(st))
        msg = _(u"%d match found") % count if count == 1 else _(u"%d matches found") % count
        self.lblCount.SetLabel(msg)
        self.dialog.Layout()
        self.dialog.Fit()

    def _OnReplace(self, evt):
        st = self.txtFindR.GetValue()
        r  = self.txtReplace.GetValue()
        if not st:
            return
        self._AddToHistory(self.txtFindR,  st)
        self._AddToHistory(self.txtFind,   st)
        self._AddToHistory(self.txtReplace, r)
        flags = self._get_flags()
        text  = self.owner.text
        if text.GetSelectedText() == st or (
                not (flags & wx.stc.STC_FIND_MATCHCASE) and
                text.GetSelectedText().lower() == st.lower()):
            text.ReplaceSelection(r)
        self._OnFindNext(evt, silent_wrap=True)

    def _OnReplaceAll(self, evt):
        st = self.txtFindR.GetValue()
        r  = self.txtReplace.GetValue()
        if not st:
            return
        self._AddToHistory(self.txtFindR,   st)
        self._AddToHistory(self.txtFind,    st)
        self._AddToHistory(self.txtReplace, r)
        flags = self._get_flags()
        text  = self.owner.text
        with undo_action(text):
            text.SetSelection(0, 0)
            c = 0
            p = 0
            while True:
                result = text.FindText(p, text.GetLength(), st, flags)
                pos = result[0] if isinstance(result, tuple) else result
                if pos == -1:
                    break
                text.SetTargetStart(pos)
                text.SetTargetEnd(pos + len(st))
                p = pos + text.ReplaceTarget(r)
                c += 1
        wx.MessageDialog(
            self.dialog,
            _(u"%d text occurrences have been replaced") % (c,),
            self.owner.appName, wx.OK | wx.ICON_INFORMATION
        ).ShowModal()

    def _OnCancel(self, evt):
        if self.dialog is not None:
            self.dialog.Destroy()
            self.dialog = None
        self.owner.findReplaceDialog = None

    def _OnClose(self, evt):
        # Rimuove le evidenziazioni da editor e preview alla chiusura del dialogo
        try:
            self.owner.text.ClearFindHighlight()
            self.owner.previewCanvas.ClearFindWord()
        except Exception:
            pass
        self.dialog = None
        self.owner.findReplaceDialog = None
        evt.Skip()

    # --- Colore evidenziazione: load / save / pick -------------------------

    _DEFAULT_HL_HEX = '#FFDC00'   # giallo default

    def _load_find_colour(self):
        """Legge il colore salvato in wx.Config; restituisce wx.Colour."""
        try:
            cfg = wx.Config.Get()
            cfg.SetPath('/FindHighlight')
            h = cfg.Read('colourHex')
            cfg.SetPath('/')
            if h:
                h = h.strip().lstrip('#')
                if len(h) == 6:
                    return wx.Colour(int(h[0:2], 16),
                                     int(h[2:4], 16),
                                     int(h[4:6], 16))
        except Exception:
            pass
        h = self._DEFAULT_HL_HEX.lstrip('#')
        return wx.Colour(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    def _save_find_colour(self, colour):
        """Salva il colore in wx.Config."""
        try:
            cfg = wx.Config.Get()
            cfg.SetPath('/FindHighlight')
            cfg.Write('colourHex', '#%02X%02X%02X' % (
                colour.Red(), colour.Green(), colour.Blue()))
            cfg.SetPath('/')
            cfg.Flush()
        except Exception:
            pass

    def _apply_hl_colour(self, colour):
        """Propaga il colore all'editor e al preview decorator."""
        try:
            self.owner.text.SetFindHighlightColour(colour)
        except Exception:
            pass
        try:
            self.owner.previewCanvas.SetFindHighlightColour(colour)
        except Exception:
            pass

    def _OnPickHlColour(self, evt):
        """Apre wx.ColourDialog per scegliere il colore di evidenziazione."""
        data = wx.ColourData()
        data.SetColour(self._hl_colour)
        data.SetChooseFull(True)
        dlg = wx.ColourDialog(self.dialog, data)
        if dlg.ShowModal() == wx.ID_OK:
            chosen = dlg.GetColourData().GetColour()
            self._hl_colour = chosen
            self.swatchHl.SetBackgroundColour(chosen)
            self.swatchHl.Refresh()
            self._apply_hl_colour(chosen)
            self._save_find_colour(chosen)
            # Riapplica l'highlight con il nuovo colore se c'è una parola cercata
            st    = self._ActiveFindCtrl().GetValue()
            flags = self._get_flags()
            if st:
                self.owner.text.SetFindHighlight(st, flags)
                if self.rbHlBoth.GetValue():
                    self.owner.previewCanvas.SetFindWord(st, flags, colour=chosen)
        dlg.Destroy()

    def _OnDefaultHlColour(self, evt):
        """Ripristina il colore di evidenziazione al default (#FFDC00)."""
        h = self._DEFAULT_HL_HEX.lstrip('#')
        default = wx.Colour(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        self._hl_colour = default
        self.swatchHl.SetBackgroundColour(default)
        self.swatchHl.Refresh()
        self._apply_hl_colour(default)
        self._save_find_colour(default)
        st    = self._ActiveFindCtrl().GetValue()
        flags = self._get_flags()
        if st:
            self.owner.text.SetFindHighlight(st, flags)
            if self.rbHlBoth.GetValue():
                self.owner.previewCanvas.SetFindWord(st, flags, colour=default)

    # -----------------------------------------------------------------------

    def OnClose(self, evt):
        if self.dialog:
            self.dialog.Destroy()
            self.dialog = None



if platform.system() == 'Linux':
    # Apparently there is a problem with linux FileOpen dialog box in wxPython:
    # it does not support multiple extensions in a filter.
    _import_formats = [
        (_("All supported files"), ["crd", "cho", "chordpro", "chopro", "tab", "cpm"]),
        #(_("Chordpro files (*.crd)"), ["crd"]),
        #(_("Tab files (*.tab)"), ["tab"]),
        #(_("Chordpro files (*.cho)"), ["cho"]),
        #(_("Chordpro files (*.chordpro)"), ["chordpro"]),
        #(_("Chordpro files (*.chopro)"), ["chopro"]),
        #(_("Chordpro files (*.pro)"), ["pro"]),
    ]
else:
    _import_formats = [
        (_("All supported files"), ["crd", "cho", "chordpro", "chopro", "pro", "tab"]),
        (_("Chordpro files (*.crd, *.cho, *.chordpro, *.chopro, *.pro)"), ["crd", "cho", "chordpro", "chopro", "pro"]),
        (_("Tab files (*.tab)"), ["tab"]),
    ]


class SongpressPrintout(wx.Printout):
    """
    Printout class for Songpress++.

    Supports explicit page breaks via the {new_page} command:
    the text is split into segments, each printed on one or more pages.
    Within each segment, the content scrolls automatically if
    it exceeds the page height.
    """

    _SCREEN_PPI = 96

    def __init__(self, frame_obj, title="Song", two_pages_per_sheet=False):
        wx.Printout.__init__(self, title)
        self.frame_obj = frame_obj
        self.two_pages_per_sheet = two_pages_per_sheet
        self._page_offsets  = None   # list of (segment_idx, y_offset_px)
        self._segments      = None   # list of text strings (split on {new_page})
        self._scale_x       = None
        self._scale_y       = None
        self._margin_du     = None
        self._usable_w_du   = None
        self._song_info     = None   # (full_song, line_start, line_end)
        self._col_h_px      = 0     # altezza colonna di testo in px schermo (0 = illimitata)
        # Contatori strofe iniziali per ogni segmento {new_page}: seg_idx -> (verseCount, labelCount, chorusCount)
        self._seg_verse_start = {}
        # Used only in two_pages_per_sheet mode
        self._col_w_du      = None
        self._gap_du        = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _mm_to_du(self, mm, ppi):
        return int(mm * ppi / 25.4)

    @staticmethod
    def _split_on_new_page(text):
        """
        Splits the text on {new_page} or {np} commands (case-insensitive).
        Returns a list of text segments (at least one).
        Le righe commentate con '#' (es. # {new_page}) vengono ignorate:
        i comandi in esse contenuti non producono divisioni di pagina.
        """
        import re
        cmd_pat     = re.compile(r'\{\s*(?:new_page|np)\s*\}', re.IGNORECASE)
        comment_pat = re.compile(r'^\s*#')

        # Raccoglie le posizioni (start, end) dei {new_page} non commentati
        split_positions = []
        offset = 0
        for line in text.splitlines(keepends=True):
            if not comment_pat.match(line):
                for m in cmd_pat.finditer(line):
                    split_positions.append((offset + m.start(), offset + m.end()))
            offset += len(line)

        if not split_positions:
            return [text]

        # Costruisce i segmenti spezzando nelle posizioni trovate
        parts = []
        prev = 0
        for start, end in split_positions:
            parts.append(text[prev:start])
            prev = end
        parts.append(text[prev:])

        result = [p for p in parts if p.strip()] or [text]
        return result

    def _make_renderer(self):
        decorator = (
            self.frame_obj.pref.decorator
            if self.frame_obj.pref.labelVerses
            else SongDecorator()
        )
        r = Renderer(
            self.frame_obj.pref.format,
            decorator,
            self.frame_obj.pref.notations,
        )
        r.tempoDisplay = getattr(self.frame_obj.pref, 'tempoDisplay', 0)
        r.timeDisplay = getattr(self.frame_obj.pref, 'timeDisplay', True)
        r.keyDisplay = getattr(self.frame_obj.pref, 'keyDisplay', True)
        r.tempoIconSize = getattr(self.frame_obj.pref, 'tempoIconSize', 24)
        r.gridDisplayMode = getattr(self.frame_obj.pref, 'gridDisplayMode', 'pipe')
        r.gridDefaultLabel = getattr(self.frame_obj.pref, 'gridDefaultLabel', None)
        r.gridSizeDir = getattr(self.frame_obj.pref, 'gridSizeDir', 'both')
        r.columns = getattr(self.frame_obj, '_columns_per_page', 1)
        r.columnHeight = getattr(self, '_col_h_px', 0)
        return r

    def _ensure_layout(self, dc):
        if self._page_offsets is not None:
            return

        pw, ph = self.GetPageSizePixels()
        ppi_x, ppi_y = dc.GetPPI()

        ml = self._mm_to_du(self.frame_obj._margin_left,   ppi_x)
        mr = self._mm_to_du(self.frame_obj._margin_right,  ppi_x)
        mt = self._mm_to_du(self.frame_obj._margin_top,    ppi_y)
        mb = self._mm_to_du(self.frame_obj._margin_bottom, ppi_y)
        self._margin_du = (ml, mt, mr, mb)

        columns_per_page = getattr(self.frame_obj, '_columns_per_page', 1)

        if self.two_pages_per_sheet:
            # Split the physical sheet into two equal columns with a small central gap
            gap = self._mm_to_du(5, ppi_x)   # 5 mm gap
            col_w = (pw - ml - mr - gap) // 2
            usable_w = col_w
            usable_h = ph - mt - mb
            self._col_w_du = col_w
            self._gap_du   = gap
        else:
            usable_w = pw - ml - mr
            usable_h = ph - mt - mb

        # Colonne di testo nella singola pagina logica
        if columns_per_page >= 2:
            col_gap_du = self._mm_to_du(8, ppi_x)   # 8 mm tra colonne di testo
            text_col_w = (usable_w - col_gap_du) // 2
            # Altezza colonna = altezza pagina intera (il renderer distribuirà i blocchi)
            self._col_h_px = usable_h / (ppi_y / self._SCREEN_PPI)
            # Per il renderer la larghezza "utile" è quella della singola colonna di testo
            # moltiplicata per il numero di colonne (il renderer le affianca orizzontalmente)
            # La scala orizzontale deve adattarsi alla singola colonna di testo
            usable_w_for_scale = text_col_w
        else:
            self._col_h_px = 0
            usable_w_for_scale = usable_w

        self._usable_w_du = usable_w

        self._scale_x = ppi_x / self._SCREEN_PPI
        self._scale_y = ppi_y / self._SCREEN_PPI

        # Recupera selezione / testo intero
        start, end   = self.frame_obj.text.GetSelection()
        full_song    = (start == end)
        line_start   = self.frame_obj.text.LineFromPosition(start)
        line_end     = self.frame_obj.text.LineFromPosition(end)
        full_text    = SongpressFrame._strip_hash_commands(self.frame_obj.text.GetText())
        
        self._song_info = (full_song, line_start, line_end)

        # Se stiamo stampando una selezione non dividiamo sui {new_page}
        if full_song:
            self._segments = self._split_on_new_page(full_text)
        else:
            self._segments = [full_text]   # la selezione viene gestita in OnPrintPage

        # Misura ciascun segmento con un MemoryDC e calcola gli offsets di pagina
        mdc = wx.MemoryDC(wx.Bitmap(1, 1))
        self._page_offsets = []   # list of (seg_idx, y_px_float)

        verse_count, label_count, chorus_count = 0, 0, 0
        for seg_idx, seg_text in enumerate(self._segments):
            r = self._make_renderer()
            r.initialVerseCount = verse_count
            r.initialLabelCount = label_count
            r.initialChorusCount = chorus_count
            self._seg_verse_start[seg_idx] = (verse_count, label_count, chorus_count)
            if full_song:
                sw, sh = r.Render(seg_text, mdc)
            else:
                sw, sh = r.Render(full_text, mdc, line_start, line_end)
            sw, sh = max(1, sw), max(1, sh)
            verse_count  = r.song.verseCount
            label_count  = r.song.labelCount
            chorus_count = r.song.chorusCount

            # Adjust horizontal scale if necessary (use the most restrictive)
            natural_w = sw * self._scale_x
            if natural_w > usable_w_for_scale:
                fit = usable_w_for_scale / natural_w
                self._scale_x = min(self._scale_x, self._scale_x * fit)
                self._scale_y = min(self._scale_y, self._scale_y * fit)

        # Ricalcola con la scala definitiva
        px_per_page = usable_h / self._scale_y

        # Riduci e adatta alla pagina: se attivo, scala ulteriormente in modo che
        # l'intero contenuto di ciascun segmento entri in una sola pagina (verticalmente).
        if getattr(self.frame_obj, '_fit_to_page', False):
            for seg_idx, seg_text in enumerate(self._segments):
                r = self._make_renderer()
                vc, lc, cc = self._seg_verse_start.get(seg_idx, (0, 0, 0))
                r.initialVerseCount = vc
                r.initialLabelCount = lc
                r.initialChorusCount = cc
                if full_song:
                    sw, sh = r.Render(seg_text, mdc)
                else:
                    sw, sh = r.Render(full_text, mdc, line_start, line_end)
                sh = max(1, sh)
                if sh > px_per_page:
                    fit_v = px_per_page / sh
                    self._scale_x *= fit_v
                    self._scale_y *= fit_v
                    px_per_page = usable_h / self._scale_y  # aggiorna dopo riduzione

        # Shrink to fit current page: evita il taglio del contenuto in fondo pagina.
        #
        # Il problema fondamentale: il renderer disegna il canzone in modo continuo
        # e il clipping di pagina taglia le righe a metà. Non esiste una soglia sicura
        # da controllare sull'ultima pagina — ogni confine di pagina può tagliare.
        #
        # Approccio: ricerca binaria sul fattore di scala (e/o sui margini) per trovare
        # il valore che fa sì che NESSUNA pagina sia "spezzata a metà di riga".
        # Misura l'altezza di una riga singola e verifica che px_per_page sia un multiplo
        # intero dell'altezza di riga — oppure, più robusto, che il contenuto di ogni
        # "fetta" di pagina si fermi a un confine di riga.
        #
        # Poiché il renderer non espone i breakpoint, usiamo l'approccio indiretto:
        # misuriamo l'altezza di una riga rappresentativa e troviamo la scala che
        # fa sì che px_per_page sia il più vicino possibile a N * row_h senza superarlo.
        #
        # Passo 1: usa margini per recuperare spazio (fino al minimo configurabile).
        # Passo 2: riduce la scala se i margini non bastano.
        if getattr(self.frame_obj, '_shrink_to_fit', False):
            import math

            # Misura altezza di una riga rappresentativa (testo + accordo sopra)
            r_probe = self._make_renderer()
            _, row_h = r_probe.Render("[C]x", mdc)
            row_h = max(1, row_h)

            def _best_ppp(ppp):
                """Trovato il numero intero di righe che sta in ppp, restituisce
                il px_per_page ideale = N*row_h <= ppp, con N >= 1."""
                n_rows = max(1, int(math.floor(ppp / row_h)))
                return n_rows * row_h

            def _apply_margins(reduction_du):
                """Applica una riduzione simmetrica ai margini (device units).
                Restituisce il nuovo usable_h e px_per_page."""
                mt_du, mb_du = self._margin_du[1], self._margin_du[3]
                min_margin_mm = float(getattr(self.frame_obj, '_min_margin_shrink', 5))
                min_du = self._mm_to_du(min_margin_mm, ppi_y)
                new_mt = max(min_du, mt_du - math.ceil(reduction_du / 2.0))
                new_mb = max(min_du, mb_du - math.floor(reduction_du / 2.0))
                ml_du, mr_du = self._margin_du[0], self._margin_du[2]
                self._margin_du = (ml_du, new_mt, mr_du, new_mb)
                uh = ph - new_mt - new_mb
                return uh, uh / self._scale_y

            # px_per_page ideale con scala corrente (multiplo di row_h)
            ideal_ppp = _best_ppp(px_per_page)
            gap = px_per_page - ideal_ppp  # spazio "sprecato" tra px_per_page e il multiplo inferiore

            if gap > 0:
                # Quanto gap (in device units) dobbiamo recuperare riducendo usable_h
                # di esattamente gap * scale_y — così px_per_page scende al multiplo.
                gap_du = gap * self._scale_y

                # -- Passo 1: prova a recuperare riducendo i margini top+bottom --
                mt_du, mb_du = self._margin_du[1], self._margin_du[3]
                min_margin_mm = float(getattr(self.frame_obj, '_min_margin_shrink', 5))
                min_du = self._mm_to_du(min_margin_mm, ppi_y)
                reducible_du = float(max(0, (mt_du - min_du) + (mb_du - min_du)))

                if reducible_du >= gap_du:
                    # I margini bastano: riduciamo solo quanto serve per eliminare il gap
                    usable_h, px_per_page = _apply_margins(gap_du)
                    px_per_page = _best_ppp(px_per_page)  # riallinea per sicurezza
                else:
                    # Usiamo tutto il riducibile dai margini
                    if reducible_du > 0:
                        usable_h, px_per_page = _apply_margins(reducible_du)
                        # Dopo la riduzione dei margini, ricalcola il gap residuo
                        ideal_ppp = _best_ppp(px_per_page)
                        gap = px_per_page - ideal_ppp
                        gap_du = gap * self._scale_y

                    # -- Passo 2: riduci la scala per eliminare il gap residuo --
                    # Vogliamo che usable_h / scale_y_new sia un multiplo di row_h.
                    # usable_h / (scale_y * f) = n_rows * row_h
                    # → f = usable_h / (scale_y * n_rows * row_h)
                    # dove n_rows = floor(px_per_page / row_h) — il numero di righe
                    # che già stanno in px_per_page (non aggiungiamo righe, solo allineamo).
                    if gap > 0:
                        n_rows_now = max(1, int(math.floor(px_per_page / row_h)))
                        target_ppp = n_rows_now * row_h  # allinea al multiplo inferiore
                        # f = usable_h / (scale_y * target_ppp)  → scala la riga a target_ppp
                        f = usable_h / (self._scale_y * target_ppp)
                        if f < 1.0:
                            self._scale_x *= f
                            self._scale_y *= f
                            px_per_page = usable_h / self._scale_y
                            px_per_page = _best_ppp(px_per_page)  # verifica finale

        for seg_idx, seg_text in enumerate(self._segments):
            r = self._make_renderer()
            vc, lc, cc = self._seg_verse_start.get(seg_idx, (0, 0, 0))
            r.initialVerseCount = vc
            r.initialLabelCount = lc
            r.initialChorusCount = cc
            if full_song:
                sw, sh = r.Render(seg_text, mdc)
            else:
                sw, sh = r.Render(full_text, mdc, line_start, line_end)
            sw, sh = max(1, sw), max(1, sh)

            # Skip blank/empty segments when _remove_blank_pages is active
            if getattr(self.frame_obj, '_remove_blank_pages', False) and sh <= 2:
                continue

            # Scan the segment height page by page
            y = 0.0
            while y < sh:
                self._page_offsets.append((seg_idx, y))
                y += px_per_page

        if not self._page_offsets:
            self._page_offsets = [(0, 0.0)]

    # ------------------------------------------------------------------
    # wx.Printout interface
    # ------------------------------------------------------------------

    def _n_sheets(self):
        """
        Restituisce il numero di fogli fisici da stampare.
        Forza il calcolo del layout se non ancora eseguito, ottenendo il DC
        dal framework wx (necessario per conoscere PPI e dimensioni foglio).
        Se il DC non è ancora disponibile, usa 1 come valore provvisorio sicuro:
        wx chiamerà nuovamente GetPageInfo dopo OnPreparePrinting, quindi il
        valore definitivo verrà restituito in quella seconda chiamata.
        """
        import math
        if self._page_offsets is None:
            dc = self.GetDC()
            if dc and dc.IsOk():
                self._ensure_layout(dc)
        n_logical = len(self._page_offsets) if self._page_offsets else 1
        if self.two_pages_per_sheet:
            return max(1, math.ceil(n_logical / 2))
        return max(1, n_logical)

    def GetPageInfo(self):
        """
        In 2-pages-per-sheet mode, we return the number of physical sheets
        (each sheet contains 2 logical pages).
        """
        n = self._n_sheets()
        return 1, n, 1, n

    def HasPage(self, page):
        return 1 <= page <= self._n_sheets()

    def OnPreparePrinting(self):
        dc = self.GetDC()
        if dc:
            self._ensure_layout(dc)

    def _render_logical_page(self, dc, logical_page_idx, origin_x, origin_y):
        """
        Renderizza la pagina logica `logical_page_idx` (0-based) posizionandola
        a (origin_x, origin_y) nel DC fisico.
        """
        if logical_page_idx >= len(self._page_offsets):
            return

        seg_idx, y_offset_px = self._page_offsets[logical_page_idx]
        ml, mt, mr, mb = self._margin_du
        usable_h_du = self.GetPageSizePixels()[1] - mt - mb
        full_song, line_start, line_end = self._song_info

        if full_song:
            seg_text = self._segments[seg_idx]
        else:
            seg_text = SongpressFrame._strip_hash_commands(self.frame_obj.text.GetText())

        dc.SetClippingRegion(origin_x, origin_y, self._usable_w_du, usable_h_du)
        dc.SetDeviceOrigin(origin_x, origin_y - int(y_offset_px * self._scale_y))
        dc.SetUserScale(self._scale_x, self._scale_y)

        r = self._make_renderer()
        vc, lc, cc = self._seg_verse_start.get(seg_idx, (0, 0, 0))
        r.initialVerseCount = vc
        r.initialLabelCount = lc
        r.initialChorusCount = cc
        if full_song:
            r.Render(seg_text, dc)
        else:
            r.Render(seg_text, dc, line_start, line_end)

        dc.SetUserScale(1.0, 1.0)
        dc.SetDeviceOrigin(0, 0)
        dc.DestroyClippingRegion()

    def OnPrintPage(self, page):
        dc = self.GetDC()
        self._ensure_layout(dc)

        ml, mt, mr, mb = self._margin_du
        pw, ph = self.GetPageSizePixels()

        if self.two_pages_per_sheet:
            # page is 1-based; each physical sheet contains 2 logical pages
            left_idx  = (page - 1) * 2      # pagina logica sinistra (0-based)
            right_idx = left_idx + 1         # pagina logica destra  (0-based)

            # Se la pagina logica destra non esiste (es. contenuto su 1 sola pagina),
            # la seconda metà del foglio mostra la stessa pagina sinistra (copia),
            # a meno che _no_mirror_right sia attivo: in quel caso lascia bianco.
            n_logical = len(self._page_offsets)
            no_mirror = getattr(self.frame_obj, '_no_mirror_right', False)
            if right_idx >= n_logical:
                if no_mirror:
                    right_idx = None   # lascia bianca la metà destra
                else:
                    right_idx = left_idx   # replica la stessa pagina logica

            left_x  = ml
            right_x = ml + self._col_w_du + self._gap_du

            # Linea divisoria verticale centrale (tratteggiata, grigia)
            center_x = ml + self._col_w_du + self._gap_du // 2
            dc.SetPen(wx.Pen(wx.Colour(180, 180, 180), 1, wx.PENSTYLE_DOT))
            dc.DrawLine(center_x, mt, center_x, ph - mb)
            dc.SetPen(wx.NullPen)

            self._render_logical_page(dc, left_idx,  left_x,  mt)
            if right_idx is not None:
                self._render_logical_page(dc, right_idx, right_x, mt)

        else:
            page_idx = page - 1
            if page_idx >= len(self._page_offsets):
                return False
            self._render_logical_page(dc, page_idx, ml, mt)

        return True


class SongpressFrame(SDIMainFrame):
    def __init__(self, res):
        SDIMainFrame.__init__(
            self,
            res,
            'MainFrame',
            'Songpress++',
            'Skeed',
            _('song'),
            'crd',
            _('Songpress++ - The Song Editor'),
            glb.AddPath('img/songpress++.ico'),
            glb.VERSION,
            _("Original version website: http://www.skeed.it/songpress"),
            (_(u"Copyright (c) 2009-{year} Luca Allulli - Skeed\nLocalization:\n{translations}\n\nSongpress++ is a fork of Songpress by Luca Allulli - Skeed\n(http://www.skeed.it/songpress), maintained and extended by Denisov21.\n(https://github.com/Denisov21/Songpressplusplus)")).format(
                year=glb.YEAR,
                translations="\n".join([u"- {}: {}".format(glb.languages[x], glb.translators[x]) for x in glb.languages])
            ),
            _("Licensed under the terms and conditions of the GNU General Public License, version 2"),
            _(
                "Special thanks to:\n  * The Pyhton programming language (http://www.python.org)\n  * wxWidgets (http://www.wxwidgets.org)\n  * wxPython (http://www.wxpython.org)\n  * Editra (http://editra.org/) (for the error reporting dialog and... the editor itself!)\n  * python-pptx (for PowerPoint export)"),
            _import_formats,
        )
        self.pref = Preferences()
        if not hasattr(self.pref, 'tempoDisplay'):
            self.pref.tempoDisplay = 0
        if not hasattr(self.pref, 'timeDisplay'):
            self.pref.timeDisplay = True
        if not hasattr(self.pref, 'keyDisplay'):
            self.pref.keyDisplay = True
        if not hasattr(self.pref, 'tempoIconSize'):
            self.pref.tempoIconSize = 24
        if not hasattr(self.pref, 'klavierHighlightHex'):
            self.pref.klavierHighlightHex = '#D23C3C'
        self.SetDefaultExtension(self.pref.defaultExtension)
        self.statusBar = self.frame.GetStatusBar()
        self._statusTimer = wx.Timer(self.frame)
        self.frame.Bind(wx.EVT_TIMER, self._OnStatusTimerExpired, self._statusTimer)
        # Workaround: wx.lib.agw.aui framemanager crashes with a wxAssertionError
        # in BufferedDC when the frame is resized to zero (e.g. minimised).
        # Skip the event before AUI can attempt to repaint with invalid dimensions.
        def _OnFrameSize(evt):
            w, h = evt.GetSize()
            if w > 0 and h > 0:
                evt.Skip()
        self.frame.Bind(wx.EVT_SIZE, _OnFrameSize)
        self.text = Editor(self)
        dt = SDIDropTarget(self)
        self.text.SetDropTarget(dt)
        self.frame.Bind(wx.stc.EVT_STC_UPDATEUI, self.OnUpdateUI, self.text)
        self.text.Bind(wx.EVT_KEY_DOWN, self.OnTextKeyDown, self.text)
        self.text.Bind(wx.stc.EVT_STC_AUTOCOMP_SELECTION, self._OnIntellisenseSelection, self.text)
        self._RegisterIntellisenseImages()
        # Other objects
        self.previewCanvas = PreviewCanvas(self.frame, self.pref.format, self.pref.notations, self.pref.decorator)
        # Registra la callback doppio-click: naviga alla riga sorgente nell'editor
        self.previewCanvas.SetClickCallback(self._OnPreviewClick)
        self._mgr.AddPane(
            self.text,
            aui.AuiPaneInfo()
                .Center()
                .Name('_main')
                .Caption(_('Editor'))
                .CaptionVisible(True)
                .CloseButton(False)
                .MaximizeButton(False)
                .Floatable(False)
                .Movable(False)
                .PaneBorder(False)
        )
        _preview_min = wx.Size(370, 520) if getattr(self.pref, 'previewMinSize', True) else wx.Size(-1, -1)
        self.AddPane(self.previewCanvas.main_panel,
                     aui.AuiPaneInfo().Right().BestSize(370, 520).MinSize(_preview_min),
                     _('Songpress++ Preview'), 'preview')
        self.previewCanvas.main_panel.Bind(wx.adv.EVT_HYPERLINK, self.OnCopyAsImage, self.previewCanvas.link)

        # ── Caption bar personalizzata per Editor e Anteprima ──────────
        class _SongpressDockArt(aui.AuiDefaultDockArt):
            """Colora la caption bar in base al nome del pannello:
               - '_main'   (Editor)    → colore pref.captionEditorActiveHex
               - 'preview' (Anteprima) → colore pref.captionPreviewActiveHex
            I colori attivo/inattivo sono calcolati automaticamente dal colore base.
            """

            def __init__(self, pref):
                super().__init__()
                self._pref = pref

            @staticmethod
            def _hex_to_colour(h, fallback):
                try:
                    h = h.strip().lstrip('#')
                    if len(h) == 6:
                        return wx.Colour(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
                except Exception:
                    pass
                return fallback

            @staticmethod
            def _darken(c, f=0.75):
                return wx.Colour(int(c.Red()*f), int(c.Green()*f), int(c.Blue()*f))

            @staticmethod
            def _lighten(c, f=1.5):
                return wx.Colour(min(255, int(c.Red()*f)), min(255, int(c.Green()*f)), min(255, int(c.Blue()*f)))

            def DrawCaption(self, dc, window, text, rect, pane):
                name = pane.name if pane else ''
                active = bool(pane and pane.HasFlag(pane.optionActive))
                if name == '_main':
                    base = self._hex_to_colour(
                        getattr(self._pref, 'captionEditorActiveHex', '#4682C8'),
                        wx.Colour(70, 130, 200)
                    )
                elif name == 'preview':
                    base = self._hex_to_colour(
                        getattr(self._pref, 'captionPreviewActiveHex', '#329B82'),
                        wx.Colour(50, 155, 130)
                    )
                else:
                    super().DrawCaption(dc, window, text, rect, pane)
                    return
                if active:
                    c1, c2 = base, self._darken(base)
                else:
                    c1, c2 = self._lighten(base), base
                dc.GradientFillLinear(rect, c1, c2, wx.SOUTH)
                dc.SetTextForeground(wx.WHITE if active else wx.Colour(40, 40, 40))
                dc.SetFont(self._caption_font)
                w, h = dc.GetTextExtent(text)
                dc.DrawText(text, rect.x + 4, rect.y + (rect.height - h) // 2)

        self._dockArt = _SongpressDockArt(self.pref)
        self._mgr.SetArtProvider(self._dockArt)
        # ───────────────────────────────────────────────────────────────

        self.mainToolBar = aui.AuiToolBar(self.frame, wx.ID_ANY, wx.DefaultPosition, agwStyle=aui.AUI_TB_PLAIN_BACKGROUND)
        self.mainToolBar.SetToolBitmapSize(wx.Size(16, 16))
        self.AddTool(self.mainToolBar, 'new', 'img/new.png', _("New"), _("Create a new song"))
        self.AddTool(self.mainToolBar, 'open', 'img/open.png', _("Open"), _("Open an existing song"))
        self.AddTool(self.mainToolBar, 'save', 'img/save.png', _("Save"), _("Save the song with the current file name"))
        self.mainToolBar.AddSeparator()
        self.undoTool = self.AddTool(self.mainToolBar, 'undo', 'img/undo.png', _("Undo"), _("Undo the last change"))
        self.redoTool = self.AddTool(self.mainToolBar, 'redo',
            'img/redo.png', _("Redo"), _("Redo the last undone change"))
        self.redoTool = wx.xrc.XRCID('redo')
        self.mainToolBar.AddSeparator()
        self.cutTool = self.AddTool(self.mainToolBar, 'cut', 'img/cut.png', _("Cut"),
                                                                _("Move selected text to the clipboard"))
        self.copyTool = self.AddTool(self.mainToolBar, 'copy', 'img/copy.png', _("Copy"),
                                                                 _("Copy selected text to the clipboard"))
        self.copyOnlyTextTool = wx.xrc.XRCID('copyOnlyText')
        self.AddTool(self.mainToolBar, 'copyAsImage', 'img/copyAsImage2.png', _("Copy as image"),
                                     _("Copy the entire FORMATTED song (or selected verses) to the clipboard"))
        self.pasteTool = self.AddTool(self.mainToolBar, 'paste', 'img/paste.png', _("Paste"),
                                                                    _("Read text from the clipboard and insert it at the cursor position"))
        self.pasteChordsTool = self.AddTool(self.mainToolBar, 'pasteChords', 'img/pasteChords.png', _("Paste chords"),
                                                                                _("Merge chords from the copied text into the current selection"))
        self.mainToolBar.AddSeparator()
        self.syntaxCheckTool = self.AddTool(
            self.mainToolBar,
            'syntaxCheck',
            'img/syntaxCheck.png',
            _("Check syntax"),
            _("Check ChordPro syntax of the document")
        )
        self.mainToolBar.Realize()
        self.mainToolBarPane = self.AddPane(self.mainToolBar, aui.AuiPaneInfo().ToolbarPane().Top().Row(1).Position(1),
                                                                                _('Standard'), 'standard')
        self.formatToolBar = aui.AuiToolBar(self.frame, wx.ID_ANY, agwStyle=aui.AUI_TB_PLAIN_BACKGROUND)
        self.formatToolBar.SetExtraStyle(aui.AUI_TB_PLAIN_BACKGROUND)
        self.fontChooser = FontComboBox(self.formatToolBar, -1, self.pref.format.face)
        self.formatToolBar.AddControl(self.fontChooser)
        self.frame.Bind(wx.EVT_COMBOBOX, self.OnFontSelected, self.fontChooser)
        wx.UpdateUIEvent.SetUpdateInterval(500)
        self.frame.Bind(wx.EVT_UPDATE_UI, self.OnIdle, self.frame)
        self.frame.Bind(wx.EVT_TEXT_CUT, self.OnTextCutCopy, self.text)
        self.frame.Bind(wx.EVT_TEXT_COPY, self.OnTextCutCopy, self.text)
        self.fontChooser.Bind(wx.EVT_TEXT_ENTER, self.OnFontSelected, self.fontChooser)
        self.fontChooser.Bind(wx.EVT_KILL_FOCUS, self.OnFontSelected, self.fontChooser)
        self.AddTool(self.formatToolBar, 'title', 'img/title.png', _("Insert title"),
                                 _("Insert a command to display the song title"))
        self.AddTool(self.formatToolBar, 'chord', 'img/chord.png', _("Insert chord"),
                                 _("Insert square brackets that will contain a chord"))
        self.AddTool(self.formatToolBar, 'chorus', 'img/chorus.png', _("Insert chorus"),
                                 _("Insert a pair of commands that will contain the chorus"))
        self.AddTool(
            self.formatToolBar,
            'verseWithCustomLabelOrWithoutLabel',
            'img/verse.png',
            _("Insert verse with custom label or without label"),
            _("Insert a verse with a custom label or without label"),
        )
        labelVersesTool = self.formatToolBar.AddToggleTool(  # AddToggleTool (agw) or AddTool
            wx.xrc.XRCID('labelVerses'),
            wx.Bitmap(wx.Image(glb.AddPath("img/labelVerses.png"))),
            wx.NullBitmap,
            True,
            None,
            _("Show verse labels"),
            _("Show or hide verse and chorus labels"),
        )
        self.labelVersesToolId = labelVersesTool.GetId()
        showChordsIcon = wx.StaticBitmap(self.formatToolBar, -1, wx.Bitmap(wx.Image(glb.AddPath('img/showChords.png'))))
        self.formatToolBar.AddControl(showChordsIcon)
        self.showChordsChooser = wx.Slider(self.formatToolBar, -1, 0, 0, 2, wx.DefaultPosition, (100, -1),
                                                                             wx.SL_AUTOTICKS | wx.SL_HORIZONTAL)
        tt1 = wx.ToolTip(_("Hide or show chords in the formatted song"))
        tt2 = wx.ToolTip(_("Hide or show chords in the formatted song"))
        self.showChordsChooser.SetToolTip(tt1)
        showChordsIcon.SetToolTip(tt2)
        self.frame.Bind(wx.EVT_SCROLL, self.OnFontSelected, self.showChordsChooser)
        self.formatToolBar.AddControl(
            self.showChordsChooser,
            "pippo"
        )
        self.formatToolBar.Realize()
        self.formatToolBarPane = self.AddPane(self.formatToolBar, aui.AuiPaneInfo().ToolbarPane().Top().Row(1).Position(2),
                                                                                    _('Format'), 'format')
        self.BindMyMenu()
        self._BuildNewFromTemplateMenu()
        self.frame.Bind(EVT_TEXT_CHANGED, self.OnTextChanged)
        self.frame.Bind(wx.EVT_CHAR_HOOK, self._OnGlobalCharHook)
        self.exportMenuId = xrc.XRCID('export')
        self.exportToClipboardAsAVectorImage = xrc.XRCID('exportToClipboardAsAVectorImage')
        self.exportAsEmfMenuId = xrc.XRCID('exportAsEmf')
        self.cutMenuId = xrc.XRCID('cut')
        self.copyMenuId = xrc.XRCID('copy')
        self.copyAsImageMenuId = xrc.XRCID('copyAsImage')
        self.pasteMenuId = xrc.XRCID('paste')
        self.pasteChordsMenuId = xrc.XRCID('pasteChords')
        self.propagateVerseChordsMenuId = xrc.XRCID('propagateVerseChords')
        self.propagateChorusChordsMenuId = xrc.XRCID('propagateChorusChords')
        self.removeChordsMenuId = xrc.XRCID('removeChords')
        self.labelVersesMenuId = xrc.XRCID('labelVerses')
        self.noChordsMenuId = xrc.XRCID('noChords')
        self.oneVerseForEachChordPatternMenuId = xrc.XRCID('oneVerseForEachChordPattern')
        self.wholeSongMenuId = xrc.XRCID('wholeSong')
        self.chordsAboveMenuId = xrc.XRCID('chordsAbove')
        self.chordsBelowMenuId = xrc.XRCID('chordsBelow')
        if platform.system() != 'Windows':
            self.menuBar.GetMenu(0).FindItemById(self.exportMenuId).GetSubMenu().Delete(self.exportAsEmfMenuId)
        # Persistent print settings (paper size, orientation, margins)
        self._print_data = wx.PrintData()
        self._print_data.SetPaperId(wx.PAPER_A4)
        self._print_data.SetOrientation(wx.PORTRAIT)
        # Margins in mm (top, bottom, left, right)
        self._margin_top    = 15
        self._margin_bottom = 15
        self._margin_left   = 15
        self._margin_right  = 15
        self._LoadPageMargins()
        self._LoadTempoDisplay()
        self._LoadKlavierColour()
        self._LoadGuidePrefs()
        self._applyKlavierHighlightColor()
        self._applyFingerNumColor()
        self._LoadCustomColours()
        self._two_pages_per_sheet = False
        self._columns_per_page = 1  # 1 = colonna singola, 2 = due colonne per pagina
        self._fit_to_page = False   # True = riduci e adatta alla pagina
        self._no_mirror_right = False  # True = non replicare il brano sulla metà destra
        self._remove_blank_pages = False  # True = skip blank/empty logical pages
        self._shrink_to_fit = False  # True = auto-shrink to avoid bottom clipping
        self._min_margin_shrink = 5   # margine minimo (mm) usato dallo shrink automatico
        self._print_options_pinned = False  # True = keep print options dialog open after OK
        self._chord_dialog_pinned = False   # True = keep insert-chord dialog open after OK
        self._showPageBreakLines = True
        self._showColumnBreakLines = True
        self._showDurationBeats = True
        self._showPageBreakLinesMenuId = xrc.XRCID('showPageBreakLines')
        self._showColumnBreakLinesMenuId = xrc.XRCID('showColumnBreakLines')
        self._showDurationBeatsMenuId = xrc.XRCID('showDurationBeats')
        self.findReplaceDialog = None
        self._lastFindSt    = ''
        self._lastFindFlags = 0
        self._lastFindDown  = True
        self.CheckLabelVerses()
        self.CheckChordsPosition()
        self.SetFont()
        self.text.SetFont(self.pref.editorFace, self.pref.editorSize)
        self.text.SetBgColour(getattr(self.pref, 'editorBgHex', '#FFFFFF'))
        self.text.SetSelColour(getattr(self.pref, 'selColourHex', '#3399FF'))
        _sc = getattr(self.pref, 'syntaxColours', {})
        for _k, _sid in [('normal', 11), ('chorus', 15), ('chord', 12), ('command', 13), ('attr', 14), ('comment', 16), ('tabgrid', 17)]:
            if _k in _sc:
                self.text.SetSyntaxColour(_sid, _sc[_k])
        self.text.ApplyMultiCursor(getattr(self.pref, 'multiCursor', False))
        # Se la perspective è stata salvata prima dell'introduzione della barra
        # "Editor" sul pannello centrale, va resettata una volta sola.
        self.config.SetPath('/SDIMainFrame')
        if not self.config.ReadBool('EditorCaptionPane', False):
            self.config.DeleteEntry('Perspective', False)
            self.config.WriteBool('EditorCaptionPane', True)
        self.FinalizePaneInitialization()
        # Reassign caption value to override caption saved in preferences (it could be another language)
        self._mgr.GetPane('_main').caption = _('Editor')
        self._mgr.GetPane('preview').caption = _('Songpress++ Preview')
        self._mgr.GetPane('standard').caption = _('Standard')
        self._mgr.GetPane('format').caption = _('Format')
        # LoadPerspective sovrascrive MinSize: lo reimponiamo sempre dopo
        self._ApplyPreviewMinSize()
        self._mgr.Update()
        self._UpdateBreakLinesMenuState()
        self.RestoreWindowGeometry()
        if 'firstTimeEasyKey' in self.pref.notices:
            msg = _(
                "You are not a skilled guitarist? Songpress++ can help you: when you open a song, it can detect if chords are difficult. If this is the case, Songpress++ will alert you, and offer to transpose your song to the easiest key, automatically.\n\nDo you want to turn this option on?")
            d = wx.MessageDialog(self.frame, msg, _("Songpress++"), wx.YES_NO | wx.ICON_QUESTION)
            if d.ShowModal() == wx.ID_YES:
                self.pref.autoAdjustEasyKey = True
                msg = _(
                    "Please take a minute to set up your skill as a guitarist. For each group of chords, tell Songpress++ how much you like them.")
                d = wx.MessageDialog(self.frame, msg, _("Songpress++"), wx.OK)
                d.ShowModal()
                f = MyPreferencesDialog(self.frame, self.pref, easyChords,
                                            previewCanvas=self.previewCanvas)
                f.notebook.SetSelection(1)
                if f.ShowModal() == wx.ID_OK:
                    self.text.SetFont(self.pref.editorFace, int(self.pref.editorSize))
                    self.SetDefaultExtension(self.pref.defaultExtension)

    def OnClose(self, evt):
        self.SaveWindowGeometry()
        self._SavePageMargins()
        self._SaveTempoDisplay()
        self._SaveGuidePrefs()
        self._SaveKlavierColour()
        self._SaveCustomColours()
        self.pref.Save()
        self.config.Flush()
        super().OnClose(evt)

    def _SavePageMargins(self):
        """Salva i margini, il formato carta, l'orientamento e le opzioni
        di riduzione automatica nel config."""
        try:
            self.config.SetPath('/PageSetup')
            self.config.Write('margin_top',    str(self._margin_top))
            self.config.Write('margin_bottom', str(self._margin_bottom))
            self.config.Write('margin_left',   str(self._margin_left))
            self.config.Write('margin_right',  str(self._margin_right))
            self.config.Write('paper_id',      str(self._print_data.GetPaperId()))
            self.config.Write('orientation',   str(self._print_data.GetOrientation()))
            self.config.Write('shrink_to_fit',     '1' if self._shrink_to_fit else '0')
            self.config.Write('min_margin_shrink', str(self._min_margin_shrink))
        except Exception:
            pass

    def _LoadPageMargins(self):
        """Ripristina i margini, il formato carta, l'orientamento e le opzioni
        di riduzione automatica dal config."""
        try:
            self.config.SetPath('/PageSetup')
            top    = self.config.Read('margin_top')
            bottom = self.config.Read('margin_bottom')
            left   = self.config.Read('margin_left')
            right  = self.config.Read('margin_right')
            if top:    self._margin_top    = int(top)
            if bottom: self._margin_bottom = int(bottom)
            if left:   self._margin_left   = int(left)
            if right:  self._margin_right  = int(right)
            paper_id = self.config.Read('paper_id')
            if paper_id:
                self._print_data.SetPaperId(int(paper_id))
            orientation = self.config.Read('orientation')
            if orientation:
                self._print_data.SetOrientation(int(orientation))
            shrink = self.config.Read('shrink_to_fit')
            if shrink:
                self._shrink_to_fit = (shrink == '1')
            min_m = self.config.Read('min_margin_shrink')
            if min_m:
                self._min_margin_shrink = int(min_m)
        except Exception:
            pass

    def _SaveTempoDisplay(self):
        """Salva le modalità di visualizzazione di tempo, misura e tonalità nel config."""
        try:
            self.config.SetPath('/TempoDisplay')
            self.config.Write('tempoDisplay', str(getattr(self.pref, 'tempoDisplay', 0)))
            self.config.SetPath('/TimeDisplay')
            self.config.Write('timeDisplay', '1' if getattr(self.pref, 'timeDisplay', True) else '0')
            self.config.SetPath('/KeyDisplay')
            self.config.Write('keyDisplay', '1' if getattr(self.pref, 'keyDisplay', True) else '0')
        except Exception:
            pass

    def _LoadTempoDisplay(self):
        """Ripristina le modalità di visualizzazione di tempo, misura e tonalità dal config."""
        try:
            self.config.SetPath('/TempoDisplay')
            val = self.config.Read('tempoDisplay')
            if val:
                self.pref.tempoDisplay = int(val)
            self.config.SetPath('/TimeDisplay')
            val = self.config.Read('timeDisplay')
            if val:
                self.pref.timeDisplay = (val == '1')
            self.config.SetPath('/KeyDisplay')
            val = self.config.Read('keyDisplay')
            if val:
                self.pref.keyDisplay = (val == '1')
        except Exception:
            pass

    def _SaveGuidePrefs(self):
        """Salva le preferenze della guida rapida (zoom e tema) nel config."""
        try:
            self.config.SetPath('/GuidePrefs')
            self.config.Write('zoom', str(getattr(self.pref, 'guideZoom', 100)))
            self.config.Write('darkMode', '1' if getattr(self.pref, 'guideDarkMode', False) else '0')
        except Exception:
            pass

    def _LoadGuidePrefs(self):
        """Ripristina le preferenze della guida rapida (zoom e tema) dal config."""
        try:
            self.config.SetPath('/GuidePrefs')
            val = self.config.Read('zoom')
            if val:
                self.pref.guideZoom = max(50, min(200, int(val)))
            else:
                self.pref.guideZoom = 100
            val = self.config.Read('darkMode')
            self.pref.guideDarkMode = (val == '1')
        except Exception:
            self.pref.guideZoom = 100
            self.pref.guideDarkMode = False

    def _SaveKlavierColour(self):
        """Salva il colore dei tasti klavier nel config."""
        try:
            self.config.SetPath('/KlavierColour')
            self.config.Write('highlightHex', getattr(self.pref, 'klavierHighlightHex', '#D23C3C'))
        except Exception:
            pass

    def _LoadKlavierColour(self):
        """Ripristina il colore dei tasti klavier dal config."""
        try:
            self.config.SetPath('/KlavierColour')
            val = self.config.Read('highlightHex')
            if val:
                self.pref.klavierHighlightHex = val
        except Exception:
            pass

    def _SaveCustomColours(self):
        """Salva i colori personalizzati dei due ColourDialog nel config."""
        try:
            self.config.SetPath('/CustomColoursKlavier')
            for i, hex_str in enumerate(getattr(self.pref, 'customColoursKlavier', [])[:16]):
                self.config.Write('colour%d' % i, hex_str)
            self.config.SetPath('/CustomColoursEditorBg')
            for i, hex_str in enumerate(getattr(self.pref, 'customColoursEditorBg', [])[:16]):
                self.config.Write('colour%d' % i, hex_str)
            self.config.SetPath('/CustomColoursSelColour')
            for i, hex_str in enumerate(getattr(self.pref, 'customColoursSelColour', [])[:16]):
                self.config.Write('colour%d' % i, hex_str)
            self.config.SetPath('/CustomColoursCapEditor')
            for i, hex_str in enumerate(getattr(self.pref, 'customColoursCapEditor', [])[:16]):
                self.config.Write('colour%d' % i, hex_str)
            self.config.SetPath('/CustomColoursCapPreview')
            for i, hex_str in enumerate(getattr(self.pref, 'customColoursCapPreview', [])[:16]):
                self.config.Write('colour%d' % i, hex_str)
        except Exception:
            pass

    def _LoadCustomColours(self):
        """Ripristina i colori personalizzati dei due ColourDialog dal config."""
        try:
            self.config.SetPath('/CustomColoursKlavier')
            self.pref.customColoursKlavier = [
                self.config.Read('colour%d' % i) or '#FFFFFF' for i in range(16)
            ]
        except Exception:
            self.pref.customColoursKlavier = ['#FFFFFF'] * 16
        try:
            self.config.SetPath('/CustomColoursEditorBg')
            self.pref.customColoursEditorBg = [
                self.config.Read('colour%d' % i) or '#FFFFFF' for i in range(16)
            ]
        except Exception:
            self.pref.customColoursEditorBg = ['#FFFFFF'] * 16
        try:
            self.config.SetPath('/CustomColoursSelColour')
            self.pref.customColoursSelColour = [
                self.config.Read('colour%d' % i) or '#FFFFFF' for i in range(16)
            ]
        except Exception:
            self.pref.customColoursSelColour = ['#FFFFFF'] * 16
        try:
            self.config.SetPath('/CustomColoursCapEditor')
            self.pref.customColoursCapEditor = [
                self.config.Read('colour%d' % i) or '#FFFFFF' for i in range(16)
            ]
        except Exception:
            self.pref.customColoursCapEditor = ['#FFFFFF'] * 16
        try:
            self.config.SetPath('/CustomColoursCapPreview')
            self.pref.customColoursCapPreview = [
                self.config.Read('colour%d' % i) or '#FFFFFF' for i in range(16)
            ]
        except Exception:
            self.pref.customColoursCapPreview = ['#FFFFFF'] * 16

    def SaveWindowGeometry(self):
        """Save window size, position and maximized state to config."""
        if not getattr(self.pref, 'saveWindowGeometry', True):
            return
        try:
            maximized = self.frame.IsMaximized()
            self.config.SetPath('/Window')
            self.config.Write('maximized', '1' if maximized else '0')
            if not maximized:
                x, y = self.frame.GetPosition()
                w, h = self.frame.GetSize()
                self.config.Write('x', str(x))
                self.config.Write('y', str(y))
                self.config.Write('w', str(w))
                self.config.Write('h', str(h))
        except Exception:
            pass

    def RestoreWindowGeometry(self):
        """Restore window size and position from config, with multimonitor safety."""
        if not getattr(self.pref, 'saveWindowGeometry', True):
            return
        try:
            self.config.SetPath('/Window')
            maximized = self.config.Read('maximized')
            x = self.config.Read('x')
            y = self.config.Read('y')
            w = self.config.Read('w')
            h = self.config.Read('h')
            if w and h:
                w, h = int(w), int(h)
                # Enforce minimum size
                w = max(w, 400)
                h = max(h, 300)
                if x and y:
                    x, y = int(x), int(y)
                    # Verify that the saved position is visible on at least one connected display
                    visible = False
                    for i in range(wx.Display.GetCount()):
                        display = wx.Display(i)
                        client_rect = display.GetClientArea()
                        # The window is considered visible if at least its top-left
                        # 100x50 px area falls inside the display's client area
                        if (client_rect.Contains(wx.Point(x + 100, y + 50)) or
                                client_rect.Contains(wx.Point(x, y))):
                            visible = True
                            break
                    if visible:
                        self.frame.SetPosition(wx.Point(x, y))
                    else:
                        # Off-screen: centre on primary display
                        self.frame.Centre()
                self.frame.SetSize(wx.Size(w, h))
            if maximized == '1':
                self.frame.Maximize(True)
        except Exception:
            pass

    def BindMyMenu(self):
        """Bind a menu item, by xrc name, to a handler"""

        def Bind(handler, xrcname):
            self.Bind(wx.EVT_MENU, handler, xrcname)

        Bind(self.OnCopyAsImage, 'exportToClipboardAsAVectorImage')
        Bind(self.OnExportAsSvg, 'exportAsSvg')
        Bind(self.OnExportAsEmf, 'exportAsEmf')
        Bind(self.OnExportAsPng, 'exportAsPng')
        Bind(self.OnExportAsHtml, 'exportAsHtml')
        Bind(self.OnExportAsTab, 'exportAsTab')
        Bind(self.OnExportAsPptx, 'exportAsPptx')
        Bind(self.OnExportAsPdf, 'exportAsPdf')
        Bind(self.OnSongbook, 'songbook')
        Bind(self.OnPrint, 'print')
        Bind(self.OnPrintPreview, 'printPreview')
        Bind(self.OnPageSetup, 'pageSetup')
        Bind(self.OnUndo, 'undo')
        Bind(self.OnRedo, 'redo')
        Bind(self.OnCut, 'cut')
        Bind(self.OnCopy, 'copy')
        Bind(self.OnCopyAsImage, 'copyAsImage')
        Bind(self.OnCopyOnlyText, 'copyOnlyText')
        Bind(self.OnPaste, 'paste')
        Bind(self.OnPasteChords, 'pasteChords')
        Bind(self.OnPropagateVerseChords, 'propagateVerseChords')
        Bind(self.OnPropagateChorusChords, 'propagateChorusChords')
        Bind(self.OnFind, 'find')
        Bind(self.OnFindNext, 'findNext')
        Bind(self.OnFindPrevious, 'findPrevious')
        Bind(self.OnReplace, 'replace')
        Bind(self.OnSelectAll, 'selectAll')
        Bind(self.OnSelectNextChord, 'selectNextChord')
        Bind(self.OnSelectPreviousChord, 'selectPreviousChord')
        Bind(self.OnMoveChordRight, 'moveChordRight')
        Bind(self.OnMoveChordLeft, 'moveChordLeft')
        Bind(self.OnRemoveChords, 'removeChords')
        Bind(self.OnIntegrateChords, 'integrateChords')
        Bind(self.OnTitle, 'title')
        Bind(self.OnSubtitle, 'subtitle')
        Bind(self.OnChord, 'chord')
        Bind(self.OnChorus, 'chorus')
        Bind(self.OnVerse, 'verseWithCustomLabelOrWithoutLabel')
        Bind(self.OnComment, 'comment')
        Bind(self.OnFormatFont, 'songFont')
        Bind(self.OnTextFont, 'textFont')
        Bind(self.OnChordFont, 'chordFont')
        Bind(self.OnLabelVerses, 'labelVerses')
        Bind(self.OnChorusLabel, 'chorusLabel')
        Bind(self.OnNoChords, 'noChords')
        Bind(self.OnOneVerseForEachChordPattern, 'oneVerseForEachChordPattern')
        Bind(self.OnWholeSong, 'wholeSong')
        Bind(self.OnChordsAbove, 'chordsAbove')
        Bind(self.OnChordsBelow, 'chordsBelow')
        Bind(self.OnTogglePageBreakLines, 'showPageBreakLines')
        Bind(self.OnToggleColumnBreakLines, 'showColumnBreakLines')
        Bind(self.OnToggleDurationBeats, 'showDurationBeats')
        Bind(self.OnTranspose, 'transpose')
        Bind(self.OnSimplifyChords, 'simplifyChords')
        Bind(self.OnChangeChordNotation, 'changeChordNotation')
        Bind(self.OnNormalizeChords, 'cleanupChords')
        Bind(self.OnConvertTabToChordpro, 'convertTabToChordpro')
        Bind(self.OnRemoveSpuriousBlankLines, 'removeSpuriousBlankLines')
        Bind(self.OnOptions, 'options')
        Bind(self.OnGuide, 'guide')
        Bind(self.OnGuideMarkdown, 'guideMarkdown')
        # --- NUOVO: Normalizza spazi multipli ---
        Bind(self.OnNormalizeSpaces, 'normalizeSpaces')
        # --- NUOVO: Formato => Altro ---
        Bind(self.OnInsertLinespacing, 'insertLinespacing')
        Bind(self.OnInsertChordtopspacing, 'insertChordtopspacing')
        Bind(self.OnInsertPageBreak, 'insertPageBreak')
        Bind(self.OnInsertColumnBreak, 'insertColumnBreak')
        # --- NEW: Insert => Other (structured blocks) ---
        Bind(self.OnInsertVerse, 'insertVerse')
        Bind(self.OnInsertVerseNum, 'insertVerseNum')
        Bind(self.OnInsertChorusBlock, 'insertChorusBlock')
        Bind(self.OnInsertChordBlock, 'insertChordBlock')
        Bind(self.OnInsertBridge, 'insertBridge')
        Bind(self.OnInsertGrid, 'insertGrid')
        Bind(self.OnInsertTempo, 'insertTempo')
        Bind(self.OnInsertTime, 'insertTime')
        Bind(self.OnInsertKey, 'insertKey')
        Bind(self.OnInsertBeatsTime, 'insertDuration')
        Bind(self.OnInsertCapo, 'insertCapo')
        Bind(self.OnInsertArtist, 'insertArtist')
        Bind(self.OnInsertComposer, 'insertComposer')
        Bind(self.OnInsertAlbum, 'insertAlbum')
        Bind(self.OnInsertYear, 'insertYear')
        Bind(self.OnInsertCopyright, 'insertCopyright')
        # --- Insert => Chord keyboard (klavier) ---
        Bind(self.OnInsertKlavierChord, 'insertTaste')
        Bind(self.OnInsertDefine, 'insertDefine')
        Bind(self.OnInsertFingering, 'insertFingering')
        Bind(self.OnInsertImage, 'insertImage')
        Bind(self.OnInsertMusicalSymbol, 'insertMusicalSymbol')
        # --- File => Importa da PDF ---
        Bind(self.OnImportFromPdf, 'importFromPdf')
        # --- Verifica sintattica ---
        Bind(self.OnSyntaxCheck, 'syntaxCheck')
        Bind(self.OnSongStatistics, 'songStatistics')
        self.frame.Bind(EVT_SYNTAX_GOTO, self.OnSyntaxGoto)

    # ------------------------------------------------------------------
    # Template "Nuovo da template"
    # ------------------------------------------------------------------

    def _BuildNewFromTemplateMenu(self):
        """Popola dinamicamente il sottomenu 'Nuovo da template'
        con i file .crd trovati in templates/songs.

        Scansiona in modo difensivo due cartelle distinte:
          - glb.path/templates/songs/      (package, globale)
          - glb.data_path/templates/songs/ (dati utente, locale)
        Se una delle due non esiste viene ignorata silenziosamente.
        I file utente sovrascrivono omonimi globali (stessa logica
        di ListLocalGlobalDir, ma senza crash su cartella mancante).
        Viene chiamato una sola volta durante l'inizializzazione.
        """
        template_rel = os.path.join('templates', 'songs')
        search_roots = [glb.path]
        if getattr(glb, 'data_path', None):
            search_roots.append(glb.data_path)

        found = {}  # nome_base_lower -> percorso assoluto
        for root in search_roots:
            folder = os.path.join(root, template_rel)
            if not os.path.isdir(folder):
                continue
            try:
                for fname in sorted(os.listdir(folder)):
                    if fname.lower().endswith('.crd'):
                        key = os.path.splitext(fname)[0].lower()
                        found[key] = os.path.join(folder, fname)
            except OSError:
                pass

        # Ordina alfabeticamente per nome visualizzato
        template_paths = [found[k] for k in sorted(found)]

        # Recupera il sottomenu dall'XRC tramite XRCID — robusto rispetto alla lingua,
        # usa lo stesso meccanismo degli altri ID di menu nel codice.
        file_menu = self.menuBar.GetMenu(0)
        submenu = None
        nft_id = xrc.XRCID('newFromTemplate')
        menu_item = file_menu.FindItemById(nft_id)
        if menu_item is not None:
            submenu = menu_item.GetSubMenu()

        if submenu is None:
            # Sottomenu non trovato nell'XRC: niente da fare
            return

        # Svuota eventuali voci residue
        for old_item in submenu.GetMenuItems():
            submenu.Delete(old_item)

        self._template_paths = {}  # id voce di menu -> percorso assoluto

        if not template_paths:
            placeholder = submenu.Append(wx.ID_ANY, _("(no template available)"))
            submenu.Enable(placeholder.GetId(), False)
            return

        for path in template_paths:
            name = os.path.splitext(os.path.basename(path))[0]
            item = submenu.Append(wx.ID_ANY, name)
            self._template_paths[item.GetId()] = path
            self.frame.Bind(wx.EVT_MENU, self._OnNewFromTemplate, id=item.GetId())

    def _OnNewFromTemplate(self, evt):
        """Carica il template come nuovo documento non salvato.

        Il file template non viene mai modificato: il suo contenuto
        viene copiato in un nuovo documento 'senza nome' che l'utente
        dovrà salvare con 'Salva con nome'.
        """
        path = getattr(self, '_template_paths', {}).get(evt.GetId())
        if path is None or not os.path.isfile(path):
            wx.MessageBox(
                _("Template not found:\n%s") % (path or ''),
                _("Songpress++"),
                wx.OK | wx.ICON_ERROR,
                self.frame,
            )
            return

        # Se il documento corrente ha modifiche non salvate, chiede conferma
        # (usa AskSaveModified() di SDIMainFrame, identico a OnNew)
        if not self.AskSaveModified():
            return

        # Legge il contenuto del template
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as exc:
            wx.MessageBox(
                str(exc),
                _("Error opening template"),
                wx.OK | wx.ICON_ERROR,
                self.frame,
            )
            return

        # Replica esattamente OnNew di SDIMainFrame, poi inserisce il template.
        # document='', modified=True → 'Salva' aprirà 'Salva con nome',
        # il file template originale non viene mai toccato.
        self.document = ''
        self.text.AutoChangeMode(True)
        self.text.New()
        self.text.SetText(content)
        self.text.AutoChangeMode(False)
        self.modified = True
        self.UpdateTitle()
        self.UpdateEverything()
        self.previewCanvas.Refresh(self._get_display_text())

    def OnNormalizeSpaces(self, evt):
        """
        Replace multiple consecutive spaces with a single space
        in the selected text or the whole text if nothing is selected.
        """
        import re
        s, e = self.text.GetSelection()
        if s == e:  # niente selezione: usa tutto il testo
            text = self.text.GetText()
            new_text = re.sub(r' {2,}', ' ', text)
            self.text.SetText(new_text)
        else:  # usa solo la selezione
            text = self.text.GetTextRange(s, e)
            new_text = re.sub(r' {2,}', ' ', text)
            self.text.ReplaceSelection(new_text)

    def OnSyntaxCheck(self, evt):
        """Esegue la verifica sintattica ChordPro e mostra il dialogo con i risultati."""
        text = self.text.GetText()
        result = syntax_check(text)
        dlg = SyntaxCheckerDialog(self.frame, result)
        dlg.ShowModal()
        dlg.Destroy()

    # ------------------------------------------------------------------
    # Song statistics
    # ------------------------------------------------------------------

    def OnSongStatistics(self, evt):
        """Analizza il brano e mostra un dialogo con statistiche e valutazione."""
        import re, math

        text = self.text.GetText()

        # ── 1. Estrai metadati dalla direttive ─────────────────────────
        def _meta(key):
            m = re.search(r'\{\s*' + key + r'\s*:\s*([^}]+)\}', text, re.IGNORECASE)
            return m.group(1).strip() if m else ''

        song_title  = _meta('title') or _meta('t')
        song_key    = _meta('key')
        song_tempo  = _meta('tempo') or _meta('tempo_s') or _meta('tempo_m')
        song_time   = _meta('time')
        song_capo   = _meta('capo')
        song_artist = _meta('artist')

        # ── 2. Righe attive (escludi commenti e direttive pure) ────────
        lines_all = text.splitlines()
        lines_active = [l for l in lines_all
                        if l.strip() and not l.strip().startswith('#')
                        and not re.match(r'\s*\{[^}]+\}\s*$', l)]

        # ── 3. Conteggio accordi unici e totali ────────────────────────
        all_chords_raw = re.findall(r'\[([A-Ga-g][^\]]*?)\]', text)
        all_chords = [c.strip() for c in all_chords_raw if c.strip()]
        unique_chords = set(re.sub(r'/[A-G][#b]?$', '', c) for c in all_chords)
        n_chords_total  = len(all_chords)
        n_chords_unique = len(unique_chords)

        # ── 4. Conteggio strofe e ritornelli ──────────────────────────
        n_verses  = len(re.findall(
            r'\{\s*(?:start_of_verse|start_verse(?:_num)?|sov)\b[^}]*\}',
            text, re.IGNORECASE))
        n_chorus  = len(re.findall(
            r'\{\s*(?:start_of_chorus|start_chorus|soc)\b[^}]*\}',
            text, re.IGNORECASE))
        n_bridge  = len(re.findall(
            r'\{\s*(?:start_of_bridge|start_bridge|sob)\b[^}]*\}',
            text, re.IGNORECASE))
        n_pages   = len(re.findall(
            r'\{\s*(?:new_page|np)\s*\}', text, re.IGNORECASE)) + 1

        # ── 5. Parole del testo (escludi accordi e direttive) ─────────
        text_no_chords = re.sub(r'\[[^\]]*\]', '', text)
        text_no_dir    = re.sub(r'\{[^}]*\}', '', text_no_chords)
        text_no_comm   = re.sub(r'^#.*$', '', text_no_dir, flags=re.MULTILINE)
        words = re.findall(r"[\w'\u00C0-\u024F]+", text_no_comm)
        n_words = len(words)
        n_lines = len(lines_active)

        # ── 6. Complessità accordi (semplice euristica) ───────────────
        # Accordi "difficili": con 7, 9, 11, 13, dim, aug, sus, add, maj, m7, °
        hard_pat = re.compile(
            r'(?:7|9|11|13|dim|aug|sus|add|maj|°|\+)', re.IGNORECASE)
        n_hard = sum(1 for c in unique_chords if hard_pat.search(c))
        pct_hard = (n_hard / n_chords_unique * 100) if n_chords_unique else 0

        # ── 7. Durata: esplicita {duration:MM:SS} oppure stima automatica ──
        duration_str = ''
        duration_is_explicit = False

        # Cerca {duration:MM:SS} non commentato (la riga non deve iniziare con #)
        _dur_explicit = None
        for _line in lines_all:
            _ls = _line.strip()
            if _ls.startswith('#'):
                continue  # riga commentata → ignora
            _m = re.search(r'\{\s*duration\s*:\s*(\d{1,2}:\d{2})\s*\}', _ls, re.IGNORECASE)
            if _m:
                _dur_explicit = _m.group(1)
                break

        if _dur_explicit:
            # Durata dichiarata esplicitamente nel brano
            duration_str = _dur_explicit
            duration_is_explicit = True
        else:
            # Nessuna {duration:} attiva → calcolo automatico
            try:
                bpm   = int(re.search(r'\d+', song_tempo).group()) if song_tempo else 0
                num_m = int(re.search(r'(\d+)/', song_time).group(1)) if song_time else 0
                # conta i cambi accordo come battute approssimate
                if bpm > 0 and num_m > 0 and n_chords_total > 0:
                    beats_total = n_chords_total * num_m  # stima grossolana
                    secs = beats_total / bpm * 60
                    duration_str = '%d:%02d' % (int(secs) // 60, int(secs) % 60)
            except Exception:
                pass

        # ── 8. Valutazione complessiva ────────────────────────────────
        # Punteggio 0-100, poi mappiamo su stelle e giudizio
        score = 100

        # Troppi accordi unici = difficile
        if n_chords_unique > 12:
            score -= min(30, (n_chords_unique - 12) * 3)
        # Accordi difficili
        score -= int(pct_hard * 0.4)
        # Struttura complessa
        if n_verses + n_chorus > 8:
            score -= 10
        # Brano vuoto o quasi
        if n_chords_total == 0:
            score = 0
        score = max(0, min(100, score))

        if score >= 85:
            stars, verdict = '★★★★★', _('Excellent for beginners')
        elif score >= 70:
            stars, verdict = '★★★★☆', _('Accessible')
        elif score >= 50:
            stars, verdict = '★★★☆☆', _('Intermediate')
        elif score >= 30:
            stars, verdict = '★★☆☆☆', _('Advanced')
        else:
            stars, verdict = '★☆☆☆☆', _('Very difficult')

        # ── 9. Costruzione dialogo ────────────────────────────────────
        dlg = wx.Dialog(
            self.frame,
            title=_('Song Statistics'),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        dlg.SetMinSize(wx.Size(400, 300))

        BG      = wx.Colour(250, 250, 252)
        HDR     = wx.Colour(52, 101, 164)
        STAR_ON = wx.Colour(255, 180, 0)

        # ── Contenitore esterno (dialogo) ─────────────────────────────
        # Layout: intestazione fissa in cima + area scorrevole + OK fisso in fondo
        outer_panel = wx.Panel(dlg)
        outer_panel.SetBackgroundColour(BG)
        outer_sz = wx.BoxSizer(wx.VERTICAL)

        # ── Intestazione (fissa, non scorre) ──────────────────────────
        hdr_panel = wx.Panel(outer_panel)
        hdr_panel.SetBackgroundColour(HDR)
        hdr_sz = wx.BoxSizer(wx.VERTICAL)

        lbl_name = wx.StaticText(hdr_panel,
            label=song_title if song_title else _('(untitled)'))
        f = lbl_name.GetFont()
        f.SetWeight(wx.FONTWEIGHT_BOLD)
        f.SetPointSize(f.GetPointSize() + 3)
        lbl_name.SetFont(f)
        lbl_name.SetForegroundColour(wx.WHITE)

        if song_artist:
            lbl_artist = wx.StaticText(hdr_panel, label=song_artist)
            lbl_artist.SetForegroundColour(wx.Colour(200, 220, 255))

        hdr_sz.Add(lbl_name, 0, wx.ALL, 10)
        if song_artist:
            hdr_sz.Add(lbl_artist, 0, wx.LEFT | wx.BOTTOM, 10)
        hdr_panel.SetSizer(hdr_sz)
        outer_sz.Add(hdr_panel, 0, wx.EXPAND)

        # ── Area scorrevole ───────────────────────────────────────────
        # wx.VSCROLL: barra verticale automatica quando il contenuto supera l'altezza
        scroll = wx.ScrolledWindow(
            outer_panel,
            style=wx.VSCROLL | wx.BORDER_NONE,
        )
        scroll.SetScrollRate(0, 12)          # scorrimento verticale a passi di 12 px
        scroll.SetBackgroundColour(BG)

        body = wx.BoxSizer(wx.VERTICAL)

        # ── Valutazione con stelle ────────────────────────────────────
        eval_panel = wx.Panel(scroll)
        eval_panel.SetBackgroundColour(wx.Colour(240, 245, 255))
        eval_sz = wx.BoxSizer(wx.HORIZONTAL)

        lbl_stars = wx.StaticText(eval_panel, label=stars)
        f_stars = lbl_stars.GetFont()
        f_stars.SetPointSize(f_stars.GetPointSize() + 6)
        lbl_stars.SetFont(f_stars)
        lbl_stars.SetForegroundColour(STAR_ON)

        lbl_verdict = wx.StaticText(eval_panel, label='  ' + verdict)
        f_v = lbl_verdict.GetFont()
        f_v.SetWeight(wx.FONTWEIGHT_BOLD)
        lbl_verdict.SetFont(f_v)

        eval_sz.Add(lbl_stars,   0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)
        eval_sz.Add(lbl_verdict, 0, wx.ALIGN_CENTER_VERTICAL)
        eval_panel.SetSizer(eval_sz)
        body.Add(eval_panel, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 6)

        # ── Barra punteggio ───────────────────────────────────────────
        gauge = wx.Gauge(scroll, range=100, size=(-1, 8))
        gauge.SetValue(score)
        body.Add(gauge, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)

        body.AddSpacer(10)

        # ── Griglia statistiche ───────────────────────────────────────
        def _section(label):
            lbl = wx.StaticText(scroll, label=label)
            f2 = lbl.GetFont()
            f2.SetWeight(wx.FONTWEIGHT_BOLD)
            f2.SetPointSize(f2.GetPointSize() + 1)
            lbl.SetFont(f2)
            lbl.SetForegroundColour(HDR)
            body.Add(lbl, 0, wx.LEFT | wx.TOP, 12)
            body.Add(wx.StaticLine(scroll), 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        def _row(key, value):
            hz = wx.BoxSizer(wx.HORIZONTAL)
            k_lbl = wx.StaticText(scroll, label=key)
            v_lbl = wx.StaticText(scroll, label=str(value))
            fv = v_lbl.GetFont()
            fv.SetWeight(wx.FONTWEIGHT_BOLD)
            v_lbl.SetFont(fv)
            hz.Add(k_lbl, 1, wx.ALIGN_CENTER_VERTICAL)
            hz.Add(v_lbl, 0, wx.ALIGN_CENTER_VERTICAL)
            body.Add(hz, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 16)
            body.AddSpacer(3)

        _section(_('Structure'))
        _row(_('Verses'),          n_verses if n_verses else '—')
        _row(_('Choruses'),        n_chorus if n_chorus else '—')
        _row(_('Bridges'),         n_bridge if n_bridge else '—')
        _row(_('Estimated pages'), n_pages)

        _section(_('Lyrics'))
        _row(_('Lyrics lines'), n_lines)
        _row(_('Words'),        n_words)

        _section(_('Chords'))
        _row(_('Total chords'),   n_chords_total)
        _row(_('Unique chords'),  n_chords_unique)
        _row(_('Of which complex'),
             '%d  (%.0f%%)' % (n_hard, pct_hard) if n_chords_unique else '—')

        _section(_('Metadata'))
        if song_key:   _row(_('Key'),              song_key)
        if song_tempo: _row(_('Tempo'),             song_tempo + ' BPM')
        if song_time:  _row(_('Time signature'),    song_time)
        if song_capo:  _row(_('Capo'),              song_capo)
        if duration_str:
            if duration_is_explicit:
                _row(_('Duration'),           duration_str)
            else:
                _row(_('Estimated duration'), duration_str)

        if not any([song_key, song_tempo, song_time, song_capo]):
            body.Add(wx.StaticText(scroll,
                label=_('  (no musical metadata found)')),
                0, wx.LEFT | wx.BOTTOM, 16)

        body.AddSpacer(10)

        scroll.SetSizer(body)
        body.FitInside(scroll)          # comunica a ScrolledWindow le dimensioni virtuali

        outer_sz.Add(scroll, 1, wx.EXPAND)

        # ── Fondo: pulsante OK centrato + grip nell'angolo in basso a destra ──
        btn = wx.Button(outer_panel, wx.ID_OK, 'OK')
        btn.SetDefault()

        # Grip triangolare stile "Opzioni Songpress++" (immagine di riferimento)
        # Parametri misurati sul grip nativo wxPython di quella finestra:
        #   pannello 22×22 px, puntini 4×4, passo 7, colori sistema
        GRIP_SZ = 22
        grip = wx.Panel(outer_panel, size=(GRIP_SZ, GRIP_SZ))
        grip.SetBackgroundColour(outer_panel.GetBackgroundColour())

        def _on_grip_paint(evt, _g=grip, _sz=GRIP_SZ):
            dc = wx.PaintDC(_g)
            dc.SetBackground(wx.Brush(_g.GetBackgroundColour()))
            dc.Clear()
            dc.SetPen(wx.TRANSPARENT_PEN)
            # Colori identici al grip nativo wxPython/Windows:
            #   hi   = bianco puro       → bordo in alto-sinistra (rilievo)
            #   mid  = grigio medio A0   → corpo del quadratino
            #   sh   = grigio scuro 60   → bordo in basso-destra (ombra)
            col_hi  = wx.Colour(255, 255, 255)   # highlight bianco
            col_mid = wx.Colour(160, 160, 160)   # grigio medio (corpo)
            col_sh  = wx.Colour(96,  96,  96)    # grigio scuro (ombra)
            CELL = 7   # passo tra quadratini (uguale al grip nativo osservato)
            DOT  = 4   # lato totale del quadratino (hi 1px + corpo 2px + ombra 1px)
            # Griglia 3×3 ancorata in basso a destra, forma triangolare
            ox = _sz - 3 * CELL
            oy = _sz - 3 * CELL
            for row in range(3):
                for col in range(3):
                    if col + row < 2:
                        continue          # triangolo: salta metà alta-sinistra
                    x = ox + col * CELL
                    y = oy + row * CELL
                    # corpo grigio medio
                    dc.SetBrush(wx.Brush(col_mid))
                    dc.DrawRectangle(x, y, DOT, DOT)
                    # highlight: 1 px sopra e a sinistra
                    dc.SetBrush(wx.Brush(col_hi))
                    dc.DrawRectangle(x, y, DOT - 1, 1)       # bordo top
                    dc.DrawRectangle(x, y, 1, DOT - 1)       # bordo left
                    # ombra: 1 px sotto e a destra
                    dc.SetBrush(wx.Brush(col_sh))
                    dc.DrawRectangle(x + DOT - 1, y, 1, DOT) # bordo right
                    dc.DrawRectangle(x, y + DOT - 1, DOT, 1) # bordo bottom

        grip.Bind(wx.EVT_PAINT, _on_grip_paint)

        # riga inferiore: spazio sx | pulsante centrato | grip a destra
        bottom_sz = wx.BoxSizer(wx.HORIZONTAL)
        bottom_sz.AddStretchSpacer(1)
        bottom_sz.Add(btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM, 12)
        bottom_sz.AddStretchSpacer(1)
        bottom_sz.Add(grip, 0, wx.ALIGN_BOTTOM | wx.RIGHT | wx.BOTTOM, 1)
        outer_sz.Add(bottom_sz, 0, wx.EXPAND)

        outer_panel.SetSizer(outer_sz)

        dlg_sz = wx.BoxSizer(wx.VERTICAL)
        dlg_sz.Add(outer_panel, 1, wx.EXPAND)
        dlg.SetSizer(dlg_sz)

        # Calcola l'altezza ideale (contenuto completo) e limita al 90% dello schermo
        dlg.Fit()
        ideal_h = dlg.GetBestSize().GetHeight()
        screen_h = wx.Display().GetClientArea().GetHeight()
        max_h    = int(screen_h * 0.90)
        final_h  = min(ideal_h, max_h)
        dlg.SetSize(wx.Size(dlg.GetSize().GetWidth(), final_h))
        dlg.SetMinSize(wx.Size(400, 300))

        dlg.ShowModal()
        dlg.Destroy()

    def OnSyntaxGoto(self, evt):
        """Sposta il cursore alla riga/colonna dell'errore selezionato nel dialogo."""
        text = self.text.GetText()
        lines = text.splitlines(keepends=True)
        target_line = evt.line - 1    # 0-based
        target_col  = evt.column - 1  # 0-based
        pos = sum(len(l) for l in lines[:target_line]) + target_col
        pos = max(0, min(pos, len(text)))
        self.text.SetInsertionPoint(pos)
        self.text.SetFocus()

    def OnInsertLinespacing(self, evt):
        """Inserisce la direttiva {linespacing: <valore>}."""
        msg = _("Enter the line spacing value (e.g. 0 to remove extra space):")
        d = wx.NumberEntryDialog(self.frame, msg, _("Value:"), _("Line spacing"), 13, 0, 100)
        if d.ShowModal() == wx.ID_OK:
            val = d.GetValue()
            self.InsertWithCaret("{linespacing: %s}" % val) #modifica qui con x_linespacing

    def OnInsertChordtopspacing(self, evt):
        """Inserisce la direttiva {chordtopspacing: <valore>}."""
        msg = _("Enter the space above chords value (e.g. 0 to remove extra space):")
        d = wx.NumberEntryDialog(self.frame, msg, _("Value:"), _("Space above chords"), 0, 0, 100)
        if d.ShowModal() == wx.ID_OK:
            val = d.GetValue()
            self.InsertWithCaret("{chordtopspacing: %s}" % val)

    def OnInsertVerse(self, evt):
        """Inserisce una strofa non numerata: {start_verse} ... {end_verse}"""
        self.InsertWithCaret("{start_verse}\n|\n{end_verse}\n")

    def OnInsertVerseNum(self, evt):
        """Inserisce una strofa numerata: {start_verse_num} ... {end_verse_num}"""
        self.InsertWithCaret("{start_verse_num}\n|\n{end_verse_num}\n")

    def OnInsertChorusBlock(self, evt):
        """Insert a chorus block: {start_chorus} ... {end_chorus}"""
        default = self.pref.decoratorFormat.GetChorusLabel()
        label = wx.GetTextFromUser(
            _("Enter a label for the chorus, or press Cancel to omit the label."),
            _("Chorus label"),
            default,
            self.frame,
        )
        if label == default or not label.strip():
            self.InsertWithCaret("{start_chorus}\n|\n{end_chorus}\n")
        else:
            self.InsertWithCaret("{start_chorus:%s}\n|\n{end_chorus}\n" % label)

    def OnInsertChordBlock(self, evt):
        """Insert an intro chord block: {start_chord} ... {end_chord}"""
        default = _("Intro")
        label = wx.GetTextFromUser(
            _("Enter a label for the intro chords, or press Cancel to use '%s'.") % default,
            _("Intro chords label"),
            default,
            self.frame,
        )
        if label.strip():
            self.InsertWithCaret("{start_chord:%s}\n|\n{end_chord}\n" % label)
        else:
            self.InsertWithCaret("{start_chord}\n|\n{end_chord}\n")

    def OnInsertBridge(self, evt):
        """Insert a bridge block: {start_bridge} ... {end_bridge}"""
        default = _("Bridge")
        label = wx.GetTextFromUser(
            _("Enter a label for the bridge, or press Cancel to use '%s'.") % default,
            _("Bridge label"),
            default,
            self.frame,
        )
        if label.strip():
            self.InsertWithCaret("{start_bridge:%s}\n|\n{end_bridge}\n" % label)
        else:
            self.InsertWithCaret("{start_bridge}\n|\n{end_bridge}\n")

    def OnInsertGrid(self, evt):
        """Insert a grid block: {start_of_grid} ... {end_of_grid}"""
        default = getattr(self.pref, 'gridDefaultLabel', _("Grid"))
        label = wx.GetTextFromUser(
            _("Enter a label for the grid, or press Cancel to omit the label."),
            _("Grid label"),
            default,
            self.frame,
        )
        if label == default or not label.strip():
            self.InsertWithCaret("{start_of_grid}\n| | | |\n{end_of_grid}\n")
        else:
            self.InsertWithCaret("{start_of_grid:%s}\n| | | |\n{end_of_grid}\n" % label)

    def OnInsertTime(self, evt):
        """Inserisce la direttiva {time: <numeratore>/<denominatore>}."""
        d = wx.Dialog(self.frame, title=_("Time signature"))
        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(wx.StaticText(d, -1, _("Enter the time signature (e.g. 4/4, 3/4, 6/8):")), 0, wx.ALL, 8)
        txt = wx.TextCtrl(d, -1, "4/4")
        vbox.Add(txt, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        cb_meta = wx.CheckBox(d, -1, _("Metadata"))
        vbox.Add(cb_meta, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 8)

        is_meta = not getattr(self.pref, 'timeDisplay', True)
        cb_meta.SetValue(is_meta)
        txt.Enable(not is_meta)

        def on_meta(e):
            txt.Enable(not cb_meta.GetValue())
        cb_meta.Bind(wx.EVT_CHECKBOX, on_meta)

        btn_sizer = d.CreateButtonSizer(wx.OK | wx.CANCEL)
        vbox.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 8)
        d.SetSizer(vbox)
        vbox.Fit(d)

        if d.ShowModal() == wx.ID_OK:
            self.pref.timeDisplay = not cb_meta.GetValue()
            self.previewCanvas.SetTimeDisplay(self.pref.timeDisplay)
            val = txt.GetValue().strip()
            if val:
                self.InsertWithCaret("{time:%s}" % val)
            else:
                self.InsertWithCaret("{time:|}")
            self.previewCanvas.Refresh(self._get_display_text())
        d.Destroy()

    def OnInsertTempo(self, evt):
        """Inserisce la direttiva {tempo: <valore>}."""
        d = wx.Dialog(self.frame, title=_("Tempo"))
        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(wx.StaticText(d, -1, _("Enter the song tempo (e.g. 120):")), 0, wx.ALL, 8)
        txt = wx.TextCtrl(d, -1, "")
        vbox.Add(txt, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        vbox.Add(wx.StaticText(d, -1, _("Display as:")), 0, wx.LEFT | wx.TOP, 8)
        hbox_rb = wx.BoxSizer(wx.HORIZONTAL)
        rb_none = wx.RadioButton(d, -1, _("Tempo:  "), style=wx.RB_GROUP)
        rb_note = wx.RadioButton(d, -1, "")
        _icon_sz = getattr(self.pref, 'tempoIconSize', 24)
        _note_img = wx.Image(glb.AddPath("img/tempo_note.png"))
        _note_img = _note_img.Scale(_icon_sz, _icon_sz, wx.IMAGE_QUALITY_HIGH)
        note_bmp = wx.Bitmap(_note_img)
        note_icon = wx.StaticBitmap(d, -1, note_bmp)
        note_icon.Bind(wx.EVT_LEFT_DOWN, lambda e: rb_note.SetValue(True))
        rb_bpm  = wx.RadioButton(d, -1, "BPM")
        _metro_img = wx.Image(glb.AddPath("img/metronomeWindows.png"))
        _metro_img = _metro_img.Scale(_icon_sz, _icon_sz, wx.IMAGE_QUALITY_HIGH)
        metro_bmp = wx.Bitmap(_metro_img)
        metro_icon = wx.StaticBitmap(d, -1, metro_bmp)
        rb_metro = wx.RadioButton(d, -1, "")
        metro_icon.Bind(wx.EVT_LEFT_DOWN, lambda e: rb_metro.SetValue(True))
        hbox_rb.Add(rb_none, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)
        hbox_rb.Add(rb_note, 0, wx.ALIGN_CENTER_VERTICAL)
        hbox_rb.Add(note_icon, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)
        hbox_rb.Add(rb_bpm,  0, wx.ALIGN_CENTER_VERTICAL)
        hbox_rb.Add(rb_metro, 0, wx.ALIGN_CENTER_VERTICAL)
        hbox_rb.Add(metro_icon, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)
        vbox.Add(hbox_rb, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 8)

        cb_meta = wx.CheckBox(d, -1, _("Metadata"))
        vbox.Add(cb_meta, 0, wx.LEFT | wx.BOTTOM, 8)

        td = getattr(self.pref, 'tempoDisplay', 0)
        is_meta = (td == -1)
        cb_meta.SetValue(is_meta)
        rb_none.SetValue(td == 0)
        rb_note.SetValue(td == 1)
        rb_bpm.SetValue(td == 2)
        rb_metro.SetValue(td == 3)
        for ctrl in (rb_none, rb_note, rb_bpm, note_icon, rb_metro, metro_icon):
            ctrl.Enable(not is_meta)

        def on_meta(e):
            enabled = not cb_meta.GetValue()
            for ctrl in (rb_none, rb_note, rb_bpm, note_icon, rb_metro, metro_icon):
                ctrl.Enable(enabled)
        cb_meta.Bind(wx.EVT_CHECKBOX, on_meta)

        btn_sizer = d.CreateButtonSizer(wx.OK | wx.CANCEL)
        vbox.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 8)
        d.SetSizer(vbox)
        vbox.Fit(d)

        if d.ShowModal() == wx.ID_OK:
            val = txt.GetValue().strip()
            if cb_meta.GetValue():
                self.pref.tempoDisplay = -1
            elif rb_note.GetValue():
                self.pref.tempoDisplay = 1
            elif rb_bpm.GetValue():
                self.pref.tempoDisplay = 2
            elif rb_metro.GetValue():
                self.pref.tempoDisplay = 3
            else:
                self.pref.tempoDisplay = 0
            self.previewCanvas.SetTempoDisplay(self.pref.tempoDisplay)
            self.previewCanvas.SetTempoIconSize(getattr(self.pref, 'tempoIconSize', 24))
            self._SaveTempoDisplay()
            if val:
                self.InsertWithCaret("{tempo:%s}" % val)
            else:
                self.InsertWithCaret("{tempo:|}")
            self.previewCanvas.Refresh(self._get_display_text())
        d.Destroy()

    def OnInsertKey(self, evt):
        """Inserisce la direttiva {key: <tonalità>}."""
        d = wx.Dialog(self.frame, title=_(u"Key"))
        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(wx.StaticText(d, -1, _(u"Enter the song key (e.g. Am, C, G, F#m):")), 0, wx.ALL, 8)
        txt = wx.TextCtrl(d, -1, u"")
        vbox.Add(txt, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        # --- Rileva automaticamente ---
        cb_detect = wx.CheckBox(d, -1, _(u"Detect automatically from chords"))
        cb_detect.SetToolTip(_(
            u"Analyses the chords in the song (text between [ ]) "
            u"and fills in the most likely key automatically."))
        vbox.Add(cb_detect, 0, wx.LEFT | wx.TOP, 8)
        lbl_detect = wx.StaticText(d, -1, u"")
        lbl_detect.SetForegroundColour(wx.Colour(0, 100, 0))
        vbox.Add(lbl_detect, 0, wx.LEFT | wx.BOTTOM, 8)

        cb_meta = wx.CheckBox(d, -1, _("Metadata"))
        vbox.Add(cb_meta, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 8)

        is_meta = not getattr(self.pref, 'keyDisplay', True)
        cb_meta.SetValue(is_meta)
        txt.Enable(not is_meta)

        def _do_detect():
            """Rileva la tonalità dagli accordi del testo corrente."""
            try:
                t = self.text.GetText()
                notation = autodetectNotation(t, self.pref.notations)
                count, detected_key, dc, easiest_key, de = findEasiestKey(
                    t, self.pref.GetEasyChords(), notation)
                if count > 0 and detected_key:
                    # Converti nella notazione preferita dall'utente
                    key_str = translateChord(detected_key, notation, notation)
                    txt.SetValue(key_str)
                    lbl_detect.SetLabel(
                        _(u"✔ Detected: %s (from %d chords)") % (key_str, count))
                    lbl_detect.SetForegroundColour(wx.Colour(0, 120, 0))
                else:
                    txt.SetValue(u"")
                    lbl_detect.SetLabel(_(u"⚠ No chords found in the document"))
                    lbl_detect.SetForegroundColour(wx.Colour(180, 80, 0))
            except Exception:
                lbl_detect.SetLabel(_(u"⚠ Detection failed"))
                lbl_detect.SetForegroundColour(wx.Colour(180, 0, 0))
            d.Layout()
            d.Fit()

        def on_detect(e):
            if cb_detect.GetValue():
                txt.Enable(False)
                _do_detect()
            else:
                lbl_detect.SetLabel(u"")
                txt.SetValue(u"")
                txt.Enable(not cb_meta.GetValue())
                d.Layout()
                d.Fit()

        def on_meta(e):
            if not cb_detect.GetValue():
                txt.Enable(not cb_meta.GetValue())

        cb_detect.Bind(wx.EVT_CHECKBOX, on_detect)
        cb_meta.Bind(wx.EVT_CHECKBOX, on_meta)

        btn_sizer = d.CreateButtonSizer(wx.OK | wx.CANCEL)
        vbox.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 8)
        d.SetSizer(vbox)
        vbox.Fit(d)

        if d.ShowModal() == wx.ID_OK:
            self.pref.keyDisplay = not cb_meta.GetValue()
            self.previewCanvas.SetKeyDisplay(self.pref.keyDisplay)
            val = txt.GetValue().strip()
            if val:
                self.InsertWithCaret(u"{key:%s}" % val)
            else:
                self.InsertWithCaret(u"{key:|}")
            self.previewCanvas.Refresh(self._get_display_text())
        d.Destroy()

    def _InsertSimpleDirective(self, directive, label, example):
        """Helper generico: chiede un testo e inserisce {directive:testo}."""
        d = wx.TextEntryDialog(self.frame, label, directive, example)
        if d.ShowModal() == wx.ID_OK:
            val = d.GetValue().strip()
            if val:
                self.InsertWithCaret(u"{%s:%s}" % (directive, val))
            else:
                self.InsertWithCaret(u"{%s:|}" % directive)
        d.Destroy()

    def OnInsertCapo(self, evt):
        """Inserisce la direttiva {capo: <n>}."""
        self._InsertSimpleDirective('capo', _(u"Enter the capo fret number (e.g. 2, 3):"), u"2")

    def OnInsertArtist(self, evt):
        """Inserisce la direttiva {artist: <nome>}."""
        self._InsertSimpleDirective('artist', _(u"Enter the artist / performer name:"), u"")

    def OnInsertComposer(self, evt):
        """Inserisce la direttiva {composer: <nome>}."""
        self._InsertSimpleDirective('composer', _(u"Enter the composer name:"), u"")

    def OnInsertAlbum(self, evt):
        """Inserisce la direttiva {album: <titolo>}."""
        self._InsertSimpleDirective('album', _(u"Enter the album title:"), u"")

    def OnInsertYear(self, evt):
        """Inserisce la direttiva {year: <anno>}."""
        self._InsertSimpleDirective('year', _(u"Enter the year (e.g. 1975):"), u"")

    def OnInsertBeatsTime(self, evt):
        """Inserisce la direttiva {beats_time: }.
        
        Se nella riga immediatamente successiva al cursore sono presenti accordi
        nella forma [Accordo], propone un dialogo per assegnare il numero di battiti
        a ciascun accordo, producendo {beats_time: DO=2 SOL=1 ...}.
        In caso contrario inserisce semplicemente {beats_time: }.
        """
        import re

        # ── 1. Leggi la riga successiva a quella corrente ────────────────
        stc       = self.text
        cur_pos   = stc.GetCurrentPos()
        cur_line  = stc.LineFromPosition(cur_pos)
        next_line = cur_line + 1
        next_text = stc.GetLine(next_line) if next_line < stc.GetLineCount() else u""

        # ── 2. Estrai accordi unici mantenendo l'ordine di comparsa ──────
        raw_chords = re.findall(r'\[([^\]]+)\]', next_text)
        # rimuovi suffissi di basso (tutto dopo '/') e tieni unici in ordine
        seen   = {}
        chords = []
        for c in raw_chords:
            root = c.split('/')[0].strip()
            if root and root not in seen:
                seen[root] = True
                chords.append(root)

        # ── 3a. Nessun accordo trovato: inserimento semplice ─────────────
        if not chords:
            self.InsertWithCaret(u"{beats_time: }")
            return

        # ── 3b. Accordi trovati: dialogo per i battiti ───────────────────
        dlg = wx.Dialog(
            self.frame,
            title=_(u"Beats_time — beats per chord"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        outer = wx.BoxSizer(wx.VERTICAL)

        # Istruzione
        lbl_intro = wx.StaticText(
            dlg,
            label=_(u"Assign the number of beats to each chord.\n"
                    u"Leave blank to omit a chord from the directive.")
        )
        outer.Add(lbl_intro, 0, wx.ALL, 10)

        # Griglia accordo → SpinCtrl
        grid = wx.FlexGridSizer(cols=2, hgap=8, vgap=6)
        grid.AddGrowableCol(1)
        spin_map = {}   # root → SpinCtrl

        for chord in chords:
            grid.Add(
                wx.StaticText(dlg, label=chord),
                0, wx.ALIGN_CENTER_VERTICAL
            )
            spin = wx.SpinCtrl(dlg, value=u"1", min=0, max=32, initial=1, size=(70, -1))
            # 0 = ometti
            spin.SetToolTip(_(u"0 = omit this chord"))
            grid.Add(spin, 0, wx.EXPAND)
            spin_map[chord] = spin

        outer.Add(grid, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Anteprima della direttiva generata
        lbl_preview_title = wx.StaticText(dlg, label=_(u"Preview:"))
        outer.Add(lbl_preview_title, 0, wx.LEFT | wx.RIGHT, 10)
        lbl_preview = wx.StaticText(dlg, label=u"")
        lbl_preview.SetForegroundColour(wx.Colour(0, 100, 0))
        font_preview = lbl_preview.GetFont()
        font_preview.SetFamily(wx.FONTFAMILY_TELETYPE)
        lbl_preview.SetFont(font_preview)
        outer.Add(lbl_preview, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        btn_sizer = dlg.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        outer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 8)

        dlg.SetSizerAndFit(outer)
        dlg.CentreOnParent()

        def _update_preview(_evt=None):
            parts = []
            for ch in chords:
                v = spin_map[ch].GetValue()
                if v > 0:
                    parts.append(u"%s=%d" % (ch, v))
            directive = u"{beats_time: %s}" % u" ".join(parts) if parts else u"{beats_time: }"
            lbl_preview.SetLabel(directive)
            dlg.Layout()

        for sp in spin_map.values():
            sp.Bind(wx.EVT_SPINCTRL, _update_preview)
            sp.Bind(wx.EVT_TEXT,     _update_preview)

        _update_preview()   # mostra anteprima iniziale

        if dlg.ShowModal() == wx.ID_OK:
            parts = []
            for ch in chords:
                v = spin_map[ch].GetValue()
                if v > 0:
                    parts.append(u"%s=%d" % (ch, v))
            directive = u"{beats_time: %s}" % u" ".join(parts) if parts else u"{beats_time: }"
            self.InsertWithCaret(directive)

        dlg.Destroy()

    def OnInsertMusicalSymbol(self, evt):
        """Apre la Symbol Map musicale e inserisce il carattere scelto nel cursore."""
        scale_enabled  = getattr(self.pref, 'symbolScaleEnabled', False)
        font_size      = getattr(self.pref, 'symbolFontSize', 24)
        insert_verse   = getattr(self.pref, 'symbolInsertVerse', False)

        dlg = MusicalSymbolDialog(self.frame,
                                  scale_enabled=scale_enabled,
                                  font_size=font_size,
                                  insert_verse=insert_verse)
        if dlg.ShowModal() == wx.ID_OK:
            sym = dlg.GetSymbol()
            if sym:
                self.InsertWithCaret(sym)

        # Aggiorna pref in memoria (senza salvare su disco: ci pensa pref.Save() in OnOK)
        self.pref.symbolScaleEnabled = dlg.GetScaleEnabled()
        self.pref.symbolFontSize     = dlg.GetFontSize()
        self.pref.symbolInsertVerse  = dlg.GetInsertVerse()
        dlg.Destroy()

    def OnAbout(self, evt):
        """Mostra la finestra About con link cliccabili."""
        translations = "\n".join([
            u"- {}: {}".format(glb.languages[x], glb.translators[x])
            for x in glb.languages
        ])
        dlg = wx.Dialog(self.frame, title=_("About Songpress++ - The Song Editor"))
        dlg.SetBackgroundColour(wx.WHITE)
        panel = wx.Panel(dlg)
        panel.SetBackgroundColour(wx.WHITE)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Icona + titolo
        try:
            icon_path = glb.AddPath('img/songpress++.ico')
            icon_bmp = wx.StaticBitmap(panel, bitmap=wx.Bitmap(icon_path, wx.BITMAP_TYPE_ICO))
            hbox_title = wx.BoxSizer(wx.HORIZONTAL)
            hbox_title.Add(icon_bmp, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
            title_lbl = wx.StaticText(panel, label=u"Songpress++ - The Song Editor {}".format(glb.VERSION))
            font_title = title_lbl.GetFont()
            font_title.SetWeight(wx.FONTWEIGHT_BOLD)
            font_title.SetPointSize(font_title.GetPointSize() + 2)
            title_lbl.SetFont(font_title)
            hbox_title.Add(title_lbl, 0, wx.ALIGN_CENTER_VERTICAL)
            vbox.Add(hbox_title, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        except Exception:
            title_lbl = wx.StaticText(panel, label=u"Songpress++ - The Song Editor {}".format(glb.VERSION))
            vbox.Add(title_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        def add_text(text):
            lbl = wx.StaticText(panel, label=text)
            vbox.Add(lbl, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 15)

        def add_link(label, url):
            lnk = wx.adv.HyperlinkCtrl(panel, label=label, url=url)
            vbox.Add(lnk, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 15)

        add_text(u"Copyright \u00a9 2009-{} Luca Allulli - Skeed".format(glb.YEAR))
        add_text(u"Copyright \u00a9 2026-{} Denisov21".format(glb.YEAR))
        add_text(u"Localization:\n{}".format(translations))
        vbox.AddSpacer(8)
        add_text(_(u"Songpress++ is a fork of Songpress by Luca Allulli - Skeed,"))
        add_text(_(u"maintained and extended by Denisov21."))
        vbox.AddSpacer(4)
        add_link(_(u"Original version website: http://www.skeed.it/songpress"), "http://www.skeed.it/songpress")
        add_link(_(u"Fork repository: https://github.com/Denisov21/Songpressplusplus"), "https://github.com/Denisov21/Songpressplusplus")
        vbox.AddSpacer(8)
        add_text(_(u"Licensed under the terms and conditions of the GNU General Public License, version 2"))
        vbox.AddSpacer(8)
        add_text(_(
            u"Special thanks to:\n"
            u"  * The Python programming language (http://www.python.org)\n"
            u"  * wxWidgets (http://www.wxwidgets.org)\n"
            u"  * wxPython (http://www.wxpython.org)\n"
            u"  * Editra (http://editra.org/) (for the error reporting dialog and... the editor itself!)\n"
            u"  * python-pptx (for PowerPoint export)"
        ))
        vbox.AddSpacer(10)

        btn_ok = wx.Button(panel, wx.ID_OK, "OK")
        vbox.Add(btn_ok, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        panel.SetSizer(vbox)
        vbox.Fit(panel)
        dlg_sizer = wx.BoxSizer(wx.VERTICAL)
        dlg_sizer.Add(panel, 1, wx.EXPAND)
        dlg.SetSizer(dlg_sizer)
        dlg_sizer.Fit(dlg)
        dlg.ShowModal()
        dlg.Destroy()

    def OnInsertCopyright(self, evt):
        """Inserisce la direttiva {copyright: <testo>}."""
        self._InsertSimpleDirective('copyright', _(u"Enter the copyright text:"), u"")

    def OnInsertKlavierChord(self, evt):
        """Inserts the {taste:<chord>} directive for a chord keyboard display (klavier)."""
        d = wx.TextEntryDialog(
            self.frame,
            _("Enter the chord name (e.g. C, G, Am, D7):"), 
            _("Chord keys"),
            "",
        )
        if d.ShowModal() == wx.ID_OK:
            chord = d.GetValue().strip()
            if chord:
                self.InsertWithCaret("{taste:%s}" % chord)
            else:
                self.InsertWithCaret("{taste:|}")
        d.Destroy()

    def OnInsertDefine(self, evt):
        """Inserts the {define:} directive for a guitar chord diagram."""
        d = wx.TextEntryDialog(
            self.frame,
            _("Enter chord definition (e.g. C base-fret 1 frets X 3 2 0 1 0):"),
            _("Guitar chord diagram"),
            "",
        )
        if d.ShowModal() == wx.ID_OK:
            value = d.GetValue().strip()
            if value:
                self.InsertWithCaret("{define: %s}" % value)
            else:
                self.InsertWithCaret("{define: |}")
        d.Destroy()

    def OnInsertFingering(self, evt):
        """Dialog per {fingering:} — accordo + numero dito per ogni nota."""

        # ── Notazione corrente dalle preferenze ───────────────────────
        _cur_notation = self.pref.notations[0] if self.pref.notations else None

        # Notazione italiana di riferimento (usata da KlavierRenderer)
        _it_notation = None
        for _n in self.pref.notations:
            if hasattr(_n, 'id') and ('it' in _n.id.lower() or 'italian' in _n.id.lower()):
                _it_notation = _n
                break

        # Mappa semitono → nome nota nella notazione italiana (base per KlavierRenderer)
        _IT_12 = ['Do', 'Do#', 'Re', 'Re#', 'Mi', 'Fa',
                  'Fa#', 'Sol', 'Sol#', 'La', 'La#', 'Si']

        def _semi_to_note(semi):
            """Restituisce il nome della nota (semitono 0-11) nella notazione corrente."""
            it_name = _IT_12[semi % 12]
            if _cur_notation is None or _it_notation is None:
                return it_name
            try:
                return translateChord(it_name, _it_notation, _cur_notation)
            except Exception:
                return it_name

        def _chord_to_it(chord_str):
            """Converte un accordo dalla notazione corrente all'italiana per il parser."""
            if _cur_notation is None or _it_notation is None:
                return chord_str
            try:
                return translateChord(chord_str, _cur_notation, _it_notation)
            except Exception:
                return chord_str

        # Note italiane -> semitono (per il parser interno)
        _IT_SEMITONE = {
            'do': 0,  'do#': 1, 'dob': 11,
            're': 2,  're#': 3, 'reb': 1,
            'mi': 4,  'mi#': 5, 'mib': 3,
            'fa': 5,  'fa#': 6, 'fab': 4,
            'sol': 7, 'sol#': 8,'solb': 6,
            'la': 9,  'la#': 10,'lab': 8,
            'si': 11, 'si#': 0, 'sib': 10,
        }
        _CHORD_INTERVALS = [
            ('maj7', [0,4,7,11]), ('maj', [0,4,7]),
            ('m7b5', [0,3,6,10]), ('m7',  [0,3,7,10]),
            ('min',  [0,3,7]),    ('m',   [0,3,7]),
            ('dim7', [0,3,6,9]), ('dim',  [0,3,6]),
            ('aug',  [0,4,8]),   ('sus4', [0,5,7]),
            ('sus2', [0,2,7]),   ('7',    [0,4,7,10]),
            ('5',    [0,7]),     ('-',    [0,3,7]),
            ('',     [0,4,7]),
        ]

        def chord_semitones(chord_str):
            """
            Parsa chord_str nella notazione corrente, restituisce i nomi delle
            note dell'accordo nella notazione corrente (per la griglia dita).
            """
            # Normalizza verso italiano per il parser
            it_chord = _chord_to_it(chord_str.strip())
            sl = it_chord.lower()
            root = None; rest = ''
            for name, semi in sorted(_IT_SEMITONE.items(), key=lambda x: -len(x[0])):
                if sl.startswith(name):
                    root = semi; rest = it_chord[len(name):]; break
            if root is None:
                return []
            rest = rest.split('/')[0].strip()
            ivs = [0, 4, 7]
            for suffix, intervals in _CHORD_INTERVALS:
                if rest.lower().startswith(suffix.lower()):
                    ivs = intervals; break
            # Restituisce i nomi nella notazione corrente
            return [_semi_to_note((root + i) % 12) for i in ivs]

        # ── Costruisce il dialog ──────────────────────────────────────
        dlg = wx.Dialog(self.frame, title=_(u"First chord fingering"),
                        style=wx.DEFAULT_DIALOG_STYLE)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Campo accordo
        hbox_chord = wx.BoxSizer(wx.HORIZONTAL)
        hbox_chord.Add(wx.StaticText(dlg, -1, _(u"Chord:")),
                       0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        txt_chord = wx.TextCtrl(dlg, -1, u"", size=(120, -1))
        hbox_chord.Add(txt_chord, 0)
        vbox.Add(hbox_chord, 0, wx.ALL, 10)

        # Mano destra / sinistra
        hbox_hand = wx.BoxSizer(wx.HORIZONTAL)
        hbox_hand.Add(wx.StaticText(dlg, -1, _(u"Hand:")),
                      0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        rb_right = wx.RadioButton(dlg, -1, _(u"Right"), style=wx.RB_GROUP)
        rb_left  = wx.RadioButton(dlg, -1, _(u"Left"))
        rb_right.SetValue(True)
        hbox_hand.Add(rb_right, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        hbox_hand.Add(rb_left,  0, wx.ALIGN_CENTER_VERTICAL)
        vbox.Add(hbox_hand, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Istruzione
        lbl_info = wx.StaticText(
            dlg, -1,
            _(u"Assign a finger number to each note of the chord.\n"
              u"(1=thumb  2=index  3=middle  4=ring  5=little)\n"
              u"Leave '\u2014' for fingers not used."))
        vbox.Add(lbl_info, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Pannello contenitore per la griglia — viene ricostruita dinamicamente
        grid_panel = wx.Panel(dlg, -1)
        grid_panel.SetSizer(wx.BoxSizer(wx.VERTICAL))   # sizer vuoto iniziale
        vbox.Add(grid_panel, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Anteprima direttiva
        vbox.Add(wx.StaticLine(dlg), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
        vbox.Add(wx.StaticText(dlg, -1, _(u"Directive preview:")),
                 0, wx.LEFT | wx.TOP, 10)
        txt_preview = wx.TextCtrl(dlg, -1, u"{fingering: }",
                                  style=wx.TE_READONLY)
        txt_preview.SetBackgroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        vbox.Add(txt_preview, 0, wx.EXPAND | wx.ALL, 10)

        # ── Checkbox anteprima tastiera ───────────────────────────────
        cb_kbd = wx.CheckBox(dlg, -1, _(u"Show keyboard preview"))
        vbox.Add(cb_kbd, 0, wx.LEFT | wx.BOTTOM, 10)

        # Pannello di anteprima tastiera (visibile solo se checkbox attiva)
        _KBD_WHITE_W = 18
        _KBD_W       = _KBD_WHITE_W * 7   # 126 px
        _KBD_H       = 50
        _LABEL_H     = 18
        _PANEL_W     = _KBD_W + 40
        _PANEL_H     = _LABEL_H + _KBD_H + 10

        kbd_panel = wx.Panel(dlg, -1, size=(_PANEL_W, _PANEL_H))
        kbd_panel.SetBackgroundColour(wx.WHITE)
        kbd_panel.Show(False)
        vbox.Add(kbd_panel, 0, wx.LEFT | wx.BOTTOM, 10)

        def _draw_kbd_preview(event=None):
            """Ridisegna il mini-pannello tastiera con la diteggiatura attuale."""
            dc = wx.PaintDC(kbd_panel) if event is not None else wx.ClientDC(kbd_panel)
            dc.Clear()

            chord = txt_chord.GetValue().strip()
            if not chord:
                return

            # Ricava semitoni accordo e finger_map dalla direttiva corrente
            directive_text = txt_preview.GetValue()
            # Estrae la parte interna di {fingering: ...}
            import re as _re
            m = _re.match(r'\{fingering:\s*(.*)\}', directive_text)
            inner = m.group(1).strip() if m else chord
            chord_name, finger_map, _hand = KlavierRenderer.parse_fingering(inner)
            if chord_name is None:
                chord_name = chord
                finger_map = {}

            keys = KlavierRenderer.get_chord_keys(chord_name)
            if keys is None:
                return

            ox = 14   # offset x
            oy = _LABEL_H + 4   # offset y per la tastiera

            # ── Etichetta mano (sinistra/destra) ─────────────────────
            hand_font = wx.Font(
                8, wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            dc.SetFont(hand_font)
            dc.SetTextForeground(wx.Colour(80, 80, 80))
            hand_str = _(u"Right hand") if rb_right.GetValue() else _(u"Left hand")
            hw, _hh = dc.GetTextExtent(hand_str)
            dc.DrawText(hand_str, ox + _KBD_W - hw, 2)

            # ── Etichetta accordo in grassetto ────────────────────────
            label_font = wx.Font(
                8, wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

            # ── Tastiera (colori dalle preferenze) ────────────────────
            highlight_color  = self._getKlavierHighlightColour()
            finger_num_color = self._getFingerNumColour()
            KlavierRenderer.draw_keyboard(
                dc, ox, oy, _KBD_W, _KBD_H,
                chord_name, keys, label_font,
                highlight_color, finger_map=finger_map,
                finger_num_color=finger_num_color,
            )

        kbd_panel.Bind(wx.EVT_PAINT, _draw_kbd_preview)

        def _refresh_kbd(e=None):
            if kbd_panel.IsShown():
                kbd_panel.Refresh()

        def _on_cb_kbd(e=None):
            kbd_panel.Show(cb_kbd.GetValue())
            vbox.Layout()
            vbox.Fit(dlg)
            if cb_kbd.GetValue():
                kbd_panel.Refresh()

        cb_kbd.Bind(wx.EVT_CHECKBOX, _on_cb_kbd)

        btn_sizer = dlg.CreateButtonSizer(wx.OK | wx.CANCEL)
        vbox.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 8)
        dlg.SetSizer(vbox)

        # ── Stato dinamico ────────────────────────────────────────────
        finger_choices = [u"\u2014", u"1", u"2", u"3", u"4", u"5"]
        current_notes  = []   # note attuali
        note_rows      = []   # (StaticText, Choice) correnti

        def _build():
            chord = txt_chord.GetValue().strip()
            if not chord:
                return u"{fingering: }"
            hand = u"R" if rb_right.GetValue() else u"L"
            parts = [chord, u"hand=%s" % hand]
            for i, (lbl, ch) in enumerate(note_rows):
                sel = ch.GetSelection()
                if sel > 0:
                    parts.append(u"%d=%s" % (sel, current_notes[i]))
            return u"{fingering: %s}" % u" ".join(parts)

        def _update_preview(e=None):
            txt_preview.SetValue(_build())
            _refresh_kbd()

        def _rebuild_grid(notes):
            """Distrugge e ricrea la griglia nel grid_panel con le note date."""
            note_rows.clear()
            # Rimuovi tutti i figli esistenti
            for child in grid_panel.GetChildren():
                child.Destroy()

            if not notes:
                grid_panel.GetSizer().Layout()
                return

            # FlexGridSizer: 2 colonne, righe variabili
            fgs = wx.FlexGridSizer(cols=2, vgap=6, hgap=12)
            fgs.Add(wx.StaticText(grid_panel, -1, _(u"Note")),
                    0, wx.ALIGN_CENTER)
            fgs.Add(wx.StaticText(grid_panel, -1, _(u"Finger")),
                    0, wx.ALIGN_CENTER)
            for note in notes:
                lbl = wx.StaticText(grid_panel, -1, note)
                ch  = wx.Choice(grid_panel, -1, choices=finger_choices)
                ch.SetSelection(0)
                ch.Bind(wx.EVT_CHOICE, _update_preview)
                fgs.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)
                fgs.Add(ch,  0, wx.ALIGN_CENTER_VERTICAL)
                note_rows.append((lbl, ch))

            # Sostituisce il sizer del panel
            grid_panel.SetSizer(fgs)
            fgs.Layout()

        def _on_chord_change(e=None):
            chord = txt_chord.GetValue().strip()
            notes = chord_semitones(chord) if chord else []
            current_notes.clear()
            current_notes.extend(notes)
            _rebuild_grid(notes)
            # Ricalcola il layout dell'intero dialog
            vbox.Layout()
            vbox.Fit(dlg)
            _update_preview()

        txt_chord.Bind(wx.EVT_TEXT, _on_chord_change)
        rb_right.Bind(wx.EVT_RADIOBUTTON, lambda e: (_update_preview(), _refresh_kbd()))
        rb_left.Bind(wx.EVT_RADIOBUTTON,  lambda e: (_update_preview(), _refresh_kbd()))

        vbox.Fit(dlg)
        dlg.CentreOnParent()

        if dlg.ShowModal() == wx.ID_OK:
            directive = _build()
            if directive != u"{fingering: }":
                self.InsertWithCaret(directive)
            else:
                self.InsertWithCaret(u"{fingering: |}")
        dlg.Destroy()

    def OnImportFromPdf(self, evt):
        """Import text from a PDF file (selectable text only, no OCR)."""
        try:
            from pypdf import PdfReader
        except ImportError:
            wx.MessageBox(
                _("La libreria pypdf non è installata.\nInstalla con:  pip install pypdf"),
                _("pypdf non trovato"),
                wx.OK | wx.ICON_ERROR,
                self.frame,
            )
            return

        with wx.FileDialog(
            self.frame,
            _("Import text from PDF"),
            wildcard=_("PDF files (*.pdf)|*.pdf"),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            path = dlg.GetPath()

        try:
            reader = PdfReader(path)
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages).strip()
        except Exception as e:
            wx.MessageBox(
                _("Error reading the PDF:\n%s") % str(e),
                _("Import error"),
                wx.OK | wx.ICON_ERROR,
                self.frame,
            )
            return

        if not text:
            wx.MessageBox(
                _("The PDF contains no extractable text.\nIt may be a scanned (image-only) PDF."),
                _("No text found"),
                wx.OK | wx.ICON_WARNING,
                self.frame,
            )
            return

        if not self.AskSaveModified():
            return

        self.document = ''
        self.text.AutoChangeMode(True)
        self.text.New()
        self.text.SetText(text)
        self.text.AutoChangeMode(False)
        self.SetModified()

    def OnInsertImage(self, evt):
        """Dialog per inserire {image: ...} con selezione file e parametri."""
        doc = getattr(self, 'document', '') or ''
        default_dir = os.path.dirname(os.path.abspath(doc)) if doc else ''
        # Estensione del file documento corrente (dalle preferenze)
        doc_ext = getattr(getattr(self, 'pref', None), 'defaultExtension', None) or 'crd'''

        d = wx.Dialog(self.frame, title=_("Insert image"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # --- File ---
        vbox.Add(wx.StaticText(d, -1, _("Image file:")), 0, wx.LEFT | wx.TOP, 8)
        hbox_file = wx.BoxSizer(wx.HORIZONTAL)
        txt_path = wx.TextCtrl(d, -1, "", size=(300, -1))
        btn_browse = wx.Button(d, -1, _("Browse..."))
        hbox_file.Add(txt_path, 1, wx.EXPAND | wx.RIGHT, 4)
        hbox_file.Add(btn_browse, 0)
        vbox.Add(hbox_file, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # --- Dimensioni ---
        gb = wx.GridBagSizer(4, 8)

        # Width — SpinCtrlDouble: solo interi (step=1), vuoto = non specificato
        gb.Add(wx.StaticText(d, -1, _("Width:")), pos=(0, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        txt_w = wx.SpinCtrlDouble(d, -1, "", min=0, max=9999, inc=1, size=(70, -1))
        txt_w.SetDigits(0)
        txt_w.SetValue(0)
        gb.Add(txt_w, pos=(0, 1), flag=wx.EXPAND)
        ch_w_unit = wx.Choice(d, -1, choices=["pt", "%"])
        ch_w_unit.SetSelection(0)   # default: pt
        gb.Add(ch_w_unit, pos=(0, 2), flag=wx.ALIGN_CENTER_VERTICAL)

        # Height — SpinCtrlDouble: solo interi
        gb.Add(wx.StaticText(d, -1, _("Height:")), pos=(1, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        txt_h = wx.SpinCtrlDouble(d, -1, "", min=0, max=9999, inc=1, size=(70, -1))
        txt_h.SetDigits(0)
        txt_h.SetValue(0)
        gb.Add(txt_h, pos=(1, 1), flag=wx.EXPAND)
        ch_h_unit = wx.Choice(d, -1, choices=["pt", "%"])
        ch_h_unit.SetSelection(0)   # default: pt
        gb.Add(ch_h_unit, pos=(1, 2), flag=wx.ALIGN_CENTER_VERTICAL)

        # Scale — SpinCtrlDouble: valori decimali 1–500, step 1
        gb.Add(wx.StaticText(d, -1, _("Scale:")), pos=(2, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        txt_scale = wx.SpinCtrlDouble(d, -1, "", min=1, max=500, inc=1, size=(70, -1))
        txt_scale.SetDigits(1)
        txt_scale.SetValue(100)
        gb.Add(txt_scale, pos=(2, 1), flag=wx.EXPAND)
        gb.Add(wx.StaticText(d, -1, "%"), pos=(2, 2), flag=wx.ALIGN_CENTER_VERTICAL)

        vbox.Add(gb, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # --- Allineamento ---
        hbox_align = wx.BoxSizer(wx.HORIZONTAL)
        hbox_align.Add(wx.StaticText(d, -1, _("Align:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        rb_left   = wx.RadioButton(d, -1, _("Left"),   style=wx.RB_GROUP)
        rb_center = wx.RadioButton(d, -1, _("Center"))
        rb_right  = wx.RadioButton(d, -1, _("Right"))
        rb_center.SetValue(True)
        hbox_align.Add(rb_left,   0, wx.RIGHT, 8)
        hbox_align.Add(rb_center, 0, wx.RIGHT, 8)
        hbox_align.Add(rb_right,  0)
        vbox.Add(hbox_align, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # --- Bordo ---
        hbox_border = wx.BoxSizer(wx.HORIZONTAL)
        cb_border = wx.CheckBox(d, -1, _("Border (pt):"))
        txt_border = wx.SpinCtrlDouble(d, -1, "", min=0, max=50, inc=0.5, size=(60, -1))
        txt_border.SetDigits(1)
        txt_border.SetValue(1)
        txt_border.Enable(False)
        hbox_border.Add(cb_border, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        hbox_border.Add(txt_border, 0)
        vbox.Add(hbox_border, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # --- Incorpora nel file ---
        vbox.Add(wx.StaticLine(d), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
        cb_embed = wx.CheckBox(d, -1, _("Embed image in file (base64, no external dependency)"))
        cb_embed.SetToolTip(
            _("If checked, the image data is encoded in base64 and stored directly "
              "inside the .crd file. The song becomes self-contained but the file "
              "size grows. If unchecked, only the file path is stored (link)."
            ).replace(".crd", ".%s" % doc_ext))
        vbox.Add(cb_embed, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        lbl_embed_warn = wx.StaticText(d, -1, "")
        lbl_embed_warn.SetForegroundColour(wx.Colour(160, 100, 0))
        vbox.Add(lbl_embed_warn, 0, wx.LEFT | wx.BOTTOM, 8)

        # --- Anteprima direttiva ---
        vbox.Add(wx.StaticLine(d), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
        vbox.Add(wx.StaticText(d, -1, _("Directive preview:")), 0, wx.LEFT | wx.TOP, 8)
        txt_preview = wx.TextCtrl(d, -1, "{image: }", style=wx.TE_READONLY)
        txt_preview.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        vbox.Add(txt_preview, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        btn_sizer = d.CreateButtonSizer(wx.OK | wx.CANCEL)
        vbox.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 8)
        d.SetSizer(vbox)
        vbox.Fit(d)

        # --- Funzione aggiornamento anteprima ---
        def _build_options():
            """Restituisce la lista delle opzioni (width, height, scale, align, border)
            come lista di stringhe, indipendentemente dal path/token dell'immagine.
            Condivisa tra anteprima e inserimento finale."""
            opts = []
            w = int(txt_w.GetValue())
            if w > 0:
                unit = ch_w_unit.GetStringSelection()
                opts.append("width=%d%s" % (w, "%" if unit == "%" else ""))
            h = int(txt_h.GetValue())
            if h > 0:
                unit = ch_h_unit.GetStringSelection()
                opts.append("height=%d%s" % (h, "%" if unit == "%" else ""))
            sc = txt_scale.GetValue()
            if sc != 100.0:
                opts.append("scale=%g%%" % sc)
            if rb_left.GetValue():
                opts.append("align=left")
            elif rb_right.GetValue():
                opts.append("align=right")
            # center è il default, non serve scriverlo
            if cb_border.GetValue():
                bv = txt_border.GetValue()
                opts.append("border=%g" % bv if bv != 1.0 else "border")
            return opts

        def _build_directive(for_insert=False):
            """Costruisce la stringa della direttiva {image: ...}.

            Se for_insert=True e la checkbox 'incorpora' è attiva, il file viene
            letto, codificato in base64 e incorporato direttamente come data: URI.
            Altrimenti viene usato il percorso (relativo se nella stessa cartella).
            """
            path = txt_path.GetValue().strip()
            if not path:
                return "{image: }"

            embed = cb_embed.GetValue()

            if for_insert and embed and os.path.isfile(path):
                # ── Incorpora come data: URI base64 ──────────────────────
                import base64, mimetypes
                mime = mimetypes.guess_type(path)[0] or "image/png"
                with open(path, "rb") as _f:
                    b64 = base64.b64encode(_f.read()).decode("ascii")
                path_token = "data:%s;base64,%s" % (mime, b64)
            else:
                # ── Percorso file (relativo o assoluto) ──────────────────
                if default_dir and os.path.isabs(path):
                    try:
                        if os.path.dirname(os.path.abspath(path)) == default_dir:
                            path = os.path.basename(path)
                    except Exception:
                        pass
                if ' ' in path or '\\' in path:
                    path_token = '"%s"' % path.replace('"', '\\"')
                else:
                    path_token = path

            return "{image: %s}" % " ".join([path_token] + _build_options())

        def _update_embed_warn(e=None):
            """Aggiorna il label con la stima dei KB aggiunti al file."""
            if not cb_embed.GetValue():
                lbl_embed_warn.SetLabel("")
                lbl_embed_warn.GetParent().Layout()
                return
            path = txt_path.GetValue().strip()
            if path and os.path.isfile(path):
                size_kb = os.path.getsize(path) / 1024
                est_kb  = size_kb * 1.34   # base64 aumenta di ~33%
                if est_kb >= 1024:
                    lbl_embed_warn.SetLabel(
                        (_(u"⚠ Approx. %.1f MB will be added to the .crd file") % (est_kb / 1024)
                         ).replace(".crd", ".%s" % doc_ext))
                else:
                    lbl_embed_warn.SetLabel(
                        (_(u"⚠ Approx. %.0f KB will be added to the .crd file") % est_kb
                         ).replace(".crd", ".%s" % doc_ext))
            else:
                lbl_embed_warn.SetLabel("")
            lbl_embed_warn.GetParent().Layout()

        def _update_preview(e=None):
            embed = cb_embed.GetValue()
            path  = txt_path.GetValue().strip()
            if embed and path and os.path.isfile(path):
                # Il dato base64 è illeggibile nell'anteprima: mostra
                # "<embedded>" al posto del token, ma include tutte le
                # opzioni reali (width, height, scale, align, border)
                # così l'utente può vedere e modificare le impostazioni.
                opts = _build_options()
                tokens = ["data:<embedded>"] + opts
                txt_preview.SetValue("{image: %s}" % " ".join(tokens))
            else:
                txt_preview.SetValue(_build_directive(for_insert=False))
            _update_embed_warn()

        def _on_browse(e):
            fd = wx.FileDialog(
                d,
                _("Select image"),
                default_dir,
                "",
                _("Image files (*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.tiff;*.tif)|*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.tiff;*.tif|All files (*.*)|*.*"),
                wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            )
            if fd.ShowModal() == wx.ID_OK:
                path = fd.GetPath()
                # Usa solo il nome se è nella stessa cartella del documento
                if default_dir and os.path.dirname(os.path.abspath(path)) == default_dir:
                    path = os.path.basename(path)
                txt_path.SetValue(path)
            fd.Destroy()

        # ── Bind aggiornamento anteprima ─────────────────────────────────
        txt_path.Bind(wx.EVT_TEXT, _update_preview)
        for ctrl in (txt_w, txt_h, txt_scale, txt_border):
            ctrl.Bind(wx.EVT_SPINCTRLDOUBLE, _update_preview)
        for ctrl in (ch_w_unit, ch_h_unit):
            ctrl.Bind(wx.EVT_CHOICE, _update_preview)
        def _on_radio(e):
            # wx.CallAfter garantisce che GetValue() di tutti i radio button
            # sia già aggiornato quando _update_preview legge rb_left/rb_right.
            wx.CallAfter(_update_preview)
            e.Skip()
        for ctrl in (rb_left, rb_center, rb_right):
            ctrl.Bind(wx.EVT_RADIOBUTTON, _on_radio)
        cb_border.Bind(wx.EVT_CHECKBOX,
                       lambda e: (txt_border.Enable(cb_border.GetValue()), _update_preview()))
        cb_embed.Bind(wx.EVT_CHECKBOX, _update_preview)

        btn_browse.Bind(wx.EVT_BUTTON, _on_browse)

        if d.ShowModal() == wx.ID_OK:
            directive = _build_directive(for_insert=True)
            if directive != "{image: }":
                self.InsertWithCaret(directive)
        d.Destroy()

    def AddTool(self, toolbar, resource_string, icon_path, label, help):
        tool = wx.xrc.XRCID(resource_string)
        toolbar.AddTool(
            tool,
            label,
            wx.Bitmap(wx.Image(glb.AddPath(icon_path))),
            wx.NullBitmap,
            wx.ITEM_NORMAL,
            label,
            help,
            None
        )
        return tool

    def New(self):
        self.text.AutoChangeMode(True)
        self.text.New()
        self.text.AutoChangeMode(False)
        self.UpdateEverything()

    def Open(self):
        self.text.AutoChangeMode(True)
        self.text.Open()
        self.text.AutoChangeMode(False)
        self.UpdateEverything()
        self.AutoAdjust(0, self.text.GetLength())

    def Save(self):
        self.text.Save()
        self.UpdateEverything()

    def SavePreferences(self):
        self.pref.Save()

    def UpdateUndoRedo(self):
        self.mainToolBar.EnableTool(self.undoTool, self.text.CanUndo())
        self.mainToolBar.EnableTool(self.redoTool, self.text.CanRedo())

    def UpdateCutCopyPaste(self):
        s, e = self.text.GetSelection()
        self.mainToolBar.EnableTool(self.cutTool, s != e)
        self.menuBar.Enable(self.cutMenuId, s != e)
        self.mainToolBar.EnableTool(self.copyTool, s != e)
        self.menuBar.Enable(self.copyOnlyTextTool, s != e)
        self.menuBar.Enable(self.copyMenuId, s != e)
        if platform.system() == 'Windows':
            cp = self.text.CanPaste()
        else:
            # Workaround for weird error in wxGTK
            cp = True
        self.mainToolBar.EnableTool(self.pasteTool, cp)
        self.menuBar.Enable(self.pasteMenuId, cp)
        self.mainToolBar.EnableTool(self.pasteChordsTool, cp)
        self.menuBar.Enable(self.pasteChordsMenuId, cp)
        self.menuBar.Enable(self.removeChordsMenuId, s != e)

    @staticmethod
    def _strip_hash_commands(text):
        """
        Rimuove le righe della forma  # {comando}  (con spazi opzionali),
        es.  # {new_page}  # {linespacing: 13}  #{np}
        Tali righe non devono comparire ne nell'anteprima ne in stampa.
        Le normali righe di commento libero  # testo  vengono lasciate invariate.
        """
        import re
        pattern = re.compile(r'^\s*#\s*\{[^}]*\}\s*$')
        lines = text.split('\n')
        filtered = [l for l in lines if not pattern.match(l)]
        return '\n'.join(filtered)

    def _get_display_text(self):
        """Restituisce il testo del documento con i comandi # {...} rimossi.
        Aggiorna anche la directory del documento nel renderer, in modo che
        i percorsi relativi di {image: ...} vengano risolti correttamente.
        """
        self.previewCanvas.SetDocumentDir(self.document)
        return self._strip_hash_commands(self.text.GetText())

    def UpdateEverything(self):
        self.UpdateUndoRedo()
        self.UpdateCutCopyPaste()

    def TextUpdated(self):
        self.previewCanvas.Refresh(self._get_display_text())

    # self.UpdateEverything()

    def DrawOnDC(self, dc):
        """
        Draw song on DC and return the tuple (width, height) of rendered song
        """
        if self.pref.labelVerses:
            import copy
            decorator = copy.copy(self.pref.decorator)
        else:
            decorator = SongDecorator()
        decorator.showKlavier = True
        decorator.showGuitarDiagrams = True
        decorator.exportMode = False
        decorator.showPageBreakLines = getattr(self, '_showPageBreakLines', True)
        decorator.showColumnBreakLines = getattr(self, '_showColumnBreakLines', True)
        decorator.showDurationBeats      = getattr(self, '_showDurationBeats', True)
        decorator.durationBeatsColourHex = getattr(self.pref, 'durationBeatsColourHex', '#6464C8')
        decorator.durationBeatsSizePct   = getattr(self.pref, 'durationBeatsSizePct', 60)
        decorator.durationBeatsBold      = getattr(self.pref, 'durationBeatsBold', False)
        decorator.durationBeatsAlign     = getattr(self.pref, 'durationBeatsAlign', 'right')
        decorator.durationBeatsMode     = getattr(self.pref, 'durationBeatsMode', 'number')
        decorator.klavierHighlightColor = self._getKlavierHighlightColour()
        decorator.fingerNumColor = self._getFingerNumColour()
        r = Renderer(self.pref.format, decorator, self.pref.notations)
        r.tempoDisplay = getattr(self.pref, 'tempoDisplay', 0)
        r.timeDisplay = getattr(self.pref, 'timeDisplay', True)
        r.keyDisplay = getattr(self.pref, 'keyDisplay', True)
        r.tempoIconSize = getattr(self.pref, 'tempoIconSize', 24)
        r.gridDisplayMode = getattr(self.pref, 'gridDisplayMode', 'pipe')
        r.gridDefaultLabel = getattr(self.pref, 'gridDefaultLabel', None)
        r.gridSizeDir = getattr(self.pref, 'gridSizeDir', 'both')
        # oppure rileva automaticamente {column_break} nel testo (come fa PreviewCanvas).
        import re
        song_text = self._strip_hash_commands(self.text.GetText())
        columns = getattr(self, '_columns_per_page', 1)
        if columns < 2:
            has_col_break = bool(re.search(r'\{\s*(?:column_break|colb)\s*\}', song_text, re.IGNORECASE))
            if has_col_break:
                columns = 2
        r.columns = columns
        r.columnHeight = 0  # nessun limite di altezza per colonna nell'export
        start, end = self.text.GetSelection()
        if start == end:
            w, h = r.Render(song_text, dc)
        else:
            w, h = r.Render(song_text, dc, self.text.LineFromPosition(start), self.text.LineFromPosition(end))
        return w, h

    def AskExportFileName(self, type, ext):
        """Ask the filename (without saving); return None if user cancels, the file name ow"""
        leave = False;
        consensus = False;
        while not leave:
            dlg = wx.FileDialog(
                self.frame,
                "Choose a name for the output file",
                "",
                os.path.splitext(self.document)[0],
                "%s files (*.%s)|*.%s|All files (*.*)|*.*" % (type, ext, ext),
                wx.FD_SAVE
            )

            if dlg.ShowModal() == wx.ID_OK:

                fn = dlg.GetPath()
                if os.path.isfile(fn):
                    msg = "File \"%s\" already exists. Do you want to overwrite it?" % (fn,)
                    d = wx.MessageDialog(
                        self.frame,
                        msg,
                        self.appLongName,
                        wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION
                    )
                    res = d.ShowModal()
                    if res == wx.ID_CANCEL:
                        leave = True
                        consensus = False
                    elif res == wx.ID_NO:
                        leave = False
                        consensus = False
                    else:  # wxID_YES
                        leave = True
                        consensus = True
                else:
                    leave = True
                    consensus = True

            else:
                leave = True
                consensus = False

        if consensus:
            return fn
        else:
            return None

    def ComputeRenderedSize(self):
        """
        Compute and return rendered size as tuple (with, height)
        """
        dc = wx.MemoryDC(wx.Bitmap(1, 1))
        w, h = self.DrawOnDC(dc)
        return max(1, w), max(1, h)

    def RenderAsPng(self, scale=1, size=None):
        if size is None:
            size = self.ComputeRenderedSize()
        w, h = size
        b = wx.Bitmap(int(w * scale), int(h * scale))
        dc = wx.MemoryDC(b)
        dc.SetUserScale(scale, scale)
        dc.SetBackground(wx.WHITE_BRUSH)
        dc.Clear()
        self.DrawOnDC(dc)
        return b

    def OnExportAsPng(self, evt):
        n = self.AskExportFileName(_("PNG image"), "png")
        if n is not None:
            b = self.RenderAsPng()
            i = b.ConvertToImage()
            i.SaveFile(n, wx.BITMAP_TYPE_PNG)

    def OnExportAsHtml(self, evt):
        n = self.AskExportFileName(_("HTML file"), "html")
        if n is not None:
            h = HtmlExporter(self.pref.format)
            r = Renderer(self.pref.format, h, self.pref.notations)
            start, end = self.text.GetSelection()
            display_text = self._strip_hash_commands(self.text.GetText())
            if start == end:
                r.Render(display_text, None)
            else:
                r.Render(display_text, None, self.text.LineFromPosition(start), self.text.LineFromPosition(end))
            with open(n, "w", encoding='utf-8') as f:
                f.write(h.getHtml())

    def OnExportAsTab(self, evt):
        n = self.AskExportFileName(_("TAB file"), "tab")
        if n is not None:
            t = TabExporter(self.pref.format)
            r = Renderer(self.pref.format, t, self.pref.notations)
            start, end = self.text.GetSelection()
            display_text = self._strip_hash_commands(self.text.GetText())
            if start == end:
                r.Render(display_text, None)
            else:
                r.Render(display_text, None, self.text.LineFromPosition(start), self.text.LineFromPosition(end))
            with open(n, "w", encoding='utf-8') as f:
                f.write(t.getTab())

    def SaveSvg(self, filename, size=None):
        if size is None:
            size = self.ComputeRenderedSize()
        w, h = size
        dc = wx.SVGFileDC(filename, int(w), int(h))
        self.DrawOnDC(dc)

    def OnExportAsSvg(self, evt):
        n = self.AskExportFileName(_("SVG image"), "svg")
        if n is not None:
            self.SaveSvg(n)

    def OnExportAsEmf(self, evt):
        n = self.AskExportFileName(_("Enhanced Metafile"), "emf")
        if n is not None:
            dc = wx.msw.MetafileDC(n)
            self.DrawOnDC(dc)
            dc.Close()

    def OnExportAsEps(self, evt):
        n = self.AskExportFileName(_("EPS image"), "eps")
        if n is not None:
            pd = wx.PrintData()
            pd.SetPaperId(wx.PAPER_NONE)
            pd.SetPrintMode(wx.PRINT_MODE_FILE)
            pd.SetFilename(n)
            dc = wx.PostScriptDC(pd)
            dc.StartDoc(_("Exporting image as EPS..."))
            self.DrawOnDC(dc)
            dc.EndDoc()

    def OnExportAsPdf(self, evt):
        """Esporta la canzone come PDF. Delega a PdfExporter."""
        # Prima chiedi le impostazioni di pagina
        data = wx.PageSetupDialogData(self._print_data)
        data.SetMarginTopLeft(wx.Point(self._margin_left, self._margin_top))
        data.SetMarginBottomRight(wx.Point(self._margin_right, self._margin_bottom))
        dlg = wx.PageSetupDialog(self.frame, data)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        result = dlg.GetPageSetupData()
        self._print_data = wx.PrintData(result.GetPrintData())
        tl = result.GetMarginTopLeft()
        br = result.GetMarginBottomRight()
        self._margin_left   = tl.x
        self._margin_top    = tl.y
        self._margin_right  = br.x
        self._margin_bottom = br.y
        dlg.Destroy()

        n = self.AskExportFileName(_("PDF"), "pdf")
        if n is None:
            return
        if not n.lower().endswith('.pdf'):
            n += '.pdf'
        title = os.path.splitext(os.path.basename(self.document))[0] if self.document else _("Song")
        PdfExporter.export_as_pdf(self, n, title)

    def OnSongbook(self, evt):
        """Crea un Songbook PDF da una cartella di brani."""
        SongbookExporter.create_songbook(self, self.frame)

    def OnExportAsPptx(self, evt):
        try:
            from . import songimpress
        except ImportError:
            msg = _("Please install the python-pptx module to use this feature")
            d = wx.MessageDialog(self.frame, msg, "Songpress++", wx.OK | wx.ICON_ERROR)
            d.ShowModal()
            return
        text = replaceTitles(self.text.GetTextOrSelection(), '---')
        text = removeChordPro(text).strip()
        if text != '':
            template_rel = os.path.join('templates', 'slides')
            template_paths = [f for f in glb.ListLocalGlobalDir(template_rel) if f[-5:].upper() == '.PPTX']
            template_names = [os.path.split(f)[1][:-5] for f in template_paths]
            mld = MyListDialog(
                self.frame,
                _("Please select a template for your PowerPoint presentation:"),
                _("Export as PowerPoint"),
                template_names,
            )
            if mld.ShowModal() == wx.ID_OK:
                output_file = self.AskExportFileName(_("PPTX presentation"), "pptx")
                if output_file is not None:
                    i = mld.GetSelectedIndex()
                    songimpress.to_presentation(text.splitlines(), output_file, template_paths[i])

    def OnUpdateUI(self, evt):
        self.UpdateEverything()
        evt.Skip()

    def OnUndo(self, evt):
        if self.text.CanUndo():
            self.text.Undo()
            self.UpdateUndoRedo()

    def OnRedo(self, evt):
        if self.text.CanRedo():
            self.text.Redo()
            self.UpdateUndoRedo()

    def OnCut(self, evt):
        self.text.Cut()

    def OnTextCutCopy(self, evt):
        self.UpdateCutCopyPaste()
        evt.Skip()

    def OnTextKeyDown(self, evt):
        # 314: left
        # 316: right
        map = {
            (314, True, True, False): self.MoveChordLeft,
            (316, True, True, False): self.MoveChordRight,
            (ord('D'), False, False, True): self.CopyAsImage,
        }
        tp = (
            evt.GetKeyCode(),
            evt.ShiftDown(),
            evt.AltDown(),
            evt.ControlDown(),
        )

        # Ctrl+Space → intellisense direttive ChordPro
        if tp == (wx.WXK_SPACE, False, False, True):
            if getattr(self.pref, 'intellisense', True):
                self._ShowDirectiveIntellisense()
            evt.Skip(False)
            return

        # Dentro {start_of_grid}: Alt+Shift+← / → spostano la cella del grid
        if tp == (314, True, True, False):
            if self._GetGridContext() is not None:
                self._MoveGridCellLeft()
                evt.Skip(False)
                return
        if tp == (316, True, True, False):
            if self._GetGridContext() is not None:
                self._MoveGridCellRight()
                evt.Skip(False)
                return

        if (method := map.get(tp)) is not None:
            method()
            evt.Skip(False)
        else:
            evt.Skip()

    # ── Lista completa delle direttive ChordPro supportate da Songpress++ ──
    # Direttive proprietarie di Songpress++ (non standard ChordPro)
    # Direttive NON presenti nella specifica ufficiale chordpro.org → icona 🔧
    # Fonte: https://www.chordpro.org/chordpro/chordpro-directives/
    _SONGPRESSPLUSPLUS_DIRECTIVES = {
        # Metadati estesi non ufficiali
        'beats_time',                              # S++ – battiti per accordo
        'ccli',                                    # S++ – codice CCLI (non in spec)
        'arranger',                                # S++ – non in spec ufficiale
        'keywords', 'topic', 'collection',        # S++ – non in spec ufficiale
        'language',                                # S++ – non in spec ufficiale
        # Varianti tempo proprietarie
        'tempo_m', 'tempo_s', 'tempo_sp',
        'tempo_c', 'tempo_cp',
        # Struttura proprietaria
        'start_of_part', 'end_of_part',           # S++ – non in spec
        'start_verse', 'end_verse',               # S++ – non in spec
        'start_verse_num', 'end_verse_num',       # S++ – non in spec
        'start_chord', 'end_chord',               # S++ – non in spec
        'row', 'bar',                             # S++ – non in spec
        'sop', 'eop',                             # S++ – alias non ufficiali
        # Formattazione proprietaria
        'linespacing', 'chordtopspacing',         # S++ – non in spec
        # Diagrammi/tastiera proprietari
        'taste', 'fingering',                     # S++ – estensioni S++
    }

    # ID immagine per AutoComp (Scintilla RegisterImage)
    # Tipo 1 -> icona verde "✅" = direttiva ChordPro standard ufficiale
    # Tipo 2 -> icona arancione "🔧" = direttiva esclusiva Songpress++
    _AUTOCOMP_IMG_CHORDPRO   = 1
    _AUTOCOMP_IMG_SPPLUSPLUS = 2

    def _RegisterIntellisenseImages(self):
        """Registra le icone 16x16 usate nel popup intellisense.

        Tipo 1 -> ✅ sfondo verde   = direttiva ChordPro ufficiale
                     (fonte: chordpro.org/chordpro/chordpro-directives/)
        Tipo 2 -> 🔧 sfondo arancione = direttiva esclusiva Songpress++
        """
        def _make_icon(label, bg, fg):
            """Crea bitmap 16x16 con label centrata (supporta emoji Unicode)."""
            bmp = wx.Bitmap(16, 16, 32)
            dc = wx.MemoryDC(bmp)
            dc.SetBackground(wx.Brush(wx.Colour(*bg)))
            dc.Clear()
            dc.SetTextForeground(wx.Colour(*fg))
            # Font leggermente più piccolo per lasciare spazio alle emoji
            font = wx.Font(wx.FontInfo(8).FaceName('Segoe UI Emoji')
                           if wx.Platform == '__WXMSW__'
                           else wx.FontInfo(8))
            dc.SetFont(font)
            tw, th = dc.GetTextExtent(label)
            dc.DrawText(label, max(0, (16 - tw) // 2), max(0, (16 - th) // 2))
            dc.SelectObject(wx.NullBitmap)
            return bmp

        # ✅ verde scuro su bianco — ChordPro ufficiale
        img_cp = _make_icon(u'\u2705', bg=(235, 250, 235), fg=(30, 130, 30))
        # 🔧 chiave su arancione chiaro — Songpress++ esclusivo
        img_sp = _make_icon(u'\U0001F527', bg=(255, 240, 220), fg=(180, 90, 0))
        self.text.RegisterImage(self._AUTOCOMP_IMG_CHORDPRO,   img_cp)
        self.text.RegisterImage(self._AUTOCOMP_IMG_SPPLUSPLUS, img_sp)

    # Lista completa direttive mostrate nell'intellisense.
    # La classificazione ✅/🔧 è derivata dalla specifica ufficiale:
    # https://www.chordpro.org/chordpro/chordpro-directives/
    _CHORDPRO_DIRECTIVES = [
        # ── Metadati ufficiali ChordPro ✅ ────────────────────────────
        'title', 'subtitle', 'artist', 'composer', 'lyricist',
        'copyright', 'album', 'year', 'key', 'time', 'tempo', 'capo',
        'duration', 'sorttitle', 'meta',
        # ── Metadati estesi ✅ (ChordPro 6) ───────────────────────────
        'pagetype', 'columns',
        # ── Metadati Songpress++ 🔧 ────────────────────────────────────
        'arranger',                                        # non in spec
        'beats_time',                                      # S++ esclusivo
        'ccli',                                            # non in spec
        'keywords', 'topic', 'collection', 'language',    # non in spec
        'tempo_m', 'tempo_s', 'tempo_sp', 'tempo_c', 'tempo_cp',
        # ── Struttura ufficiale ChordPro ✅ ───────────────────────────
        'start_of_chorus', 'end_of_chorus',
        'start_of_verse', 'end_of_verse',
        'start_of_bridge', 'end_of_bridge',
        'start_of_tab', 'end_of_tab',
        'start_of_grid', 'end_of_grid',
        'new_page', 'column_break',
        'new_song',
        # ── Struttura Songpress++ 🔧 ───────────────────────────────────
        'start_of_part', 'end_of_part',
        'start_verse', 'end_verse',
        'start_verse_num', 'end_verse_num',
        'start_chord', 'end_chord',
        'row', 'bar',
        # ── Formattazione ufficiale ChordPro ✅ ───────────────────────
        'comment', 'comment_italic', 'comment_box',
        'image',
        'textfont', 'textsize', 'textcolour',
        'chordfont', 'chordsize', 'chordcolour',
        'transpose',
        # ── Formattazione Songpress++ 🔧 ───────────────────────────────
        'linespacing', 'chordtopspacing',
        # ── Alias ufficiali ChordPro ✅ ───────────────────────────────
        't', 'st', 'c', 'ci', 'cb', 'np',
        'soc', 'eoc', 'sov', 'eov', 'sob', 'eob', 'sot', 'eot',
        # ── Alias Songpress++ 🔧 ───────────────────────────────────────
        'sop', 'eop',
        # ── Diagrammi/accordi ufficiali ChordPro ✅ ───────────────────
        'define',
        # ── Diagrammi/tastiera Songpress++ 🔧 ─────────────────────────
        'taste', 'fingering',
    ]

    def _ShowDirectiveIntellisense(self):
        """Mostra il popup di completamento direttive ChordPro (Ctrl+Space).

        Logica:
        - Legge il testo della riga corrente dal primo carattere fino al cursore.
        - Se trova una '{' aperta (senza '}' successiva), estrae il prefisso
          digitato dopo '{' (solo la parte prima di ':' o ' ').
        - Filtra _CHORDPRO_DIRECTIVES con quel prefisso (case-insensitive).
        - Chiama AutoCompShow() con le corrispondenze ordinate.
        - Se la lista è già attiva (l'utente ha già aperto il popup), la aggiorna.
        """
        stc = self.text

        # Se c'è già un autocomplete attivo, lo chiudiamo per riaprirlo aggiornato
        if stc.AutoCompActive():
            stc.AutoCompCancel()

        pos      = stc.GetCurrentPos()
        line_num = stc.LineFromPosition(pos)
        line_start = stc.PositionFromLine(line_num)
        # Testo dalla riga fino alla posizione cursore
        text_before = stc.GetTextRange(line_start, pos)

        # Cerchiamo l'ultima '{' non chiusa nel testo prima del cursore
        brace_pos = text_before.rfind('{')
        if brace_pos == -1:
            # Nessuna parentesi graffa: mostriamo tutte le direttive
            prefix = ''
            typed_len = 0
        else:
            after_brace = text_before[brace_pos + 1:]
            # Se c'è già una '}' dopo l'ultima '{', siamo fuori da una direttiva
            if '}' in after_brace:
                prefix = ''
                typed_len = 0
            else:
                # Il prefisso è quello digitato dopo '{', fino a ':' o spazio
                prefix = after_brace.split(':')[0].split(' ')[0]
                typed_len = len(prefix)

        # Filtra la lista (case-insensitive)
        prefix_lower = prefix.lower()
        matches = sorted(
            d for d in self._CHORDPRO_DIRECTIVES
            if d.startswith(prefix_lower)
        )

        if not matches:
            return

        # Aggiunge il suffisso ?N per mostrare l'icona nel popup:
        #   ?1 = icona "C" azzurra  -> direttiva ChordPro standard
        #   ?2 = icona "S" arancione -> direttiva esclusiva Songpress++
        def _tagged(d):
            img_id = (self._AUTOCOMP_IMG_SPPLUSPLUS
                      if d in self._SONGPRESSPLUSPLUS_DIRECTIVES
                      else self._AUTOCOMP_IMG_CHORDPRO)
            return '%s?%d' % (d, img_id)

        # Scintilla vuole la lista separata da spazi (o da AutoCompSetSeparator)
        # NOTA: il separatore deve essere diverso da '?' usato per le immagini.
        stc.AutoCompSetSeparator(ord(' '))
        stc.AutoCompSetIgnoreCase(True)
        stc.AutoCompSetAutoHide(True)
        stc.AutoCompSetDropRestOfWord(False)
        stc.AutoCompShow(typed_len, ' '.join(_tagged(d) for d in matches))

    # Direttive che non accettano valore (si chiudono con '}' direttamente)
    _DIRECTIVES_NO_VALUE = {
        'end_of_chorus', 'end_of_verse', 'end_of_bridge',
        'end_of_tab', 'end_of_grid', 'end_verse', 'end_verse_num',
        'end_chord', 'new_page', 'column_break',
        'end_of_part', 'row', 'bar',
        'eoc', 'eov', 'eob', 'eot', 'np', 'eop',
        'new_song',
    }

    def _OnIntellisenseSelection(self, evt):
        """Gestisce la selezione dall'autocomplete ChordPro.

        EVT_STC_AUTOCOMP_SELECTION scatta PRIMA che Scintilla inserisca il testo
        selezionato. Usare wx.CallAfter garantisce che il suffisso venga aggiunto
        solo dopo che Scintilla ha completato l'inserimento.
        """
        directive = evt.GetText().lower()
        wx.CallAfter(self._ApplyDirectiveSuffix, directive)
        evt.Skip()   # lascia che Scintilla proceda con l'inserimento normale

    def _ApplyDirectiveSuffix(self, directive):
        """Aggiunge ':|}' o '}' dopo la direttiva appena inserita da Scintilla
        e posiziona il cursore nel punto giusto per digitare il valore.
        Chiamata tramite wx.CallAfter, quindi il testo è già aggiornato."""
        stc = self.text

        pos = stc.GetCurrentPos()
        char_after = stc.GetTextRange(pos, stc.PositionAfter(pos))

        # Se la direttiva è già seguita da ':' o '}' l'utente stava modificando
        # una direttiva esistente: non toccare nulla.
        if char_after == ':':
            return

        line_num   = stc.LineFromPosition(pos)
        line_start = stc.PositionFromLine(line_num)
        text_before = stc.GetTextRange(line_start, pos)
        has_open_brace = '{' in text_before and text_before.rfind('{') > text_before.rfind('}')

        if directive in self._DIRECTIVES_NO_VALUE:
            # Direttiva senza valore: chiude con '}'
            if char_after == '}':
                stc.GotoPos(stc.PositionAfter(pos))
            elif has_open_brace:
                stc.InsertText(pos, '}')
                stc.GotoPos(pos + 1)
            else:
                dir_len = len(directive)
                stc.SetTargetStart(pos - dir_len)
                stc.SetTargetEnd(pos)
                stc.ReplaceTarget('{' + directive + '}')
                stc.GotoPos(pos - dir_len + len('{' + directive + '}'))
        else:
            # Direttiva con valore: aggiunge ':|}' e seleziona il placeholder
            if char_after == '}':
                # '}' presente ma manca ':valore' — sostituisce '}' con ':|}'
                pos_close = stc.PositionAfter(pos)
                stc.SetTargetStart(pos)
                stc.SetTargetEnd(pos_close)
                stc.ReplaceTarget(':|')
                stc.InsertText(pos + 2, '}')
                stc.GotoPos(pos + 1)
                stc.SetSelection(pos + 1, pos + 2)
            elif has_open_brace:
                stc.InsertText(pos, ':|}')
                stc.GotoPos(pos + 1)
                stc.SetSelection(pos + 1, pos + 2)
            else:
                full = '{' + directive + ':|}' 
                dir_len = len(directive)
                stc.SetTargetStart(pos - dir_len)
                stc.SetTargetEnd(pos)
                stc.ReplaceTarget(full)
                cursor_pos = pos - dir_len + len('{' + directive + ':')
                stc.GotoPos(cursor_pos)
                stc.SetSelection(cursor_pos, cursor_pos + 1)

    def Copy(self):
        self.text.Copy()

    def OnCopy(self, evt):
        self.Copy()

    def OnCopyOnlyText(self, evt):
        self.text.CopyOnlyText()

    def CopyAsImage(self):
        if platform.system() == 'Windows':
            # Windows Metafile
            dc = wx.MetafileDC()
            self.DrawOnDC(dc)
            m = dc.Close()
            m.SetClipboard(dc.MaxX(), dc.MaxY())

        else:
            composite = wx.DataObjectComposite()
            size = self.ComputeRenderedSize()

            # 1. SVG
            with temp_dir() as path:
                svg_obj = wx.CustomDataObject("image/svg+xml")
                fp = os.path.join(path, 'temp.svg')
                self.SaveSvg(fp, size=size)
                with open(fp, 'rb') as f:
                    svg_obj.SetData(f.read())
                composite.Add(svg_obj, preferred=True)

            # 2. PNG
            bmp = self.RenderAsPng(scale=2, size=size)
            png_obj = wx.BitmapDataObject(bmp)
            composite.Add(png_obj)

            # Place on Clipboard
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(composite)
                wx.TheClipboard.Close()

    def OnCopyAsImage(self, evt):
        self.CopyAsImage()

    def OnPaste(self, evt):
        self.text.Paste()

    def OnPasteChords(self, evt):
        self.text.PasteChords()

    # ------------------------------------------------------------------
    # Propagate chords from first verse / first chorus to all matching
    # blocks (same type, same number of content lines).
    #
    # Verse formats supported:
    #   1. Plain blocks separated by blank lines (no directive)
    #   2. {start_of_verse} ... {end_of_verse}  (also sov/eov)
    #   3. {verse}  (single-line tag: treats the following plain block
    #                as the verse body)
    # Chorus formats supported:
    #   {start_of_chorus} ... {end_of_chorus}  (also soc/eoc)
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_chordpro_blocks(text):
        """
        Parse ChordPro text into a list of blocks.

        Each block is a dict with keys:
          'type'  : 'verse' | 'chorus' | 'header' | 'blank'
          'lines' : list of raw lines (newline stripped)
          'start' : index of first line in the full line list

        For tagged blocks ({sov}…{eov}, {soc}…{eoc}) the delimiter
        lines are included in 'lines' and excluded from the content
        count when building the chord map (see _propagate_chords).

        For plain verse blocks (no delimiter) all lines are content.

        For {verse}-tagged blocks the {verse} directive line is stored
        as a separate 'header' block immediately before the 'verse'
        block that follows it, so the verse content lines are plain.
        """
        import re
        lines = text.split('\n')
        blocks = []
        i = 0

        SOV = re.compile(r'^\s*\{s(?:ov|tart_of_verse)[^}]*\}',   re.IGNORECASE)
        EOV = re.compile(r'^\s*\{e(?:ov|nd_of_verse)[^}]*\}',     re.IGNORECASE)
        SOC = re.compile(r'^\s*\{s(?:oc|tart_of_chorus)[^}]*\}',  re.IGNORECASE)
        EOC = re.compile(r'^\s*\{e(?:oc|nd_of_chorus)[^}]*\}',    re.IGNORECASE)
        # {verse} or {verse:label}
        VERSE_TAG  = re.compile(r'^\s*\{verse(?:[:\s][^}]*)?\}',   re.IGNORECASE)
        # {chorus} single-tag (without soc/eoc)
        CHORUS_TAG = re.compile(r'^\s*\{chorus(?:[:\s][^}]*)?\}',  re.IGNORECASE)
        DIRECTIVE  = re.compile(r'^\s*\{[^}]+\}',                  re.IGNORECASE)
        COMMENT    = re.compile(r'^\s*#')
        # paired block delimiters whose content must NOT be treated as verse
        # (start_chord/end_chord, grid/end_grid, tab/end_tab, bridge, etc.)
        SOB = re.compile(
            r'^\s*\{(?:start_chord|start_bridge|start_of_bridge|sob|start_of_tab|sot'
            r'|start_of_grid|sog|grid)[^}]*\}',
            re.IGNORECASE,
        )
        EOB = re.compile(
            r'^\s*\{(?:end_chord|end_bridge|end_of_bridge|eob|end_of_tab|eot'
            r'|end_of_grid|eog)\s*\}',
            re.IGNORECASE,
        )

        while i < len(lines):
            line = lines[i]

            # --- paired non-verse blocks (start_chord/end_chord, grid, tab, bridge…) ---
            # treat their entire content as header so it is never mistaken for a verse
            if SOB.match(line):
                block_lines = [line]
                i += 1
                while i < len(lines):
                    block_lines.append(lines[i])
                    if EOB.match(lines[i]):
                        i += 1
                        break
                    i += 1
                blocks.append({'type': 'header', 'lines': block_lines,
                                'start': i - len(block_lines), 'tagged': False})
                continue

            # --- {start_of_verse} … {end_of_verse} ---
            if SOV.match(line):
                block_lines = [line]
                i += 1
                while i < len(lines):
                    block_lines.append(lines[i])
                    if EOV.match(lines[i]):
                        i += 1
                        break
                    i += 1
                blocks.append({'type': 'verse', 'lines': block_lines,
                                'start': i - len(block_lines),
                                'tagged': True})
                continue

            # --- {start_of_chorus} … {end_of_chorus} ---
            if SOC.match(line):
                block_lines = [line]
                i += 1
                while i < len(lines):
                    block_lines.append(lines[i])
                    if EOC.match(lines[i]):
                        i += 1
                        break
                    i += 1
                blocks.append({'type': 'chorus', 'lines': block_lines,
                                'start': i - len(block_lines),
                                'tagged': True})
                continue

            # --- {verse} single tag: emit header, then collect following plain lines ---
            if VERSE_TAG.match(line):
                blocks.append({'type': 'header', 'lines': [line], 'start': i, 'tagged': False})
                i += 1
                # collect the plain-text verse body that follows
                body = []
                while i < len(lines):
                    l = lines[i]
                    if (l.strip() == '' or SOV.match(l) or SOC.match(l)
                            or VERSE_TAG.match(l) or CHORUS_TAG.match(l)
                            or EOV.match(l) or EOC.match(l)
                            or DIRECTIVE.match(l) or COMMENT.match(l)):
                        break
                    body.append(l)
                    i += 1
                if body:
                    blocks.append({'type': 'verse', 'lines': body,
                                   'start': i - len(body),
                                   'tagged': False})
                continue

            # --- {chorus} single tag (treat similarly to {verse}) ---
            if CHORUS_TAG.match(line):
                blocks.append({'type': 'header', 'lines': [line], 'start': i, 'tagged': False})
                i += 1
                body = []
                while i < len(lines):
                    l = lines[i]
                    if (l.strip() == '' or SOV.match(l) or SOC.match(l)
                            or VERSE_TAG.match(l) or CHORUS_TAG.match(l)
                            or EOV.match(l) or EOC.match(l)
                            or DIRECTIVE.match(l) or COMMENT.match(l)):
                        break
                    body.append(l)
                    i += 1
                if body:
                    blocks.append({'type': 'chorus', 'lines': body,
                                   'start': i - len(body),
                                   'tagged': False})
                continue

            # --- blank line(s) ---
            if line.strip() == '':
                block_lines = [line]
                i += 1
                while i < len(lines) and lines[i].strip() == '':
                    block_lines.append(lines[i])
                    i += 1
                blocks.append({'type': 'blank', 'lines': block_lines,
                                'start': i - len(block_lines), 'tagged': False})
                continue

            # --- generic directive / comment → header ---
            if DIRECTIVE.match(line) or COMMENT.match(line):
                blocks.append({'type': 'header', 'lines': [line], 'start': i, 'tagged': False})
                i += 1
                continue

            # --- plain verse block (no delimiter) ---
            block_lines = [line]
            i += 1
            while i < len(lines):
                l = lines[i]
                if (l.strip() == '' or SOV.match(l) or SOC.match(l)
                        or VERSE_TAG.match(l) or CHORUS_TAG.match(l)
                        or DIRECTIVE.match(l) or COMMENT.match(l)):
                    break
                block_lines.append(l)
                i += 1
            blocks.append({'type': 'verse', 'lines': block_lines,
                            'start': i - len(block_lines),
                            'tagged': False})

        return blocks, lines

    @staticmethod
    def _strip_chords_from_line(line):
        import re
        return re.sub(r'\[[^\]]*\]', '', line)

    @staticmethod
    def _visible_len(s):
        """Length of s excluding ChordPro soft-hyphen '_' characters."""
        return sum(1 for c in s if c != '_')

    @staticmethod
    def _visible_pos(s, raw_pos):
        """Convert a raw string index to a visible-character index (ignoring '_')."""
        return sum(1 for c in s[:raw_pos] if c != '_')

    @staticmethod
    def _raw_pos_from_visible(s, vis_pos):
        """
        Convert a visible-character index back to a raw string index.
        Returns the raw index where the vis_pos-th non-'_' character starts.
        If vis_pos >= number of visible chars, returns len(s).
        """
        count = 0
        for idx, c in enumerate(s):
            if c != '_':
                if count == vis_pos:
                    return idx
                count += 1
        return len(s)

    @staticmethod
    def _extract_chord_map(lines):
        """
        Return a list parallel to `lines`; each element is a list of
        (visible_position, chord_name) tuples.
        Visible position counts characters excluding ChordPro '_' (soft hyphen).
        """
        import re
        CHORD_RE = re.compile(r'\[([^\]]*)\]')
        result = []
        for line in lines:
            positions = []
            clean_pos = 0   # visible chars so far (excluding '_')
            raw_pos   = 0
            for m in CHORD_RE.finditer(line):
                segment = line[raw_pos:m.start()]
                clean_pos += sum(1 for c in segment if c != '_')
                positions.append((clean_pos, m.group(1)))
                raw_pos = m.end()
            result.append(positions)
        return result

    @staticmethod
    def _apply_chord_map(lines, chord_map):
        """
        Re-insert chords from chord_map into lines (already stripped of chords).
        Positions are visible-character indices (ignoring '_').
        """
        result = []
        for i, line in enumerate(lines):
            if i >= len(chord_map) or not chord_map[i]:
                result.append(line)
                continue
            out      = []
            raw_src  = 0
            for vis_pos, chord in chord_map[i]:
                # find the raw index corresponding to vis_pos visible chars
                count = 0
                insert_at = len(line)
                for idx, c in enumerate(line):
                    if c != '_':
                        if count == vis_pos:
                            insert_at = idx
                            break
                        count += 1
                out.append(line[raw_src:insert_at])
                out.append('[' + chord + ']')
                raw_src = insert_at
            out.append(line[raw_src:])
            result.append(''.join(out))
        return result

    def _propagate_chords(self, block_type):
        """
        Propagate chords from the first block of `block_type` ('verse' or
        'chorus') to all subsequent blocks of the same type that have the
        same number of content lines.

        For tagged blocks ({sov}…{eov}, {soc}…{eoc}) the delimiter lines
        are excluded from the content used for the chord map.
        Returns the modified full text, or None if nothing was done.
        """
        text = self.text.GetText()
        blocks, all_lines = self._parse_chordpro_blocks(text)

        typed = [b for b in blocks if b['type'] == block_type]
        if len(typed) < 2:
            return None

        source = typed[0]
        tagged = source.get('tagged', False)

        if tagged:
            # delimiter lines are first and last; content is in between
            src_content = source['lines'][1:-1]
            src_offset  = source['start'] + 1
        else:
            src_content = source['lines']
            src_offset  = source['start']

        chord_map      = self._extract_chord_map(src_content)
        src_line_count = len(src_content)

        result_lines = list(all_lines)
        modified     = False

        for target in typed[1:]:
            t_tagged = target.get('tagged', False)
            if t_tagged:
                tgt_content = target['lines'][1:-1]
                tgt_offset  = target['start'] + 1
            else:
                tgt_content = target['lines']
                tgt_offset  = target['start']

            if len(tgt_content) != src_line_count:
                continue   # metrica diversa, salta

            stripped    = [self._strip_chords_from_line(l) for l in tgt_content]
            new_content = self._apply_chord_map(stripped, chord_map)

            for j, new_line in enumerate(new_content):
                result_lines[tgt_offset + j] = new_line

            modified = True

        return '\n'.join(result_lines) if modified else None

    def OnPropagateVerseChords(self, evt):
        """Copy chords from the first verse to all verses with the same number of lines."""
        result = self._propagate_chords('verse')
        if result is None:
            wx.MessageBox(
                _("No compatible verse found.\n"
                  "Make sure the song has at least two verses with the same number of lines."),
                _("Propagate verse chords"),
                wx.OK | wx.ICON_INFORMATION,
                self.frame,
            )
            return
        with undo_action(self.text):
            self.text.SetSelection(0, self.text.GetLength())
            self.text.ReplaceSelection(result)

    def OnPropagateChorusChords(self, evt):
        """Copy chords from the first chorus to all choruses with the same number of lines."""
        result = self._propagate_chords('chorus')
        if result is None:
            wx.MessageBox(
                _("No compatible chorus found.\n"
                  "Make sure the song has at least two choruses with the same number of lines."),
                _("Propagate chorus chords"),
                wx.OK | wx.ICON_INFORMATION,
                self.frame,
            )
            return
        with undo_action(self.text):
            self.text.SetSelection(0, self.text.GetLength())
            self.text.ReplaceSelection(result)

    def _OnGlobalCharHook(self, evt):
        """F3 = trova successivo, Shift+F3 = trova precedente, anche a dialogo chiuso."""
        kc = evt.GetKeyCode()
        if kc == wx.WXK_F3:
            if evt.ShiftDown():
                self.OnFindPrevious(evt)
            else:
                self.OnFindNext(evt)
        else:
            evt.Skip()

    def OnFind(self, evt):
        if self.findReplaceDialog is not None and self.findReplaceDialog.dialog is not None:
            self.findReplaceDialog.notebook.SetSelection(0)
            self.findReplaceDialog._UpdateButtons()
            self.findReplaceDialog._FocusFindField()
            self.findReplaceDialog.dialog.Raise()
        else:
            self.findReplaceDialog = SongpressFindReplaceDialog(self, replace=False)

    def OnFindNext(self, evt):
        dlg = self.findReplaceDialog
        if dlg is not None and dlg.dialog is not None:
            # Forza direzione giù sul radio della tab attiva
            if dlg._IsReplaceTab():
                dlg.rbDownR.SetValue(True)
            else:
                dlg.rbDown.SetValue(True)
            dlg._OnFindNext(evt)
        else:
            self._FindInEditor(down=True)

    def OnFindPrevious(self, evt):
        dlg = self.findReplaceDialog
        if dlg is not None and dlg.dialog is not None:
            # Forza direzione su sul radio della tab attiva
            if dlg._IsReplaceTab():
                dlg.rbUpR.SetValue(True)
            else:
                dlg.rbUp.SetValue(True)
            dlg._OnFindNext(evt)
        else:
            self._FindInEditor(down=False)

    def _FindInEditor(self, down=True):
        """Cerca nel testo usando l'ultimo termine e flags memorizzati."""
        st    = getattr(self, '_lastFindSt', '')
        flags = getattr(self, '_lastFindFlags', 0)
        if not st:
            return
        text = self.text
        if down:
            s, e = text.GetSelection()
            text.SetSelection(e, e)
            text.SearchAnchor()
            p = text.SearchNext(flags, st)
        else:
            s, e = text.GetSelection()
            text.SetSelection(s, s)
            text.SearchAnchor()
            p = text.SearchPrev(flags, st)
        if p != -1:
            text.SetSelection(p, p + len(st))
        else:
            # Ricomincia dall'inizio/fine
            if down:
                newStart, wherefrom, where = 0, _("Reached the end"), _("beginning")
            else:
                newStart, wherefrom, where = text.GetLength(), _("Reached the beginning"), _("end")
            d = wx.MessageDialog(
                self.frame,
                _("%s of the song, restarting search from the %s") % (wherefrom, where),
                self.appName,
                wx.OK | wx.CANCEL | wx.ICON_INFORMATION
            )
            if d.ShowModal() == wx.ID_OK:
                text.SetSelection(newStart, newStart)
                self._FindInEditor(down=down)

    def OnReplace(self, evt):
        if self.findReplaceDialog is not None and self.findReplaceDialog.dialog is not None:
            self.findReplaceDialog.notebook.SetSelection(1)
            self.findReplaceDialog._UpdateButtons()
            self.findReplaceDialog._FocusFindField()
            self.findReplaceDialog.dialog.Raise()
        else:
            self.findReplaceDialog = SongpressFindReplaceDialog(self, replace=True)

    def OnSelectAll(self, evt):
        self.text.SelectAll()

    def OnSelectNextChord(self, evt):
        self.text.SelectNextChord()

    def OnSelectPreviousChord(self, evt):
        self.text.SelectPreviousChord()

    def _GetGridContext(self):
        """Se il cursore è dentro un blocco {start_of_grid}...{end_of_grid},
        restituisce (line_num, line_text, col_in_line). Altrimenti None.
        """
        import re
        pos = self.text.GetCurrentPos()
        cur_line = self.text.LineFromPosition(pos)
        SOG = re.compile(r'^\s*\{(?:start_of_grid|sog|grid)[^}]*\}', re.IGNORECASE)
        EOG = re.compile(r'^\s*\{(?:end_of_grid|eog)[^}]*\}',        re.IGNORECASE)
        for ln in range(cur_line - 1, -1, -1):
            txt = self.text.GetLine(ln).rstrip('\r\n')
            if EOG.match(txt):
                return None   # siamo dopo una chiusura: non nel grid
            if SOG.match(txt):
                line_txt = self.text.GetLine(cur_line).rstrip('\r\n')
                col = pos - self.text.PositionFromLine(cur_line)
                return (cur_line, line_txt, col)
        return None

    def _MoveGridCellRight(self):
        """Dentro {start_of_grid}: gestisce la barra spaziatrice in modalità pipe.

        - Nessun pipe sulla riga: inserisce '| ' davanti al testo corrente
          e posiziona il cursore dopo il pipe (pronto a digitare il primo accordo).
        - Pipe già presente a sinistra del cursore: inserisce '  |' prima della
          cella corrente (sposta l'accordo a destra) e posiziona il cursore
          nella nuova cella vuota appena creata.
        """
        ctx = self._GetGridContext()
        if ctx is None:
            return False
        cur_line, line_txt, col = ctx
        line_start = self.text.PositionFromLine(cur_line)

        pipe_pos = line_txt.rfind('|', 0, col)

        if pipe_pos == -1:
            # Nessun pipe sulla riga: inizia la struttura pipe all'inizio della riga.
            # Inserisce '| ' prima del testo esistente, cursore subito dopo il pipe.
            with undo_action(self.text):
                self.text.SetSelection(line_start, line_start)
                self.text.ReplaceSelection('| ')
            new_pos = line_start + 2   # dopo '| ', pronto a digitare l'accordo
            self.text.SetSelection(new_pos, new_pos)
        else:
            # Pipe già presente: inserisce '  |' dopo il pipe sinistro,
            # spostando la cella corrente di 3 posizioni a destra.
            insert_at = line_start + pipe_pos + 1
            with undo_action(self.text):
                self.text.SetSelection(insert_at, insert_at)
                self.text.ReplaceSelection('  |')
            # Cursore nella nuova cella vuota (un carattere dopo il pipe originale)
            new_pos = insert_at + 1
            self.text.SetSelection(new_pos, new_pos)

        return True

    def _MoveGridCellLeft(self):
        """Dentro {start_of_grid}: rimuove la cella vuota precedente a quella corrente,
        spostando l'accordo di una posizione verso sinistra.
        Stesso effetto visivo di MoveChordLeft in {start_chord}.
        """
        ctx = self._GetGridContext()
        if ctx is None:
            return False
        cur_line, line_txt, col = ctx
        pipe_pos = line_txt.rfind('|', 0, col)
        if pipe_pos == -1:
            return False
        prev_pipe = line_txt.rfind('|', 0, pipe_pos)
        if prev_pipe == -1:
            return False
        between = line_txt[prev_pipe + 1: pipe_pos]
        if between.strip() != '':
            return False   # cella precedente non vuota: impossibile spostare
        line_start = self.text.PositionFromLine(cur_line)
        remove_start = line_start + prev_pipe + 1
        remove_end   = line_start + pipe_pos + 1
        with undo_action(self.text):
            self.text.SetSelection(remove_start, remove_end)
            self.text.ReplaceSelection('')
        return True

    def MoveChordRight(self, position=None):
        """
        Move the chord 1 position to the right, hooking its neighbords

        Apply to the chord at `position`, or under the cursor if `position`
        is not specified.

        :return: `False` if the chord is at the end of the song and cannot be moved,
            `True` otherwise
        """

        r = self.text.GetChordUnderCursor(position)
        if r is None:
            return True
        n = self.text.GetLength()
        s, e, c = r

        if e >= n:
            return False
        with undo_action(self.text):
            # Recursively push to the right the next adjacent chord (if any)
            if not self.MoveChordRight(e + 1):
                return False

            e1 = self.text.PositionAfter(e)
            self.text.SetSelection(e, e1)
            l = self.text.GetTextRange(e, e1)
            self.text.ReplaceSelection('')
            self.text.SetSelection(s, s)
            self.text.ReplaceSelection(l)
            s2 = self.text.PositionAfter(self.text.PositionAfter(s))
            self.text.SetSelection(s2, s2)
            return True

    def OnMoveChordRight(self, evt):
        self.MoveChordRight()

    def MoveChordLeft(self, position=None):
        """
        Move the chord 1 position to the left, hooking its neighbords

        Apply to the chord at `position`, or under the cursor if `position`
        is not specified.

        :return: `False` if the chord is at the beginnig of the song and cannot be moved,
            `True` otherwise
        """
        r = self.text.GetChordUnderCursor(position)
        if r is None:
            return True
        s, e, c = r
        if s == 0:
            return False
        with undo_action(self.text):
            # Recursively push to the left the previous adjacent chord (if any)
            if not self.MoveChordLeft(s - 1):
                return False

            s1 = self.text.PositionBefore(s)
            l = self.text.GetTextRange(s1, s)
            self.text.SetSelection(e, e)
            self.text.ReplaceSelection(l)
            self.text.SetSelection(s1, s)
            self.text.ReplaceSelection('')
            s = self.text.PositionAfter(s1)
            self.text.SetSelection(s, s)
            return True

    def OnMoveChordLeft(self, evt):
        self.MoveChordLeft()

    def OnRemoveChords(self, evt):
        self.text.RemoveChordsInSelection()

    def _OnStatusTimerExpired(self, evt):
        if self.statusBar:
            self.statusBar.SetStatusText("")

    def OnIntegrateChords(self, evt):
        ln = self.text.GetCurrentLine()
        if ln < self.text.GetLineCount() - 1:
            chords = self.text.GetLine(ln).strip("\r\n")
            text = self.text.GetLine(ln + 1).strip("\r\n")
            chordpro = integrateChords(chords, text)
            self.text.SetSelectionStart(self.text.PositionFromLine(ln))
            self.text.SetSelectionEnd(self.text.GetLineEndPosition(ln + 1))
            self.text.ReplaceSelection(chordpro)
        else:
            if self.statusBar:
                self.statusBar.SetStatusText(_("Command 'Paste chords': Select 1st chord line, 2nd text line"))
                self._statusTimer.StartOnce(10000)

    def OnFontSelected(self, evt):
        font = self.fontChooser.GetValue()
        showChords = self.showChordsChooser.GetValue()
        self.pref.SetFont(font, showChords)
        self.SetFont(True)
        evt.Skip()

    def OnGuide(self, evt):
        wx.LaunchDefaultBrowser(_("http://www.skeed.it/songpress-manual"))

    def OnGuideMarkdown(self, evt):
        import os
        import wx.html

        # Determina il codice lingua dalla locale wx attiva
        locale = wx.GetLocale()
        lang_code = ''
        if locale:
            canonical = locale.GetCanonicalName()   # es. "it_IT"
            if canonical:
                lang_code = canonical.split('_')[0].lower()  # → "it", "en", "fr"

        base_dir = os.path.dirname(__file__)

        # Priorità: guida_<lang>.md  →  guida.md  →  errore
        candidates = []
        if lang_code:
            candidates.append(os.path.join(base_dir, 'guida_%s.md' % lang_code))
        candidates.append(os.path.join(base_dir, 'guida.md'))

        guide_path = None
        for path in candidates:
            if os.path.exists(path):
                guide_path = path
                break

        if guide_path is None:
            wx.MessageBox(
                _("Guide file not found in the program folder."),
                _("Help"),
                wx.ICON_ERROR,
            )
            return

        try:
            with open(guide_path, 'r', encoding='utf-8') as f:
                md_text = f.read()
        except Exception as e:
            wx.MessageBox(str(e), _("Error"), wx.ICON_ERROR)
            return

        # Riscrittura percorsi immagini (normalizza tutte le varianti)
        import re
        # Pattern che cattura qualsiasi variante del percorso verso img/GUIDE/
        _guide_pat = re.compile(
            r'(!\[[^\]]*\]\()(?:\.\.\/src\/songpressPlusPlus\/|\.\/)?img\/GUIDE\/'
        )
        if getattr(self.pref, 'guideMarkdownImgPath', False):
            # Typora: percorso assoluto relativo alla root del progetto
            md_text = _guide_pat.sub(r'\1../src/songpressPlusPlus/img/GUIDE/', md_text)
        else:
            # App: percorso relativo al file .md in src/songpress/
            md_text = _guide_pat.sub(r'\1img/GUIDE/', md_text)

        html = self._md_to_html(md_text)

        dlg = wx.Dialog(
            self.frame,
            title=_("Quick guide - Songpress++"),
            size=(760, 620),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
        )
        dlg.SetMinSize(wx.Size(550, 400))

        sizer = wx.BoxSizer(wx.VERTICAL)

        hw = wx.html.HtmlWindow(dlg, style=wx.html.HW_SCROLLBAR_AUTO)

        # ── Stato ricerca nella guida ─────────────────────────────────
        _search_state = {'term': '', 'matches': [], 'idx': -1, 'html_orig': ''}

        def _guide_search_open():
            """Apre un mini-dialogo di ricerca testuale nella guida."""
            import re as _re2

            sdlg = wx.Dialog(
                dlg, title=_("Find in guide"),
                style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP,
            )
            vsz = wx.BoxSizer(wx.VERTICAL)

            # ── Riga 1: etichetta + campo testo ───────────────────────
            row_find = wx.BoxSizer(wx.HORIZONTAL)
            row_find.Add(
                wx.StaticText(sdlg, label=_("Find:")),
                0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6,
            )
            txt = wx.TextCtrl(
                sdlg, value=_search_state['term'],
                size=(260, -1), style=wx.TE_PROCESS_ENTER,
            )
            row_find.Add(txt, 1, wx.EXPAND)
            vsz.Add(row_find, 0, wx.EXPAND | wx.ALL, 10)

            # ── Riga 2: bottoni navigazione + contatore + Chiudi ──────
            row_btns = wx.BoxSizer(wx.HORIZONTAL)

            # Frecce: stesse icone wx usate dalla toolbar di anteprima stampa
            def _make_arrow_btn(parent, art_id, img_name, label_fallback):
                """
                Crea un BitmapButton con l'icona wx.ArtProvider (stessa usata
                dal PreviewControlBar). Fallback: PNG img/, poi testo puro.
                """
                bmp = wx.ArtProvider.GetBitmap(art_id, wx.ART_BUTTON, (24, 24))
                if not bmp.IsOk():
                    img = wx.Image(glb.AddPath('img/' + img_name))
                    bmp = wx.Bitmap(img) if img.IsOk() else wx.NullBitmap
                if bmp.IsOk():
                    btn = wx.BitmapButton(parent, bitmap=bmp,
                                         style=wx.BU_AUTODRAW)
                    btn.SetToolTip(label_fallback)
                else:
                    btn = wx.Button(parent, label=label_fallback)
                return btn

            btn_prev = _make_arrow_btn(sdlg, wx.ART_GO_BACK,    'arrow_left.png',  _("Previous"))
            btn_next = _make_arrow_btn(sdlg, wx.ART_GO_FORWARD,  'arrow_right.png', _("Next"))
            btn_next.SetDefault()

            lbl_count = wx.StaticText(sdlg, label='', size=(90, -1))
            lbl_count.SetForegroundColour(wx.Colour(80, 80, 80))

            btn_close = wx.Button(sdlg, wx.ID_CANCEL, _("Close"))

            row_btns.Add(btn_prev,  0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
            row_btns.Add(btn_next,  0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
            row_btns.Add(lbl_count, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
            row_btns.AddStretchSpacer()
            row_btns.Add(btn_close, 0, wx.ALIGN_CENTER_VERTICAL)
            vsz.Add(row_btns, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

            sdlg.SetSizer(vsz)
            vsz.Fit(sdlg)
            # Larghezza minima per evitare tagli del contatore
            cur_w, cur_h = sdlg.GetSize()
            sdlg.SetMinSize(wx.Size(max(cur_w, 440), cur_h))
            sdlg.SetSize(wx.Size(max(cur_w, 440), cur_h))

            # ── Logica di ricerca ─────────────────────────────────────
            def _do_search(term, goto_idx=0):
                """Evidenzia tutte le occorrenze di *term* nell'HtmlWindow.
                Il match attivo è in yellowgreen; gli altri in giallo chiaro.
                Un anchor <a name="__active__"> sul match attivo permette
                a wx.html.HtmlWindow di scorrere automaticamente fino ad esso."""
                _search_state['term'] = term
                orig = _search_state.get('html_orig', '')
                if not orig:
                    return
                if not term:
                    hw.SetPage(orig)
                    _search_state['matches'] = []
                    _search_state['idx'] = -1
                    lbl_count.SetLabel('')
                    return
                escaped = _re2.escape(term)
                # Conta le occorrenze nel testo plain (prima di applicare l'HTML)
                plain = _re2.sub(r'<[^>]+>', '', orig)
                matches = [m.start() for m in _re2.finditer(
                    escaped, plain, _re2.IGNORECASE)]
                n = len(matches)
                if n == 0:
                    hw.SetPage(orig)
                    lbl_count.SetLabel(_("Not found"))
                    lbl_count.SetForegroundColour(wx.Colour(180, 0, 0))
                    _search_state['matches'] = matches
                    _search_state['idx'] = -1
                    lbl_count.GetParent().Layout()
                    return
                idx = max(0, min(goto_idx, n - 1))
                _search_state['matches'] = matches
                _search_state['idx'] = idx
                lbl_count.SetLabel(_("%d of %d") % (idx + 1, n))
                lbl_count.SetForegroundColour(wx.Colour(80, 80, 80))
                lbl_count.GetParent().Layout()
                # Costruisce l'HTML con tutti i match evidenziati;
                # il match attivo riceve bgcolor yellowgreen + anchor navigabile.
                counter = [0]
                def _replace_match(m):
                    i = counter[0]
                    counter[0] += 1
                    text = m.group(1)
                    if i == idx:
                        return ('<a name="__active__"></a>'
                                '<font bgcolor="#9ACD32" color="#000000"><b>' + text + '</b></font>')
                    return '<font bgcolor="#FFFF99" color="#000000">' + text + '</font>'
                highlighted = _re2.sub(r'(?i)(%s)' % escaped, _replace_match, orig)
                hw.SetPage(highlighted)
                # Scorre fino al match attivo tramite l'ancora __active__
                hw.ScrollToAnchor("__active__")

            def _on_next(e):
                term = txt.GetValue().strip()
                if not term:
                    return
                idx = _search_state['idx']
                n   = len(_search_state['matches'])
                _do_search(term, (idx + 1) % n if n else 0)

            def _on_prev(e):
                term = txt.GetValue().strip()
                if not term:
                    return
                idx = _search_state['idx']
                n   = len(_search_state['matches'])
                _do_search(term, (idx - 1) % n if n else 0)

            def _on_close_search(e):
                orig = _search_state.get('html_orig', '')
                if orig:
                    hw.SetPage(orig)
                _search_state['matches'] = []
                _search_state['idx'] = -1
                sdlg.EndModal(wx.ID_CANCEL)

            btn_next.Bind(wx.EVT_BUTTON, _on_next)
            btn_prev.Bind(wx.EVT_BUTTON, _on_prev)
            btn_close.Bind(wx.EVT_BUTTON, _on_close_search)
            txt.Bind(wx.EVT_TEXT_ENTER, _on_next)
            sdlg.Bind(wx.EVT_CLOSE, _on_close_search)

            txt.SetFocus()
            txt.SetSelection(-1, -1)   # seleziona tutto il testo preesistente
            if _search_state['term']:
                _do_search(_search_state['term'])

            sdlg.ShowModal()
            sdlg.Destroy()

        # ── Menu contestuale tasto destro ──────────────────────────────
        def _on_hw_right_click(evt):
            menu = wx.Menu()

            # Icona copy.png dalla cartella img del progetto
            _copy_img = wx.Image(glb.AddPath('img/copy.png'))
            bmp_copy = wx.Bitmap(_copy_img) if _copy_img.IsOk() else wx.NullBitmap

            item_copy = wx.MenuItem(menu, wx.ID_COPY, _("Copy"))
            if bmp_copy.IsOk():
                item_copy.SetBitmap(bmp_copy)
            menu.Append(item_copy)

            # Abilita "Copia" solo se c'è testo selezionato
            sel = hw.SelectionToText()
            menu.Enable(wx.ID_COPY, bool(sel))

            def _copy(e):
                text = hw.SelectionToText()
                if text and wx.TheClipboard.Open():
                    wx.TheClipboard.SetData(wx.TextDataObject(text))
                    wx.TheClipboard.Close()

            menu.Bind(wx.EVT_MENU, _copy, id=wx.ID_COPY)

            menu.AppendSeparator()

            # ── Voce "Cerca" con icona img/search.png ─────────────────
            _id_search = wx.NewIdRef()
            _search_img = wx.Image(glb.AddPath('img/search.png'))
            _bmp_search = wx.Bitmap(_search_img) if _search_img.IsOk() \
                else wx.ArtProvider.GetBitmap(wx.ART_FIND, wx.ART_MENU, (16, 16))
            item_search = wx.MenuItem(menu, _id_search, _("Find in guide..."))
            if _bmp_search.IsOk():
                item_search.SetBitmap(_bmp_search)
            menu.Append(item_search)

            def _on_search(e):
                # Salva l'HTML corrente la prima volta (prima di ogni evidenziazione)
                if not _search_state.get('html_orig'):
                    _search_state['html_orig'] = hw.GetParser().GetSource() \
                        if hw.GetParser() else ''
                _guide_search_open()

            menu.Bind(wx.EVT_MENU, _on_search, id=_id_search)

            hw.PopupMenu(menu)
            menu.Destroy()

        hw.Bind(wx.EVT_RIGHT_DOWN, _on_hw_right_click)
        # ── Fine menu contestuale ──────────────────────────────────────

        sizer.Add(hw, 1, wx.EXPAND | wx.ALL, 4)

        # ── Stato zoom e tema — ripristinati dalle preferenze ────────
        _zoom_pct = [max(50, min(200, getattr(self.pref, 'guideZoom', 100)))]
        _dark_mode = [bool(getattr(self.pref, 'guideDarkMode', False))]

        # Palette colori per i due temi
        _THEME = {
            False: {   # chiaro
                'bg':       '#ffffff',
                'text':     '#000000',
                'link':     '#0066cc',
                'pre_bg':   '#f4f4f4',
                'pre_fg':   '#000000',
                'th_bg':    '#e8e8e8',
                'td_border':'#cccccc',
                'bq_fg':    '#555555',
                'h_fg':     '#000000',
            },
            True: {    # scuro
                'bg':       '#1e1e1e',
                'text':     '#d4d4d4',
                'link':     '#4fc1ff',
                'pre_bg':   '#2d2d2d',
                'pre_fg':   '#ce9178',
                'th_bg':    '#3a3a3a',
                'td_border':'#555555',
                'bq_fg':    '#999999',
                'h_fg':     '#9cdcfe',
            },
        }

        import re as _re

        def _colorize_body(body_html, dark):
            """
            wx.html.HtmlWindow non applica CSS <style>: usa solo attributi HTML
            legacy. Sostituiamo quindi i tag rilevanti con versioni colorate via
            attributi bgcolor/color/text.
            """
            p = _THEME[dark]

            # <pre ...> → <pre bgcolor="..." color="...">
            body_html = _re.sub(
                r'<pre(\s[^>]*)?>',
                lambda m: '<pre bgcolor="%s"><font color="%s">' % (p['pre_bg'], p['pre_fg']),
                body_html, flags=_re.IGNORECASE,
            )
            body_html = _re.sub(r'</pre>', '</font></pre>', body_html, flags=_re.IGNORECASE)

            # <th ...> → <th bgcolor="...">
            body_html = _re.sub(
                r'<th(\s[^>]*)?>',
                lambda m: '<th bgcolor="%s">' % p['th_bg'],
                body_html, flags=_re.IGNORECASE,
            )

            # Colore intestazioni h1-h4
            for hn in ('h1', 'h2', 'h3', 'h4'):
                body_html = _re.sub(
                    r'<' + hn + r'(\s[^>]*)?>',
                    lambda m, _hn=hn: '<%s><font color="%s">' % (_hn, p['h_fg']),
                    body_html, flags=_re.IGNORECASE,
                )
                body_html = _re.sub(
                    r'</' + hn + r'>',
                    '</font></%s>' % hn,
                    body_html, flags=_re.IGNORECASE,
                )

            return body_html

        def _rebuild_page(dark):
            """Ricostruisce l'HTML con attributi colore compatibili con
            wx.html.HtmlWindow e aggiorna anche il colore di sfondo del widget."""
            p = _THEME[dark]
            body_colored = _colorize_body(html_body, dark)

            # Attributi <body> legacy: bgcolor, text, link
            styled = (
                '<html><head></head>'
                '<body bgcolor="%s" text="%s" link="%s">'
                '%s'
                '</body></html>'
            ) % (p['bg'], p['text'], p['link'], body_colored)

            # Colore di sfondo del widget wx (visibile durante lo scroll)
            hw.SetBackgroundColour(wx.Colour(
                int(p['bg'][1:3], 16),
                int(p['bg'][3:5], 16),
                int(p['bg'][5:7], 16),
            ))
            hw.SetPage(styled)
            hw.Bind(wx.html.EVT_HTML_LINK_CLICKED,
                    lambda e: wx.LaunchDefaultBrowser(e.GetLinkInfo().GetHref()))

        # Estraiamo il body dall'HTML già generato per poterlo riciclare
        _body_m = _re.search(r'<body>(.*)</body>', html, _re.DOTALL | _re.IGNORECASE)
        html_body = _body_m.group(1) if _body_m else html

        # Carichiamo la pagina iniziale con il tema salvato
        _rebuild_page(_dark_mode[0])

        # ── Barra inferiore ──────────────────────────────────────────
        btn_row = wx.BoxSizer(wx.HORIZONTAL)

        # Pulsante Schermo intero
        btn_max = wx.Button(dlg, wx.ID_ANY, _("Full screen"))
        btn_max.SetToolTip(_("Toggle full screen"))

        def _on_toggle_max(e):
            if dlg.IsMaximized():
                dlg.Restore()
                btn_max.SetLabel(_("Full screen"))
            else:
                dlg.Maximize()
                btn_max.SetLabel(_("Restore"))

        btn_max.Bind(wx.EVT_BUTTON, _on_toggle_max)

        def _fix_btn_max_size():
            dc = wx.ClientDC(btn_max)
            dc.SetFont(btn_max.GetFont())
            w1 = dc.GetTextExtent(_("Full screen"))[0]
            w2 = dc.GetTextExtent(_("Restore"))[0]
            best = btn_max.GetBestSize()
            cur_tw = dc.GetTextExtent(btn_max.GetLabel())[0]
            padding = best.width - cur_tw
            min_w = max(w1, w2) + max(padding, 20)
            btn_max.SetMinSize(wx.Size(min_w, best.height))
            btn_max.GetContainingSizer().Layout()
        wx.CallAfter(_fix_btn_max_size)

        # ── Zoom: pulsante −, slider, pulsante +, etichetta % ────────
        btn_zoom_out = wx.Button(dlg, wx.ID_ANY, u"−", size=(28, -1))
        btn_zoom_out.SetToolTip(_("Zoom out"))

        zoom_slider = wx.Slider(
            dlg, value=_zoom_pct[0], minValue=50, maxValue=200,
            size=(160, -1),
            style=wx.SL_HORIZONTAL,
        )
        zoom_slider.SetToolTip(_("Zoom (50% – 200%)"))

        btn_zoom_in = wx.Button(dlg, wx.ID_ANY, u"+", size=(28, -1))
        btn_zoom_in.SetToolTip(_("Zoom in"))

        lbl_zoom = wx.StaticText(dlg, label=u"%d%%" % _zoom_pct[0], size=(40, -1))

        def _apply_zoom(pct):
            _zoom_pct[0] = max(50, min(200, pct))
            zoom_slider.SetValue(_zoom_pct[0])
            lbl_zoom.SetLabel(u"%d%%" % _zoom_pct[0])
            # wx.html.HtmlWindow espone SetFonts per variare la dimensione
            # Il secondo argomento è il font fisso; i successivi sono le 7 taglie
            base = _zoom_pct[0] // 10   # 5‥20 per zoom 50‥200
            sizes = [base - 2, base - 1, base, base + 1,
                     base + 2, base + 4, base + 6]
            hw.SetFonts("", "", sizes)
            hw.Refresh()

        def _on_zoom_out(e):
            _apply_zoom(_zoom_pct[0] - 10)
        def _on_zoom_in(e):
            _apply_zoom(_zoom_pct[0] + 10)
        def _on_slider(e):
            _apply_zoom(zoom_slider.GetValue())

        btn_zoom_out.Bind(wx.EVT_BUTTON, _on_zoom_out)
        btn_zoom_in.Bind(wx.EVT_BUTTON,  _on_zoom_in)
        zoom_slider.Bind(wx.EVT_SLIDER,  _on_slider)

        # ── Radiobutton tema Chiaro / Scuro ──────────────────────────
        rb_light = wx.RadioButton(dlg, label=_(u"Chiaro"), style=wx.RB_GROUP)
        rb_dark  = wx.RadioButton(dlg, label=_(u"Scuro"))
        # Icone sole / luna
        _sun_bmp  = wx.Bitmap(wx.Image(glb.AddPath('img/sun.png')))
        _moon_bmp = wx.Bitmap(wx.Image(glb.AddPath('img/moon.png')))
        icon_light = wx.StaticBitmap(dlg, -1, _sun_bmp)
        icon_dark  = wx.StaticBitmap(dlg, -1, _moon_bmp)
        # Ripristina la selezione salvata
        rb_dark.SetValue(_dark_mode[0])
        rb_light.SetValue(not _dark_mode[0])

        def _on_theme(e):
            dark = rb_dark.GetValue()
            _dark_mode[0] = dark
            _rebuild_page(dark)
            _apply_zoom(_zoom_pct[0])   # riapplica lo zoom dopo il reload

        rb_light.Bind(wx.EVT_RADIOBUTTON, _on_theme)
        rb_dark.Bind(wx.EVT_RADIOBUTTON,  _on_theme)

        btn_close = wx.Button(dlg, wx.ID_OK, _("Close"))

        # Layout barra: [Schermo intero]  [−][slider][+][%]  [Chiaro ☀][Scuro ☾]  [Chiudi]
        btn_row.Add(btn_max,      0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        btn_row.AddStretchSpacer()
        btn_row.Add(btn_zoom_out, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 2)
        btn_row.Add(zoom_slider,  0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 2)
        btn_row.Add(btn_zoom_in,  0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        btn_row.Add(lbl_zoom,     0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
        btn_row.Add(icon_light,   0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 2)
        btn_row.Add(rb_light,     0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        btn_row.Add(icon_dark,    0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 2)
        btn_row.Add(rb_dark,      0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
        btn_row.Add(btn_close,    0, wx.ALIGN_CENTER_VERTICAL)

        sizer.Add(btn_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        dlg.SetSizer(sizer)
        dlg.Layout()

        # Applica zoom e tema iniziali (dopo che tutti i controlli sono creati)
        _apply_zoom(_zoom_pct[0])

        dlg.ShowModal()

        # Salva le preferenze in pref (su disco le scriverà OnClose/_SaveGuidePrefs)
        self.pref.guideZoom     = _zoom_pct[0]
        self.pref.guideDarkMode = _dark_mode[0]

        dlg.Destroy()

    def _md_to_html(self, md_text):
        """Converte Markdown in HTML per wx.html.HtmlWindow.
        Il viewer usato dipende dalla preferenza pref.guideViewer:
          'markdown' → python-markdown (fallback: mistune → builtin)
          'mistune'  → mistune (fallback: builtin)
          'builtin'  → parser interno sempre
        """
        viewer = getattr(self.pref, 'guideViewer', 'markdown')

        if viewer in ('markdown', 'auto'):
            try:
                import markdown as _markdown_lib
                body = _markdown_lib.markdown(
                    md_text,
                    extensions=['tables', 'fenced_code'],
                )
                return self._md_wrap_html(body)
            except ImportError:
                pass
            # fallthrough a mistune
            viewer = 'mistune'

        if viewer == 'mistune':
            try:
                import mistune as _mistune_lib
                body = _mistune_lib.html(md_text)
                return self._md_wrap_html(body)
            except ImportError:
                pass
            # fallthrough a builtin

        # Parser interno (sempre disponibile)
        return self._md_to_html_builtin(md_text)

    @staticmethod
    def _md_wrap_html(body):
        """Avvolge il corpo HTML con head e stili comuni."""
        return (
            '<html><head><style>'
            'body{font-family:Arial,sans-serif;margin:16px;font-size:13px;}'
            'a{color:#0066cc;}'
            'pre{background:#f4f4f4;padding:8px;border-radius:4px;}'
            'code{background:#f0f0f0;padding:1px 4px;}'
            'table{border-collapse:collapse;}'
            'th,td{border:1px solid #ccc;padding:4px 8px;}'
            'th{background:#e8e8e8;font-weight:bold;}'
            'blockquote{border-left:3px solid #ccc;margin:0 0 0 12px;padding-left:8px;color:#555;}'
            '</style></head>'
            f'<body>{body}</body></html>'
        )

    def _md_to_html_builtin(self, md_text):
        """Parser Markdown interno, usato quando nessuna libreria esterna è disponibile."""
        import re

        # ── Helper ────────────────────────────────────────────────────
        def esc(s):
            """Escape caratteri HTML speciali."""
            return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        def inline(s):
            """Applica le sostituzioni inline (grassetto, corsivo, code, link, img)."""
            # Grassetto+corsivo combinati: ***testo***
            s = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', s)
            # Grassetto: **testo** o __testo__
            s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
            s = re.sub(r'__(.+?)__',     r'<b>\1</b>', s)
            # Corsivo: *testo* o _testo_
            s = re.sub(r'\*(.+?)\*', r'<i>\1</i>', s)
            s = re.sub(r'_(.+?)_',   r'<i>\1</i>', s)
            # Codice inline
            s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
            # Immagini cliccabili: [![alt](src)](href) — deve precedere link e img
            s = re.sub(r'\[(<img [^>]+>)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
            # Immagini: ![alt](src)
            s = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',
                       r'<img src="\2" alt="\1" style="max-width:100%;">', s)
            # Link: [testo](url)
            s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
            return s

        def close_lists(html_lines, list_stack):
            """Chiude tutti i livelli di lista aperti."""
            while list_stack:
                html_lines.append('</' + list_stack.pop() + '>')

        lines = md_text.split('\n')
        html_lines = []
        in_code    = False
        in_table   = False
        table_header_done = False
        in_blockquote = False
        list_stack = []   # stack di 'ul' / 'ol' per liste annidate
        blank_count = 0   # righe vuote consecutive

        for line in lines:
            # ── Blocco codice ─────────────────────────────────────────
            if line.startswith('```'):
                close_lists(html_lines, list_stack)
                if in_table:
                    html_lines.append('</table>')
                    in_table = False
                if in_blockquote:
                    html_lines.append('</blockquote>')
                    in_blockquote = False
                if in_code:
                    html_lines.append('</pre>')
                    in_code = False
                else:
                    html_lines.append('<pre>')
                    in_code = True
                blank_count = 0
                continue

            if in_code:
                html_lines.append(esc(line))
                continue

            # ── Tabella ───────────────────────────────────────────────
            if line.startswith('|'):
                close_lists(html_lines, list_stack)
                if in_blockquote:
                    html_lines.append('</blockquote>')
                    in_blockquote = False
                if not in_table:
                    html_lines.append(
                        '<table border="1" cellpadding="4" cellspacing="0"'
                        ' style="border-collapse:collapse;">'
                    )
                    in_table = True
                    table_header_done = False
                # Riga separatrice (|---|---|) → segna fine intestazione
                if re.match(r'^\|[-| :]+\|$', line):
                    table_header_done = True
                    continue
                cells = [inline(esc(c.strip())) for c in line.strip('|').split('|')]
                if not table_header_done:
                    html_lines.append(
                        '<tr>' + ''.join(f'<th>{c}</th>' for c in cells) + '</tr>'
                    )
                else:
                    html_lines.append(
                        '<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>'
                    )
                blank_count = 0
                continue
            else:
                if in_table:
                    html_lines.append('</table>')
                    in_table = False

            # ── Riga vuota ────────────────────────────────────────────
            if line.strip() == '':
                blank_count += 1
                # Chiude blockquote alla prima riga vuota
                if in_blockquote:
                    html_lines.append('</blockquote>')
                    in_blockquote = False
                # Una sola riga vuota tra paragrafi è sufficiente
                if blank_count == 1:
                    html_lines.append('<p style="margin:4px 0"> </p>')
                continue
            blank_count = 0

            # ── Blockquote: > testo ───────────────────────────────────
            bq_match = re.match(r'^> ?(.*)', line)
            if bq_match:
                close_lists(html_lines, list_stack)
                if not in_blockquote:
                    html_lines.append('<blockquote>')
                    in_blockquote = False  # rimane False; il tag è già aperto
                    in_blockquote = True
                html_lines.append(f'<p style="margin:2px 0">{inline(esc(bq_match.group(1)))}</p>')
                continue
            else:
                if in_blockquote:
                    html_lines.append('</blockquote>')
                    in_blockquote = False

            # ── Intestazioni (fino a ######) ──────────────────────────
            h_match = re.match(r'^(#{1,6}) (.*)', line)
            if h_match:
                close_lists(html_lines, list_stack)
                level = len(h_match.group(1))
                html_lines.append(f'<h{level}>{inline(esc(h_match.group(2)))}</h{level}>')
                continue

            # ── Separatore orizzontale ────────────────────────────────
            if re.match(r'^(-{3,}|\*{3,}|_{3,})$', line.strip()):
                close_lists(html_lines, list_stack)
                html_lines.append('<hr/>')
                continue

            # ── Liste puntate (-, *, +) con indentazione ──────────────
            ul_match = re.match(r'^( *)[-*+] (.*)', line)
            if ul_match:
                indent = len(ul_match.group(1)) // 2  # livello 0-based
                content = inline(esc(ul_match.group(2)))
                # Aggiusta lo stack al livello corrente
                while len(list_stack) > indent + 1:
                    html_lines.append('</' + list_stack.pop() + '>')
                if len(list_stack) < indent + 1:
                    html_lines.append('<ul>')
                    list_stack.append('ul')
                elif list_stack and list_stack[-1] == 'ol':
                    html_lines.append('</ol>')
                    list_stack.pop()
                    html_lines.append('<ul>')
                    list_stack.append('ul')
                html_lines.append(f'<li>{content}</li>')
                continue

            # ── Liste numerate (1. 2. …) ──────────────────────────────
            ol_match = re.match(r'^( *)\d+\. (.*)', line)
            if ol_match:
                indent = len(ol_match.group(1)) // 2
                content = inline(esc(ol_match.group(2)))
                while len(list_stack) > indent + 1:
                    html_lines.append('</' + list_stack.pop() + '>')
                if len(list_stack) < indent + 1:
                    html_lines.append('<ol>')
                    list_stack.append('ol')
                elif list_stack and list_stack[-1] == 'ul':
                    html_lines.append('</ul>')
                    list_stack.pop()
                    html_lines.append('<ol>')
                    list_stack.append('ol')
                html_lines.append(f'<li>{content}</li>')
                continue

            # ── Paragrafo generico ────────────────────────────────────
            close_lists(html_lines, list_stack)
            html_lines.append(f'<p style="margin:2px 0">{inline(esc(line))}</p>')

        # ── Chiusura tag rimasti aperti ───────────────────────────────
        close_lists(html_lines, list_stack)
        if in_table:
            html_lines.append('</table>')
        if in_code:
            html_lines.append('</pre>')
        if in_blockquote:
            html_lines.append('</blockquote>')

        body = '\n'.join(html_lines)
        return self._md_wrap_html(body)

    def OnIdle(self, evt):
        try:
            cp = self.text.CanPaste()
            self.mainToolBar.EnableTool(self.pasteTool, cp)
            self.menuBar.Enable(self.pasteMenuId, cp)
            self.mainToolBar.EnableTool(self.pasteChordsTool, cp)
            self.menuBar.Enable(self.pasteChordsMenuId, cp)
        except Exception:
            # When frame is closed, this method may still be executed, generating an exception
            # because UI elements have been destroyed. Simply ignore it.
            pass
        evt.Skip()

    def OnFormatFont(self, evt):
        f = FontFaceDialog(
            self.frame,
            wx.ID_ANY,
            _("Song font - Songpress++"),
            self.pref.format,
            self.pref.decorator,
            self.pref.decoratorFormat,
            greyBackground=getattr(self.pref, 'greyBackground', True)
        )
        if f.ShowModal() == wx.ID_OK:
            self.pref.SetFont(f.GetValue())
            self.SetFont()

    def OnTextFont(self, evt):
        data = wx.FontData()
        data.SetInitialFont(self.pref.format.wxFont)
        data.SetColour(self.pref.format.color)

        dialog = wx.FontDialog(self.frame, data)
        dialog.SetTitle(_("Text font - Songpress++"))
        if dialog.ShowModal() == wx.ID_OK:
            retData = dialog.GetFontData()
            font = retData.GetChosenFont()
            face = font.GetFaceName()
            size = font.GetPointSize()
            color = retData.GetColour().GetAsString(wx.C2S_HTML_SYNTAX)
            s = f"{{textfont:{face}}}{{textsize:{size}}}{{textcolour:{color}}}|"
            s += "{textfont}{textsize}{textcolour}"
            self.InsertWithCaret(s)

    def OnChordFont(self, evt):
        data = wx.FontData()
        data.SetInitialFont(self.pref.format.wxFont)
        data.SetColour(self.pref.format.color)

        dialog = wx.FontDialog(self.frame, data)
        dialog.SetTitle(_("Chord font - Songpress++"))
        if dialog.ShowModal() == wx.ID_OK:
            retData = dialog.GetFontData()
            font = retData.GetChosenFont()
            face = font.GetFaceName()
            size = font.GetPointSize()
            color = retData.GetColour().GetAsString(wx.C2S_HTML_SYNTAX)
            s = f"{{chordfont:{face}}}{{chordsize:{size}}}{{chordcolour:{color}}}|"
            s += "{chordfont}{chordsize}{chordcolour}"
            self.InsertWithCaret(s)

    # ------------------------------------------------------------------
    # Mappa PaperId wxPython -> (larghezza_mm, altezza_mm) in portrait.
    # I valori coprono i formati piu' comuni; per quelli non elencati
    # si usa A4 come fallback.
    # ------------------------------------------------------------------
    _PAPER_SIZE_MM = {
        wx.PAPER_A3:        (297.0, 420.0),
        wx.PAPER_A4:        (210.0, 297.0),
        wx.PAPER_A5:        (148.0, 210.0),
        wx.PAPER_B4:        (250.0, 354.0),
        wx.PAPER_B5:        (176.0, 250.0),
        wx.PAPER_LETTER:    (215.9, 279.4),
        wx.PAPER_LEGAL:     (215.9, 355.6),
        wx.PAPER_TABLOID:   (279.4, 431.8),
        wx.PAPER_EXECUTIVE: (184.1, 266.7),
    }

    def _GetPaperSizeMm(self):
        """Restituisce (w_mm, h_mm) del foglio corrente tenendo conto
        dell'orientamento (portrait / landscape)."""
        pid = self._print_data.GetPaperId()
        w, h = self._PAPER_SIZE_MM.get(pid, (210.0, 297.0))
        if self._print_data.GetOrientation() == wx.LANDSCAPE:
            w, h = h, w
        return w, h

    def OnPageSetup(self, evt):
        """Open the page setup dialog (paper size, orientation, margins)."""
        data = wx.PageSetupDialogData(self._print_data)
        data.SetMarginTopLeft(wx.Point(self._margin_left, self._margin_top))
        data.SetMarginBottomRight(wx.Point(self._margin_right, self._margin_bottom))
        dlg = wx.PageSetupDialog(self.frame, data)
        if dlg.ShowModal() == wx.ID_OK:
            result = dlg.GetPageSetupData()
            self._print_data = wx.PrintData(result.GetPrintData())
            tl = result.GetMarginTopLeft()
            br = result.GetMarginBottomRight()
            self._margin_left   = tl.x
            self._margin_top    = tl.y
            self._margin_right  = br.x
            self._margin_bottom = br.y
            # Aggiorna indicatore di pagina nell'anteprima
            w_mm, h_mm = self._GetPaperSizeMm()
            self.previewCanvas.SetPageSizeMm(w_mm, h_mm)
            self.previewCanvas.SetPageMarginsMm(self._margin_top, self._margin_bottom)
        dlg.Destroy()


    def _reopen_print_options_if_pinned(self):
        """Riapre il dialog delle opzioni di stampa sul preview frame corrente,
        se il pin era attivo. Chiamato da wx.CallLater dopo che OnPrintPreview
        ha creato il nuovo pf."""
        if not getattr(self, '_print_options_pinned', False):
            return
        pf = getattr(self, '_preview_frame', None)
        if pf is None or not pf.IsShown():
            return
        # Ripeti on_print_options sul nuovo pf — stessa logica del caller originale
        _dlg_ref = [None]

        def _do_apply():
            self.previewCanvas.SetColumns(self._columns_per_page)
            self.previewCanvas.Refresh(self._get_display_text())
            if self._print_options_pinned and _dlg_ref[0] is not None:
                dlg = _dlg_ref[0]
                dlg.EndModal(wx.ID_OK)
                def _deferred_reopen():
                    pf.Close()
                    self.OnPrintPreview(None)
                    wx.CallAfter(
                        wx.CallLater, 50,
                        lambda: self._reopen_print_options_if_pinned()
                    )
                wx.CallAfter(_deferred_reopen)
            else:
                pf.Close()
                wx.CallAfter(self.OnPrintPreview, None)

        self._ask_two_pages_per_sheet(parent=pf, on_apply=_do_apply, _dlg_ref=_dlg_ref)

    def _ask_two_pages_per_sheet(self, parent=None, on_apply=None, _dlg_ref=None):
        """
        Shows a small dialog asking the user whether they want to print
        2 pages per sheet and/or use multiple columns per page.
        Updates self._two_pages_per_sheet and self._columns_per_page.
        Returns True if the user confirmed (OK), False if cancelled.

        A pin button (📌/📍) keeps the dialog open after OK so the user can
        tweak settings repeatedly without reopening.  When pinned, each OK
        immediately calls ``on_apply()`` (if provided) so the preview updates.

        Args:
            parent:   parent window (falls back to self.frame if None)
            on_apply: optional callable invoked after options are saved,
                      both in normal mode (before closing) and while pinned.
            _dlg_ref: optional list [None] — populated with the wx.Dialog
                      instance so the caller can reparent it if needed.
        """
        dialog_parent = parent if parent is not None else self.frame

        dlg = wx.Dialog(dialog_parent, title=_("Print options"),
                        style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)

        # Expose the dialog instance to the caller if requested
        if _dlg_ref is not None:
            _dlg_ref[0] = dlg
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Checkbox for 2 pages per sheet
        cb = wx.CheckBox(dlg, label=_("Print 2 pages per sheet"))
        cb.SetValue(self._two_pages_per_sheet)
        sizer.Add(cb, 0, wx.ALL, 12)

        # Radio buttons: colonne per pagina
        sizer.Add(wx.StaticText(dlg, label=_("Columns per page:")), 0, wx.LEFT | wx.RIGHT, 12)
        rb_col1 = wx.RadioButton(dlg, -1, _("1 column"), style=wx.RB_GROUP)
        rb_col2 = wx.RadioButton(dlg, -1, _("2 columns"))
        rb_col1.SetValue(self._columns_per_page == 1)
        rb_col2.SetValue(self._columns_per_page == 2)
        col_sizer = wx.BoxSizer(wx.HORIZONTAL)
        col_sizer.Add(rb_col1, 0, wx.RIGHT, 16)
        col_sizer.Add(rb_col2, 0)
        sizer.Add(col_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # Checkbox: riduci e adatta alla pagina
        cb_fit = wx.CheckBox(dlg, label=_("Fit to page"))
        cb_fit.SetValue(self._fit_to_page)
        sizer.Add(cb_fit, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # Checkbox: riduzione automatica per evitare il taglio del testo in fondo pagina
        cb_shrink = wx.CheckBox(dlg, label=_("Shrink to fit current page (prevent bottom clipping)"))
        cb_shrink.SetValue(self._shrink_to_fit)
        sizer.Add(cb_shrink, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # SpinCtrl: margine minimo per la riduzione automatica (abilitato solo se cb_shrink attivo)
        shrink_margin_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lbl_min_margin = wx.StaticText(dlg, label=_("Min margin for auto-shrink (mm):"))
        spin_min_margin = wx.SpinCtrl(dlg, min=0, max=50,
                                      value=str(getattr(self, '_min_margin_shrink', 5)),
                                      size=(60, -1))
        shrink_margin_sizer.Add(lbl_min_margin, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        shrink_margin_sizer.Add(spin_min_margin, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(shrink_margin_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        # Abilita/disabilita lo spin in base allo stato di cb_shrink
        lbl_min_margin.Enable(self._shrink_to_fit)
        spin_min_margin.Enable(self._shrink_to_fit)
        def on_shrink_changed(evt):
            enabled = cb_shrink.GetValue()
            lbl_min_margin.Enable(enabled)
            spin_min_margin.Enable(enabled)
            evt.Skip()
        cb_shrink.Bind(wx.EVT_CHECKBOX, on_shrink_changed)

        # Checkbox: non replicare il brano sulla metà destra (visibile solo con 2 pag/foglio)
        cb_no_mirror = wx.CheckBox(dlg, label=_("Do not replicate (leave right half blank)"))
        cb_no_mirror.SetValue(self._no_mirror_right)
        cb_no_mirror.Enable(self._two_pages_per_sheet)
        sizer.Add(cb_no_mirror, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # Checkbox: rimuovi pagine bianche
        cb_remove_blank = wx.CheckBox(dlg, label=_("Remove blank pages"))
        cb_remove_blank.SetValue(self._remove_blank_pages)
        sizer.Add(cb_remove_blank, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        # Abilita/disabilita cb_no_mirror al variare di cb (2 pagine per foglio)
        def on_cb_changed(evt):
            cb_no_mirror.Enable(cb.GetValue())
            evt.Skip()
        cb.Bind(wx.EVT_CHECKBOX, on_cb_changed)

        # --- Bottoni: [📌] [OK] [Annulla] ---
        PIN_OFF = u"📌"
        PIN_ON  = u"📍"
        _pinned = [getattr(self, '_print_options_pinned', False)]

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_pin    = wx.Button(dlg, wx.ID_ANY, PIN_ON if _pinned[0] else PIN_OFF, size=(32, -1))
        btn_pin.SetToolTip(_("Keep this dialog open after applying"))
        btn_ok     = wx.Button(dlg, wx.ID_OK,     _("OK"))
        btn_cancel = wx.Button(dlg, wx.ID_CANCEL, _("Cancel"))
        btn_ok.SetDefault()

        btn_sizer.Add(btn_pin,    0, wx.RIGHT, 4)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(btn_ok,     0, wx.RIGHT, 4)
        btn_sizer.Add(btn_cancel, 0)
        sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 8)

        dlg.SetSizerAndFit(sizer)
        dlg.CentreOnParent()

        # Salva le opzioni su self, poi invoca on_apply se fornito
        def _apply_options():
            self._two_pages_per_sheet = cb.GetValue()
            self._columns_per_page    = 2 if rb_col2.GetValue() else 1
            self._fit_to_page         = cb_fit.GetValue()
            self._shrink_to_fit       = cb_shrink.GetValue()
            self._min_margin_shrink   = spin_min_margin.GetValue()
            self._no_mirror_right     = cb_no_mirror.GetValue()
            self._remove_blank_pages  = cb_remove_blank.GetValue()
            if on_apply is not None:
                on_apply()

        def on_pin(evt):
            _pinned[0] = not _pinned[0]
            self._print_options_pinned = _pinned[0]
            btn_pin.SetLabel(PIN_ON if _pinned[0] else PIN_OFF)

        def on_ok(evt):
            _apply_options()
            if not _pinned[0]:
                dlg.EndModal(wx.ID_OK)

        btn_pin.Bind(wx.EVT_BUTTON, on_pin)
        btn_ok.Bind(wx.EVT_BUTTON, on_ok)

        result = dlg.ShowModal()
        dlg.Destroy()
        return result == wx.ID_OK

    def OnPrint(self, evt):
        """Print the song exactly as shown in the preview."""
        # Se la preferenza showPrintPreview è attiva, mostra prima l'anteprima di stampa.
        if getattr(self.pref, 'showPrintPreview', True):
            self.OnPrintPreview(evt)
            return

        # Su Windows 11 il dialog nativo (usato da wx.Printer.Print con showDialog=True)
        # mostra "Questa app non supporta l'anteprima di stampa".
        # Si usa wx.PrintDialog separato per raccogliere le impostazioni, poi si stampa
        # con showDialog=False per evitare il dialog nativo problematico.
        pdd = wx.PrintDialogData(self._print_data)
        dlg = wx.PrintDialog(self.frame, pdd)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        self._print_data = wx.PrintData(dlg.GetPrintDialogData().GetPrintData())
        dlg.Destroy()

        pdd2 = wx.PrintDialogData(self._print_data)
        printer = wx.Printer(pdd2)
        printout = SongpressPrintout(self, _("Print"), two_pages_per_sheet=self._two_pages_per_sheet)
        success = printer.Print(self.frame, printout, False)
        if not success:
            if printer.GetLastError() == wx.PRINTER_ERROR:
                wx.MessageBox(
                    _("An error occurred while printing.\nPlease check your printer settings."),
                    _("Print error"),
                    wx.OK | wx.ICON_ERROR,
                    self.frame,
                )
        printout.Destroy()

    def OnPrintPreview(self, evt):
        """Show a print preview of the song."""
        title = os.path.splitext(os.path.basename(self.document))[0] if self.document else _("Print")
        printout1 = SongpressPrintout(self, title, two_pages_per_sheet=self._two_pages_per_sheet)
        printout2 = SongpressPrintout(self, title, two_pages_per_sheet=self._two_pages_per_sheet)
        preview = wx.PrintPreview(printout1, printout2, self._print_data)
        if not preview.IsOk():
            wx.MessageBox(
                _("Unable to create print preview.\nPlease check your printer settings."),
                _("Print preview error"),
                wx.OK | wx.ICON_ERROR,
                self.frame,
            )
            return
        pf = wx.PreviewFrame(preview, self.frame, _("Print preview"))
        pf.Initialize()
        self._preview_frame = pf   # saved for _reopen_print_options_if_pinned

        # Rename the default "Print with icon" button to "Print..."
        # and add a "Page setup..." button to the preview toolbar.
        # wx.PreviewFrame exposes the control bar via GetControlBar() only
        # after Initialize(); on some wxPython builds the method is missing,
        # so we fall back to iterating child windows.
        ctrl_bar = None
        get_cb = getattr(pf, 'GetControlBar', None)
        if get_cb is not None:
            ctrl_bar = get_cb()
        if ctrl_bar is None:
            for child in pf.GetChildren():
                if isinstance(child, wx.PreviewControlBar):
                    ctrl_bar = child
                    break

        if ctrl_bar is not None:
            # Rename the built-in wxWidgets buttons using our translation catalog.
            # wx.PreviewControlBar sets these labels in English; we override them
            # so they follow the active wx.Locale set by i18n.setLang().
            #
            # NOTE: wx.ID_PREVIEW_* constants are NOT exposed in wxPython, so we
            # identify buttons by their current English label text instead.
            # wx.ID_PRINT and wx.ID_CLOSE are standard wx constants and are safe.
            _label_map = {
                "Print":     _("Print..."),
                "Print...":  _("Print..."),
                "Next":      _("Next page"),
                "Prev":      _("Previous page"),
                "Previous":  _("Previous page"),
                "First":     _("First page"),
                "Last":      _("Last page"),
                "Close":     _("Close"),
            }
            for child in ctrl_bar.GetChildren():
                if isinstance(child, wx.Button):
                    lbl = child.GetLabel().strip()
                    if lbl in _label_map:
                        child.SetLabel(_label_map[lbl])
            # wx.ID_PRINT is a safe standard constant — rename directly too
            # in case the button uses that ID but a non-standard label
            btn_print = ctrl_bar.FindWindowById(wx.ID_PRINT)
            if btn_print is not None:
                btn_print.SetLabel(_("Print..."))
            
            # NEW: Add "Print options..." button with icon
            btn_options = wx.Button(ctrl_bar, wx.ID_ANY, _("Print options..."))
            _icon_path = glb.AddPath('img/productivity-expert-icon.png')
            if os.path.isfile(_icon_path):
                _icon_img = wx.Image(_icon_path, wx.BITMAP_TYPE_PNG)
                btn_options.SetBitmap(wx.Bitmap(_icon_img))
                btn_options.SetBitmapPosition(wx.LEFT)
            
            def on_print_options(e):
                """Callback to open the print options dialog"""

                # _dlg_ref viene popolato da _ask_two_pages_per_sheet tramite il
                # meccanismo on_apply; lo usiamo per reparentare il dialog prima
                # di chiudere pf, evitando che venga distrutto insieme al parent.
                _dlg_ref = [None]

                def _do_apply():
                    self.previewCanvas.SetColumns(self._columns_per_page)
                    self.previewCanvas.Refresh(self._get_display_text())
                    if self._print_options_pinned and _dlg_ref[0] is not None:
                        # Con il pin attivo dobbiamo chiudere pf e riaprire la preview.
                        # Per farlo in sicurezza: chiudiamo prima il ShowModal del dialog
                        # (EndModal), poi con CallAfter riapriamo preview+dialog.
                        dlg = _dlg_ref[0]
                        dlg.EndModal(wx.ID_OK)   # esce da ShowModal senza distruggere dlg
                        def _deferred_reopen():
                            pf.Close()
                            self.OnPrintPreview(None)
                            # Riapre il dialog delle opzioni sul nuovo pf tramite
                            # un secondo CallAfter (dopo che OnPrintPreview ha creato pf)
                            wx.CallAfter(
                                wx.CallLater, 50,
                                lambda: self._reopen_print_options_if_pinned()
                            )
                        wx.CallAfter(_deferred_reopen)
                    else:
                        pf.Close()
                        wx.CallAfter(self.OnPrintPreview, None)

                dlg_instance = self._ask_two_pages_per_sheet(
                    parent=pf, on_apply=_do_apply, _dlg_ref=_dlg_ref
                )
            
            btn_options.Bind(wx.EVT_BUTTON, on_print_options)
            
            # NEW: Add "Page setup..." button
            btn_page_setup = wx.Button(ctrl_bar, wx.ID_ANY, _("Page setup..."))
            _page_icon_path = glb.AddPath('img/file-black-icon.png')
            if os.path.isfile(_page_icon_path):
                _page_img = wx.Image(_page_icon_path, wx.BITMAP_TYPE_PNG)
                btn_page_setup.SetBitmap(wx.Bitmap(_page_img))
                btn_page_setup.SetBitmapPosition(wx.LEFT)

            def on_page_setup_preview(e):
                """Callback to open the page setup dialog from the preview"""
                data = wx.PageSetupDialogData(self._print_data)
                data.SetMarginTopLeft(wx.Point(self._margin_left, self._margin_top))
                data.SetMarginBottomRight(wx.Point(self._margin_right, self._margin_bottom))
                dlg = wx.PageSetupDialog(pf, data)
                if dlg.ShowModal() == wx.ID_OK:
                    result = dlg.GetPageSetupData()
                    self._print_data = wx.PrintData(result.GetPrintData())
                    tl = result.GetMarginTopLeft()
                    br = result.GetMarginBottomRight()
                    self._margin_left   = tl.x
                    self._margin_top    = tl.y
                    self._margin_right  = br.x
                    self._margin_bottom = br.y
                    dlg.Destroy()
                    pf.Close()
                    wx.CallAfter(self.OnPrintPreview, None)
                else:
                    dlg.Destroy()

            btn_page_setup.Bind(wx.EVT_BUTTON, on_page_setup_preview)

            # Explicit "Close" button (the native one from wx.PreviewControlBar
            # disappears when we manipulate the sizer, so we add our own).
            btn_close = wx.Button(ctrl_bar, wx.ID_ANY, _("Close"))
            btn_close.Bind(wx.EVT_BUTTON, lambda e: pf.Close())

            # Hide the native Close button: wx.PreviewControlBar uses an internal
            # ID not exposed in wxPython, so we search by label as fallback.
            native_close = ctrl_bar.FindWindowById(wx.ID_CLOSE)
            if native_close is not None:
                native_close.Hide()
            else:
                for child in ctrl_bar.GetChildren():
                    if isinstance(child, wx.AnyButton) and child.GetLabel().strip() in ('Close', _('Close')):
                        child.Hide()
                        break

            # Append all three custom buttons at the right end of the sizer,
            # AFTER the stretch spacer that wx.PreviewControlBar inserts to push
            # its own buttons to the right. We find the spacer by scanning items
            # from the end and insert our buttons after it.
            sizer = ctrl_bar.GetSizer()
            if sizer:
                # Find the last stretch spacer index
                spacer_idx = None
                for i in range(sizer.GetItemCount() - 1, -1, -1):
                    item = sizer.GetItem(i)
                    if item.IsSpacer() and item.GetProportion() > 0:
                        spacer_idx = i
                        break
                if spacer_idx is not None:
                    # Insert our buttons right after the spacer
                    ins = spacer_idx + 1
                    sizer.Insert(ins,     btn_page_setup, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
                    sizer.Insert(ins + 1, btn_options,    0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
                    sizer.Insert(ins + 2, btn_close,      0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
                else:
                    # Fallback: just append at the end
                    sizer.Add(btn_page_setup, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
                    sizer.Add(btn_options,    0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
                    sizer.Add(btn_close,      0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)

            # Uniform button height: use btn_options (tallest, has icon) as reference
            ref_h = btn_options.GetBestSize().height
            for btn in (btn_page_setup, btn_close):
                btn.SetMinSize(wx.Size(btn.GetBestSize().width, ref_h))
            ctrl_bar.Layout()

            # Second pass after Show() so GetSize() returns real pixel values.
            def _equalize_heights():
                try:
                    h = btn_options.GetSize().height
                    if h < 4:
                        return
                    for btn in (btn_page_setup, btn_close):
                        bw = btn.GetSize().width
                        btn.SetMinSize(wx.Size(bw, h))
                        btn.SetSize(wx.Size(bw, h))
                    ctrl_bar.Layout()
                except Exception:
                    pass
            wx.CallAfter(_equalize_heights)

        pf.Show()

        # Resize the preview window safely:
        # if the main frame is maximized GetSize() returns
        # the full screen size, causing the window to be positioned
        # off-screen. Use the display work area instead.
        display_idx = wx.Display.GetFromWindow(self.frame)
        if display_idx == wx.NOT_FOUND:
            display_idx = 0
        display = wx.Display(display_idx)
        client_area = display.GetClientArea()   # area without taskbar
        # Window at 90% of the work area, never larger than it
        preview_w = min(int(client_area.width  * 0.90), client_area.width)
        preview_h = min(int(client_area.height * 0.90), client_area.height)
        pf.SetSize(wx.Size(preview_w, preview_h))
        pf.CentreOnScreen()

    def OnTranspose(self, evt):
        t = MyTransposeDialog(self.frame, self.pref.notations, self.text.GetTextOrSelection())
        if t.ShowModal() == wx.ID_OK:
            self.text.ReplaceTextOrSelection(t.GetTransposed())

    def OnSimplifyChords(self, evt):
        self.text.AutoChangeMode(True)
        t = self.text.GetTextOrSelection()
        notation = autodetectNotation(t, self.pref.notations)
        count, c, dc, e, de = findEasiestKey(t, self.pref.GetEasyChords(), notation)
        title = _("Simplify chords")
        if count > 0 and dc != de:
            msg = _("The key of your song, %s, is not the easiest to play (difficulty: %.1f/5.0).\n") % (c, 5 * dc)
            msg += _("Do you want to transpose the key %s, which is the easiest one (difficulty: %.1f/5.0)?") % (e, 5 * de)
            d = wx.MessageDialog(self.frame, msg, title, wx.YES_NO | wx.ICON_QUESTION)
            if d.ShowModal() == wx.ID_YES:
                t = transposeChordPro(translateChord(c, notation), translateChord(e, notation), t, notation)
                self.text.ReplaceTextOrSelection(t)
        else:
            if count > 0:
                msg = _("The key of your song, %s, is already the easiest to play (difficulty: %.1f/5.0).\n") % (c, 5 * dc)
            else:
                msg = _("Your song or current selection does not contain any chords.")
            d = wx.MessageDialog(self.frame, msg, title, wx.OK | wx.ICON_INFORMATION)
            d.ShowModal()
        self.text.AutoChangeMode(False)

    def OnChangeChordNotation(self, evt):
        t = MyNotationDialog(self.frame, self.pref.notations, self.text.GetTextOrSelection())
        if t.ShowModal() == wx.ID_OK:
            self.text.ReplaceTextOrSelection(t.ChangeChordNotation())

    def OnNormalizeChords(self, evt):
        t = MyNormalizeDialog(self.frame, self.pref.notations, self.text.GetTextOrSelection())
        if t.ShowModal() == wx.ID_OK:
            self.text.ReplaceTextOrSelection(t.NormalizeChords())

    def OnConvertTabToChordpro(self, evt):
        t = self.text.GetTextOrSelection()
        n = testTabFormat(t, self.pref.notations)
        if n is not None:
            self.text.ReplaceTextOrSelection(tab2ChordPro(t, n))

    def OnRemoveSpuriousBlankLines(self, evt):
        self.text.ReplaceTextOrSelection(removeSpuriousLines(self.text.GetTextOrSelection()))

    def OnOptions(self, evt):
        def _apply_prefs():
            self.text.SetFont(self.pref.editorFace, int(self.pref.editorSize))
            self.SetDefaultExtension(self.pref.defaultExtension)
            self.previewCanvas.SetLineWidths(self.pref.titleLineWidth, self.pref.verseBoxWidth)
            self._applyKlavierHighlightColor()
            self._applyFingerNumColor()
            self.text.SetBgColour(getattr(self.pref, 'editorBgHex', '#FFFFFF'))
            self.text.SetSelColour(getattr(self.pref, 'selColourHex', '#3399FF'))
            _sc = getattr(self.pref, 'syntaxColours', {})
            for _k, _sid in [('normal', 11), ('chorus', 15), ('chord', 12), ('command', 13), ('attr', 14), ('comment', 16), ('tabgrid', 17)]:
                if _k in _sc:
                    self.text.SetSyntaxColour(_sid, _sc[_k])
            self.text.ApplyMultiCursor(getattr(self.pref, 'multiCursor', False))
            self._SaveCustomColours()
            self.previewCanvas.SetTempoDisplay(getattr(self.pref, 'tempoDisplay', 0))
            self.previewCanvas.SetTempoIconSize(getattr(self.pref, 'tempoIconSize', 24))
            self.previewCanvas.SetGridDisplayMode(getattr(self.pref, 'gridDisplayMode', 'pipe'))
            self.previewCanvas.SetGridDefaultLabel(getattr(self.pref, 'gridDefaultLabel', None))
            self.previewCanvas.SetGridSizeDir(getattr(self.pref, 'gridSizeDir', 'both'))
            self.previewCanvas.SetPageMarginsMm(self._margin_top, self._margin_bottom)
            self.previewCanvas.SetDurationBeatsPrefs(
                getattr(self.pref, 'durationBeatsColourHex', '#6464C8'),
                getattr(self.pref, 'durationBeatsSizePct', 60),
                getattr(self.pref, 'durationBeatsBold', False),
                getattr(self.pref, 'durationBeatsAlign', 'right'),
                getattr(self.pref, 'durationBeatsMode', 'number'),
            )
            self.previewCanvas.Refresh(self._get_display_text())
            # Aggiorna il MinSize del pane AUI in base alla preferenza corrente
            self._ApplyPreviewMinSize()
            # Aggiorna i colori delle caption bar con i nuovi valori da pref
            self._dockArt._pref = self.pref
            self._mgr.Update()

        f = MyPreferencesDialog(self.frame, self.pref, easyChords, on_apply=_apply_prefs,
                                previewCanvas=self.previewCanvas)
        if f.ShowModal() == wx.ID_OK:
            _apply_prefs()
        if f.clearRecentFiles:
            self._ClearRecentFiles()

    def _ClearRecentFiles(self):
        """Remove all entries from the recent files history."""
        self.ClearRecentFiles()

    def _applyKlavierHighlightColor(self):
        """Converte klavierHighlightHex in wx.Colour e lo applica al decorator."""
        self.pref.decorator.klavierHighlightColor = self._getKlavierHighlightColour()

    def _getKlavierHighlightColour(self):
        """Restituisce wx.Colour dal valore hex salvato nelle preferenze."""
        hex_str = getattr(self.pref, 'klavierHighlightHex', '#D23C3C')
        try:
            h = hex_str.strip().lstrip('#')
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return wx.Colour(r, g, b)
        except Exception:
            return wx.Colour(210, 60, 60)

    def _getFingerNumColour(self):
        """Restituisce wx.Colour per i numeri delle dita sulla tastiera."""
        hex_str = getattr(self.pref, 'fingerNumColourHex', '#1A1A1A')
        try:
            h = hex_str.strip().lstrip('#')
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return wx.Colour(r, g, b)
        except Exception:
            return wx.Colour(26, 26, 26)

    def _applyFingerNumColor(self):
        """Applica il colore dei numeri dita al decorator."""
        self.pref.decorator.fingerNumColor = self._getFingerNumColour()

    def StripSelection(self):
        """
        Update selection, moving blank characters out of it
        """
        s, e = self.text.GetSelection()
        mod = False
        while e > s and self.text.GetTextRange((ep := self.text.PositionBefore(e)), e).strip() == '':
            e = ep
            mod = True
        while s < e and self.text.GetTextRange(s, (sa := self.text.PositionAfter(s))).strip() == '':
            s = sa
            mod = True
        if mod:
            self.text.SetSelection(s, e)

    def InsertWithCaret(self, st):
        n = self.text.GetSelections()
        if n > 1:
            # --- Multicursore: inserisci su ogni selezione in ordine inverso ---
            # Raccoglie (start, end) di tutte le selezioni ordinate dalla più lontana
            # alla più vicina, così ogni modifica non sposta le posizioni successive.
            sels = sorted(
                [(self.text.GetSelectionNStart(i), self.text.GetSelectionNEnd(i))
                 for i in range(n)],
                reverse=True
            )
            c = st.find('|')
            for s, e in sels:
                self.text.SetSelection(s, e)
                self.StripSelection()
                s2, e2 = self.text.GetSelection()
                if c != -1:
                    sel_text = self.text.GetSelectedText()
                    self.text.ReplaceSelection(st[:c] + sel_text + st[c + 1:])
                    self.text.SetSelection(s2 + c, e2 + c)
                else:
                    self.text.ReplaceSelection(st)
                    self.text.SetSelection(s2 + len(st), s2 + len(st))
        else:
            # --- Cursore singolo: comportamento originale ---
            self.StripSelection()
            s, e = self.text.GetSelection()
            c = st.find('|')
            if c != -1:
                sel_text = self.text.GetSelectedText()
                self.text.ReplaceSelection(st[:c] + sel_text + st[c + 1:])
                self.text.SetSelection(s + c, e + c)
            else:
                self.text.ReplaceSelection(st)
                self.text.SetSelection(s + len(st), s + len(st))

    def OnTitle(self, evt):
        self.InsertWithCaret("{title:|}")

    def OnSubtitle(self, evt):
        self.InsertWithCaret("{subtitle:|}")

    def OnChord(self, evt):
        # Se il dialogo è già aperto (modalità pinnata), riportalo in primo piano
        if getattr(self, '_chord_dlg', None) is not None:
            try:
                self._chord_dlg.Raise()
                self._chord_dlg.SetFocus()
                return
            except Exception:
                self._chord_dlg = None

        PIN_OFF = u"📌"
        PIN_ON  = u"📍"

        # Dialogo non modale: il cursore dell'editor rimane raggiungibile con le frecce
        dlg = wx.Dialog(
            self.frame,
            title=_(u"Insert chord"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP,
        )
        self._chord_dlg = dlg

        vbox = wx.BoxSizer(wx.VERTICAL)

        # Campo testo
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(dlg, label=_(u"Chord:")),
                0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        txt = wx.TextCtrl(dlg, size=(140, -1), style=wx.TE_PROCESS_ENTER)
        row.Add(txt, 1, wx.EXPAND)
        vbox.Add(row, 0, wx.EXPAND | wx.ALL, 10)

        # Bottoni: [📌] [OK] [Annulla]
        btn_pin    = wx.Button(dlg, wx.ID_ANY,
                               PIN_ON if self._chord_dialog_pinned else PIN_OFF,
                               size=(32, -1))
        btn_pin.SetToolTip(_(u"Keep this dialog open after inserting"))
        btn_ok     = wx.Button(dlg, wx.ID_OK,     _(u"OK"))
        btn_cancel = wx.Button(dlg, wx.ID_CANCEL, _(u"Cancel"))
        btn_ok.SetDefault()

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(btn_pin,    0, wx.RIGHT, 4)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(btn_ok,     0, wx.RIGHT, 4)
        btn_sizer.Add(btn_cancel, 0)
        vbox.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        dlg.SetSizer(vbox)
        vbox.Fit(dlg)

        def _insert():
            chord = txt.GetValue().strip()
            if chord:
                self.InsertWithCaret("[%s]" % chord)
            else:
                self.InsertWithCaret("[|]")
            # Dopo inserimento: focus torna all'editor per usare le frecce
            self.text.SetFocus()

        def on_pin(e):
            self._chord_dialog_pinned = not self._chord_dialog_pinned
            btn_pin.SetLabel(PIN_ON if self._chord_dialog_pinned else PIN_OFF)

        def on_ok(e):
            _insert()
            if self._chord_dialog_pinned:
                txt.SetValue("")
                # Focus all'editor: le frecce spostano il cursore nel testo
                self.text.SetFocus()
            else:
                dlg.Destroy()

        def on_cancel(e):
            dlg.Destroy()

        def on_close(e):
            self._chord_dlg = None
            e.Skip()

        # Enter nel campo testo = OK
        txt.Bind(wx.EVT_TEXT_ENTER, on_ok)
        btn_pin.Bind(wx.EVT_BUTTON, on_pin)
        btn_ok.Bind(wx.EVT_BUTTON, on_ok)
        btn_cancel.Bind(wx.EVT_BUTTON, on_cancel)
        dlg.Bind(wx.EVT_CLOSE, on_close)

        # Dialogo non modale: Show() invece di ShowModal()
        dlg.Show()

    def OnVerse(self, evt):
        label = wx.GetTextFromUser(
            _("Insert a label for verse, or press Cancel if you want to omit label."),
            _("Verse label"),
            "",
            self.frame,
        )
        self.InsertWithCaret("{Verse:%s}|" % label)

    def OnChorus(self, evt):
        default = self.pref.decoratorFormat.GetChorusLabel()
        label = wx.GetTextFromUser(
            _("Insert a label for chorus, or press Cancel if you want to omit label."),
            _("Chorus label"),
            default,
            self.frame,
        )
        if label == default:
            self.InsertWithCaret("{soc}\n|\n{eoc}\n")
        else:
            self.InsertWithCaret("{soc:%s}\n|\n{eoc}\n" % label)

    def OnComment(self, evt):
        """Chiede il tipo di commento e il testo, poi inserisce la direttiva scelta."""
        d = wx.Dialog(self.frame, title=_(u"Comment"))
        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(wx.StaticText(d, -1, _(u"Comment type:")), 0, wx.ALL, 8)
        rb_comment = wx.RadioButton(d, -1, u"{comment:}", style=wx.RB_GROUP)
        rb_box     = wx.RadioButton(d, -1, u"{comment_box:}")
        rb_hash    = wx.RadioButton(d, -1, u"# commento")
        rb_comment.SetValue(True)
        for rb in (rb_comment, rb_box, rb_hash):
            vbox.Add(rb, 0, wx.LEFT | wx.BOTTOM, 8)

        vbox.Add(wx.StaticText(d, -1, _(u"Comment text:")), 0, wx.LEFT, 8)
        txt = wx.TextCtrl(d, -1, u"")
        vbox.Add(txt, 0, wx.EXPAND | wx.ALL, 8)

        btn_sizer = d.CreateButtonSizer(wx.OK | wx.CANCEL)
        vbox.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 8)
        d.SetSizer(vbox)
        vbox.Fit(d)

        if d.ShowModal() == wx.ID_OK:
            val = txt.GetValue()
            if rb_box.GetValue():
                directive = u"comment_box"
                self.InsertWithCaret(u"{%s:%s|}" % (directive, val) if not val else u"{%s:%s}" % (directive, val))
            elif rb_hash.GetValue():
                self.InsertWithCaret(u"# %s" % val)
            else:
                directive = u"comment"
                self.InsertWithCaret(u"{%s:%s|}" % (directive, val) if not val else u"{%s:%s}" % (directive, val))
        d.Destroy()

    def OnInsertPageBreak(self, evt):
        """Inserisce un'interruzione di pagina esplicita per la stampa."""
        self.InsertWithCaret("{new_page}\n")

    def OnInsertColumnBreak(self, evt):
        """Inserisce un'interruzione di colonna esplicita per il layout a due colonne."""
        self.InsertWithCaret("{column_break}\n")

    def OnLabelVerses(self, evt):
        self.pref.labelVerses = not self.pref.labelVerses
        self.CheckLabelVerses()

    def _OnPreviewClick(self, line_number):
        """Callback dal doppio-click sull'anteprima.

        Porta il cursore alla riga sorgente trovata tramite hit-test,
        seleziona l'intera riga per renderla visibile e sposta il focus
        sull'editor.

        line_number e' 0-based, corrisponde alla riga ChordPro piu' vicina
        al punto cliccato (risolto con hit-test preciso sui SongBox).
        """
        try:
            pos_start = self.text.PositionFromLine(line_number)
            pos_end   = self.text.GetLineEndPosition(line_number)
            # Seleziona la riga trovata cosi' e' immediatamente visibile
            self.text.SetSelection(pos_start, pos_end)
            self.text.EnsureCaretVisible()
            self.text.SetFocus()
        except Exception:
            pass

    def OnTogglePageBreakLines(self, evt):

        self._showPageBreakLines = evt.IsChecked()
        self.previewCanvas.SetShowPageBreakLines(self._showPageBreakLines)
        self.previewCanvas.Refresh(self._get_display_text())

    def OnToggleColumnBreakLines(self, evt):
        self._showColumnBreakLines = evt.IsChecked()
        self.previewCanvas.SetShowColumnBreakLines(self._showColumnBreakLines)
        self.previewCanvas.Refresh(self._get_display_text())

    def OnToggleDurationBeats(self, evt):
        self._showDurationBeats = evt.IsChecked()
        self.previewCanvas.SetShowDurationBeats(self._showDurationBeats)
        self.previewCanvas.SetDurationBeatsPrefs(
            getattr(self.pref, 'durationBeatsColourHex', '#6464C8'),
            getattr(self.pref, 'durationBeatsSizePct', 60),
            getattr(self.pref, 'durationBeatsBold', False),
            getattr(self.pref, 'durationBeatsAlign', 'right'),
            getattr(self.pref, 'durationBeatsMode', 'number'),
        )
        self.previewCanvas.Refresh(self._get_display_text())

    def _UpdateBreakLinesMenuState(self):
        """Abilita o disabilita le voci di menu delle linee di interruzione
        in base alla visibilità del pannello anteprima."""
        preview_visible = self._mgr.GetPane('preview').IsShown()
        self.menuBar.Enable(self._showPageBreakLinesMenuId, preview_visible)
        self.menuBar.Enable(self._showColumnBreakLinesMenuId, preview_visible)
        self.menuBar.Enable(self._showDurationBeatsMenuId, preview_visible)

    def _ApplyPreviewMinSize(self):
        """Reimposta BestSize e MinSize sul pane 'preview' e sul main_panel.
        Deve essere chiamata dopo LoadPerspective, dopo ogni toggle di visibilità,
        e dopo che l'utente cambia la preferenza nelle opzioni.
        LoadPerspective sovrascrive queste proprietà con i valori salvati,
        che possono essere arbitrariamente piccoli.
        """
        enabled = getattr(self.pref, 'previewMinSize', True)
        if enabled:
            min_sz = wx.Size(370, 520)
        else:
            min_sz = wx.Size(-1, -1)
        # Aggiorna il pane AUI
        pane = self._mgr.GetPane('preview')
        pane.BestSize(370, 520).MinSize(min_sz)
        # Aggiorna anche il wx.Window sottostante (doppio vincolo)
        self.previewCanvas.main_panel.SetMinSize(min_sz)

    def OnTogglePaneView(self, evt):
        super().OnTogglePaneView(evt)
        # Dopo il toggle, se il pannello preview è ora visibile,
        # reimpostiamo MinSize perché LoadPerspective potrebbe averlo azzerato
        pane = self._mgr.GetPane('preview')
        if pane.IsShown():
            self._ApplyPreviewMinSize()
            self._mgr.Update()
        self._UpdateBreakLinesMenuState()

    def OnPaneClose(self, evt):
        super().OnPaneClose(evt)
        # EVT_AUI_PANE_CLOSE scatta prima che IsShown() venga aggiornato:
        # se il pane che si chiude è 'preview', disabilita subito le voci.
        if evt.GetPane().name == 'preview':
            self.menuBar.Enable(self._showPageBreakLinesMenuId, False)
            self.menuBar.Enable(self._showColumnBreakLinesMenuId, False)
            self.menuBar.Enable(self._showDurationBeatsMenuId, False)
        else:
            self._UpdateBreakLinesMenuState()

    def OnChorusLabel(self, evt):
        c = self.pref.decoratorFormat.GetChorusLabel()
        msg = _("Please enter a label for chorus")
        d = wx.TextEntryDialog(self.frame, msg, _("Songpress++"), c)
        if d.ShowModal() == wx.ID_OK:
            c = d.GetValue()
            self.pref.SetChorusLabel(c)
            self.previewCanvas.Refresh(self._get_display_text())

    def OnNoChords(self, evt):
        self.pref.format.showChords = 0
        self.SetFont(True)

    def OnOneVerseForEachChordPattern(self, evt):
        self.pref.format.showChords = 1
        self.SetFont(True)

    def OnWholeSong(self, evt):
        self.pref.format.showChords = 2
        self.SetFont(True)

    def OnChordsAbove(self, evt):
        self.pref.SetChordsPosition('above')
        self.CheckChordsPosition()
        self.previewCanvas.Refresh(self._get_display_text())

    def OnChordsBelow(self, evt):
        self.pref.SetChordsPosition('below')
        self.CheckChordsPosition()
        self.previewCanvas.Refresh(self._get_display_text())

    def CheckChordsPosition(self):
        above = (self.pref.chordsPosition == 'above')
        self.menuBar.Check(self.chordsAboveMenuId, above)
        self.menuBar.Check(self.chordsBelowMenuId, not above)
        self.previewCanvas.SetChordsBelow(not above)

    def OnTextChanged(self, evt):
        self.AutoAdjust(evt.lastPos, evt.currentPos)

    def AutoAdjust(self, lastPos, currentPos):
        if self.text.GetSelections() > 1:
            return  # non interferire con il multicursore attivo
        self.text.AutoChangeMode(True)
        t = self.text.GetTextRange(lastPos, currentPos)
        if self.pref.autoAdjustSpuriousLines:
            if testSpuriousLines(t):
                msg = _("It looks like there are spurious blank lines in the song.\n")
                msg += _("Do you want to try to remove them automatically?")
                title = _("Remove spurious blank lines")
                d = wx.MessageDialog(self.frame, msg, title, wx.YES_NO | wx.ICON_QUESTION)
                if d.ShowModal() == wx.ID_YES:
                    self.text.SetSelection(lastPos, currentPos)
                    t = removeSpuriousLines(t)
                    self.text.ReplaceSelection(t)
                    currentPos = self.text.GetCurrentPos()
        if self.pref.autoAdjustTab2Chordpro:
            n = testTabFormat(t, self.pref.notations)
            if n is not None:
                msg = _("It looks like your song is in tab format (i.e., chords are above the text).\n")
                msg += _("Do you want to convert it to ChordPro automatically?")
                title = _("Convert to ChordPro")
                d = wx.MessageDialog(self.frame, msg, title, wx.YES_NO | wx.ICON_QUESTION)
                if d.ShowModal() == wx.ID_YES:
                    self.text.SetSelection(lastPos, currentPos)
                    t = tab2ChordPro(t, n)
                    self.text.ReplaceSelection(t)
        if self.pref.autoAdjustEasyKey:
            notation = autodetectNotation(t, self.pref.notations)
            count, c, dc, e, de = findEasiestKey(t, self.pref.GetEasyChords(), notation)
            if count > 10 and dc != de:
                msg = _("The key of your song, %s, is not the easiest to play (difficulty: %.1f/5.0).\n") % (c, 5 * dc)
                msg += _("Do you want to transpose the key %s, which is the easiest one (difficulty: %.1f/5.0)?") % (e, 5 * de)
                title = _("Simplify chords")
                d = wx.MessageDialog(self.frame, msg, title, wx.YES_NO | wx.ICON_QUESTION)
                if d.ShowModal() == wx.ID_YES:
                    self.text.SetSelection(lastPos, currentPos)
                    t = transposeChordPro(translateChord(c, notation), translateChord(e, notation), t, notation)
                    self.text.ReplaceSelection(t)
        self.text.AutoChangeMode(False)

    def SetFont(self, updateFontChooser=True):
        try:
            if updateFontChooser:
                self.fontChooser.SetValue(self.pref.format.face)
                self.showChordsChooser.SetValue(self.pref.format.showChords)
                ids = [self.noChordsMenuId, self.oneVerseForEachChordPatternMenuId, self.wholeSongMenuId]
                self.menuBar.Check(ids[self.pref.format.showChords], True)

            self.previewCanvas.SetTempoDisplay(getattr(self.pref, 'tempoDisplay', 0))
            self.previewCanvas.SetTimeDisplay(getattr(self.pref, 'timeDisplay', True))
            self.previewCanvas.SetKeyDisplay(getattr(self.pref, 'keyDisplay', True))
            self.previewCanvas.SetTempoIconSize(getattr(self.pref, 'tempoIconSize', 24))
            self.previewCanvas.SetGridDisplayMode(getattr(self.pref, 'gridDisplayMode', 'pipe'))
            self.previewCanvas.SetGridDefaultLabel(getattr(self.pref, 'gridDefaultLabel', None))
            self.previewCanvas.SetGridSizeDir(getattr(self.pref, 'gridSizeDir', 'both'))
            self.previewCanvas.SetShowPageIndicator(getattr(self.pref, 'showPageIndicator', True))
            self.previewCanvas.SetGreyBackground(getattr(self.pref, 'greyBackground', True))
            _pw, _ph = self._GetPaperSizeMm()
            self.previewCanvas.SetPageSizeMm(_pw, _ph)
            self.previewCanvas.SetPageMarginsMm(self._margin_top, self._margin_bottom)
            self.previewCanvas.Refresh(self._get_display_text())
        except wx._core.PyDeadObjectError:
            # When frame is closed, this method may still be executed, generating an exception
            # because UI elements have been destroyed. Simply ignore it.
            pass

    def CheckLabelVerses(self):
        self.formatToolBar.ToggleTool(self.labelVersesToolId, self.pref.labelVerses)
        self.formatToolBar.Refresh()
        self.menuBar.Check(self.labelVersesMenuId, self.pref.labelVerses)
        if self.pref.labelVerses:
            self.pref.decorator.drawLabels = True
            self.pref.decorator.showKlavier = True
            self.pref.decorator.showGuitarDiagrams = True
            self.previewCanvas.SetDecorator(self.pref.decorator)
        else:
            sd = SongDecorator()
            sd.drawLabels = False
            sd.showKlavier = True
            sd.showGuitarDiagrams = True
            sd.klavierHighlightColor = self._getKlavierHighlightColour()
            sd.fingerNumColor = self._getFingerNumColour()
            self.previewCanvas.SetDecorator(sd)
        self.previewCanvas.SetLineWidths(self.pref.titleLineWidth, self.pref.verseBoxWidth)
        self.previewCanvas.SetShowPageBreakLines(getattr(self, '_showPageBreakLines', True))
        self.previewCanvas.SetShowColumnBreakLines(getattr(self, '_showColumnBreakLines', True))
        self.previewCanvas.SetShowDurationBeats(getattr(self, '_showDurationBeats', True))
        self.previewCanvas.SetDurationBeatsPrefs(
            getattr(self.pref, 'durationBeatsColourHex', '#6464C8'),
            getattr(self.pref, 'durationBeatsSizePct', 60),
            getattr(self.pref, 'durationBeatsBold', False),
            getattr(self.pref, 'durationBeatsAlign', 'right'),
            getattr(self.pref, 'durationBeatsMode', 'number'),
        )
        self.previewCanvas.Refresh(self._get_display_text())