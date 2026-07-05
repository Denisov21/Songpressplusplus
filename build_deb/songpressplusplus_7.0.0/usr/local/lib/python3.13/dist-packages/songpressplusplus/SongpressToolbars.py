###############################################################
# Name:         SongpressToolbars.py
# Purpose:      Toolbar construction mixin for Songpress++
# Author:       Denisov21
# Created:      2026
# Copyright:    Modifications © 2026 Denisov21
# License:      GNU GPL v2
###############################################################

import wx
import wx.lib.agw.aui as aui
from wx import xrc

from .FontComboBox import FontComboBox
from .Globals import glb

_ = wx.GetTranslation


class SongpressToolbarsMixin:
    """Mixin che raccoglie la costruzione delle tre AuiToolBar di Songpress++.

    Deve essere ereditato insieme a SongpressFrame (o la sua base SDIMainFrame)
    in modo che self.frame, self.pref, self.AddPane, self.AddTool e i bind
    agli handler siano già disponibili quando _BuildToolbars() viene chiamato.

    Uso tipico nel __init__ di SongpressFrame, subito dopo la creazione dei pane
    principali::

        self._BuildToolbars()
    """

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def _BuildToolbars(self):
        """Costruisce mainToolBar, formatToolBar, insertToolBar e viewToolBar e
        le aggiunge all'AUI manager."""
        self._BuildMainToolBar()
        self._BuildFormatToolBar()
        self._BuildInsertToolBar()
        self._BuildViewToolBar()

    # ------------------------------------------------------------------
    # Standard toolbar — mappa icone/flag di visibilità
    # ------------------------------------------------------------------

    MAIN_TOOLBAR_ITEMS = [
        ('new',          _(u'New'),            'tbm_new'),
        ('open',         _(u'Open'),           'tbm_open'),
        ('save',         _(u'Save'),           'tbm_save'),
        ('printPreview', _(u'Print preview'),  'tbm_printPreview'),
        ('print',        _(u'Print'),          'tbm_print'),
        ('undo',         _(u'Undo'),           'tbm_undo'),
        ('redo',         _(u'Redo'),           'tbm_redo'),
        ('cut',          _(u'Cut'),            'tbm_cut'),
        ('copy',         _(u'Copy'),           'tbm_copy'),
        ('copyAsImage',  _(u'Copy as image'),  'tbm_copyAsImage'),
        ('paste',        _(u'Paste'),          'tbm_paste'),
        ('pasteChords',  _(u'Paste chords'),   'tbm_pasteChords'),
        ('syntaxCheck',  _(u'Check syntax'),   'tbm_syntaxCheck'),
        ('options',      _(u'Options...'),     'tbm_options'),
    ]

    _MAIN_TOOLBAR_SEPARATORS_AFTER = {
        'save', 'print', 'redo', 'pasteChords', 'syntaxCheck',
    }

    def _ApplyMainToolBarVisibility(self):
        """Ricostruisce la main toolbar rispettando i flag tbm_* in self.pref."""
        self.mainToolBar.ClearTools()

        prev_was_sep = True
        last_added = None

        for xrc_name, label, pref_key in self.MAIN_TOOLBAR_ITEMS:
            if not getattr(self.pref, pref_key, True):
                continue
            if last_added in self._MAIN_TOOLBAR_SEPARATORS_AFTER and not prev_was_sep:
                self.mainToolBar.AddSeparator()
                prev_was_sep = True
            tool = self.AddTool(self.mainToolBar, xrc_name,
                                self._main_toolbar_icons[xrc_name],
                                label,
                                self._main_toolbar_helps[xrc_name])
            # Aggiorna i riferimenti agli strumenti usati da OnIdle / UpdateUI
            if xrc_name == 'save':
                self.saveTool = tool
            elif xrc_name == 'undo':
                self.undoTool = tool
            elif xrc_name == 'redo':
                self.redoTool = tool
            elif xrc_name == 'cut':
                self.cutTool = tool
            elif xrc_name == 'copy':
                self.copyTool = tool
            elif xrc_name == 'paste':
                self.pasteTool = tool
            elif xrc_name == 'pasteChords':
                self.pasteChordsTool = tool
            elif xrc_name == 'syntaxCheck':
                self.syntaxCheckTool = tool
            prev_was_sep = False
            last_added = xrc_name

        self.mainToolBar.Realize()
        self._mgr.Update()

    # ------------------------------------------------------------------
    # Format toolbar — mappa icone/flag di visibilità
    # ------------------------------------------------------------------

    FORMAT_TOOLBAR_ITEMS = [
        ('fontChooser',       _(u'Font used in the Songpress++ preview'),      'tbf_fontChooser'),
        ('showChordsChooser', _(u'Hide or show chords in the formatted song'), 'tbf_showChords'),
        ('insertLinespacing', _(u'Linespacing'),                               'tbf_insertLinespacing'),
    ]

    _FORMAT_TOOLBAR_SEPARATORS_AFTER = {'showChordsChooser'}

    def _ApplyFormatToolBarVisibility(self):
        """Ricostruisce la format toolbar in base ai flag tbf_* in self.pref.

        AuiToolBar non gestisce in modo affidabile Show/Hide sui controlli
        custom (FontComboBox, Slider) aggiunti via AddControl: l'unico approccio
        robusto è distruggere i controlli esistenti e ricrearli, esattamente come
        fanno _ApplyMainToolBarVisibility e _ApplyInsertToolBarVisibility.
        """
        show_font   = getattr(self.pref, 'tbf_fontChooser',       True)
        show_chords = getattr(self.pref, 'tbf_showChords',         True)
        show_ls     = getattr(self.pref, 'tbf_insertLinespacing',  True)

        # Salva il valore corrente di fontChooser e showChordsChooser
        # prima di distruggerli, per poterlo ripristinare dopo.
        saved_font_face   = self.pref.format.face
        saved_show_chords = self.pref.format.showChords

        # Distrugge i controlli custom (FontComboBox e Slider) prima di
        # ClearTools, altrimenti restano orfani nella toolbar.
        for ctrl in getattr(self, '_format_font_controls', []):
            ctrl.Destroy()
        self._format_font_controls = []
        for ctrl in getattr(self, '_format_chords_controls', []):
            ctrl.Destroy()
        self._format_chords_controls = []

        self.formatToolBar.ClearTools()

        # ── Carattere ─────────────────────────────────────────────────
        if show_font:
            fontIcon = wx.StaticBitmap(
                self.formatToolBar, -1,
                wx.Bitmap(wx.Image(glb.AddPath('img/font1.png')))
            )
            fontIcon.SetToolTip(_("Font used in the Songpress++ preview"))
            self.formatToolBar.AddControl(fontIcon)
            self.fontChooser = FontComboBox(self.formatToolBar, -1, saved_font_face)
            self.fontChooser.SetToolTip(_("Font used in the Songpress++ preview"))
            self.formatToolBar.AddControl(self.fontChooser)
            self.frame.Bind(wx.EVT_COMBOBOX,        self.OnFontSelected, self.fontChooser)
            self.fontChooser.Bind(wx.EVT_TEXT_ENTER, self.OnFontSelected, self.fontChooser)
            self.fontChooser.Bind(wx.EVT_KILL_FOCUS, self.OnFontSelected, self.fontChooser)
            self._format_font_controls = [fontIcon, self.fontChooser]
        else:
            # fontChooser non esiste più: crea un dummy non visibile per
            # non rompere il codice che chiama self.fontChooser.SetValue()
            self.fontChooser = FontComboBox(self.formatToolBar, -1, saved_font_face)
            self.fontChooser.Hide()
            self._format_font_controls = []

        # ── Mostra/nascondi accordi ────────────────────────────────────
        if show_chords:
            showChordsIcon = wx.StaticBitmap(
                self.formatToolBar, -1,
                wx.Bitmap(wx.Image(glb.AddPath('img/showChords.png')))
            )
            self.formatToolBar.AddControl(showChordsIcon)
            self.showChordsChooser = wx.Slider(
                self.formatToolBar, -1, saved_show_chords, 0, 2,
                wx.DefaultPosition, (100, 32),
                wx.SL_AUTOTICKS | wx.SL_HORIZONTAL
            )
            tt1 = wx.ToolTip(_("Hide or show chords in the formatted song"))
            tt2 = wx.ToolTip(_("Hide or show chords in the formatted song"))
            self.showChordsChooser.SetToolTip(tt1)
            showChordsIcon.SetToolTip(tt2)
            self.frame.Bind(wx.EVT_SCROLL, self.OnFontSelected, self.showChordsChooser)
            self.formatToolBar.AddControl(self.showChordsChooser, "pippo")
            self._format_chords_controls = [showChordsIcon, self.showChordsChooser]
        else:
            # showChordsChooser non esiste più: dummy nascosto
            self.showChordsChooser = wx.Slider(
                self.formatToolBar, -1, saved_show_chords, 0, 2,
                wx.DefaultPosition, (100, 32),
                wx.SL_AUTOTICKS | wx.SL_HORIZONTAL
            )
            self.showChordsChooser.Hide()
            self._format_chords_controls = []

        # ── Interlinea ─────────────────────────────────────────────────
        if show_font or show_chords:
            self.formatToolBar.AddSeparator()
        if show_ls:
            self.AddTool(self.formatToolBar, 'insertLinespacing', 'img/line_spacing.png',
                         _(u"Linespacing"), _(u"Insert a {linespacing} command"))

        self.formatToolBar.Realize()
        self._mgr.Update()

    # ------------------------------------------------------------------
    # Main toolbar  (Standard)
    # ------------------------------------------------------------------

    def _BuildMainToolBar(self):
        self.mainToolBar = aui.AuiToolBar(
            self.frame, wx.ID_ANY, wx.DefaultPosition,
            agwStyle=aui.AUI_TB_PLAIN_BACKGROUND
        )
        self.mainToolBar.SetToolBitmapSize(wx.Size(16, 16))

        self._main_toolbar_icons = {
            'new':          'img/new.png',
            'open':         'img/open.png',
            'save':         'img/save.png',
            'printPreview': 'img/printPreview.png',
            'print':        'img/print.png',
            'undo':         'img/undo.png',
            'redo':         'img/redo.png',
            'cut':          'img/cut.png',
            'copy':         'img/copy.png',
            'copyAsImage':  'img/copyAsImage2.png',
            'paste':        'img/paste.png',
            'pasteChords':  'img/pasteChords.png',
            'syntaxCheck':  'img/syntaxCheck.png',
            'options':      'img/setting.png',
        }
        self._main_toolbar_helps = {
            'new':          _("Create a new song"),
            'open':         _("Open an existing song"),
            'save':         _("Save the song with the current file name"),
            'printPreview': _(u"Preview the song before printing"),
            'print':        _(u"Print the song"),
            'undo':         _("Undo the last change"),
            'redo':         _("Redo the last undone change"),
            'cut':          _("Move selected text to the clipboard"),
            'copy':         _("Copy selected text to the clipboard"),
            'copyAsImage':  _("Copy the entire FORMATTED song (or selected verses) to the clipboard"),
            'paste':        _("Read text from the clipboard and insert it at the cursor position"),
            'pasteChords':  _("Merge chords from the copied text into the current selection"),
            'syntaxCheck':  _("Check ChordPro syntax of the document"),
            'options':      _(u"Set program options"),
        }

        # copyOnlyText è solo un ID menu, non un tool nella toolbar
        self.copyOnlyTextTool = wx.xrc.XRCID('copyOnlyText')

        self._ApplyMainToolBarVisibility()

        self.mainToolBarPane = self.AddPane(
            self.mainToolBar,
            aui.AuiPaneInfo().ToolbarPane().Top().Row(1).Position(1),
            _('Standard'), 'standard'
        )

    # ------------------------------------------------------------------
    # Format toolbar
    # ------------------------------------------------------------------

    def _BuildFormatToolBar(self):
        self.formatToolBar = aui.AuiToolBar(
            self.frame, wx.ID_ANY, wx.DefaultPosition,
            agwStyle=aui.AUI_TB_PLAIN_BACKGROUND
        )
        self.formatToolBar.SetToolBitmapSize(wx.Size(16, 16))
        self.formatToolBar.SetExtraStyle(aui.AUI_TB_PLAIN_BACKGROUND)

        # Font chooser
        fontIcon = wx.StaticBitmap(
            self.formatToolBar, -1,
            wx.Bitmap(wx.Image(glb.AddPath('img/font1.png')))
        )
        fontIcon.SetToolTip(_("Font used in the Songpress++ preview"))
        self.formatToolBar.AddControl(fontIcon)
        self.fontChooser = FontComboBox(self.formatToolBar, -1, self.pref.format.face)
        self.fontChooser.SetToolTip(_("Font used in the Songpress++ preview"))
        self.formatToolBar.AddControl(self.fontChooser)
        self.frame.Bind(wx.EVT_COMBOBOX,    self.OnFontSelected, self.fontChooser)
        self.fontChooser.Bind(wx.EVT_TEXT_ENTER, self.OnFontSelected, self.fontChooser)
        self.fontChooser.Bind(wx.EVT_KILL_FOCUS, self.OnFontSelected, self.fontChooser)
        # Teniamo i riferimenti per Show/Hide
        self._format_font_controls = [fontIcon, self.fontChooser]

        # Binding globali legati al format toolbar (non puramente al controllo)
        wx.UpdateUIEvent.SetUpdateInterval(500)
        self.frame.Bind(wx.EVT_UPDATE_UI,  self.OnIdle,        self.frame)
        self.frame.Bind(wx.EVT_TEXT_CUT,   self.OnTextCutCopy, self.text)
        self.frame.Bind(wx.EVT_TEXT_COPY,  self.OnTextCutCopy, self.text)

        # Show-chords slider
        showChordsIcon = wx.StaticBitmap(
            self.formatToolBar, -1,
            wx.Bitmap(wx.Image(glb.AddPath('img/showChords.png')))
        )
        self.formatToolBar.AddControl(showChordsIcon)
        self.showChordsChooser = wx.Slider(
            self.formatToolBar, -1, 0, 0, 2,
            wx.DefaultPosition, (100, 32), #permette di modifica l'altezza della barra secondo valore!!!
            wx.SL_AUTOTICKS | wx.SL_HORIZONTAL
        )
        tt1 = wx.ToolTip(_("Hide or show chords in the formatted song"))
        tt2 = wx.ToolTip(_("Hide or show chords in the formatted song"))
        self.showChordsChooser.SetToolTip(tt1)
        showChordsIcon.SetToolTip(tt2)
        self.frame.Bind(wx.EVT_SCROLL, self.OnFontSelected, self.showChordsChooser)
        self.formatToolBar.AddControl(self.showChordsChooser, "pippo")
        # Teniamo i riferimenti per Show/Hide
        self._format_chords_controls = [showChordsIcon, self.showChordsChooser]

        self.formatToolBar.AddSeparator()
        self.AddTool(self.formatToolBar, 'insertLinespacing', 'img/line_spacing.png',
                     _(u"Linespacing"), _(u"Insert a {linespacing} command"))

        self.formatToolBar.Realize()
        self.formatToolBar.SetMinSize(self.mainToolBar.GetMinSize())
        self.formatToolBarPane = self.AddPane(
            self.formatToolBar,
            aui.AuiPaneInfo().ToolbarPane().Top().Row(1).Position(2),
            _('Format'), 'format'
        )

    # ------------------------------------------------------------------
    # Insert toolbar — mappa icone/flag di visibilità
    # ------------------------------------------------------------------

    # Ogni voce: (xrc_name, label_i18n, pref_key)
    # pref_key è il nome dell'attributo booleano in self.pref (default True).
    INSERT_TOOLBAR_ITEMS = [
        ('title',                             _(u'Title'),                                              'tb_title'),
        ('subtitle',                          _(u'Subtitle'),                                           'tb_subtitle'),
        ('chord',                             _(u'Chord...'),                                           'tb_chord'),
        ('chorus',                            _(u'Chorus...'),                                          'tb_chorus'),
        ('verseWithCustomLabelOrWithoutLabel',_(u'Verse with custom label or without label...'),        'tb_verse'),
        ('comment',                           _(u'Comment...'),                                         'tb_comment'),
        ('insertPageBreak',                   _(u'Page break'),                         'tb_pageBreak'),
        ('insertColumnBreak',                 _(u'Column break'),                       'tb_columnBreak'),
        ('insertVerse',                       _(u'Unnumbered verse {start_verse}\\{end_verse}'),          'tb_insertVerse'),
        ('insertVerseNum',                    _(u'Numbered verse {start_verse_num}\\{end_verse_num}'),    'tb_insertVerseNum'),
        ('insertChorusBlock',                 _(u'Chorus {start_chorus}\\{end_chorus}...'),               'tb_insertChorusBlock'),
        ('insertChordBlock',                  _(u'Intro chords {start_chord}\\{end_chord}...'),           'tb_insertChordBlock'),
        ('insertBridge',                      _(u'Bridge {start_bridge}\\{end_bridge}...'),               'tb_insertBridge'),
        ('insertGrid',                        _(u'Grid {start_of_grid}\\{end_of_grid}...'),               'tb_insertGrid'),
        ('insertTempo',                       _(u'Tempo {tempo:}...'),                                    'tb_insertTempo'),
        ('insertTempoLabel',                  _(u'Tempo marking {tempo_label:}...'),                      'tb_insertTempoLabel'),
        ('insertTime',                        _(u'Time signature {time:}...'),                            'tb_insertTime'),
        ('insertKey',                         _(u'Key {key:}'),                                           'tb_insertKey'),
        ('insertDuration',                    _(u'Duration {beats_time:}...'),                            'tb_insertDuration'),
        ('insertTaste',                       _(u'Chord keyboard {taste:}...'),                           'tb_insertTaste'),
        ('insertFingering',                   _(u'First chord fingering {fingering:}...'),                'tb_insertFingering'),
        ('insertDefine',                      _(u'Guitar chord diagram {define:}...'),                    'tb_insertDefine'),
        ('insertImage',                       _(u'Image {image:}...'),                                    'tb_insertImage'),
        ('insertTransposerImage',             _(u'Transposer image {start_of_tab:TP}\\{end_of_tab}'),     'tb_insertTransposerImage'),
        ('insertMusicalSymbol',               _(u'Musical symbol (Unicode)'),                             'tb_insertMusicalSymbol'),
    ]

    # Separatori: dopo quale xrc_name inserire un separatore
    _INSERT_TOOLBAR_SEPARATORS_AFTER = {
        'comment', 'insertColumnBreak', 'insertGrid',
        'insertDuration', 'insertDefine',
    }

    def _ApplyInsertToolBarVisibility(self):
        """Ricostruisce la insert toolbar mostrando solo i tool con pref.tb_* == True.

        AuiToolBar non supporta Show/Hide per singola icona: l'unico modo
        affidabile è cancellare tutti i tool e reinserire quelli visibili.
        """
        self.insertToolBar.ClearTools()

        prev_was_separator = True   # evita separatore iniziale
        last_added_xrc = None

        for xrc_name, label, pref_key in self.INSERT_TOOLBAR_ITEMS:
            visible = getattr(self.pref, pref_key, True)
            if not visible:
                continue

            # Separatore prima del gruppo (se necessario)
            # Il separatore viene aggiunto *prima* del primo elemento del nuovo
            # gruppo, non dopo l'ultimo del gruppo precedente, così non restano
            # separatori finali orphan quando tutti gli elementi di un gruppo
            # sono nascosti.
            needs_sep = (last_added_xrc in self._INSERT_TOOLBAR_SEPARATORS_AFTER)
            if needs_sep and not prev_was_separator:
                self.insertToolBar.AddSeparator()
                prev_was_separator = True

            self.AddTool(self.insertToolBar, xrc_name,
                         self._insert_toolbar_icons[xrc_name],
                         label,
                         self._insert_toolbar_helps[xrc_name])
            prev_was_separator = False
            last_added_xrc = xrc_name

        self.insertToolBar.Realize()
        self._mgr.Update()

    # ------------------------------------------------------------------
    # Insert toolbar
    # ------------------------------------------------------------------

    def _BuildInsertToolBar(self):
        self.insertToolBar = aui.AuiToolBar(
            self.frame, wx.ID_ANY, wx.DefaultPosition,
            agwStyle=aui.AUI_TB_PLAIN_BACKGROUND
        )
        self.insertToolBar.SetToolBitmapSize(wx.Size(16, 16))

        # Dizionari icon-path e help per ogni tool: usati da _ApplyInsertToolBarVisibility
        # per ricostruire la toolbar quando la visibilità cambia.
        self._insert_toolbar_icons = {
            'title':                             'img/title.png',
            'subtitle':                          'img/subtitle.png',
            'chord':                             'img/chord.png',
            'chorus':                            'img/chorus.png',
            'verseWithCustomLabelOrWithoutLabel':'img/verse.png',
            'comment':                           'img/comment.png',
            'insertPageBreak':                   'img/new_page.png',
            'insertColumnBreak':                 'img/column.png',
            'insertVerse':                       'img/verse_un_num.png',
            'insertVerseNum':                    'img/verse_num.png',
            'insertChorusBlock':                 'img/repeat.png',
            'insertChordBlock':                  'img/chord_intro.png',
            'insertBridge':                      'img/bridge.png',
            'insertGrid':                        'img/grid.png',
            'insertTempo':                       'img/metronome.png',
            'insertTempoLabel':                  'img/agogic.png',
            'insertTime':                        'img/time.png',
            'insertKey':                         'img/key.png',
            'insertDuration':                    'img/beats.png',
            'insertTaste':                       'img/taste.png',
            'insertFingering':                   'img/taste2.png',
            'insertDefine':                      'img/guitar.png',
            'insertImage':                       'img/picture.png',
            'insertTransposerImage':             'img/transposer.png',
            'insertMusicalSymbol':               'img/symbol.png',
        }
        self._insert_toolbar_helps = {
            'title':                             _(u"Insert a command to display the song title"),
            'subtitle':                          _(u"Insert a command to display the song subtitle"),
            'chord':                             _(u"Insert square brackets that will contain a chord"),
            'chorus':                            _(u"Insert a pair of commands that will contain the chorus"),
            'verseWithCustomLabelOrWithoutLabel':_(u"Insert a verse with a custom label or without label"),
            'comment':                           _(u"Insert a command to display a comment"),
            'insertPageBreak':                   _(u"Insert an explicit page break for printing"),
            'insertColumnBreak':                 _(u"Insert a column break"),
            'insertVerse':                       _(u"Insert an unnumbered verse {start_verse}\\{end_verse}"),
            'insertVerseNum':                    _(u"Insert a numbered verse {start_verse_num}\\{end_verse_num}"),
            'insertChorusBlock':                 _(u"Insert a chorus block {start_chorus}\\{end_chorus}"),
            'insertChordBlock':                  _(u"Insert an intro chord section {start_chord}\\{end_chord}"),
            'insertBridge':                      _(u"Insert a bridge block {start_bridge}\\{end_bridge}"),
            'insertGrid':                        _(u"Insert a chord grid block {start_of_grid}\\{end_of_grid}"),
            'insertTempo':                       _(u"Insert a {tempo:} command"),
            'insertTempoLabel':                  _(u"Insert a {tempo_label:} command"),
            'insertTime':                        _(u"Insert a {time:} command"),
            'insertKey':                         _(u"Insert a {key:} command"),
            'insertDuration':                    _(u"Insert a {beats_time:} command"),
            'insertTaste':                       _(u"Insert a chord keyboard {taste:}"),
            'insertFingering':                   _(u"Insert a {fingering:} command"),
            'insertDefine':                      _(u"Insert a {define:} command"),
            'insertImage':                       _(u"Insert an image (PNG, JPG, GIF) into the song"),
            'insertTransposerImage':             _(u"Insert the Transposer image and choose its position in the document"),
            'insertMusicalSymbol':               _(u"Insert a Unicode musical symbol"),
        }

        # Costruisce i tool rispettando la visibilità corrente
        self._ApplyInsertToolBarVisibility()

        self.insertToolBarPane = self.AddPane(
            self.insertToolBar,
            aui.AuiPaneInfo().ToolbarPane().Top().Row(1).Position(3),
            _('Insert'), 'insert'
        )

    # ------------------------------------------------------------------
    # View toolbar  (Visualizza)
    # ------------------------------------------------------------------

    VIEW_TOOLBAR_ITEMS = [
        ('preview',    _(u'Show Songpress++ Preview'),    'tbv_preview'),
        ('labelVerses',_(u'Show verse and chorus labels'),'tbv_labelVerses'),
    ]

    def _ApplyViewToolBarVisibility(self):
        """Ricostruisce la view toolbar rispettando i flag tbv_* in self.pref.

        I tool della view toolbar sono toggle, non normali: vanno reinseriti con
        AddToggleTool. Salviamo lo stato toggle corrente per ripristinarlo.
        """
        # Salva lo stato corrente dei toggle prima di cancellare
        _toggle_states = {}
        for xrc_name, _label, _pref_key in self.VIEW_TOOLBAR_ITEMS:
            tid = wx.xrc.XRCID(xrc_name)
            item = self.viewToolBar.FindTool(tid)
            if item is not None:
                _toggle_states[xrc_name] = self.viewToolBar.GetToolToggled(tid)

        self.viewToolBar.ClearTools()

        for xrc_name, label, pref_key in self.VIEW_TOOLBAR_ITEMS:
            if not getattr(self.pref, pref_key, True):
                continue
            icon_path = self._view_toolbar_icons[xrc_name]
            tool = self.viewToolBar.AddToggleTool(
                wx.xrc.XRCID(xrc_name),
                wx.Bitmap(wx.Image(glb.AddPath(icon_path))),
                wx.NullBitmap,
                True,
                None,
                label,
                self._view_toolbar_helps[xrc_name],
            )
            # Ripristina bind e riferimento per il toggle preview
            if xrc_name == 'preview':
                self.togglePreviewViewToolId = tool.GetId()
                self.frame.Bind(wx.EVT_TOOL, self.OnTogglePaneView,
                                id=self.togglePreviewViewToolId)
            elif xrc_name == 'labelVerses':
                self.labelVersesViewToolId = tool.GetId()
            # Ripristina lo stato toggle se era già impostato
            if xrc_name in _toggle_states:
                self.viewToolBar.ToggleTool(wx.xrc.XRCID(xrc_name),
                                            _toggle_states[xrc_name])

        self.viewToolBar.Realize()
        self._mgr.Update()

    def _BuildViewToolBar(self):
        self.viewToolBar = aui.AuiToolBar(
            self.frame, wx.ID_ANY, wx.DefaultPosition,
            agwStyle=aui.AUI_TB_PLAIN_BACKGROUND
        )
        self.viewToolBar.SetToolBitmapSize(wx.Size(16, 16))

        self._view_toolbar_icons = {
            'preview':    'img/preview.png',
            'labelVerses':'img/labelVerses.png',
        }
        self._view_toolbar_helps = {
            'preview':    _(u"Show or hide the Songpress++ Preview panel"),
            'labelVerses':_(u"Show or hide verse and chorus labels"),
        }

        # Toggle "Mostra anteprima Songpress++"
        togglePreviewViewTool = self.viewToolBar.AddToggleTool(
            wx.xrc.XRCID('preview'),
            wx.Bitmap(wx.Image(glb.AddPath("img/preview.png"))),
            wx.NullBitmap,
            True,
            None,
            _("Show Songpress++ Preview"),
            _("Show or hide the Songpress++ Preview panel"),
        )
        self.togglePreviewViewToolId = togglePreviewViewTool.GetId()
        self.frame.Bind(wx.EVT_TOOL, self.OnTogglePaneView, id=self.togglePreviewViewToolId)

        # Toggle "Mostra le etichette delle strofe e ritornelli"
        labelVersesViewTool = self.viewToolBar.AddToggleTool(
            wx.xrc.XRCID('labelVerses'),
            wx.Bitmap(wx.Image(glb.AddPath("img/labelVerses.png"))),
            wx.NullBitmap,
            True,
            None,
            _("Show verse and chorus labels"),
            _("Show or hide verse and chorus labels"),
        )
        self.labelVersesViewToolId = labelVersesViewTool.GetId()

        self.viewToolBar.Realize()
        self.viewToolBarPane = self.AddPane(
            self.viewToolBar,
            aui.AuiPaneInfo().ToolbarPane().Top().Row(1).Position(4),
            _('View'), 'view'
        )
