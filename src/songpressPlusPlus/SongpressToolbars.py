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
    # Main toolbar  (Standard)
    # ------------------------------------------------------------------

    def _BuildMainToolBar(self):
        self.mainToolBar = aui.AuiToolBar(
            self.frame, wx.ID_ANY, wx.DefaultPosition,
            agwStyle=aui.AUI_TB_PLAIN_BACKGROUND
        )
        self.mainToolBar.SetToolBitmapSize(wx.Size(16, 16))

        self.AddTool(self.mainToolBar, 'new',  'img/new.png',  _("New"),  _("Create a new song"))
        self.AddTool(self.mainToolBar, 'open', 'img/open.png', _("Open"), _("Open an existing song"))
        self.saveTool = self.AddTool(
            self.mainToolBar, 'save', 'img/save.png',
            _("Save"), _("Save the song with the current file name")
        )
        self.mainToolBar.AddSeparator()
        self.AddTool(self.mainToolBar, 'printPreview', 'img/printPreview.png',
                     _(u"Print preview"), _(u"Preview the song before printing"))
        self.AddTool(self.mainToolBar, 'print', 'img/print.png',
                     _(u"Print"), _(u"Print the song"))
        self.mainToolBar.AddSeparator()
        self.undoTool = self.AddTool(
            self.mainToolBar, 'undo', 'img/undo.png',
            _("Undo"), _("Undo the last change")
        )
        self.redoTool = self.AddTool(
            self.mainToolBar, 'redo', 'img/redo.png',
            _("Redo"), _("Redo the last undone change")
        )
        self.mainToolBar.AddSeparator()
        self.cutTool = self.AddTool(
            self.mainToolBar, 'cut', 'img/cut.png',
            _("Cut"), _("Move selected text to the clipboard")
        )
        self.copyTool = self.AddTool(
            self.mainToolBar, 'copy', 'img/copy.png',
            _("Copy"), _("Copy selected text to the clipboard")
        )
        self.copyOnlyTextTool = wx.xrc.XRCID('copyOnlyText')
        self.AddTool(
            self.mainToolBar, 'copyAsImage', 'img/copyAsImage2.png',
            _("Copy as image"),
            _("Copy the entire FORMATTED song (or selected verses) to the clipboard")
        )
        self.pasteTool = self.AddTool(
            self.mainToolBar, 'paste', 'img/paste.png',
            _("Paste"),
            _("Read text from the clipboard and insert it at the cursor position")
        )
        self.pasteChordsTool = self.AddTool(
            self.mainToolBar, 'pasteChords', 'img/pasteChords.png',
            _("Paste chords"),
            _("Merge chords from the copied text into the current selection")
        )
        self.mainToolBar.AddSeparator()
        self.syntaxCheckTool = self.AddTool(
            self.mainToolBar, 'syntaxCheck', 'img/syntaxCheck.png',
            _("Check syntax"),
            _("Check ChordPro syntax of the document")
        )
        self.mainToolBar.AddSeparator()
        self.AddTool(self.mainToolBar, 'options', 'img/setting.png',
                     _(u"Options..."), _(u"Set program options"))

        self.mainToolBar.Realize()
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
    # Insert toolbar
    # ------------------------------------------------------------------

    def _BuildInsertToolBar(self):
        self.insertToolBar = aui.AuiToolBar(
            self.frame, wx.ID_ANY, wx.DefaultPosition,
            agwStyle=aui.AUI_TB_PLAIN_BACKGROUND
        )
        self.insertToolBar.SetToolBitmapSize(wx.Size(16, 16))

        self.AddTool(self.insertToolBar, 'title',    'img/title.png',    _(u"Insert title"),    _(u"Insert a command to display the song title"))
        self.AddTool(self.insertToolBar, 'subtitle', 'img/subtitle.png', _(u"Insert subtitle"), _(u"Insert a command to display the song subtitle"))
        self.AddTool(self.insertToolBar, 'chord',    'img/chord.png',    _(u"Insert chord"),    _(u"Insert square brackets that will contain a chord"))
        self.AddTool(self.insertToolBar, 'chorus',   'img/chorus.png',   _(u"Insert chorus"),   _(u"Insert a pair of commands that will contain the chorus"))
        self.AddTool(self.insertToolBar, 'verseWithCustomLabelOrWithoutLabel',
                     'img/verse.png',
                     _(u"Insert verse with custom label or without label"),
                     _(u"Insert a verse with a custom label or without label"))
        self.AddTool(self.insertToolBar, 'comment', 'img/comment.png',
                     _(u"Insert comment"), _(u"Insert a command to display a comment"))
        self.insertToolBar.AddSeparator()

        self.AddTool(self.insertToolBar, 'insertPageBreak',   'img/new_page.png',
                     _(u"Page break"),   _(u"Insert an explicit page break for printing"))
        self.AddTool(self.insertToolBar, 'insertColumnBreak', 'img/column.png',
                     _(u"Column break"), _(u"Insert a column break"))
        self.insertToolBar.AddSeparator()

        self.AddTool(self.insertToolBar, 'insertVerse',       'img/verse_un_num.png',
                     _(u"Unnumbered verse"),  _(u"Insert an unnumbered verse {start_verse}\\{end_verse}"))
        self.AddTool(self.insertToolBar, 'insertVerseNum',    'img/verse_num.png',
                     _(u"Numbered verse"),    _(u"Insert a numbered verse {start_verse_num}\\{end_verse_num}"))
        self.AddTool(self.insertToolBar, 'insertChorusBlock', 'img/repeat.png',
                     _(u"Chorus block"),      _(u"Insert a chorus block {start_chorus}\\{end_chorus}"))
        self.AddTool(self.insertToolBar, 'insertChordBlock',  'img/chord_intro.png',
                     _(u"Intro chords"),      _(u"Insert an intro chord section {start_chord}\\{end_chord}"))
        self.AddTool(self.insertToolBar, 'insertGrid',        'img/grid.png',
                     _(u"Grid"),              _(u"Insert a chord grid block {start_of_grid}\\{end_of_grid}"))
        self.insertToolBar.AddSeparator()

        self.AddTool(self.insertToolBar, 'insertTempo',    'img/metronome.png',
                     _(u"Tempo"),          _(u"Insert a {tempo:} command"))
        self.AddTool(self.insertToolBar, 'insertTime',     'img/time.png',
                     _(u"Time signature"), _(u"Insert a {time:} command"))
        self.AddTool(self.insertToolBar, 'insertKey',      'img/key.png',
                     _(u"Key"),            _(u"Insert a {key:} command"))
        self.AddTool(self.insertToolBar, 'insertDuration', 'img/beats.png',
                     _(u"Duration"),       _(u"Insert a {beats_time:} command"))
        self.insertToolBar.AddSeparator()

        self.AddTool(self.insertToolBar, 'insertTaste',     'img/taste.png',
                     _(u"Chord keyboard"),      _(u"Insert a chord keyboard {taste:}"))
        self.AddTool(self.insertToolBar, 'insertFingering', 'img/taste2.png',
                     _(u"First chord fingering"), _(u"Insert a {fingering:} command"))
        self.AddTool(self.insertToolBar, 'insertDefine',    'img/guitar.png',
                     _(u"Guitar chord diagram"), _(u"Insert a {define:} command"))
        self.insertToolBar.AddSeparator()

        self.AddTool(self.insertToolBar, 'insertImage',           'img/picture.png',
                     _(u"Image"),            _(u"Insert an image (PNG, JPG, GIF) into the song"))
        self.AddTool(self.insertToolBar, 'insertTransposerImage', 'img/transposer.png',
                     _(u"Transposer image"), _(u"Insert the Transposer image and choose its position in the document"))
        self.AddTool(self.insertToolBar, 'insertMusicalSymbol',   'img/symbol.png',
                     _(u"Musical symbol (Unicode)"), _(u"Insert a Unicode musical symbol"))

        self.insertToolBar.Realize()
        self.insertToolBarPane = self.AddPane(
            self.insertToolBar,
            aui.AuiPaneInfo().ToolbarPane().Top().Row(1).Position(3),
            _('Insert'), 'insert'
        )

    # ------------------------------------------------------------------
    # View toolbar  (Visualizza)
    # ------------------------------------------------------------------

    def _BuildViewToolBar(self):
        self.viewToolBar = aui.AuiToolBar(
            self.frame, wx.ID_ANY, wx.DefaultPosition,
            agwStyle=aui.AUI_TB_PLAIN_BACKGROUND
        )
        self.viewToolBar.SetToolBitmapSize(wx.Size(16, 16))

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
