###############################################################
# Name:             PreferencesDialog.py
# Purpose:     Allow user to set preferences
# Author:         Luca Allulli (webmaster@roma21.it)
# Modified by:  Denisov21
# Created:     2009-10-02
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
#               Modifications copyright Denisov21
# License:     GNU GPL v2
##############################################################

import wx

from . import i18n
from .PreferencesDialog import PreferencesDialog
from .MyDecoSlider import MyDecoSlider
from .Transpose import *
from .Globals import glb


_ = wx.GetTranslation


class MyPreferencesDialog(PreferencesDialog):
    def __init__(self, parent, preferences, easyChords, on_apply=None, previewCanvas=None, on_theme_change=None):
        self.pref = preferences
        self.frame = self
        PreferencesDialog.__init__(self, parent)

        self._pinned = False
        self._on_apply = on_apply  # callback chiamato ad ogni OK con pin attivo
        self._restart_requested = False  # True se l'utente ha scelto «Riavvia ora»
        self._on_theme_change = on_theme_change  # callback chiamato quando la lista temi cambia (salva/elimina)
        self._previewCanvas = previewCanvas  # riferimento opzionale per applicare subito le opzioni anteprima
        self.easyChords = easyChords
        self.clearRecentFiles = False

        # ── Scheda "Toolbar Inserisci" — costruita programmaticamente ──
        self._BuildInsertToolBarTab()
        # ────────────────────────────────────────────────────────────────

        self.fontCB.Bind(wx.EVT_TEXT_ENTER, self.OnFontSelected, self.fontCB)
        self.fontCB.Bind(wx.EVT_COMBOBOX, self.OnFontSelected, self.fontCB)

        previewSong = _("#Comment\n{t:My Bonnie}\n\nMy [D]Bonnie lies [G]over the [D]ocean\noh [G]bring back my [A]Bonnie to [D]me!\n\n{soc}\n[D]Bring back, [E-]bring back,\n[A]bring back my Bonnie to [D]me!\n{eoc}\n\n{start_of_grid}\n| [A] | [D] | [Mi] |\n{end_of_grid}")
        self.editor.SetText(previewSong)
        self.editor.SetFont(self.pref.editorFace, self.pref.editorSize)
        self.editor.SetReadOnly(True)
        self.autoRemoveBlankLines.SetValue(self.pref.autoAdjustSpuriousLines)
        self.autoTab2Chordpro.SetValue(self.pref.autoAdjustTab2Chordpro)
        self.autoAdjustEasyKey.SetValue(self.pref.autoAdjustEasyKey)
        if self.pref.locale is None:
            lang = i18n.getLang()
        else:
            lang = self.pref.locale
        import os as _os
        def _make_flag_bmp(lang_code):
            try:
                _path = glb.AddPath('img/flags/%s.png' % lang_code)
                if not _os.path.isfile(_path):
                    return wx.NullBitmap
                _img = wx.Image(_path, wx.BITMAP_TYPE_PNG)
                if not _img.IsOk():
                    return wx.NullBitmap
                _img = _img.Scale(20, 14, wx.IMAGE_QUALITY_HIGH)
                return wx.Bitmap(_img)
            except Exception:
                return wx.NullBitmap
        for l in glb.languages:
            _bmp = _make_flag_bmp(l)
            i = self.langCh.Append(glb.languages[l], _bmp)
            self.langCh.SetClientData(i, l)
            if lang == l:
                self.langCh.SetSelection(i)
        exts = ["crd", "pro", "chopro", "chordpro", "cho", "sng"]
        i = 0
        for e in exts:
            self.extension.Append(e)
            if e == self.pref.defaultExtension:
                self.extension.SetSelection(i)
            i += 1

        # Default notation
        for n in self.pref.notations:
            i = self.notationCh.Append(n.desc)
            self.notationCh.SetClientData(i, n.id)
        self.notationCh.SetSelection(0)

        # Easy chords
        simplifyGrid = wx.FlexGridSizer(len(easyChords), 2, 0, 0)
        simplifyGrid.AddGrowableCol(1, 1)
        self.simplifyPanel.SetSizer(simplifyGrid)
        self.simplifyPanel.Layout()

        self.decoSliders = {}
        for k in easyChordsOrder:
            simplifyGrid.Add(wx.StaticText(self.simplifyPanel, wx.ID_ANY, getEasyChordsDescription(easyChords[k]), wx.DefaultPosition, wx.DefaultSize, 0), 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)
            ds = MyDecoSlider(self.simplifyPanel)
            self.decoSliders[k] = ds
            ds.slider.SetValue(self.pref.GetEasyChordsGroup(k))
            simplifyGrid.Add(ds, 1, wx.EXPAND, 5)

        simplifyGrid.FitInside(self.simplifyPanel)

        # Format tab - inizializza con i valori correnti delle preferenze
        self.titleLineWidthSpin.SetValue(self.pref.titleLineWidth)
        self.verseBoxWidthSpin.SetValue(self.pref.verseBoxWidth)

        # Context menu visibility — valori già caricati da Preferences.Load()
        self.cmUndo.SetValue(self.pref.cmUndo)
        self.cmRedo.SetValue(self.pref.cmRedo)
        self.cmCut.SetValue(self.pref.cmCut)
        self.cmCopy.SetValue(self.pref.cmCopy)
        self.cmPaste.SetValue(self.pref.cmPaste)
        self.cmDelete.SetValue(self.pref.cmDelete)
        self.cmConfirmDelete.SetValue(getattr(self.pref, 'cmConfirmDelete', False))
        self.cmPasteChords.SetValue(self.pref.cmPasteChords)
        self.cmPropagateVerseChords.SetValue(getattr(self.pref, 'cmPropagateVerseChords', True))
        self.cmPropagateChorusChords.SetValue(getattr(self.pref, 'cmPropagateChorusChords', True))
        self.cmCopyTextOnly.SetValue(self.pref.cmCopyTextOnly)
        self.cmSelectAll.SetValue(self.pref.cmSelectAll)
        self.cmShowIcons.SetValue(getattr(self.pref, 'cmShowIcons', True))

        # Klavier highlight colour
        default_hex = getattr(self.pref, 'klavierHighlightHex', '#D23C3C')
        self.klavierHexCtrl.SetValue(default_hex)
        self.klavierColourSwatch.SetBackgroundColour(self._hex_to_colour(default_hex))

        # DecoSlider bar colour
        deco_hex = getattr(self.pref, 'decoSliderBarColourHex', '#2980B9')
        self.decoBarHexCtrl.SetValue(deco_hex)
        self.decoBarColourSwatch.SetBackgroundColour(self._hex_to_colour(deco_hex))
        self.decoBarColourSwatch.Refresh()
        # Finger number colour
        fn_hex = getattr(self.pref, 'fingerNumColourHex', '#1A1A1A')
        if hasattr(self, 'fingerNumHexCtrl'):
            self.fingerNumHexCtrl.SetValue(fn_hex)
            self.fingerNumColourSwatch.SetBackgroundColour(self._hex_to_colour(fn_hex))

        # Editor background colour
        bg_hex = getattr(self.pref, 'editorBgHex', '#FFFFFF')
        if hasattr(self, 'editorBgHexCtrl'):
            self.editorBgHexCtrl.SetValue(bg_hex)
            self.editorBgSwatch.SetBackgroundColour(self._hex_to_colour(bg_hex))
            self._applyEditorBg(bg_hex)

        # Selection colour
        sel_hex = getattr(self.pref, 'selColourHex', '#C0C0C0')
        if hasattr(self, 'selColourHexCtrl'):
            self.selColourHexCtrl.SetValue(sel_hex)
            self.selColourSwatch.SetBackgroundColour(self._hex_to_colour(sel_hex))
            self._applySelColour(sel_hex)

        # Caret colour
        caret_hex = getattr(self.pref, 'caretColourHex', '#000000')
        if hasattr(self, 'caretColourHexCtrl'):
            self.caretColourHexCtrl.SetValue(caret_hex)
            self.caretColourSwatch.SetBackgroundColour(self._hex_to_colour(caret_hex))
            self._applyCaretColour(caret_hex)

        # Caption Editor colour
        cap_ed_hex = getattr(self.pref, 'captionEditorActiveHex', '#4682C8')
        self.capEditorHexCtrl.SetValue(cap_ed_hex)
        self.capEditorSwatch.SetBackgroundColour(self._hex_to_colour(cap_ed_hex))
        self.capEditorSwatch.Refresh()

        # Caption Preview colour
        cap_pv_hex = getattr(self.pref, 'captionPreviewActiveHex', '#329B82')
        self.capPreviewHexCtrl.SetValue(cap_pv_hex)
        self.capPreviewSwatch.SetBackgroundColour(self._hex_to_colour(cap_pv_hex))
        self.capPreviewSwatch.Refresh()

        # Syntax colours
        sc = getattr(self.pref, 'syntaxColours', {})
        defaults = getattr(self.pref.__class__, 'SYNTAX_COLOUR_DEFAULTS',
                           {'normal': '#000000', 'chorus': '#000000', 'chord': '#FF0000',
                            'command': '#0000FF', 'attr': '#008000', 'comment': '#808080', 'tabgrid': '#8B5A00'})
        for key in self.syntaxHexCtrls:
            hex_val = sc.get(key, defaults.get(key, '#000000'))
            self.syntaxHexCtrls[key].SetValue(hex_val)
            self.syntaxSwatches[key].SetBackgroundColour(self._hex_to_colour(hex_val))
            self.syntaxSwatches[key].Refresh()
            self._applySyntaxColour(key, hex_val)

        # Themes
        self._refreshThemeList()

        # Show print preview
        self.showPrintPreviewCB.SetValue(getattr(self.pref, 'showPrintPreview', True))

        # Multi-cursor
        self.multiCursorCB.SetValue(getattr(self.pref, 'multiCursor', False))

        # Enable Save only when modified
        self.enableSaveOnModifiedCB.SetValue(getattr(self.pref, 'enableSaveOnModified', True))

        # Salvataggio geometria finestra
        self.saveWindowGeometryCB.SetValue(getattr(self.pref, 'saveWindowGeometry', True))

        # Sostituzione spazi con '_' nei nomi file salvati
        self.replaceSpacesInFilenamesCB.SetValue(getattr(self.pref, 'replaceSpacesInFilenames', False))

        # Suggerisci {title:} come nome file in "Salva con nome"
        self.suggestTitleAsFilenameCB.SetValue(getattr(self.pref, 'suggestTitleAsFilename', False))

        # Dimensione icone toolbar
        _tbSz = getattr(self.pref, 'toolbarIconSize', 'small')
        if _tbSz == 'large':
            self.tbIconSizeLarge.SetValue(True)
        elif _tbSz == 'medium':
            self.tbIconSizeMedium.SetValue(True)
        else:
            self.tbIconSizeSmall.SetValue(True)

        # Debug messages
        self.showDebugMsgCB.SetValue(getattr(self.pref, 'showDebugMsg', False))

        # Intellisense direttive
        self.intellisenseCB.SetValue(getattr(self.pref, 'intellisense', True))

        # Single instance
        self.singleInstanceCB.SetValue(getattr(self.pref, 'singleInstance', True))
        self.showRestartMenuItemCB.SetValue(getattr(self.pref, 'showRestartMenuItem', True))

        # Opzioni anteprima (tab Songpress)
        self.showPageIndicatorCB.SetValue(getattr(self.pref, 'showPageIndicator', True))
        self.greyBackgroundCB.SetValue(getattr(self.pref, 'greyBackground', True))
        self.debounceRefreshCB.SetValue(getattr(self.pref, 'debounceRefresh', True))
        self.dblClickFocusCB.SetValue(getattr(self.pref, 'dblClickFocus', True))
        self.previewMinSizeCB.SetValue(getattr(self.pref, 'previewMinSize', True))
        self.liveDriverPollCB.SetValue(getattr(self.pref, 'liveDriverPoll', True))
        self.printPreviewAlwaysOnTopCB.SetValue(getattr(self.pref, 'printPreviewAlwaysOnTop', False))

        # Nessun accordo: blocchi da nascondere
        self.hideIntroChordCB.SetValue(getattr(self.pref, 'hideIntroChord', False))
        self.hideBridgeCB.SetValue(getattr(self.pref, 'hideBridge', False))
        self.hideGridCB.SetValue(getattr(self.pref, 'hideGrid', False))
        self.hideTempoCB.SetValue(getattr(self.pref, 'hideTempo', False))
        self.hideTimeCB.SetValue(getattr(self.pref, 'hideTime', False))

        # Viewer guida rapida
        viewer = getattr(self.pref, 'guideViewer', 'auto')
        _viewer_map = {'auto': 0, 'markdown': 1, 'mistune': 2, 'builtin': 3}
        self.guideViewerCh.SetSelection(_viewer_map.get(viewer, 0))

        # Dimensione icone tempo
        sz = getattr(self.pref, 'tempoIconSize', 24)
        self.tempoIconSize16.SetValue(sz == 16)
        self.tempoIconSize24.SetValue(sz == 24)
        self.tempoIconSize32.SetValue(sz == 32)

        # Modalità visualizzazione griglia accordi
        _gm = getattr(self.pref, 'gridDisplayMode', 'pipe')
        self.gridModePipe.SetValue(_gm == 'pipe')
        self.gridModePlain.SetValue(_gm == 'plain')
        self.gridModeTable.SetValue(_gm == 'table')
        self.gridDefaultLabelCtrl.SetValue(getattr(self.pref, 'gridDefaultLabel', _("Grid")))
        self.gridSpaceAsPipeCB.SetValue(getattr(self.pref, 'gridSpaceAsPipe', True))

        # Simbolo musicale
        self.symbolScaleCB.SetValue(getattr(self.pref, 'symbolScaleEnabled', False))
        self.symbolSizeSpin.SetValue(getattr(self.pref, 'symbolFontSize', 24))
        self.symbolSizeSpin.Enable(getattr(self.pref, 'symbolScaleEnabled', False))
        self.symbolInsertVerseCB.SetValue(getattr(self.pref, 'symbolInsertVerse', False))
        _sd = getattr(self.pref, 'gridSizeDir', 'both')
        self.gridSizeDirBoth.SetValue(_sd == 'both')
        self.gridSizeDirH.SetValue(_sd == 'horizontal')
        self.gridSizeDirV.SetValue(_sd == 'vertical')

        # Beat count ({beats_time})
        dur_hex = getattr(self.pref, 'durationBeatsColourHex', '#6464C8')
        self.durationBeatsHexCtrl.SetValue(dur_hex)
        self.durationBeatsColourSwatch.SetBackgroundColour(self._hex_to_colour(dur_hex))
        self.durationBeatsSizeSpin.SetValue(getattr(self.pref, 'durationBeatsSizePct', 60))
        self.durationBeatsBoldCB.SetValue(getattr(self.pref, 'durationBeatsBold', False))
        _da = getattr(self.pref, 'durationBeatsAlign', 'right')
        self.durationBeatsAlignLeft.SetValue(_da == 'left')
        self.durationBeatsAlignCenter.SetValue(_da == 'center')
        self.durationBeatsAlignRight.SetValue(_da == 'right')
        _dm = getattr(self.pref, 'durationBeatsMode', 'number')
        self.durationModeNumber.SetValue(_dm == 'number')
        self.durationModeDots.SetValue(_dm == 'dots')
        self.durationModeBoth.SetValue(_dm == 'both')

        # File associations (solo Windows)
        if self._fileAssocAvailable:
            import sys as _sys
            exe = _sys.executable if not getattr(_sys, 'frozen', False) else _sys.executable
            for ext, cb in self._fileAssocCBs.items():
                cb.SetValue(self._IsExtAssociated(ext, exe))

    # ------------------------------------------------------------------
    # Scheda visibilità toolbar (Standard, Formato, Inserisci)
    # ------------------------------------------------------------------

    def _BuildToolbarsTab(self):
        """Aggiunge la scheda 'Toolbar' al notebook principale del dialogo.
        Al suo interno un notebook secondario con tre sotto-schede:
        Standard, Formato, Inserisci.
        """
        from .SongpressToolbars import SongpressToolbarsMixin

        outer = wx.Panel(self.notebook)
        outer_vbox = wx.BoxSizer(wx.VERTICAL)

        inner_nb = wx.Notebook(outer)
        self._tb_checkboxes = {}   # pref_key → wx.CheckBox (tutte le barre)

        # Helper: costruisce una sotto-scheda con checkbox + Seleziona/Deseleziona
        def _make_sub_tab(items, sep_after_set, title):
            panel = wx.Panel(inner_nb)
            vbox  = wx.BoxSizer(wx.VERTICAL)

            scroll = wx.ScrolledWindow(panel, style=wx.VSCROLL)
            scroll.SetScrollRate(0, 12)
            grid = wx.BoxSizer(wx.VERTICAL)

            prev = None
            for xrc_name, label, pref_key in items:
                if prev is not None and prev in sep_after_set:
                    grid.Add(wx.StaticLine(scroll), 0,
                             wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 6)
                cb = wx.CheckBox(scroll, -1, label)
                cb.SetValue(getattr(self.pref, pref_key, True))
                self._tb_checkboxes[pref_key] = cb
                grid.Add(cb, 0, wx.LEFT | wx.TOP, 6)
                prev = xrc_name

            scroll.SetSizer(grid)
            grid.FitInside(scroll)
            scroll.SetVirtualSize(grid.GetMinSize())

            btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
            btn_all  = wx.Button(panel, -1, _("Select all"))
            btn_none = wx.Button(panel, -1, _("Deselect all"))
            btn_sizer.Add(btn_all,  0, wx.RIGHT, 6)
            btn_sizer.Add(btn_none, 0)

            # Closures sui checkbox della singola scheda (snapshot della lista)
            _keys = [pk for _, _, pk in items]
            def on_all(e, keys=_keys):
                for k in keys:
                    self._tb_checkboxes[k].SetValue(True)
            def on_none(e, keys=_keys):
                for k in keys:
                    self._tb_checkboxes[k].SetValue(False)

            btn_all.Bind(wx.EVT_BUTTON, on_all)
            btn_none.Bind(wx.EVT_BUTTON, on_none)

            vbox.Add(scroll,    1, wx.EXPAND | wx.ALL, 6)
            vbox.Add(btn_sizer, 0, wx.ALL, 6)
            panel.SetSizer(vbox)
            inner_nb.AddPage(panel, title)

        # ── Scheda Standard ──────────────────────────────────────────
        _make_sub_tab(
            SongpressToolbarsMixin.MAIN_TOOLBAR_ITEMS,
            SongpressToolbarsMixin._MAIN_TOOLBAR_SEPARATORS_AFTER,
            _("Standard"),
        )

        # ── Scheda Formato ───────────────────────────────────────────
        _make_sub_tab(
            SongpressToolbarsMixin.FORMAT_TOOLBAR_ITEMS,
            SongpressToolbarsMixin._FORMAT_TOOLBAR_SEPARATORS_AFTER,
            _("Format"),
        )

        # ── Scheda Inserisci ─────────────────────────────────────────
        _make_sub_tab(
            SongpressToolbarsMixin.INSERT_TOOLBAR_ITEMS,
            SongpressToolbarsMixin._INSERT_TOOLBAR_SEPARATORS_AFTER,
            _("Insert"),
        )

        # ── Scheda Visualizza ────────────────────────────────────────
        _make_sub_tab(
            SongpressToolbarsMixin.VIEW_TOOLBAR_ITEMS,
            set(),   # nessun separatore nella barra View
            _("View"),
        )

        outer_vbox.Add(inner_nb, 1, wx.EXPAND | wx.ALL, 4)
        outer.SetSizer(outer_vbox)
        self.notebook.AddPage(outer, _("Toolbars"))

    # Alias per compatibilità con il codice esistente che chiama _BuildInsertToolBarTab
    _BuildInsertToolBarTab = _BuildToolbarsTab

    def _hex_to_colour(self, hex_str):
        try:
            h = hex_str.strip().lstrip('#')
            if len(h) == 6:
                return wx.Colour(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except Exception:
            pass
        return wx.Colour(255, 255, 255)

    def _applyEditorBg(self, hex_str):
        """Applica il colore di sfondo all'editor di anteprima nelle preferenze."""
        self.editor.SetBgColour(hex_str)

    def _applySelColour(self, hex_str):
        """Applica il colore di selezione all'editor di anteprima nelle preferenze."""
        self.editor.SetSelColour(hex_str)

    def _applyCaretColour(self, hex_str):
        """Applica il colore del cursore (caret) all'editor di anteprima nelle preferenze."""
        self.editor.SetCaretForeground(self._hex_to_colour(hex_str))

    def _colour_to_hex(self, colour):
        if not colour.IsOk():
            return '#FFFFFF'
        return '#{:02X}{:02X}{:02X}'.format(colour.Red(), colour.Green(), colour.Blue())

    def _apply_custom_colours(self, data, pref_attr):
        """Carica i colori personalizzati salvati in pref nel ColourData."""
        colours = getattr(self.pref, pref_attr, [])
        for i, hex_str in enumerate(colours[:16]):
            try:
                h = hex_str.strip().lstrip('#')
                if len(h) == 6:
                    c = wx.Colour(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
                    data.SetCustomColour(i, c)
            except Exception:
                pass

    def _read_custom_colours(self, data, pref_attr):
        """Legge i 16 colori personalizzati dal ColourData e li salva in pref."""
        setattr(self.pref, pref_attr, [
            self._colour_to_hex(data.GetCustomColour(i)) for i in range(16)
        ])

    def OnKlavierHexChanged(self, evt):
        c = self._hex_to_colour(self.klavierHexCtrl.GetValue())
        self.klavierColourSwatch.SetBackgroundColour(c)
        self.klavierColourSwatch.Refresh()
        evt.Skip()

    def OnKlavierPickColour(self, evt):
        current = self._hex_to_colour(self.klavierHexCtrl.GetValue())
        data = wx.ColourData()
        data.SetColour(current)
        data.SetChooseFull(True)
        self._apply_custom_colours(data, 'customColoursKlavier')
        dlg = wx.ColourDialog(self, data)
        if dlg.ShowModal() == wx.ID_OK:
            result_data = dlg.GetColourData()
            chosen = result_data.GetColour()
            self._read_custom_colours(result_data, 'customColoursKlavier')
            self.klavierHexCtrl.SetValue(self._colour_to_hex(chosen))
            self.klavierColourSwatch.SetBackgroundColour(chosen)
            self.klavierColourSwatch.Refresh()
        dlg.Destroy()

    def OnFingerNumHexChanged(self, evt):
        c = self._hex_to_colour(self.fingerNumHexCtrl.GetValue())
        self.fingerNumColourSwatch.SetBackgroundColour(c)
        self.fingerNumColourSwatch.Refresh()
        evt.Skip()

    def OnFingerNumPickColour(self, evt):
        current = self._hex_to_colour(self.fingerNumHexCtrl.GetValue())
        data = wx.ColourData()
        data.SetColour(current)
        data.SetChooseFull(True)
        self._apply_custom_colours(data, 'customColoursFingerNum')
        dlg = wx.ColourDialog(self, data)
        if dlg.ShowModal() == wx.ID_OK:
            result_data = dlg.GetColourData()
            chosen = result_data.GetColour()
            self._read_custom_colours(result_data, 'customColoursFingerNum')
            self.fingerNumHexCtrl.SetValue(self._colour_to_hex(chosen))
            self.fingerNumColourSwatch.SetBackgroundColour(chosen)
            self.fingerNumColourSwatch.Refresh()
        dlg.Destroy()

    def OnDurationBeatsHexChanged(self, evt):
        c = self._hex_to_colour(self.durationBeatsHexCtrl.GetValue())
        self.durationBeatsColourSwatch.SetBackgroundColour(c)
        self.durationBeatsColourSwatch.Refresh()

    def OnDurationBeatsPickColour(self, evt):
        current = self._hex_to_colour(self.durationBeatsHexCtrl.GetValue())
        data = wx.ColourData()
        data.SetColour(current)
        data.SetChooseFull(True)
        self._apply_custom_colours(data, 'customColoursDurationBeats')
        dlg = wx.ColourDialog(self, data)
        if dlg.ShowModal() == wx.ID_OK:
            result_data = dlg.GetColourData()
            chosen = result_data.GetColour()
            self._read_custom_colours(result_data, 'customColoursDurationBeats')
            self.durationBeatsHexCtrl.SetValue(self._colour_to_hex(chosen))
            self.durationBeatsColourSwatch.SetBackgroundColour(chosen)
            self.durationBeatsColourSwatch.Refresh()
        dlg.Destroy()

    def OnEditorBgHexChanged(self, evt):
        hex_val = self.editorBgHexCtrl.GetValue()
        c = self._hex_to_colour(hex_val)
        self.editorBgSwatch.SetBackgroundColour(c)
        self.editorBgSwatch.Refresh()
        self._applyEditorBg(hex_val)
        evt.Skip()

    def OnSelColourHexChanged(self, evt):
        hex_val = self.selColourHexCtrl.GetValue()
        c = self._hex_to_colour(hex_val)
        self.selColourSwatch.SetBackgroundColour(c)
        self.selColourSwatch.Refresh()
        self._applySelColour(hex_val)
        evt.Skip()

    def OnSelColourPickColour(self, evt):
        current = self._hex_to_colour(self.selColourHexCtrl.GetValue())
        data = wx.ColourData()
        data.SetColour(current)
        data.SetChooseFull(True)
        self._apply_custom_colours(data, 'customColoursSelColour')
        dlg = wx.ColourDialog(self, data)
        if dlg.ShowModal() == wx.ID_OK:
            result_data = dlg.GetColourData()
            chosen = result_data.GetColour()
            hex_val = self._colour_to_hex(chosen)
            self._read_custom_colours(result_data, 'customColoursSelColour')
            self.selColourHexCtrl.SetValue(hex_val)
            self.selColourSwatch.SetBackgroundColour(chosen)
            self.selColourSwatch.Refresh()
            self._applySelColour(hex_val)
        dlg.Destroy()

    def OnCaretColourHexChanged(self, evt):
        hex_val = self.caretColourHexCtrl.GetValue()
        c = self._hex_to_colour(hex_val)
        self.caretColourSwatch.SetBackgroundColour(c)
        self.caretColourSwatch.Refresh()
        self._applyCaretColour(hex_val)
        evt.Skip()

    def OnCaretColourPickColour(self, evt):
        current = self._hex_to_colour(self.caretColourHexCtrl.GetValue())
        data = wx.ColourData()
        data.SetColour(current)
        data.SetChooseFull(True)
        self._apply_custom_colours(data, 'customColoursCaretColour')
        dlg = wx.ColourDialog(self, data)
        if dlg.ShowModal() == wx.ID_OK:
            result_data = dlg.GetColourData()
            chosen = result_data.GetColour()
            hex_val = self._colour_to_hex(chosen)
            self._read_custom_colours(result_data, 'customColoursCaretColour')
            self.caretColourHexCtrl.SetValue(hex_val)
            self.caretColourSwatch.SetBackgroundColour(chosen)
            self.caretColourSwatch.Refresh()
            self._applyCaretColour(hex_val)
        dlg.Destroy()

    def OnCapEditorHexChanged(self, evt):
        hex_val = self.capEditorHexCtrl.GetValue()
        c = self._hex_to_colour(hex_val)
        self.capEditorSwatch.SetBackgroundColour(c)
        self.capEditorSwatch.Refresh()
        evt.Skip()

    def OnCapEditorPickColour(self, evt):
        current = self._hex_to_colour(self.capEditorHexCtrl.GetValue())
        data = wx.ColourData()
        data.SetColour(current)
        data.SetChooseFull(True)
        self._apply_custom_colours(data, 'customColoursCapEditor')
        dlg = wx.ColourDialog(self, data)
        if dlg.ShowModal() == wx.ID_OK:
            result_data = dlg.GetColourData()
            chosen = result_data.GetColour()
            self._read_custom_colours(result_data, 'customColoursCapEditor')
            hex_val = self._colour_to_hex(chosen)
            self.capEditorHexCtrl.SetValue(hex_val)
            self.capEditorSwatch.SetBackgroundColour(chosen)
            self.capEditorSwatch.Refresh()
        dlg.Destroy()

    def OnCapPreviewHexChanged(self, evt):
        hex_val = self.capPreviewHexCtrl.GetValue()
        c = self._hex_to_colour(hex_val)
        self.capPreviewSwatch.SetBackgroundColour(c)
        self.capPreviewSwatch.Refresh()
        evt.Skip()

    def OnCapPreviewPickColour(self, evt):
        current = self._hex_to_colour(self.capPreviewHexCtrl.GetValue())
        data = wx.ColourData()
        data.SetColour(current)
        data.SetChooseFull(True)
        self._apply_custom_colours(data, 'customColoursCapPreview')
        dlg = wx.ColourDialog(self, data)
        if dlg.ShowModal() == wx.ID_OK:
            result_data = dlg.GetColourData()
            chosen = result_data.GetColour()
            self._read_custom_colours(result_data, 'customColoursCapPreview')
            hex_val = self._colour_to_hex(chosen)
            self.capPreviewHexCtrl.SetValue(hex_val)
            self.capPreviewSwatch.SetBackgroundColour(chosen)
            self.capPreviewSwatch.Refresh()
        dlg.Destroy()

    # ------------------------------------------------------------------
    # Syntax colours (normal, chorus, chord, command, attr, comment, tabgrid)
    # ------------------------------------------------------------------

    # Map from style key to STC style id (must match Editor.py constants)
    _SYNTAX_KEY_TO_STC = {
        'normal':   11,  # STC_STYLE_NORMAL
        'chorus':   15,  # STC_STYLE_CHORUS
        'chord':    12,  # STC_STYLE_CHORD
        'command':  13,  # STC_STYLE_COMMAND
        'attr':     14,  # STC_STYLE_ATTR
        'comment':  16,  # STC_STYLE_COMMENT
        'tabgrid':  17,  # STC_STYLE_TAB_GRID
    }

    def _syntaxKeyFromWidget(self, widget):
        """Restituisce la chiave sintassi associata al TextCtrl o Button dato."""
        for key in self.syntaxHexCtrls:
            if self.syntaxHexCtrls[key] is widget:
                return key
            if self.syntaxPickBtns[key] is widget:
                return key
        return None

    def _applySyntaxColour(self, key, hex_val):
        """Applica il colore sintattico all'editor di anteprima."""
        style_id = self._SYNTAX_KEY_TO_STC.get(key)
        if style_id is not None:
            self.editor.SetSyntaxColour(style_id, hex_val)

    def OnSyntaxHexChanged(self, evt):
        key = self._syntaxKeyFromWidget(evt.GetEventObject())
        if key is None:
            evt.Skip()
            return
        hex_val = self.syntaxHexCtrls[key].GetValue()
        c = self._hex_to_colour(hex_val)
        self.syntaxSwatches[key].SetBackgroundColour(c)
        self.syntaxSwatches[key].Refresh()
        self._applySyntaxColour(key, hex_val)
        evt.Skip()

    def OnSyntaxPickColour(self, evt):
        key = self._syntaxKeyFromWidget(evt.GetEventObject())
        if key is None:
            evt.Skip()
            return
        current = self._hex_to_colour(self.syntaxHexCtrls[key].GetValue())
        data = wx.ColourData()
        data.SetColour(current)
        data.SetChooseFull(True)
        pref_attr = 'customColoursSyntax_' + key
        self._apply_custom_colours(data, pref_attr)
        dlg = wx.ColourDialog(self, data)
        if dlg.ShowModal() == wx.ID_OK:
            result_data = dlg.GetColourData()
            chosen = result_data.GetColour()
            hex_val = self._colour_to_hex(chosen)
            self._read_custom_colours(result_data, pref_attr)
            self.syntaxHexCtrls[key].SetValue(hex_val)
            self.syntaxSwatches[key].SetBackgroundColour(chosen)
            self.syntaxSwatches[key].Refresh()
            self._applySyntaxColour(key, hex_val)
        dlg.Destroy()

    # ------------------------------------------------------------------
    # Themes  (templates/themes/<name>.ini)
    # ------------------------------------------------------------------

    # Chiavi scritte/lette nel file tema — stessa struttura del registro
    _THEME_COLOUR_KEYS = [
        ('bg',         'editorBgHex',            '#FFFFFF'),
        ('sel',        'selColourHex',            '#C0C0C0'),
        ('caret',      'caretColourHex',          '#000000'),
        ('capeditor',  'captionEditorActiveHex',  '#4682C8'),
        ('cappreview', 'captionPreviewActiveHex', '#329B82'),
    ]
    _THEME_SYNTAX_KEYS = ['normal', 'chorus', 'chord', 'command', 'attr', 'comment', 'tabgrid']

    def _get_themes_dir(self):
        """Restituisce la cartella templates/themes/ scrivibile.

        Delega a _get_templates_dir(), così temi e template vivono sempre nella
        stessa radice (quella del pacchetto dove è scrivibile — Windows, venv,
        portable — altrimenti la cartella dati utente) ed è esattamente quella
        che il pulsante "Apri cartella template" mostra all'utente.
        """
        import os as _os
        try:
            return _os.path.join(self._get_templates_dir(), 'themes')
        except OSError as e:
            wx.MessageBox(
                _(u"Cannot create themes folder:\n%s\n\n%s")
                % (_os.path.join('templates', 'themes'), e),
                _(u"Songpress++"), wx.OK | wx.ICON_ERROR, self
            )
            # Ultimo ripiego: la home, così il dialogo non resta senza cartella.
            themes_dir = _os.path.join(
                _os.path.expanduser('~'), '.Songpress++', 'templates', 'themes')
            _os.makedirs(themes_dir, exist_ok=True)
            return themes_dir

    def _theme_roots(self):
        """Tutte le cartelle themes/ da cui leggere, in ordine di precedenza
        crescente: prima la radice globale del pacchetto, poi quella locale
        (dati utente), che sovrascrive la globale a parità di nome.

        _get_themes_dir() restituisce solo la radice *scrivibile*: usarla da
        sola nasconde i temi distribuiti con il pacchetto, perché la data dir
        utente viene creata vuota da Globals.InitDataPath().
        """
        import os as _os
        roots = []
        pkg_path = getattr(glb, 'path', None) or \
            _os.path.dirname(_os.path.abspath(__file__))
        roots.append(_os.path.join(pkg_path, 'templates', 'themes'))
        try:
            roots.append(self._get_themes_dir())
        except OSError:
            pass
        # dedup preservando l'ordine (le due radici coincidono in modalità
        # portable / venv, dove data_path punta al pacchetto stesso)
        seen = []
        for r in roots:
            r = _os.path.normpath(r)
            if r not in seen:
                seen.append(r)
        return seen

    def _theme_files(self):
        """Nomi dei temi disponibili, unione di radice globale e locale."""
        import os as _os
        names = set()
        for d in self._theme_roots():
            try:
                for f in _os.listdir(d):
                    if f.lower().endswith('.ini'):
                        names.add(f[:-4])
            except OSError:
                continue  # cartella inesistente o illeggibile: la salto
        return sorted(names, key=lambda s: s.lower())

    def _find_theme_path(self, name):
        """Percorso del file .ini del tema, dando precedenza alla radice locale."""
        import os as _os
        for d in reversed(self._theme_roots()):  # locale prima, poi globale
            path = _os.path.join(d, name + '.ini')
            if _os.path.isfile(path):
                return path
        return None

    def _refreshThemeList(self, select_name=None):
        self.themeCh.Clear()
        names = self._theme_files()
        for n in names:
            self.themeCh.Append(n)
        if select_name and select_name in names:
            self.themeCh.SetSelection(names.index(select_name))
        elif names:
            self.themeCh.SetSelection(0)
        # abilita/disabilita tasti
        has = len(names) > 0
        self.themeLoadBtn.Enable(has)
        self.themeDeleteBtn.Enable(has)

    def _theme_to_dict(self):
        """Raccoglie tutti i colori dal dialogo corrente in un dict."""
        d = {}
        d['bg']         = self.editorBgHexCtrl.GetValue().strip()
        d['sel']        = self.selColourHexCtrl.GetValue().strip()
        d['caret']      = self.caretColourHexCtrl.GetValue().strip()
        d['capeditor']  = self.capEditorHexCtrl.GetValue().strip()
        d['cappreview'] = self.capPreviewHexCtrl.GetValue().strip()
        for key in self._THEME_SYNTAX_KEYS:
            d['syntax_' + key] = self.syntaxHexCtrls[key].GetValue().strip()
        return d

    def _apply_theme_dict(self, d):
        """Applica un dict colori a tutti i controlli del dialogo."""
        def _set(ctrl, swatch, val, apply_fn=None):
            ctrl.SetValue(val)
            swatch.SetBackgroundColour(self._hex_to_colour(val))
            swatch.Refresh()
            if apply_fn:
                apply_fn(val)

        _set(self.editorBgHexCtrl,    self.editorBgSwatch,    d.get('bg',         '#FFFFFF'), self._applyEditorBg)
        _set(self.selColourHexCtrl,   self.selColourSwatch,   d.get('sel',        '#C0C0C0'), self._applySelColour)
        _set(self.caretColourHexCtrl, self.caretColourSwatch, d.get('caret',      '#000000'), self._applyCaretColour)
        _set(self.capEditorHexCtrl,   self.capEditorSwatch,   d.get('capeditor',  '#4682C8'))
        _set(self.capPreviewHexCtrl,  self.capPreviewSwatch,  d.get('cappreview', '#329B82'))
        for key in self._THEME_SYNTAX_KEYS:
            val = d.get('syntax_' + key, '#000000')
            self.syntaxHexCtrls[key].SetValue(val)
            self.syntaxSwatches[key].SetBackgroundColour(self._hex_to_colour(val))
            self.syntaxSwatches[key].Refresh()
            self._applySyntaxColour(key, val)

    def _save_theme_file(self, name, d):
        import os as _os
        import configparser
        import datetime
        path = _os.path.join(self._get_themes_dir(), name + '.ini')
        cfg = configparser.ConfigParser()
        cfg['colours'] = d
        header = (
            "# Songpress++ colour theme\n"
            "# Name    : {name}\n"
            "# Saved   : {date}\n"
            "# Version : 1.0\n"
            "#\n"
            "# This file can be edited manually.\n"
            "# Place it in templates/themes/ to make it available in Songpress++.\n"
            "#\n"
        ).format(
            name=name,
            date=datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
        )
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(header)
                cfg.write(f)
        except Exception as e:
            wx.MessageBox(
                _(u"Cannot save theme file:\n%s") % path + "\n\n" + str(e),
                _(u"Songpress++"), wx.OK | wx.ICON_ERROR, self
            )
            return False
        return True

    def _load_theme_file(self, name):
        import os as _os
        import configparser
        path = self._find_theme_path(name)
        if path is None:
            return {}
        cfg = configparser.ConfigParser()
        try:
            cfg.read(path, encoding='utf-8')
        except (OSError, configparser.Error):
            return {}
        return dict(cfg['colours']) if 'colours' in cfg else {}

    def OnThemeLoad(self, evt):
        idx = self.themeCh.GetSelection()
        if idx == wx.NOT_FOUND:
            return
        name = self.themeCh.GetString(idx)
        d = self._load_theme_file(name)
        if d:
            self._apply_theme_dict(d)

    def OnThemeSave(self, evt):
        idx = self.themeCh.GetSelection()
        current = self.themeCh.GetString(idx) if idx != wx.NOT_FOUND else u''
        dlg = wx.TextEntryDialog(self, _(u"Theme name:"), _(u"Save theme"), current)
        result = dlg.ShowModal()
        name = dlg.GetValue().strip()
        dlg.Destroy()
        if result != wx.ID_OK or not name:
            return
        import re as _re
        import os as _os
        name = _re.sub(r'[\\/:*?"<>|]', '_', name)
        themes_dir = self._get_themes_dir()
        path = _os.path.join(themes_dir, name + '.ini')
        if getattr(self.pref, 'showDebugMsg', False):
            wx.MessageBox(
                _(u"DEBUG: saving theme to:\n%s\n\n(folder exists: %s)") % (
                    path, str(_os.path.isdir(themes_dir))
                ),
                u"Songpress++ DEBUG", wx.OK | wx.ICON_INFORMATION, self
            )
        d = self._theme_to_dict()
        if self._save_theme_file(name, d):
            self._refreshThemeList(select_name=name)
            if self._on_theme_change is not None:
                self._on_theme_change()

    def OnThemeDelete(self, evt):
        idx = self.themeCh.GetSelection()
        if idx == wx.NOT_FOUND:
            return
        name = self.themeCh.GetString(idx)
        if wx.MessageBox(
            _(u"Delete theme «%s»?") % name,
            _(u"Songpress++"),
            wx.YES_NO | wx.ICON_QUESTION, self
        ) == wx.YES:
            import os as _os
            path = self._find_theme_path(name)
            if path is None:
                return
            try:
                _os.remove(path)
            except OSError as e:
                # Tema distribuito con il pacchetto (root su Debian di sistema,
                # Program Files su Windows): non è cancellabile dall'utente.
                wx.MessageBox(
                    _(u"Cannot delete theme «%s»:\n%s\n\n%s") % (name, path, e),
                    _(u"Songpress++"), wx.OK | wx.ICON_ERROR, self
                )
                return
            self._refreshThemeList()
            if self._on_theme_change is not None:
                self._on_theme_change()

    def OnEditorBgPickColour(self, evt):
        current = self._hex_to_colour(self.editorBgHexCtrl.GetValue())
        data = wx.ColourData()
        data.SetColour(current)
        data.SetChooseFull(True)
        self._apply_custom_colours(data, 'customColoursEditorBg')
        dlg = wx.ColourDialog(self, data)
        if dlg.ShowModal() == wx.ID_OK:
            result_data = dlg.GetColourData()
            chosen = result_data.GetColour()
            hex_val = self._colour_to_hex(chosen)
            self._read_custom_colours(result_data, 'customColoursEditorBg')
            self.editorBgHexCtrl.SetValue(hex_val)
            self.editorBgSwatch.SetBackgroundColour(chosen)
            self.editorBgSwatch.Refresh()
            self._applyEditorBg(hex_val)
        dlg.Destroy()

    def OnClearRecentFiles(self, evt):
        self.clearRecentFiles = True
        self.clearRecentFilesBtn.Disable()
        evt.Skip()

    # Sottocartelle di templates/ che devono sempre esistere ed essere visibili
    # quando si preme "Apri cartella template" (parità con Windows).
    #   fonts/      → font personalizzati usati nell'anteprima/esportazione
    #   slides/     → template PowerPoint (.pptx)
    #   songs/      → template di brani (.crd)
    #   themes/     → temi colore dell'editor (.ini)
    #
    # NON contiene local_dir/: quella è lo *scheletro* che vive dentro il
    # pacchetto; ricrearne una copia vuota nella cartella dell'utente sarebbe un
    # doppione inutile. Il suo contenuto (local_dir/templates/*) viene fuso
    # direttamente nell'albero dell'utente da TemplateSeed.seed_user_templates().
    # Allineata a Globals.USER_TEMPLATE_SUBDIRS.
    _TEMPLATE_SUBDIRS = ('fonts', 'slides', 'songs', 'themes')

    @classmethod
    def _is_writable_templates_dir(cls, path):
        """Crea le sottocartelle di templates/ e verifica che siano scrivibili.

        Non basta che makedirs() riesca: su un'installazione di sistema
        (.deb) le cartelle esistono già ma appartengono a root, e
        makedirs(..., exist_ok=True) ritorna senza errore pur essendo la
        cartella in sola lettura. Serve quindi un test esplicito.
        """
        import os as _os
        try:
            # La radice deve essere creabile/scrivibile per prima.
            _os.makedirs(path, exist_ok=True)
            if not _os.access(path, _os.W_OK | _os.X_OK):
                return False
            for sub in cls._TEMPLATE_SUBDIRS:
                d = _os.path.join(path, sub)
                _os.makedirs(d, exist_ok=True)
                if not _os.access(d, _os.W_OK | _os.X_OK):
                    return False
            return True
        except OSError:
            return False

    def _get_user_data_dir(self):
        """Cartella dati utente dell'applicazione.

        Preferisce glb.data_path (valorizzata da Globals.InitDataPath()); se
        non è ancora disponibile ripiega su wx.StandardPaths, che restituisce
        %APPDATA%\\<AppName> su Windows e ~/.<appname> su Linux/macOS — cioè
        esattamente la stessa cartella, purché wx.App.SetAppName() sia stato
        chiamato all'avvio.
        """
        data_path = getattr(glb, 'data_path', None)
        if data_path:
            return data_path
        return wx.StandardPaths.Get().GetUserDataDir()

    def _get_templates_dir(self):
        """Restituisce la cartella templates/ da aprire con "Apri cartella
        template", creando tutte le sottocartelle di _TEMPLATE_SUBDIRS.

        Criterio: l'utente si aspetta di trovare *i template di esempio*
        distribuiti con l'applicazione, che stanno in glb.path/templates
        (dentro il pacchetto). La cartella dati utente viene invece creata
        vuota da Globals.InitDataPath(): aprirla mostrerebbe solo cartelle
        deserte. Quindi:

          1. glb.path/templates  → radice del pacchetto. È la scelta giusta
             ovunque l'installazione appartenga all'utente: Windows
             (%LOCALAPPDATA%\\Songpress++\\tools\\...\\site-packages\\
             songpressplusplus\\templates, anche su unità diverse da C:),
             venv, modalità portable, albero sorgenti. Contiene gli esempi ed
             è scrivibile, quindi l'utente può anche aggiungerne di propri.
          2. glb.data_path/templates → usata quando la 1 non è scrivibile:
             è il caso dell'installazione .deb di sistema, dove il pacchetto
             sta in /usr/lib/python3/dist-packages ed è di root.
          3. wx.StandardPaths → rete di sicurezza se glb.data_path manca.

        La lettura non cambia: _theme_roots() e
        SongpressFrame._PopulateTemplateMenu() scandiscono comunque entrambe
        le radici, con quella locale che sovrascrive quella globale.
        """
        import os as _os

        candidates = []

        # 1. radice del pacchetto: contiene i template di esempio.
        pkg_path = getattr(glb, 'path', None) or \
            _os.path.dirname(_os.path.abspath(__file__))
        candidates.append(_os.path.join(pkg_path, 'templates'))

        # 2./3. cartella dati utente: usata solo se il pacchetto è read-only.
        candidates.append(_os.path.join(self._get_user_data_dir(), 'templates'))

        for path in candidates:
            if self._is_writable_templates_dir(path):
                return path

        raise OSError(
            _(u"Cannot create a writable templates folder. Tried:\n%s")
            % '\n'.join(candidates))

    def _get_templates_dir_to_open(self):
        """Cartella mostrata nel file manager da "Apri cartella template".

        Deve essere **scrivibile** — altrimenti il pulsante serve solo a
        guardare — e deve **contenere i template distribuiti** con
        l'applicazione, altrimenti l'utente apre una cartella vuota.

        Le due cose stanno insieme grazie al *seeding*: al primo avvio
        TemplateSeed.seed_user_templates() copia tutto il contenuto di
        <pacchetto>/templates/ dentro la cartella dati utente
        (~/.Songpress++/templates/ su Linux). Il pulsante apre quindi
        _get_templates_dir(), cioè la radice scrivibile, che a quel punto
        contiene sia gli esempi sia i file dell'utente.

        La copia non può essere fatta dal postinst del .deb: dpkg gira come
        root, non conosce la home dell'utente e i file risulterebbero di
        proprietà di root, cioè di nuovo non scrivibili.

        Il seeding è ripetuto qui (oltre che in Globals.InitDataPath) perché è
        idempotente e a costo nullo: garantisce la cartella popolata anche se
        l'utente aggiorna solo questo file.
        """
        path = self._get_templates_dir()
        self._seed_templates_dir(path)
        return path

    @staticmethod
    def _seed_templates_dir(user_templates):
        """Copia i template del pacchetto in `user_templates` (mai due volte,
        mai sovrascrivendo i file dell'utente). Silenzioso in caso di errore.

        Delega a Globals.SeedUserTemplates() quando la cartella da popolare è
        proprio la cartella dati (il caso normale con il .deb); altrimenti —
        radice diversa, es. installazione portable/venv — chiama direttamente
        TemplateSeed.
        """
        import os as _os
        try:
            from .TemplateSeed import seed_user_templates
        except ImportError:
            return 0

        data_path = getattr(glb, 'data_path', None)
        if data_path and _os.path.normpath(user_templates) == \
                _os.path.normpath(_os.path.join(data_path, 'templates')):
            seeder = getattr(glb, 'SeedUserTemplates', None)
            if callable(seeder):
                return seeder()

        pkg_path = getattr(glb, 'path', None) or \
            _os.path.dirname(_os.path.abspath(__file__))
        return seed_user_templates(
            _os.path.join(pkg_path, 'templates'), user_templates)

    def OnOpenTemplatesFolder(self, evt):
        import os as _os
        import sys as _sys
        import subprocess

        path = None
        try:
            path = self._get_templates_dir_to_open()

            if _sys.platform == 'win32':
                # Gestisce correttamente spazi e caratteri non ASCII nel percorso
                # e non lascia processi appesi (a differenza di Popen(['explorer', ...])).
                _os.startfile(path)                    # pylint: disable=no-member
            elif _sys.platform == 'darwin':
                subprocess.Popen(['open', path])
            else:
                # Linux/BSD: xdg-open è lo standard freedesktop; su KDE inoltra
                # a kde-open/Dolphin, su GNOME a Nautilus. Fornito da xdg-utils.
                subprocess.Popen(
                    ['xdg-open', path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
        except FileNotFoundError:
            # xdg-open (o 'open') non installato: ripiego sul gestore
            # predefinito di wxWidgets.
            if not (path and wx.LaunchDefaultApplication(path)):
                wx.MessageBox(
                    _(u"Cannot open the templates folder:\n%s\n\n"
                      u"On Debian/Ubuntu install the 'xdg-utils' package:\n"
                      u"    sudo apt install xdg-utils") % (path or ''),
                    _("Songpress++"), wx.OK | wx.ICON_ERROR, self)
        except Exception as e:
            wx.MessageBox(str(e), _("Songpress++"), wx.OK | wx.ICON_ERROR, self)
        evt.Skip()

    def OnFontSelected(self, evt):
        f, s = self.GetFont()
        self.editor.SetFont(f, s)
        evt.Skip()

    def GetFont(self):
        face = self.fontCB.GetValue()
        try:
            s = int(self.sizeCB.GetValue())
        except:
            s = 12
        return (face, s)

    def GetLanguage(self):
        return self.langCh.GetClientData(self.langCh.GetSelection())

    def GetNotation(self):
        return self.notationCh.GetClientData(self.notationCh.GetSelection())

    # ------------------------------------------------------------------
    # File associations (Windows e Linux)
    # ------------------------------------------------------------------

    def _GetExePath(self):
        """Restituisce il percorso dell'eseguibile di Songpress++."""
        import sys as _sys
        return _sys.executable

    # ---- Windows ----

    def _GetLaunchCmd(self, exe):
        """Restituisce la stringa comando per aprire un file con Songpress++ (Windows)."""
        import sys as _sys
        import os as _os
        if getattr(_sys, 'frozen', False):
            return '"{}" "%1"'.format(exe)
        pkg_dir  = _os.path.dirname(_os.path.abspath(__file__))
        src_dir  = _os.path.dirname(pkg_dir)
        root_dir = _os.path.dirname(src_dir)
        main_py  = _os.path.join(root_dir, 'main.py')
        if not _os.path.isfile(main_py):
            main_py = _os.path.join(src_dir, 'main.py')
            root_dir = src_dir
        launcher = self._EnsureWinLauncher(root_dir, main_py)
        pythonw = _os.path.join(_os.path.dirname(exe), 'pythonw.exe')
        if not _os.path.isfile(pythonw):
            pythonw = exe
        return '"{}" "{}" "%1"'.format(pythonw, launcher)

    def _EnsureWinLauncher(self, root_dir, main_py):
        """Crea/aggiorna lo script launcher .pyw nella cartella dati dell'app (Windows).

        Usa runpy.run_module invece di exec(open(main_py).read()) perché main.py
        contiene import relativi (from .Globals import glb) che non funzionano
        se il file viene eseguito con exec fuori dal package.
        """
        import os as _os
        launcher_dir = _os.path.join(_os.path.expanduser('~'), 'AppData', 'Local',
                                     'Songpress', 'launcher')
        _os.makedirs(launcher_dir, exist_ok=True)
        launcher_path = _os.path.join(launcher_dir, 'songpress_open.pyw')
        script = (
            'import sys, runpy\n'
            'sys.path.insert(0, {root!r})\n'
            '# sys.argv[1] è il file da aprire, già presente grazie a Windows\n'
            'runpy.run_module("songpress.main", run_name="__main__", alter_sys=True)\n'
        ).format(root=root_dir)
        with open(launcher_path, 'w', encoding='utf-8') as f:
            f.write(script)
        return launcher_path

    def _IsExtAssociated(self, ext, exe):
        """Controlla se l'estensione è associata a Songpress++."""
        import platform as _platform
        if _platform.system() == 'Windows':
            return self._IsExtAssociatedWin(ext)
        elif _platform.system() == 'Linux':
            return self._IsExtAssociatedLinux(ext)
        return False

    # ProgID condiviso — deve corrispondere a quello usato dal NSIS installer
    _WIN_PROG_ID = 'SongpressPlusPlus.ChordPro'
    # ProgID legacy scritti da versioni precedenti (da pulire in fase di associazione)
    _WIN_LEGACY_PROG_IDS = ['Songpress.crd', 'Songpress.pro', 'Songpress.chopro',
                             'Songpress.chordpro', 'Songpress.cho', 'Songpress.tab',
                             'Songpress.ChordPro']

    def _IsExtAssociatedWin(self, ext):
        """Controlla l'associazione in HKCU (Windows).
        Verifica solo che il ProgID punti al nostro — non controlla il percorso exe.
        """
        try:
            import winreg
            prog_id = self._WIN_PROG_ID
            key_path = r'Software\Classes\.{}'.format(ext)
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as k:
                current = winreg.QueryValue(k, '')
            return current == prog_id
        except Exception:
            return False

    def _AssociateExt(self, ext, exe):
        """Associa l'estensione a Songpress++."""
        import platform as _platform
        if _platform.system() == 'Windows':
            self._AssociateExtWin(ext, exe)
        elif _platform.system() == 'Linux':
            self._AssociateExtLinux(ext, exe)

    def _GetWinAppExeName(self):
        """Restituisce il nome exe simbolico usato per Software\\Classes\\Applications\\."""
        import sys as _sys
        import os as _os
        if getattr(_sys, 'frozen', False):
            return _os.path.basename(_sys.executable)
        # In modalità sviluppo usiamo sempre un nome fisso e riconoscibile
        return 'songpress++.exe'

    def _GetWinWrapperCmd(self, exe):
        """In modalità sviluppo crea un wrapper .bat con nome fisso e lo restituisce.
        Win 11 abbina Applications\\<exe> al comando tramite il nome dell'exe nel path.
        """
        import sys as _sys
        import os as _os
        if getattr(_sys, 'frozen', False):
            return '"{}" "%1"'.format(exe)
        # Costruisci il comando reale (pythonw + launcher)
        pkg_dir  = _os.path.dirname(_os.path.abspath(__file__))
        src_dir  = _os.path.dirname(pkg_dir)
        root_dir = _os.path.dirname(src_dir)
        main_py  = _os.path.join(root_dir, 'main.py')
        if not _os.path.isfile(main_py):
            main_py = _os.path.join(src_dir, 'main.py')
            root_dir = src_dir
        launcher = self._EnsureWinLauncher(root_dir, main_py)
        pythonw = _os.path.join(_os.path.dirname(exe), 'pythonw.exe')
        if not _os.path.isfile(pythonw):
            pythonw = exe
        real_cmd = '"{}" "{}" "%1"'.format(pythonw, launcher)
        # Crea un wrapper .bat con nome fisso "songpress++.exe" (come .bat)
        # ma registralo come se fosse l'exe — Win 11 usa il nome nel path del comando
        bat_dir = _os.path.join(_os.path.expanduser('~'), 'AppData', 'Local',
                                'Songpress', 'launcher')
        _os.makedirs(bat_dir, exist_ok=True)
        bat_path = _os.path.join(bat_dir, 'songpress++.bat')
        bat_content = '@echo off\n{}\n'.format(
            real_cmd.replace('%1', '%*')
        )
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        # Il comando registrato nel registro punta al .bat
        return '"{}" "%1"'.format(bat_path)

    def _AssociateExtWin(self, ext, exe):
        """Associa l'estensione a Songpress++ in HKCU (compatibile Win 11)."""
        import winreg
        import os as _os
        prog_id  = self._WIN_PROG_ID
        app_name = self._GetWinAppExeName()          # nome fisso per Applications\
        cmd      = self._GetLaunchCmd(exe)           # comando nel ProgID
        app_cmd  = self._GetWinWrapperCmd(exe)       # comando in Applications\ (con wrapper)
        ico_path = _os.path.normpath(glb.AddPath('img/songpress++.ico'))

        # 0. Pulizia ProgID legacy per questa estensione (da versioni precedenti)
        for legacy_id in self._WIN_LEGACY_PROG_IDS:
            try:
                self._DeleteRegKeyRecursive(winreg.HKEY_CURRENT_USER,
                                            r'Software\Classes\{}'.format(legacy_id))
            except Exception:
                pass
            for owp in [r'Software\Classes\.{}\OpenWithProgids'.format(ext),
                        r'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.{}\OpenWithProgids'.format(ext)]:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, owp,
                                        access=winreg.KEY_SET_VALUE) as k:
                        winreg.DeleteValue(k, legacy_id)
                except Exception:
                    pass

        # 1. ProgID: descrizione, DefaultIcon, shell\open (MUIVerb+Icon), command
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r'Software\Classes\{}'.format(prog_id)) as k:
            winreg.SetValue(k, '', winreg.REG_SZ, 'Songpress++ ChordPro file')
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                  r'Software\Classes\{}\DefaultIcon'.format(prog_id)) as k:
                winreg.SetValue(k, '', winreg.REG_SZ, '{},0'.format(ico_path))
        except Exception:
            pass
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r'Software\Classes\{}\shell\open'.format(prog_id)) as k:
            winreg.SetValueEx(k, 'MUIVerb', 0, winreg.REG_SZ, 'Songpress++')
            winreg.SetValueEx(k, 'Icon', 0, winreg.REG_SZ, ico_path)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r'Software\Classes\{}\shell\open\command'.format(prog_id)) as k:
            winreg.SetValue(k, '', winreg.REG_SZ, cmd)

        # 2. Applications\<app_name>: FriendlyAppName, DefaultIcon, command, SupportedTypes
        #    Questa chiave è ciò che Win 11 usa per mostrare icona+nome in "Apri con"
        app_key = r'Software\Classes\Applications\{}'.format(app_name)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, app_key) as k:
            winreg.SetValueEx(k, 'FriendlyAppName', 0, winreg.REG_SZ, 'Songpress++')
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                  r'{}\DefaultIcon'.format(app_key)) as k:
                winreg.SetValue(k, '', winreg.REG_SZ, '{},0'.format(ico_path))
        except Exception:
            pass
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r'{}\shell\open\command'.format(app_key)) as k:
            winreg.SetValue(k, '', winreg.REG_SZ, app_cmd)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r'{}\SupportedTypes'.format(app_key)) as k:
            for s_ext in ["crd", "cho", "chordpro", "chopro", "pro", "tab", "sng"]:
                winreg.SetValueEx(k, '.{}'.format(s_ext), 0, winreg.REG_SZ, '')

        # 3. OpenWithList: collega l'app_name all'estensione
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r'Software\Classes\.{}\OpenWithList\{}'.format(ext, app_name)) as k:
            pass

        # 4. Default dell'estensione → nostro ProgID
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r'Software\Classes\.{}'.format(ext)) as k:
            winreg.SetValue(k, '', winreg.REG_SZ, prog_id)

        # 5. OpenWithProgids
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r'Software\Classes\.{}\OpenWithProgids'.format(ext)) as k:
            winreg.SetValueEx(k, prog_id, 0, winreg.REG_NONE, b'')

        # 6. Explorer FileExts OpenWithProgids (Win 10/11)
        try:
            uc_path = r'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.{}\UserChoice'.format(ext)
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, uc_path,
                                access=winreg.KEY_READ) as k:
                current_prog = winreg.QueryValueEx(k, 'ProgId')[0]
        except Exception:
            current_prog = None
        if current_prog != prog_id:
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                      r'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.{}\OpenWithProgids'.format(ext)) as k:
                    winreg.SetValueEx(k, prog_id, 0, winreg.REG_NONE, b'')
            except Exception:
                pass

    def _UnassociateExt(self, ext):
        """Rimuove l'associazione Songpress++."""
        import platform as _platform
        if _platform.system() == 'Windows':
            self._UnassociateExtWin(ext)
        elif _platform.system() == 'Linux':
            self._UnassociateExtLinux(ext)

    def _UnassociateExtWin(self, ext):
        """Rimuove completamente l'associazione Songpress++ per l'estensione in HKCU."""
        import winreg
        prog_id  = self._WIN_PROG_ID
        app_name = self._GetWinAppExeName()

        # 1. Rimuovi il valore default dell'estensione (solo se è il nostro ProgID)
        try:
            key_path = r'Software\Classes\.{}'.format(ext)
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path,
                                access=winreg.KEY_READ | winreg.KEY_SET_VALUE) as k:
                current = winreg.QueryValue(k, '')
                if current == prog_id:
                    winreg.DeleteValue(k, '')
        except Exception:
            pass

        # 2. Rimuovi da OpenWithProgids e OpenWithList
        for owp_path in [
            r'Software\Classes\.{}\OpenWithProgids'.format(ext),
            r'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.{}\OpenWithProgids'.format(ext),
        ]:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, owp_path,
                                    access=winreg.KEY_SET_VALUE) as k:
                    winreg.DeleteValue(k, prog_id)
            except Exception:
                pass
        try:
            self._DeleteRegKeyRecursive(
                winreg.HKEY_CURRENT_USER,
                r'Software\Classes\.{}\OpenWithList\{}'.format(ext, app_name)
            )
        except Exception:
            pass

        # 3. Elimina il ProgID e Applications\<app_name> solo se nessuna altra ext lo usa ancora.
        #    Il ProgID è condiviso: non va rimosso finché almeno un'altra estensione è associata.
        other_exts = [e for e in ["crd", "cho", "chordpro", "chopro", "pro", "tab", "sng"] if e != ext]
        if not any(self._IsExtAssociatedWin(e) for e in other_exts):
            try:
                self._DeleteRegKeyRecursive(
                    winreg.HKEY_CURRENT_USER,
                    r'Software\Classes\{}'.format(prog_id)
                )
            except Exception:
                pass
            try:
                self._DeleteRegKeyRecursive(
                    winreg.HKEY_CURRENT_USER,
                    r'Software\Classes\Applications\{}'.format(app_name)
                )
            except Exception:
                pass

    @staticmethod
    def _DeleteRegKeyRecursive(hive, key_path):
        """Elimina ricorsivamente una chiave di registro e tutte le sue sottochiavi."""
        import winreg
        try:
            with winreg.OpenKey(hive, key_path, access=winreg.KEY_READ) as k:
                subkey_count = winreg.QueryInfoKey(k)[0]
                subkeys = [winreg.EnumKey(k, i) for i in range(subkey_count)]
        except FileNotFoundError:
            return  # già assente
        for subkey in subkeys:
            MyPreferencesDialog._DeleteRegKeyRecursive(
                hive, '{}\\{}'.format(key_path, subkey))
        winreg.DeleteKey(hive, key_path)

    # ---- Linux (XDG) ----

    # MIME type usato per tutti i file ChordPro/CRD
    _LINUX_MIME_TYPE = 'text/x-chordpro'
    # Tutte le estensioni condividono lo stesso MIME type
    _LINUX_MIME_EXTS = ["crd", "cho", "chordpro", "chopro", "pro", "tab", "sng"]

    def _GetLinuxLaunchCmd(self, exe):
        """Restituisce il comando Exec per il file .desktop (Linux)."""
        import sys as _sys
        import os as _os
        if getattr(_sys, 'frozen', False):
            return '{} %f'.format(exe)
        pkg_dir  = _os.path.dirname(_os.path.abspath(__file__))
        src_dir  = _os.path.dirname(pkg_dir)
        root_dir = _os.path.dirname(src_dir)
        main_py  = _os.path.join(root_dir, 'main.py')
        if not _os.path.isfile(main_py):
            main_py = _os.path.join(src_dir, 'main.py')
        return '{} {} %f'.format(exe, main_py)

    def _GetLinuxDesktopPath(self):
        import os as _os
        apps_dir = _os.path.join(_os.path.expanduser('~'), '.local', 'share', 'applications')
        _os.makedirs(apps_dir, exist_ok=True)
        return _os.path.join(apps_dir, 'songpress.desktop')

    def _GetLinuxMimeXmlPath(self):
        import os as _os
        mime_dir = _os.path.join(_os.path.expanduser('~'), '.local', 'share', 'mime', 'packages')
        _os.makedirs(mime_dir, exist_ok=True)
        return _os.path.join(mime_dir, 'songpress-mime.xml')

    def _EnsureLinuxDesktop(self, exe):
        """Crea/aggiorna il file .desktop per Songpress++ (~/.local/share/applications/)."""
        import os as _os
        desktop_path = self._GetLinuxDesktopPath()
        exec_cmd = self._GetLinuxLaunchCmd(exe)
        # Percorso icona: preferisce il .png, fallback al .ico
        ico_path = glb.AddPath('img/songpress++.png')
        if not _os.path.isfile(ico_path):
            ico_path = glb.AddPath('img/songpress++.ico')
        mime_list = ';'.join(
            ['{}+{}'.format(self._LINUX_MIME_TYPE, ext) for ext in self._LINUX_MIME_EXTS]
            + [self._LINUX_MIME_TYPE]
        ) + ';'
        content = (
            '[Desktop Entry]\n'
            'Type=Application\n'
            'Name=Songpress++\n'
            'Comment=ChordPro song editor\n'
            'Exec={exec_cmd}\n'
            'Icon={icon}\n'
            'MimeType={mime}\n'
            'Categories=Audio;Music;\n'
            'Terminal=false\n'
        ).format(exec_cmd=exec_cmd, icon=ico_path, mime=mime_list)
        with open(desktop_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return desktop_path

    def _EnsureLinuxMimeXml(self):
        """Crea/aggiorna il file XML del MIME type personalizzato."""
        xml_path = self._GetLinuxMimeXmlPath()
        # Costruisce i glob per ogni estensione
        globs = '\n    '.join(
            '<glob pattern="*.{}"/>'.format(ext) for ext in self._LINUX_MIME_EXTS
        )
        content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">\n'
            '  <mime-type type="{mime}">\n'
            '    <comment>ChordPro song file</comment>\n'
            '    <comment xml:lang="it">File canzone ChordPro</comment>\n'
            '    <icon name="songpress"/>\n'
            '    {globs}\n'
            '  </mime-type>\n'
            '</mime-info>\n'
        ).format(mime=self._LINUX_MIME_TYPE, globs=globs)
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return xml_path

    def _IsExtAssociatedLinux(self, ext):
        """Controlla se l'estensione è associata a Songpress++ via XDG."""
        import subprocess
        try:
            mime = self._LINUX_MIME_TYPE
            result = subprocess.run(
                ['xdg-mime', 'query', 'default', mime],
                capture_output=True, text=True, timeout=5
            )
            return 'songpress' in result.stdout.lower()
        except Exception:
            return False

    def _AssociateExtLinux(self, ext, exe):
        """Associa le estensioni ChordPro a Songpress++ via XDG (Linux).
        Tutte le estensioni condividono lo stesso MIME type, quindi
        questa operazione si esegue una volta sola per tutte.
        """
        import subprocess
        import os as _os
        # 1. Installa il MIME type personalizzato
        xml_path = self._EnsureLinuxMimeXml()
        try:
            subprocess.run(['update-mime-database',
                            _os.path.join(_os.path.expanduser('~'), '.local', 'share', 'mime')],
                           timeout=10)
        except Exception:
            pass
        # 2. Installa il file .desktop
        desktop_path = self._EnsureLinuxDesktop(exe)
        try:
            subprocess.run(['update-desktop-database',
                            _os.path.join(_os.path.expanduser('~'), '.local', 'share', 'applications')],
                           timeout=10)
        except Exception:
            pass
        # 3. Imposta Songpress++ come default per il MIME type
        try:
            subprocess.run(
                ['xdg-mime', 'default', 'songpress.desktop', self._LINUX_MIME_TYPE],
                timeout=10
            )
        except Exception:
            pass

    def _UnassociateExtLinux(self, ext):
        """Rimuove il file .desktop e la registrazione MIME (Linux)."""
        import os as _os
        import subprocess
        # Rimuovi il file .desktop
        desktop_path = self._GetLinuxDesktopPath()
        try:
            if _os.path.isfile(desktop_path):
                _os.remove(desktop_path)
                subprocess.run(['update-desktop-database',
                                _os.path.join(_os.path.expanduser('~'), '.local', 'share', 'applications')],
                               timeout=10)
        except Exception:
            pass
        # Rimuovi il MIME xml
        xml_path = self._GetLinuxMimeXmlPath()
        try:
            if _os.path.isfile(xml_path):
                _os.remove(xml_path)
                subprocess.run(['update-mime-database',
                                _os.path.join(_os.path.expanduser('~'), '.local', 'share', 'mime')],
                               timeout=10)
        except Exception:
            pass

    def OnApplyFileAssoc(self, evt):
        """Applica immediatamente le associazioni file selezionate."""
        import platform as _platform
        exe = self._GetExePath()
        errors = []
        for ext, cb in self._fileAssocCBs.items():
            try:
                if cb.GetValue():
                    self._AssociateExt(ext, exe)
                else:
                    self._UnassociateExt(ext)
            except Exception as e:
                errors.append('.{}: {}'.format(ext, e))
        # Notifica il sistema del cambiamento
        if _platform.system() == 'Windows':
            try:
                import ctypes
                ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
            except Exception:
                pass
        if errors:
            wx.MessageBox(
                _("Some associations could not be changed:\n") + "\n".join(errors),
                _("Songpress++"), wx.OK | wx.ICON_WARNING, self
            )
        else:
            wx.MessageBox(
                _("File associations updated successfully."),
                _("Songpress++"), wx.OK | wx.ICON_INFORMATION, self
            )
        evt.Skip()

    def OnAssociateAll(self, evt):
        """Seleziona tutti i checkbox delle estensioni file."""
        if self._fileAssocAvailable:
            for cb in self._fileAssocCBs.values():
                cb.SetValue(True)
        evt.Skip()

    def OnUnassociateAll(self, evt):
        """Deseleziona tutti i checkbox delle estensioni file."""
        if self._fileAssocAvailable:
            for cb in self._fileAssocCBs.values():
                cb.SetValue(False)
        evt.Skip()

    def OnShowDebugMsgChanged(self, evt):
        """Aggiorna pref.showDebugMsg immediatamente, senza attendere OK."""
        self.pref.showDebugMsg = self.showDebugMsgCB.GetValue()
        evt.Skip()

    def OnCmConfirmDeleteChanged(self, evt):
        """Aggiorna pref.cmConfirmDelete immediatamente, senza attendere OK."""
        self.pref.cmConfirmDelete = self.cmConfirmDelete.GetValue()

    def OnCmShowIconsChanged(self, evt):
        """Aggiorna pref.cmShowIcons immediatamente, senza attendere OK."""
        self.pref.cmShowIcons = self.cmShowIcons.GetValue()
        evt.Skip()

    def OnOk(self, evt):
        # Assign ALL values to pref BEFORE Save() so everything is persisted
        self.pref.editorFace, self.pref.editorSize = self.GetFont()
        l = self.GetLanguage()
        self.pref.locale = l
        self.pref.SetDefaultNotation(self.GetNotation())
        self.pref.autoAdjustSpuriousLines = self.autoRemoveBlankLines.GetValue()
        self.pref.autoAdjustTab2Chordpro = self.autoTab2Chordpro.GetValue()
        self.pref.autoAdjustEasyKey = self.autoAdjustEasyKey.GetValue()
        for k in self.decoSliders:
            self.pref.SetEasyChordsGroup(k, self.decoSliders[k].slider.GetValue())
        self.pref.defaultExtension = self.extension.GetString(self.extension.GetSelection())
        self.pref.titleLineWidth = self.titleLineWidthSpin.GetValue()
        self.pref.verseBoxWidth = self.verseBoxWidthSpin.GetValue()
        self.pref.klavierHighlightHex = self.klavierHexCtrl.GetValue().strip()
        self.pref.decoSliderBarColourHex = self.decoBarHexCtrl.GetValue().strip()
        if hasattr(self, 'fingerNumHexCtrl'):
            self.pref.fingerNumColourHex = self.fingerNumHexCtrl.GetValue().strip()
        if hasattr(self, 'editorBgHexCtrl'):
            self.pref.editorBgHex = self.editorBgHexCtrl.GetValue().strip()
        if hasattr(self, 'selColourHexCtrl'):
            self.pref.selColourHex = self.selColourHexCtrl.GetValue().strip()
        if hasattr(self, 'caretColourHexCtrl'):
            self.pref.caretColourHex = self.caretColourHexCtrl.GetValue().strip()
        # Caption bar colours
        self.pref.captionEditorActiveHex  = self.capEditorHexCtrl.GetValue().strip()
        self.pref.captionPreviewActiveHex = self.capPreviewHexCtrl.GetValue().strip()
        # Syntax colours
        if not hasattr(self.pref, 'syntaxColours') or self.pref.syntaxColours is None:
            self.pref.syntaxColours = {}
        for key in self.syntaxHexCtrls:
            self.pref.syntaxColours[key] = self.syntaxHexCtrls[key].GetValue().strip()
        # Show print preview
        self.pref.showPrintPreview = self.showPrintPreviewCB.GetValue()
        # Multi-cursor
        self.pref.multiCursor = self.multiCursorCB.GetValue()
        self.pref.enableSaveOnModified = self.enableSaveOnModifiedCB.GetValue()
        # Salvataggio geometria finestra
        self.pref.saveWindowGeometry = self.saveWindowGeometryCB.GetValue()
        # Sostituzione spazi con '_' nei nomi file salvati
        self.pref.replaceSpacesInFilenames = self.replaceSpacesInFilenamesCB.GetValue()
        # Suggerisci {title:} come nome file in "Salva con nome"
        self.pref.suggestTitleAsFilename = self.suggestTitleAsFilenameCB.GetValue()
        # Dimensione icone toolbar
        if self.tbIconSizeLarge.GetValue():
            self.pref.toolbarIconSize = 'large'
        elif self.tbIconSizeMedium.GetValue():
            self.pref.toolbarIconSize = 'medium'
        else:
            self.pref.toolbarIconSize = 'small'
        self.pref.showDebugMsg = self.showDebugMsgCB.GetValue()
        # Intellisense direttive
        self.pref.intellisense = self.intellisenseCB.GetValue()
        # Single instance
        self.pref.singleInstance = self.singleInstanceCB.GetValue()
        self.pref.showRestartMenuItem = self.showRestartMenuItemCB.GetValue()
        # Opzioni anteprima (tab Songpress)
        self.pref.showPageIndicator = self.showPageIndicatorCB.GetValue()
        self.pref.greyBackground    = self.greyBackgroundCB.GetValue()
        self.pref.debounceRefresh   = self.debounceRefreshCB.GetValue()
        self.pref.dblClickFocus     = self.dblClickFocusCB.GetValue()
        self.pref.previewMinSize    = self.previewMinSizeCB.GetValue()
        self.pref.liveDriverPoll    = self.liveDriverPollCB.GetValue()
        self.pref.printPreviewAlwaysOnTop = self.printPreviewAlwaysOnTopCB.GetValue()
        # Viewer guida rapida
        _viewer_keys = ['auto', 'markdown', 'mistune', 'builtin']
        sel = self.guideViewerCh.GetSelection()
        self.pref.guideViewer = _viewer_keys[sel] if 0 <= sel < len(_viewer_keys) else 'auto'
        # Nessun accordo: blocchi da nascondere
        self.pref.hideIntroChord = self.hideIntroChordCB.GetValue()
        self.pref.hideBridge     = self.hideBridgeCB.GetValue()
        self.pref.hideGrid        = self.hideGridCB.GetValue()
        self.pref.hideTempo       = self.hideTempoCB.GetValue()
        self.pref.hideTime        = self.hideTimeCB.GetValue()
        # Applica subito sul previewCanvas se disponibile
        if self._previewCanvas is not None:
            self._previewCanvas.SetShowPageIndicator(self.pref.showPageIndicator)
            self._previewCanvas.SetGreyBackground(self.pref.greyBackground)
            self._previewCanvas.SetDebounce(self.pref.debounceRefresh)
            self._previewCanvas.SetDblClickFocus(self.pref.dblClickFocus)
            # Nota: previewMinSize è applicato dal callback _apply_prefs in SongpressFrame
            # tramite _ApplyPreviewMinSize() + _mgr.Update(), che aggiorna sia il pane AUI
            # che il main_panel. Non va gestito qui per evitare incoerenze.
        # Dimensione icone tempo
        if self.tempoIconSize16.GetValue():
            self.pref.tempoIconSize = 16
        elif self.tempoIconSize32.GetValue():
            self.pref.tempoIconSize = 32
        else:
            self.pref.tempoIconSize = 24
        # Modalità visualizzazione griglia accordi
        if self.gridModePlain.GetValue():
            self.pref.gridDisplayMode = 'plain'
        elif self.gridModeTable.GetValue():
            self.pref.gridDisplayMode = 'table'
        else:
            self.pref.gridDisplayMode = 'pipe'
        lbl = self.gridDefaultLabelCtrl.GetValue().strip()
        self.pref.gridDefaultLabel = lbl if lbl else _("Grid")
        self.pref.gridSpaceAsPipe = self.gridSpaceAsPipeCB.GetValue()

        # Simbolo musicale
        self.pref.symbolScaleEnabled = self.symbolScaleCB.GetValue()
        self.pref.symbolFontSize     = self.symbolSizeSpin.GetValue()
        self.pref.symbolInsertVerse  = self.symbolInsertVerseCB.GetValue()
        if self.gridSizeDirH.GetValue():
            self.pref.gridSizeDir = 'horizontal'
        elif self.gridSizeDirV.GetValue():
            self.pref.gridSizeDir = 'vertical'
        else:
            self.pref.gridSizeDir = 'both'
        # Beat count ({beats_time})
        self.pref.durationBeatsColourHex = self.durationBeatsHexCtrl.GetValue().strip()
        self.pref.durationBeatsSizePct   = self.durationBeatsSizeSpin.GetValue()
        self.pref.durationBeatsBold      = self.durationBeatsBoldCB.GetValue()
        if self.durationBeatsAlignLeft.GetValue():
            self.pref.durationBeatsAlign = 'left'
        elif self.durationBeatsAlignCenter.GetValue():
            self.pref.durationBeatsAlign = 'center'
        else:
            self.pref.durationBeatsAlign = 'right'
        if self.durationModeNumber.GetValue():
            self.pref.durationBeatsMode = 'number'
        elif self.durationModeDots.GetValue():
            self.pref.durationBeatsMode = 'dots'
        else:
            self.pref.durationBeatsMode = 'both'
        # Context menu visibility — scritti in pref, Save() chiama _SaveContextMenu()
        self.pref.cmUndo         = self.cmUndo.GetValue()
        self.pref.cmRedo         = self.cmRedo.GetValue()
        self.pref.cmCut          = self.cmCut.GetValue()
        self.pref.cmCopy         = self.cmCopy.GetValue()
        self.pref.cmPaste        = self.cmPaste.GetValue()
        self.pref.cmDelete       = self.cmDelete.GetValue()
        self.pref.cmConfirmDelete = self.cmConfirmDelete.GetValue()
        self.pref.cmPasteChords           = self.cmPasteChords.GetValue()
        self.pref.cmPropagateVerseChords  = self.cmPropagateVerseChords.GetValue()
        self.pref.cmPropagateChorusChords = self.cmPropagateChorusChords.GetValue()
        self.pref.cmCopyTextOnly          = self.cmCopyTextOnly.GetValue()
        self.pref.cmSelectAll    = self.cmSelectAll.GetValue()
        self.pref.cmShowIcons    = self.cmShowIcons.GetValue()
        # Visibilità icone toolbar Inserisci
        for pref_key, cb in self._tb_checkboxes.items():
            setattr(self.pref, pref_key, cb.GetValue())
        self.pref.Save()
        lang = i18n.getLang()
        l = self.GetLanguage()
        if l is not None and l != lang:
            msg = _("Language settings will be applied when you restart Songpress++.")
            d = wx.MessageDialog(
                self, msg, _("Songpress++"),
                wx.OK | wx.CANCEL | wx.ICON_INFORMATION,
            )
            d.SetOKCancelLabels(_("OK"), _("Restart now"))
            if d.ShowModal() == wx.ID_CANCEL:
                self._restart_requested = True
        # Se il pin è attivo: applica il callback senza chiudere il dialogo
        if self._pinned:
            if self._on_apply is not None:
                self._on_apply()
        else:
            evt.Skip(True)
        # Riavvio richiesto: chiude il dialogo preferenze (se ancora aperto)
        # SongpressFrame intercetterà il flag e chiamerà OnRestart.
        if self._restart_requested and not self._pinned:
            self.EndModal(wx.ID_OK)

    def OnDecoBarHexChanged(self, evt):
        c = self._hex_to_colour(self.decoBarHexCtrl.GetValue())
        self.decoBarColourSwatch.SetBackgroundColour(c)
        self.decoBarColourSwatch.Refresh()
        # Aggiorna subito tutti gli slider visibili
        self._apply_deco_bar_colour(self.decoBarHexCtrl.GetValue().strip())
        evt.Skip()

    def OnDecoBarPickColour(self, evt):
        current = self._hex_to_colour(self.decoBarHexCtrl.GetValue())
        data = wx.ColourData()
        data.SetColour(current)
        data.SetChooseFull(True)
        self._apply_custom_colours(data, 'customColoursDecoBar')
        dlg = wx.ColourDialog(self, data)
        if dlg.ShowModal() == wx.ID_OK:
            result_data = dlg.GetColourData()
            chosen = result_data.GetColour()
            self._read_custom_colours(result_data, 'customColoursDecoBar')
            self.decoBarHexCtrl.SetValue(self._colour_to_hex(chosen))
            self.decoBarColourSwatch.SetBackgroundColour(chosen)
            self.decoBarColourSwatch.Refresh()
            self._apply_deco_bar_colour(self._colour_to_hex(chosen))
        dlg.Destroy()

    def _apply_deco_bar_colour(self, hex_str):
        """Aggiorna BAR_COLOUR_FULL in MyDecoSlider e ridisegna tutti gli slider."""
        try:
            from . import MyDecoSlider as _mds
            c = self._hex_to_colour(hex_str)
            if c.IsOk():
                _mds.BAR_COLOUR_FULL = c
                for ds in self.decoSliders.values():
                    ds.panel.Refresh()
        except Exception:
            pass

    def OnPin(self, evt):
        """Toggling del pin button: mantiene il dialogo aperto dopo OK."""
        self._pinned = not self._pinned
        self.btnPin.SetLabel(u"📍" if self._pinned else u"📌")
